from __future__ import annotations

import os
from pathlib import Path
import sys


if getattr(sys, "frozen", False):
    bundle_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    sys.path.insert(0, str(bundle_dir))
    os.environ.setdefault("TCL_LIBRARY", str(bundle_dir / "tcl" / "tcl8.6"))
    os.environ.setdefault("TK_LIBRARY", str(bundle_dir / "tcl" / "tk8.6"))
