from __future__ import annotations

import hashlib
import platform
import uuid


def machine_name() -> str:
    return platform.node() or "MAQUINA_DESCONHECIDA"


def machine_id() -> str:
    raw = f"{machine_name()}-{uuid.getnode()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12].upper()

