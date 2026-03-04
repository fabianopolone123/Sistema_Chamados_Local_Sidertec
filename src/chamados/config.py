from __future__ import annotations

import json
import os
import sys
from pathlib import Path


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


def get_database_path() -> Path:
    env_path = os.getenv("CHAMADOS_DB_PATH")
    if env_path:
        return Path(env_path).expanduser()

    runtime_cfg = _runtime_dir() / CONFIG_FILE_NAME
    runtime_data = _load_json(runtime_cfg)
    runtime_db = runtime_data.get("database_path")
    if runtime_db:
        return Path(runtime_db).expanduser()

    program_data_cfg = _program_data_dir() / CONFIG_FILE_NAME
    program_data_data = _load_json(program_data_cfg)
    program_data_db = program_data_data.get("database_path")
    if program_data_db:
        return Path(program_data_db).expanduser()

    default_path = _program_data_dir() / "chamados.db"
    try:
        default_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Se houver restricao de pasta local, o erro final sera tratado na abertura do banco.
        pass
    return default_path
