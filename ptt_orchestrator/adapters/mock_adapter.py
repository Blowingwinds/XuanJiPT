"""Mock adapter used by the first scaffold."""

from __future__ import annotations

from typing import Any

from .base import BaseToolAdapter


class MockAdapter(BaseToolAdapter):
    tool_id = "mock_adapter"

    def supports(self, operator_id: str) -> bool:
        return bool(operator_id)

    def build_command(self, action: dict[str, Any]) -> dict[str, Any]:
        return {"tool_id": self.tool_id, "action": action}

    def execute(self, command: dict[str, Any]) -> dict[str, Any]:
        return {"status": "success", "command": command, "mock": True}

    def parse_result(self, raw_result: dict[str, Any]) -> dict[str, Any]:
        return raw_result

