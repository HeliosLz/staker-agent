"""MessageComposer — external message assembly for the agent loop.

The agent loop calls composer.compose(history) and gets back a full
messages list. All injection logic (memory, monitor events, etc.) is
registered as injectors and applied here, keeping the agent loop clean.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List


class MessageComposer:
    """Assembles LLM messages. Agent loop only calls compose()."""

    def __init__(self, system_prompt: str) -> None:
        self._system_prompt = system_prompt
        self._injectors: List[Callable[[str], str]] = []

    def add_system_injector(self, fn: Callable[[str], str]) -> None:
        """Register a system prompt injector.

        fn receives the current system content, returns the modified version.
        Injectors are applied in registration order.
        """
        self._injectors.append(fn)

    def compose(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build the full messages list for an LLM call."""
        system = self._system_prompt
        for injector in self._injectors:
            system = injector(system)
        return [{"role": "system", "content": system}] + history
