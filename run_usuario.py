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


if __name__ == "__main__":
    args = parse_args()
    main(start_minimized=args.minimized_to_tray)
