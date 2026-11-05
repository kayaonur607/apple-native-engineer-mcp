"""Argument parsing helpers shared by the executables in ``tools/``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .report import Report, fail_fast


def build_parser(tool: str, description: str, epilog: Optional[str] = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=tool,
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory to analyse (default: current directory)",
    )
    parser.add_argument("--json", action="store_true", help="Emit the stable machine-readable JSON envelope")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures (exit code 1 instead of 0)",
    )
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="Colourise human output (default: auto-detect TTY)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s 2.0.0",
    )
    return parser


def resolve_target(raw: str) -> Path:
    return Path(raw).expanduser().resolve()


def emit(report: Report, args: argparse.Namespace, title: Optional[str] = None) -> int:
    return report.emit(
        json_output=getattr(args, "json", False),
        strict=getattr(args, "strict", False),
        color_mode=getattr(args, "color", "auto"),
        title=title,
    )


def guard_directory(tool: str, raw: str, *, allow_file: bool = False) -> Optional[Report]:
    """Return an error report when *raw* is not a usable target.

    Auditors that read Swift sources one file at a time pass ``allow_file=True``
    so a caller can scope a run to a single changed file. Everything else still
    requires a directory: an icon validator pointed at one PNG is a different
    question, not a smaller one.
    """

    path = resolve_target(raw)
    if not path.exists():
        report = fail_fast(
            tool,
            str(path),
            f"Directory does not exist: {path}",
            code="GEN001",
            hint="Pass the root of an Xcode project or Swift package.",
        )
        return report
    if not path.is_dir():
        if allow_file and path.suffix == ".swift":
            return None
        report = fail_fast(
            tool,
            str(path),
            f"Expected a directory, got a file: {path}",
            code="GEN002",
            hint=(
                "Pass a single .swift file or the folder that contains the project."
                if allow_file
                else "Point the tool at the folder that contains the project."
            ),
        )
        return report
    return None


def main_guard(fn):
    """Decorator that converts unexpected exceptions into a JSON-safe failure."""

    def wrapper(argv=None):  # pragma: no cover - thin shim
        try:
            return fn(argv)
        except BrokenPipeError:
            return 0
        except Exception as exc:  # noqa: BLE001 - CLI boundary
            sys.stderr.write(f"error: {exc}\n")
            return 2

    wrapper.__name__ = getattr(fn, "__name__", "main")
    wrapper.__doc__ = fn.__doc__
    return wrapper
