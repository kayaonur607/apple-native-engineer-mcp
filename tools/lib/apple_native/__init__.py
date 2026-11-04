"""Shared runtime library for the Apple Native Engineer CLI tools.

Every executable tool in ``tools/`` is a thin command-line wrapper around the
analysis modules in this package. Keeping the shared concerns (report format,
exit codes, Swift source scanning, colour maths, Xcode project parsing) in one
place is what makes the individual tools small enough to audit.

The package is deliberately dependency-free: it only uses the Python standard
library so that the toolkit runs on a stock macOS / Linux machine with nothing
but ``python3``.
"""

from __future__ import annotations

__all__ = ["__version__", "REPO_ROOT"]

__version__ = "2.0.0"

import os
from pathlib import Path

#: Absolute path to the repository root (two levels above ``tools/lib``).
REPO_ROOT = Path(os.environ.get("APPLE_NATIVE_ROOT", Path(__file__).resolve().parents[3]))
