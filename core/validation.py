"""Input validation for security-sensitive fields."""
from __future__ import annotations

import re

_EVM_ADDRESS_RE = re.compile(r"\A0x[0-9a-fA-F]{40}\Z")


def is_valid_evm_address(value: str | None) -> bool:
    """Check if value is a well-formed EVM address (0x + 40 hex chars)."""
    if not value:
        return False
    return bool(_EVM_ADDRESS_RE.fullmatch(value))


def validate_evm_address(value: str | None, field_name: str = "address") -> str:
    """Validate and return a normalized EVM address, or raise ValueError."""
    if not value:
        raise ValueError(f"{field_name} is required")
    if not _EVM_ADDRESS_RE.fullmatch(value):
        raise ValueError(
            f"{field_name} must be a valid EVM address (0x followed by 40 hex characters), got: {value!r}"
        )
    return value
