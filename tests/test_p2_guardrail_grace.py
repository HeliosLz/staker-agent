"""Tests for P2: tool guardrail, smart compression, and grace call."""
from __future__ import annotations

import json
import os
import sys
from queue import Queue
from types import SimpleNamespace

import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

WEB_BACKEND = os.path.join(BASE_DIR, "web", "backend")
if WEB_BACKEND not in sys.path:
    sys.path.insert(0, WEB_BACKEND)


# ---------------------------------------------------------------------------
# Stream helpers
# ---------------------------------------------------------------------------

def _content_stream(text: str):
    return [
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content=text, tool_calls=None),
                )
            ]
        )
    ]


def _tool_stream(name: str, arguments: str, tool_id: str = "call_1"):
    return [
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(
                        content=None,
                        tool_calls=[
                            SimpleNamespace(
                                index=0,
                                id=tool_id,
                                function=SimpleNamespace(name=name, arguments=arguments),
                            )
                        ],
                    ),
                )
            ]
        )
    ]


class _FakeClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create),
        )

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class _Recorder:
    def __init__(self, agent_mod):
        self.text = []
        self.errors = []
        self.tool_starts = []
        self.tool_results = []
        self.mnemonics = []
        self.completed = 0
        self.callbacks = agent_mod.TransportCallbacks(
            on_text_delta=self.text.append,
            on_error=self.errors.append,
            on_tool_start=lambda name, inp, tid: self.tool_starts.append((name, inp, tid)),
            on_tool_result=lambda name, tid, result, success: self.tool_results.append(
                (name, tid, result, success)
            ),
            on_mnemonic=self.mnemonics.append,
            on_turn_complete=self._complete,
        )

    def _complete(self):
        self.completed += 1


def _fake_services():
    return SimpleNamespace(
        deployment=SimpleNamespace(eth_docker_path="/tmp/eth-docker"),
        agent_state=None,
        monitor_loop=None,
        notif_queue=Queue(),
        memory_store=None,
        message_composer=None,
    )


@pytest.fixture()
def agent_mod(monkeypatch):
    from staker_backend.services import agent as mod

    with mod._sessions_lock:
        mod._sessions.clear()
    monkeypatch.setattr(mod.time, "sleep", lambda _delay: None)
    yield mod
    monkeypatch.setattr(mod, "_client", None)
    with mod._sessions_lock:
        mod._sessions.clear()


# ---------------------------------------------------------------------------
# Smart compression
# ---------------------------------------------------------------------------

class TestSummarizeToolResult:
    def test_preserves_key_fields(self, agent_mod):
        data = {
            "success": True,
            "status": "running",
            "health_level": "HEALTHY",
            "network": "holesky",
        }
        summary = agent_mod._summarize_tool_result(data)
        assert "[Compacted: OK]" in summary
        assert "status=running" in summary
        assert "health_level=HEALTHY" in summary
        assert "network=holesky" in summary

    def test_preserves_error_on_failure(self, agent_mod):
        data = {"success": False, "error": "Docker daemon not found"}
        summary = agent_mod._summarize_tool_result(data)
        assert "[Compacted: FAIL]" in summary
        assert "Docker daemon not found" in summary

    def test_truncates_long_values(self, agent_mod):
        data = {"success": True, "error": "x" * 200}
        summary = agent_mod._summarize_tool_result(data)
        assert "..." in summary
        assert len(summary) < 200

    def test_micro_compact_uses_summarize(self, agent_mod):
        history = [
            {"role": "tool", "tool_call_id": "t1", "content": json.dumps({
                "success": True, "status": "running", "data": "x" * 300,
            })},
            {"role": "tool", "tool_call_id": "t2", "content": json.dumps({
                "success": False, "error": "connection refused", "data": "y" * 300,
            })},
            {"role": "tool", "tool_call_id": "t3", "content": json.dumps({"success": True})},
            {"role": "tool", "tool_call_id": "t4", "content": json.dumps({"success": True})},
            {"role": "tool", "tool_call_id": "t5", "content": json.dumps({"success": True})},
        ]
        agent_mod._micro_compact(history)
        assert "status=running" in history[0]["content"]
        assert "connection refused" in history[1]["content"]
        assert history[2]["content"] == json.dumps({"success": True})


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    def test_tool_blocked_after_consecutive_failures(self, agent_mod, monkeypatch):
        execute_count = 0

        def _counting_execute(name, tool_input, ctx):
            nonlocal execute_count
            execute_count += 1
            return {"success": False, "error": "Docker not running"}

        monkeypatch.setattr(agent_mod, "execute_tool", _counting_execute)

        limit = agent_mod.TOOL_CONSECUTIVE_FAIL_LIMIT
        outcomes = []
        for i in range(limit + 1):
            outcomes.append(_tool_stream("restart_service", '{"service":"execution"}', f"call_{i}"))
        outcomes.append(_content_stream("giving up"))
        client = _FakeClient(outcomes)
        monkeypatch.setattr(agent_mod, "_client", client)

        recorder = _Recorder(agent_mod)
        agent_mod.run_agent_turn_cb("restart", _fake_services(), "p2-cb", recorder.callbacks)

        assert execute_count == limit
        last_name, last_tid, last_result, last_success = recorder.tool_results[-1]
        assert last_result["error_type"] == "circuit_breaker"
        assert last_success is False

    def test_success_resets_fail_streak(self, agent_mod, monkeypatch):
        call_num = 0

        def _alternating_execute(name, tool_input, ctx):
            nonlocal call_num
            call_num += 1
            if call_num <= 2:
                return {"success": False, "error": "flaky"}
            return {"success": True, "data": "ok"}

        monkeypatch.setattr(agent_mod, "execute_tool", _alternating_execute)

        outcomes = [
            _tool_stream("check_environment", "{}", "call_1"),
            _tool_stream("check_environment", "{}", "call_2"),
            _tool_stream("check_environment", "{}", "call_3"),
            _content_stream("done"),
        ]
        client = _FakeClient(outcomes)
        monkeypatch.setattr(agent_mod, "_client", client)

        recorder = _Recorder(agent_mod)
        agent_mod.run_agent_turn_cb("check", _fake_services(), "p2-reset", recorder.callbacks)

        assert recorder.errors == []
        assert call_num == 3
        assert all(r[2].get("error_type") != "circuit_breaker" for r in recorder.tool_results)


