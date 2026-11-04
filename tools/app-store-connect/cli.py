#!/usr/bin/env python3
"""App Store Connect CLI — read-only account inspection for agents and humans.

Subcommands::

    verify            check credentials and connectivity
    list-apps         list apps visible to the key
    versions --app ID list App Store versions and their review state
    builds --app ID   list recent builds and processing state

Add ``--mock`` to explore the output shape without credentials (explicitly
synthetic, never a silent fallback).

Usage::

    python3 tools/app-store-connect/cli.py verify
    python3 tools/app-store-connect/cli.py --mock list-apps --json
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apple_native import __version__
from apple_native.report import Report
from asc_client import ASCError, AppStoreConnectClient, Credentials


def _shared_flags() -> "argparse.ArgumentParser":
    """Flags accepted both before and after the subcommand.

    MCP clients append flags after the subcommand, so a parent-only definition
    would break `cli.py verify --json`.
    """

    import argparse

    suppress = argparse.SUPPRESS
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--mock", action="store_true", default=suppress,
                        help="Use synthetic data (explicit; never implied)")
    common.add_argument("--json", action="store_true", default=suppress, help="Machine-readable output")
    common.add_argument("--strict", action="store_true", default=suppress, help="Treat warnings as failures")
    common.add_argument("--color", choices=("auto", "always", "never"), default=suppress)
    common.add_argument("--key-id", default=suppress, help="Override ASC_KEY_ID")
    common.add_argument("--issuer-id", default=suppress, help="Override ASC_ISSUER_ID")
    common.add_argument("--private-key-path", default=suppress, help="Override ASC_PRIVATE_KEY_PATH")
    common.add_argument("--app", default=suppress, help="App Store app ID (for versions/builds)")
    common.add_argument("--limit", type=int, default=suppress)
    return common


def _build_parser():
    import argparse

    common = _shared_flags()
    parser = argparse.ArgumentParser(
        prog="asc-cli",
        description="Read-only App Store Connect inspection.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[common],
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify", help="Verify credentials and connectivity", parents=[common])
    sub.add_parser("list-apps", help="List apps visible to the key", parents=[common])
    sub.add_parser("versions", help="List App Store versions for --app", parents=[common])
    sub.add_parser("builds", help="List recent builds for --app", parents=[common])
    return parser


def _flag(args, name, default=None):
    """Read a flag that may be defined on either the root or the subcommand parser."""

    return getattr(args, name, default)


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    args.mock = _flag(args, "mock", False)
    args.json = _flag(args, "json", False)
    args.strict = _flag(args, "strict", False)
    args.color = _flag(args, "color", "auto")
    args.app = _flag(args, "app", None)
    args.limit = _flag(args, "limit", 20)
    args.key_id = _flag(args, "key_id", None)
    args.issuer_id = _flag(args, "issuer_id", None)
    args.private_key_path = _flag(args, "private_key_path", None)
    report = Report(tool="app-store-connect", target="api.appstoreconnect.apple.com",
                    version=__version__)

    client: AppStoreConnectClient
    try:
        credentials = None
        if not args.mock:
            import os
            if args.key_id:
                os.environ["ASC_KEY_ID"] = args.key_id
            if args.issuer_id:
                os.environ["ASC_ISSUER_ID"] = args.issuer_id
            credentials = Credentials.from_env(args.private_key_path)
        client = AppStoreConnectClient(credentials=credentials, mock=args.mock)
    except ASCError as exc:
        report.error("ASC001", str(exc))
        return report.emit(json_output=args.json, strict=args.strict, color_mode=args.color)

    try:
        if args.command == "verify":
            result = client.verify()
            report.data = result
            if result.get("mode") == "mock":
                report.warn("ASC010", "Mock mode: results are synthetic and must not gate a release.")
        elif args.command == "list-apps":
            apps = client.list_apps(limit=args.limit)
            report.data = {"apps": apps, "count": len(apps)}
            if not apps:
                report.warn("ASC011", "The key can see no apps.",
                            hint="Check the key's role and that it belongs to the right team.")
        elif args.command in ("versions", "builds"):
            if not args.app:
                report.error("ASC002", f"--app is required for '{args.command}'.")
                return report.emit(json_output=args.json, strict=args.strict, color_mode=args.color)
            if args.command == "versions":
                versions = client.app_versions(args.app, limit=args.limit)
                report.data = {"app_id": args.app, "versions": versions}
                if not versions:
                    report.warn("ASC012", "No App Store versions returned for this app id.")
            else:
                builds = client.builds(args.app, limit=args.limit)
                report.data = {"app_id": args.app, "builds": builds}
                expired = [b for b in builds if b.get("expired")]
                if expired:
                    report.warn("ASC013", f"{len(expired)} build(s) are expired.",
                                hint="Upload a new build before submitting.")
        else:  # pragma: no cover - argparse enforces choices
            report.error("ASC003", f"Unknown command: {args.command}")
    except ASCError as exc:
        report.error("ASC020", str(exc))

    return report.emit(json_output=args.json, strict=args.strict, color_mode=args.color,
                       title="Apple Native Engineer — App Store Connect")


if __name__ == "__main__":
    raise SystemExit(main())
