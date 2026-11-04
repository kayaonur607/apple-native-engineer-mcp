#!/usr/bin/env python3
"""
Apple Native Engineer — App Store Connect CLI Frontend
Command-line tool for verifying credentials, listing apps, and inspecting versions/builds.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add tool directory to path
sys.path.insert(0, str(Path(__file__).parent))
from asc_client import AppStoreConnectClient

def load_env_file():
    """Loads .env file from project root or user home if present."""
    possible_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent.parent / ".env",
        Path.home() / ".appstoreconnect" / ".env"
    ]
    for p in possible_paths:
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")
            break

def main():
    load_env_file()

    parser = argparse.ArgumentParser(description="Apple Native Engineer — App Store Connect Toolkit")
    parser.add_argument("--mock", action="store_true", help="Run in mock/diagnostic mode (no live credentials needed)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: verify
    subparsers.add_parser("verify", help="Verify connection & credentials to App Store Connect API")

    # Command: list-apps
    subparsers.add_parser("list-apps", help="List registered applications in account")

    # Command: inspect-version
    p_version = subparsers.add_parser("inspect-version", help="Inspect app versions and submission states")
    p_version.add_argument("--app", required=True, help="App ID or Bundle Identifier")

    # Command: inspect-builds
    p_builds = subparsers.add_parser("inspect-builds", help="Inspect uploaded builds and processing status")
    p_builds.add_argument("--app", required=True, help="App ID or Bundle Identifier")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    client = AppStoreConnectClient(mock_mode=args.mock)

    if args.command == "verify":
        res = client.verify_connection()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("==========================================================")
            print("  App Store Connect API Connection Status                 ")
            print("==========================================================")
            print(f"Status:       {res.get('status').upper()}")
            print(f"Mode:         {res.get('mode').upper()}")
            print(f"Message:      {res.get('message', 'Ready for API operations.')}")
            print("==========================================================")

    elif args.command == "list-apps":
        apps = client.list_apps()
        if args.json:
            print(json.dumps(apps, indent=2))
        else:
            print("==========================================================")
            print(f"  App Store Connect: Registered Applications ({len(apps)})")
            print("==========================================================")
            for a in apps:
                print(f"• Name:      {a.get('name')}")
                print(f"  Bundle ID: {a.get('bundleId')}")
                print(f"  App ID:    {a.get('id')}")
                print(f"  Locale:    {a.get('primaryLocale')}")
                print("----------------------------------------------------------")

    elif args.command == "inspect-version":
        info = client.inspect_version(args.app)
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            print("==========================================================")
            print(f"  App Store Connect: Version Details for {args.app}     ")
            print("==========================================================")
            print(f"Version:      {info.get('version', 'N/A')}")
            print(f"State:        {info.get('state', 'N/A')}")
            print(f"Locales:      {', '.join(info.get('localizations_available', []))}")
            print(f"Review State: {info.get('review_state', 'N/A')}")
            print("==========================================================")

    elif args.command == "inspect-builds":
        builds = client.inspect_builds(args.app)
        if args.json:
            print(json.dumps(builds, indent=2))
        else:
            print("==========================================================")
            print(f"  App Store Connect: Builds for {args.app}                ")
            print("==========================================================")
            for b in builds:
                print(f"• Build:      {b.get('version')} ({b.get('buildNumber')})")
                print(f"  Status:     {b.get('processingState')}")
                print(f"  Uploaded:   {b.get('uploadedDate')}")
                print("----------------------------------------------------------")

if __name__ == "__main__":
    main()
