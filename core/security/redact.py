"""Secret redaction utilities.

Recursively redacts sensitive values from dicts, lists, and strings.
No Flask dependency — safe to use from core/ and web/.
"""
from __future__ import annotations

import re
from typing import Any, FrozenSet

REDACT_MARKER = "[REDACTED]"

SENSITIVE_KEYS: FrozenSet[str] = frozenset({
    "mnemonic",
    "keystore_password",
    "api_key",
    "apikey",
    "ssh_key",
    "token",
    "authorization",
    "secret",
    "password",
    "private_key",
    "secret_key",
})

# BIP-39 mnemonic patterns
# Full-value: entire string is exactly 12 or 24 lowercase words (3-8 chars)
_MNEMONIC_FULL = re.compile(r'^(?:[a-z]{3,8} ){11}[a-z]{3,8}$|^(?:[a-z]{3,8} ){23}[a-z]{3,8}$')
# Embedded: 24 consecutive lowercase words (3-8 chars) within a larger string.
# Only 24-word for embedded detection — 12-word is too prone to false positives in prose.
_MNEMONIC_EMBEDDED_24 = re.compile(r'(?<![a-z])([a-z]{3,8}(?:\s[a-z]{3,8}){23})(?![a-z])')


def redact_secrets(
    obj: Any,
    *,
    sensitive_keys: FrozenSet[str] = SENSITIVE_KEYS,
    marker: str = REDACT_MARKER,
) -> Any:
    """Return a deep copy of obj with sensitive values replaced by marker.

    - dict keys matched case-insensitively against sensitive_keys
    - Strings scanned for BIP-39 mnemonic patterns (12/24 words)
    - Input is never mutated
    """
    if obj is None:
        return None

    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if isinstance(key, str) and key.lower() in sensitive_keys:
                result[key] = marker
            else:
                result[key] = redact_secrets(value, sensitive_keys=sensitive_keys, marker=marker)
        return result

    if isinstance(obj, list):
        return [redact_secrets(item, sensitive_keys=sensitive_keys, marker=marker) for item in obj]

    if isinstance(obj, tuple):
        return tuple(redact_secrets(item, sensitive_keys=sensitive_keys, marker=marker) for item in obj)

    if isinstance(obj, str):
        return _redact_mnemonic_in_string(obj, marker)

    return obj


def _redact_mnemonic_in_string(text: str, marker: str) -> str:
    """Replace BIP-39 mnemonic patterns in a string.

    - Full-value: entire string is 12 or 24 words → replace whole string
    - Embedded: only 24-word spans (12-word too prone to false positives in prose)
    """
    if len(text) < 30:
        return text
    stripped = text.strip()
    if _MNEMONIC_FULL.match(stripped):
        return marker
    # Scan for embedded 24-word mnemonics (e.g. in error messages)
    text = _MNEMONIC_EMBEDDED_24.sub(marker, text)
    return text
