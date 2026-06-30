"""Configuration and template loaders.

This module should stay generic: it loads files and returns dictionaries.
Validation of business meaning belongs in validator.py or registries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_json(path: str | Path) -> dict[str, Any]:
    resolved = _resolve_project_path(path)
    return json.loads(resolved.read_text(encoding="utf-8"))


def load_yaml(path: str | Path) -> dict[str, Any]:
    resolved = _resolve_project_path(path)
    data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    return data or {}


def load_text(path: str | Path) -> str:
    resolved = _resolve_project_path(path)
    return resolved.read_text(encoding="utf-8")


def load_file(path: str | Path) -> Any:
    resolved = _resolve_project_path(path)
    suffix = resolved.suffix.lower()
    if suffix == ".json":
        return load_json(resolved)
    if suffix in {".yaml", ".yml"}:
        return load_yaml(resolved)
    return load_text(resolved)


def _resolve_project_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    if not candidate.exists():
        raise FileNotFoundError(f"File does not exist: {candidate}")
    if not candidate.is_file():
        raise IsADirectoryError(f"Expected a file path, got directory: {candidate}")
    return candidate
