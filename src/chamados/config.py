from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


APP_DIR_NAME = "SistemaChamados"
CONFIG_FILE_NAME = "config.json"


def _runtime_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def _program_data_dir() -> Path:
    base = os.getenv("PROGRAMDATA")
    if base:
        return Path(base) / APP_DIR_NAME
    return Path.home() / APP_DIR_NAME


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _read_config_value(key: str) -> Any:
    runtime_cfg = _runtime_dir() / CONFIG_FILE_NAME
    runtime_data = _load_json(runtime_cfg)
    if key in runtime_data:
        return runtime_data.get(key)

    program_data_cfg = _program_data_dir() / CONFIG_FILE_NAME
    program_data_data = _load_json(program_data_cfg)
    if key in program_data_data:
        return program_data_data.get(key)

    return None


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_runtime_path() -> Path:
    return _runtime_dir()


def get_database_path() -> Path:
    env_path = os.getenv("CHAMADOS_DB_PATH")
    if env_path:
        return Path(env_path).expanduser()

    runtime_db = _read_config_value("database_path")
    if runtime_db:
        return Path(runtime_db).expanduser()

    default_path = _program_data_dir() / "chamados.db"
    try:
        default_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Se houver restricao de pasta local, o erro final sera tratado na abertura do banco.
        pass
    return default_path


def get_update_manifest_path() -> Path | None:
    env_path = os.getenv("CHAMADOS_UPDATE_MANIFEST")
    if env_path:
        return Path(env_path).expanduser()

    config_value = _read_config_value("update_manifest_path")
    if config_value:
        return Path(str(config_value)).expanduser()
    return None


def get_update_check_interval_seconds(default: int = 1800) -> int:
    env_value = os.getenv("CHAMADOS_UPDATE_INTERVAL")
    if env_value:
        seconds = _as_int(env_value, default)
        return max(seconds, 60)

    config_value = _read_config_value("update_check_interval_seconds")
    seconds = _as_int(config_value, default)
    return max(seconds, 60)
