from __future__ import annotations

import argparse
import ctypes
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from .pet import DesktopPet

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "pet_config.json"


def enable_windows_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Feibi desktop pet.")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the JSON config file.",
    )
    return parser


def run(config_path: Path | None = None) -> None:
    enable_windows_dpi_awareness()
    target_config = Path(config_path or DEFAULT_CONFIG_PATH)

    root = tk.Tk()
    root.withdraw()
    try:
        DesktopPet(root, target_config)
    except Exception as exc:
        messagebox.showerror("Feibi Pet", f"Failed to start Feibi Pet:\n{exc}")
        root.destroy()
        raise

    root.deiconify()
    root.mainloop()


def main() -> None:
    args = build_parser().parse_args()
    run(args.config)
