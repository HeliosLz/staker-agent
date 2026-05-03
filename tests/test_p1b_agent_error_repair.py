"""Tests for P1b: provider error classification + tool JSON repair."""
from __future__ import annotations

import os
import sys
from queue import Queue
from types import SimpleNamespace

import httpx
import openai
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

WEB_BACKEND = os.path.join(BASE_DIR, "web", "backend")
if WEB_BACKEND not in sys.path:
    sys.path.insert(0, WEB_BACKEND)


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


class TestErrorClassification:
    def test_classifies_openai_typed_errors(self, agent_mod):
        request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
        rate_response = httpx.Response(429, request=request, json={"error": "rate limit"})
        context_response = httpx.Response(
            400,
            request=request,
            json={"error": {"code": "context_length_exceeded"}},
        )

        assert agent_mod.classify_agent_error(
            openai.RateLimitError("Rate limit", response=rate_response, body=None)
        ) == agent_mod.ERROR_RATE_LIMIT
        assert agent_mod.classify_agent_error(
            openai.APITimeoutError(request=request)
        ) == agent_mod.ERROR_TIMEOUT
        assert agent_mod.classify_agent_error(
            openai.BadRequestError(
                "provider returned 400",
                response=context_response,
                body={"error": {"code": "context_length_exceeded"}},
            )
        ) == agent_mod.ERROR_CONTEXT_OVERFLOW

    def test_classifies_provider_message_fallbacks(self, agent_mod):
        assert agent_mod.classify_agent_error(
            RuntimeError("provider said: too many tokens for this context window")
        ) == agent_mod.ERROR_CONTEXT_OVERFLOW
        assert agent_mod.classify_agent_error(
            RuntimeError("429 too many requests")
        ) == agent_mod.ERROR_RATE_LIMIT
        assert agent_mod.classify_agent_error(
            RuntimeError("upstream timed out")
        ) == agent_mod.ERROR_TIMEOUT
        assert agent_mod.classify_agent_error(
            RuntimeError("unexpected provider failure")
        ) == agent_mod.ERROR_OTHER


class TestToolArgumentRepair:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ('{"network":"holesky","client":"lighthouse"}', {"network": "holesky", "client": "lighthouse"}),
            ('```json\n{"network":"holesky"}\n```', {"network": "holesky"}),
            ('use this: {"network":"holesky"} thanks', {"network": "holesky"}),
            ('{"network":"holesky",}', {"network": "holesky"}),
            ('{"network":"holesky","client":"lighthouse"', {"network": "holesky", "client": "lighthouse"}),
        ],
    )
    def test_repairs_common_json_argument_shapes(self, agent_mod, raw, expected):
        parsed, error = agent_mod.parse_tool_arguments(raw)
        assert error is None
        assert parsed == expected

    def test_invalid_json_returns_structured_error(self, agent_mod):
        parsed, error = agent_mod.parse_tool_arguments('{"network":')
        assert parsed == {}
        assert "invalid JSON tool arguments" in error


class TestAgentLoopRecovery:
    def test_context_overflow_compacts_history_and_retries_once(self, agent_mod, monkeypatch):
        sid = "p1b-context"
        session = agent_mod._get_session(sid)
        with session.lock:
            session.history = [{"role": "user", "content": f"old message {i}"} for i in range(90)]

        client = _FakeClient([
            RuntimeError("maximum context length exceeded"),
            _content_stream("ok"),
        ])
        monkeypatch.setattr(agent_mod, "_client", client)

        recorder = _Recorder(agent_mod)
        agent_mod.run_agent_turn_cb("new message", _fake_services(), sid, recorder.callbacks)

        assert recorder.errors == []
        assert "".join(recorder.text) == "ok"
        assert len(client.calls) == 2
        assert len(client.calls[1]["messages"]) < len(client.calls[0]["messages"])

    def test_timeout_retries_stream_creation_without_context_compaction(self, agent_mod, monkeypatch):
        delays = []
        monkeypatch.setattr(agent_mod.time, "sleep", delays.append)
        client = _FakeClient([
            TimeoutError("provider timed out"),
            _content_stream("ok"),
        ])
        monkeypatch.setattr(agent_mod, "_client", client)

        recorder = _Recorder(agent_mod)
        agent_mod.run_agent_turn_cb("hello", _fake_services(), "p1b-timeout", recorder.callbacks)

        assert recorder.errors == []
        assert "".join(recorder.text) == "ok"
        assert delays == [agent_mod.RETRY_BASE_DELAY]
        assert len(client.calls[0]["messages"]) == len(client.calls[1]["messages"])

    def test_context_overflow_after_timeout_retries_still_gets_one_recovery(self, agent_mod, monkeypatch):
        delays = []
        monkeypatch.setattr(agent_mod.time, "sleep", delays.append)
        sid = "p1b-timeout-then-context"
        session = agent_mod._get_session(sid)
        with session.lock:
            session.history = [{"role": "user", "content": f"old message {i}"} for i in range(90)]

        client = _FakeClient([
            TimeoutError("provider timed out"),
            TimeoutError("provider timed out"),
            RuntimeError("maximum context length exceeded"),
            _content_stream("ok"),
        ])
        monkeypatch.setattr(agent_mod, "_client", client)

        recorder = _Recorder(agent_mod)
        agent_mod.run_agent_turn_cb("hello", _fake_services(), sid, recorder.callbacks)

        assert recorder.errors == []
        assert "".join(recorder.text) == "ok"
        assert delays == [agent_mod.RETRY_BASE_DELAY, agent_mod.RETRY_BASE_DELAY * 2]
        assert len(client.calls) == 4
        assert len(client.calls[3]["messages"]) < len(client.calls[2]["messages"])

    def test_invalid_tool_json_emits_tool_error_without_execution(self, agent_mod, monkeypatch):
        def _fail_execute(*_args, **_kwargs):
            raise AssertionError("execute_tool should not be called for invalid JSON")

        monkeypatch.setattr(agent_mod, "execute_tool", _fail_execute)
        client = _FakeClient([
            _tool_stream("check_environment", '{"network":'),
            _content_stream("recovered"),
        ])
        monkeypatch.setattr(agent_mod, "_client", client)

        recorder = _Recorder(agent_mod)
        agent_mod.run_agent_turn_cb("run tool", _fake_services(), "p1b-json-error", recorder.callbacks)

        assert recorder.errors == []
        assert recorder.tool_starts == [("check_environment", {}, "call_1")]
        name, tool_id, result, success = recorder.tool_results[0]
        assert name == "check_environment"
        assert tool_id == "call_1"
        assert success is False
        assert result["error_type"] == "invalid_tool_arguments"
        assert "invalid JSON tool arguments" in result["details"]
