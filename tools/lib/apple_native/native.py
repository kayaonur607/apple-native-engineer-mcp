"""Build and run the macOS-native helper (``tools/screenshot-studio/native_render.swift``).

The helper is compiled once with ``xcrun swiftc -O`` and cached by the hash of
its source, so later runs start instantly and an edited source is rebuilt
automatically. On machines without Xcode (Linux CI) ``native_helper()`` returns
``None`` and callers fall back or say plainly that native rendering is missing.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

SOURCE = Path(__file__).resolve().parents[2] / "screenshot-studio" / "native_render.swift"
CACHE = Path(os.environ.get("APPLE_NATIVE_CACHE", Path.home() / ".cache" / "apple-native-engineer")) / "bin"


class NativeError(RuntimeError):
    pass


def available() -> bool:
    return sys.platform == "darwin" and shutil.which("xcrun") is not None and SOURCE.exists()


def native_helper() -> Optional[Path]:
    """Return the compiled helper, building it on first use. ``None`` if impossible."""

    if os.environ.get("APPLE_NATIVE_DISABLE_NATIVE") == "1" or not available():
        return None
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()[:16]
    binary = CACHE / f"native_render-{digest}"
    if binary.exists():
        return binary
    CACHE.mkdir(parents=True, exist_ok=True)
    temporary = binary.with_suffix(".tmp")
    try:
        result = subprocess.run(["xcrun", "swiftc", "-O", str(SOURCE), "-o", str(temporary)],
                                capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not temporary.exists():
        return None
    temporary.replace(binary)
    return binary


def run_helper(arguments: List[str], timeout: float = 600) -> Dict[str, object]:
    helper = native_helper()
    if helper is None:
        raise NativeError("the native renderer needs macOS with Xcode command-line tools")
    result = subprocess.run([str(helper), *arguments], capture_output=True, text=True, timeout=timeout)
    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError) as exc:
        raise NativeError(f"native renderer failed: {result.stderr.strip() or result.stdout.strip()}") from exc
    return payload


def flatten(paths: List[Path]) -> Dict[str, object]:
    """Rewrite PNGs in place as opaque RGB at the same size and colour space."""

    if not paths:
        return {"ok": True, "results": [], "errors": []}
    return run_helper(["flatten", *[str(path) for path in paths]])