# ---------------------------------------------------------------------------
# Grace call
# ---------------------------------------------------------------------------

class TestGraceCall:
    def test_grace_turn_omits_tools(self, agent_mod, monkeypatch):
        monkeypatch.setattr(agent_mod, "MAX_TURNS", 3)
        monkeypatch.setattr(agent_mod, "GRACE_TURNS_BEFORE_END", 2)

        outcomes = [
            _tool_stream("check_environment", "{}"),
            _tool_stream("check_environment", "{}"),
            _content_stream("summary"),
        ]

        def _pass_execute(name, tool_input, ctx):
            return {"success": True}

        monkeypatch.setattr(agent_mod, "execute_tool", _pass_execute)
        client = _FakeClient(outcomes)
        monkeypatch.setattr(agent_mod, "_client", client)

        recorder = _Recorder(agent_mod)
        agent_mod.run_agent_turn_cb("deploy", _fake_services(), "p2-grace", recorder.callbacks)

        assert "tools" in client.calls[0]
        assert "tools" not in client.calls[-1]
        assert "".join(recorder.text) == "summary"

    def test_grace_warning_injected(self, agent_mod, monkeypatch):
        monkeypatch.setattr(agent_mod, "MAX_TURNS", 3)
        monkeypatch.setattr(agent_mod, "GRACE_TURNS_BEFORE_END", 2)

        outcomes = [
            _tool_stream("check_environment", "{}"),
            _tool_stream("check_environment", "{}"),
            _content_stream("wrapping up"),
        ]

        def _pass_execute(name, tool_input, ctx):
            return {"success": True}

        monkeypatch.setattr(agent_mod, "execute_tool", _pass_execute)
        client = _FakeClient(outcomes)
        monkeypatch.setattr(agent_mod, "_client", client)

        recorder = _Recorder(agent_mod)
        agent_mod.run_agent_turn_cb("deploy", _fake_services(), "p2-warn", recorder.callbacks)

        session = agent_mod._get_session("p2-warn")
        notice_msgs = [
            m for m in session.history
            if isinstance(m.get("content"), str) and "<system-notice>" in m["content"]
        ]
        assert len(notice_msgs) == 1
        assert "总结" in notice_msgs[0]["content"]

    def test_no_warning_on_short_conversations(self, agent_mod, monkeypatch):
        outcomes = [_content_stream("hello")]
        client = _FakeClient(outcomes)
        monkeypatch.setattr(agent_mod, "_client", client)

        recorder = _Recorder(agent_mod)
        agent_mod.run_agent_turn_cb("hi", _fake_services(), "p2-short", recorder.callbacks)

        session = agent_mod._get_session("p2-short")
        notice_msgs = [
            m for m in session.history
            if isinstance(m.get("content"), str) and "<system-notice>" in m["content"]
        ]
        assert notice_msgs == []
