from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from chamados.user_app import main


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="ChamadosUsuario")
    parser.add_argument(
        "--minimized-to-tray",
        action="store_true",
        help="Inicia minimizado na bandeja do sistema.",
    )
    return parser.parse_args()


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
    args = parse_args()
    try:
        main(start_minimized=args.minimized_to_tray)
    except Exception as exc:
        show_startup_error(str(exc))
        raise SystemExit(1)
