"""Base interface for tool adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseToolAdapter(ABC):
    tool_id: str

    @abstractmethod
    def supports(self, operator_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def build_command(self, action: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def execute(self, command: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def parse_result(self, raw_result: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

