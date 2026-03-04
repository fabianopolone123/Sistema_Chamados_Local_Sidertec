from __future__ import annotations

import ctypes
from dataclasses import dataclass


ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = r"Local\SistemaChamadosUsuario"


class SingleInstanceError(RuntimeError):
    pass


@dataclass
class SingleInstanceLock:
    handle: ctypes.c_void_p | None

    def release(self) -> None:
        if self.handle is None:
            return
        kernel32 = _kernel32()
        kernel32.CloseHandle(self.handle)
        self.handle = None


def _kernel32() -> ctypes.WinDLL:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    return kernel32


def acquire_single_instance(name: str = MUTEX_NAME) -> SingleInstanceLock:
    kernel32 = _kernel32()
    handle = kernel32.CreateMutexW(None, False, name)
    if not handle:
        raise OSError("Nao foi possivel criar mutex de instancia unica.")

    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        raise SingleInstanceError("Chamados Usuario ja esta em execucao.")

    return SingleInstanceLock(handle=handle)
