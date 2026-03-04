from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chamados.single_instance import SingleInstanceError, acquire_single_instance
from chamados.user_app import main


def show_startup_error(message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro ao iniciar Chamados Usuario", message)
        root.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    lock = None
    try:
        lock = acquire_single_instance()
        main()
    except SingleInstanceError:
        show_startup_error("O Chamados Usuario ja esta aberto nesta maquina.")
        raise SystemExit(0)
    except Exception as exc:
        show_startup_error(str(exc))
        raise SystemExit(1)
    finally:
        if lock is not None:
            lock.release()
