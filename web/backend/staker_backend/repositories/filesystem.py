"""Filesystem repository utilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class FileRepository:
    """Provide typed helpers around filesystem access."""

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        return Path(path).expanduser().read_text(encoding=encoding)

    def read_json(self, path: str, encoding: str = "utf-8") -> Any:
        content = self.read_text(path, encoding=encoding)
        return json.loads(content)

    def exists(self, path: str) -> bool:
        return Path(path).expanduser().exists()
