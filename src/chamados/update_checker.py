from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class UpdateInfo:
    latest_version: str
    installer_path: Path
    notes: str


def _normalize_version(version: str) -> tuple[int, ...]:
    tokens = re.split(r"[.\-_]", version.strip())
    numbers: list[int] = []
    for token in tokens:
        match = re.match(r"^(\d+)", token)
        if match:
            numbers.append(int(match.group(1)))

    if not numbers:
        return (0,)

    while numbers and numbers[-1] == 0:
        numbers.pop()
    return tuple(numbers or [0])


def is_newer_version(candidate: str, current: str) -> bool:
    a = _normalize_version(candidate)
    b = _normalize_version(current)
    max_len = max(len(a), len(b))
    a = a + (0,) * (max_len - len(a))
    b = b + (0,) * (max_len - len(b))
    return a > b


class UpdateChecker:
    def __init__(self, current_version: str, manifest_path: Path, interval_seconds: int = 1800):
        self.current_version = current_version
        self.manifest_path = Path(manifest_path)
        self.interval_seconds = max(interval_seconds, 60)
        self._prompted_versions: set[str] = set()

    def get_available_update(self) -> UpdateInfo | None:
        if not self.manifest_path.exists():
            return None

        try:
            content = self.manifest_path.read_text(encoding="utf-8")
            data = json.loads(content)
        except (OSError, json.JSONDecodeError):
            return None

        latest_version = str(data.get("latest_version", "")).strip()
        installer_raw = str(data.get("installer_path", "")).strip()
        notes = str(data.get("notes", "")).strip()

        if not latest_version or not installer_raw:
            return None
        if not is_newer_version(latest_version, self.current_version):
            return None

        installer_path = Path(installer_raw).expanduser()
        if not installer_path.is_absolute():
            installer_path = (self.manifest_path.parent / installer_path).resolve()

        return UpdateInfo(
            latest_version=latest_version,
            installer_path=installer_path,
            notes=notes,
        )

    def should_prompt(self, latest_version: str) -> bool:
        if latest_version in self._prompted_versions:
            return False
        self._prompted_versions.add(latest_version)
        return True

    def run_installer(self, installer_path: Path) -> bool:
        if not installer_path.exists():
            return False
        try:
            os.startfile(str(installer_path))
            return True
        except OSError:
            return False

