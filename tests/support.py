"""Shared helpers for the Python test suite."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
FIXTURES = REPO_ROOT / "tests" / "fixtures"
LEGACY = FIXTURES / "legacy-app"
CLEAN = FIXTURES / "clean-app"

sys.path.insert(0, str(TOOLS / "lib"))


def run_tool(script: str, *args: str, expect: Optional[int] = None) -> Dict[str, Any]:
    """Run a tool as a subprocess and return its parsed JSON envelope."""

    command = [sys.executable, str(TOOLS / script), *args, "--json"]
    proc = subprocess.run(command, capture_output=True, text=True)
    if expect is not None:
        assert proc.returncode == expect, (
            f"{script} exited {proc.returncode}, expected {expect}\n"
            f"stdout: {proc.stdout[:800]}\nstderr: {proc.stderr[:800]}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - diagnostic path
        raise AssertionError(f"{script} did not emit JSON: {proc.stdout[:800]}\n{proc.stderr[:400]}") from exc


def codes(envelope: Dict[str, Any]) -> List[str]:
    return [finding["code"] for finding in envelope["findings"]]


def load_module(name: str, relative: str):
    """Import a tool module by path (the tools are scripts, not a package)."""

    spec = importlib.util.spec_from_file_location(name, TOOLS / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
