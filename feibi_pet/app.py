from __future__ import annotations

import argparse
import ctypes
from pathlib import Path
import shutil
import sys
import tkinter as tk
from tkinter import messagebox

from .pet import DesktopPet


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def get_bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", get_app_dir())).resolve()
    return get_app_dir()


DEFAULT_CONFIG_PATH = get_app_dir() / "pet_config.json"


def bootstrap_user_files(app_dir: Path) -> None:
    """Copy editable files next to the exe on first run."""
    bundle_dir = get_bundle_dir()
    for name in ("pet_config.json", "assets", "skills"):
        source = bundle_dir / name
        target = app_dir / name
        if target.exists() or not source.exists() or source.resolve() == target.resolve():
            continue
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


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
        default=None,
        help="Path to the JSON config file.",
    )
    return parser


def run(config_path: Path | None = None) -> None:
    enable_windows_dpi_awareness()
    if config_path is None:
        bootstrap_user_files(get_app_dir())
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
