#!/usr/bin/env python3
"""Capture App Store screenshots in the Simulator: devices × locales × appearances.

This is the capture half of the screenshot pipeline. It drives ``xcrun simctl``
the way a careful human would before a submission:

1. resolve each device (a simulator name such as ``iPhone 18 Pro Max`` or an
   App Store slot id such as ``iphone-6.9``) to an available simulator, creating
   one for the newest installed runtime when none exists,
2. boot it and wait for boot to finish,
3. apply a clean status bar (9:41, full battery, full signal),
4. set light or dark appearance,
5. optionally install the ``.app`` you built,
6. relaunch the app per locale with ``-AppleLanguages``/``-AppleLocale`` and
   the screen's own launch arguments, environment variables or a deep link.
   Launch arguments are the portable route: iOS puts ``-screen insights`` in the
   NSUserDefaults argument domain, which Swift (``UserDefaults``), React Native
   (``Settings.get``) and Flutter (``SharedPreferencesAsync``) all read.
   Environment variables (forwarded as ``SIMCTL_CHILD_*``) reach native code via
   ``ProcessInfo`` but **not** Flutter, whose ``Platform.environment`` is empty
   on iOS. Custom-scheme deep links make iOS ask "Open in …?", which would end up
   in the screenshot,
7. wait for the screen to settle and save a PNG,
8. validate every file against Apple's slots and write ``manifest.json``.

It never draws or fakes a screen. ``--dry-run`` prints the exact commands
without touching the Simulator, so the plan can be reviewed first.

Plan file (JSON)::

    {
      "bundle_id": "com.example.planner",
      "app": "build/Build/Products/Debug-iphonesimulator/Planner.app",
      "devices": ["iphone-6.9", "iphone-6.3", "iPad Pro 13-inch (M5)"],
      "locales": ["en-US", "tr-TR"],
      "appearances": ["light", "dark"],
      "launch_arguments": ["-UITestScreenshotMode", "YES"],
      "screens": [
        {"name": "01-today", "arguments": ["-initialTab", "today"]},
        {"name": "02-detail", "url": "planner://item/42"},
        {"name": "03-insights", "env": {"SCREEN": "insights"}}
      ],
      "settle_seconds": 3,
      "status_bar": {"time": "9:41"},
      "flatten": true,
      "shutdown_after": false
    }

Usage::

    python3 tools/screenshot-studio/capture_batch.py plan.json --out fastlane/screenshots --dry-run
    python3 tools/screenshot-studio/capture_batch.py plan.json --out fastlane/screenshots
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import emit
from apple_native import native
from apple_native.imaging import image_info, screenshot_slots, UnsupportedImage
from apple_native.report import Report

# Apple's own marketing convention: 9:41, full battery, full bars, no carrier.
DEFAULT_STATUS_BAR = {
    "time": "9:41",
    "dataNetwork": "wifi",
    "wifiMode": "active",
    "wifiBars": 3,
    "cellularMode": "active",
    "cellularBars": 4,
    "operatorName": "",
    "batteryState": "charged",
    "batteryLevel": 100,
}
STATUS_BAR_FLAGS = set(DEFAULT_STATUS_BAR)
APPEARANCES = ("light", "dark")
LOCALE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z]{4})?(?:-[A-Z]{2})?$")
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
MAX_CAPTURES = 400


class PlanError(ValueError):
    pass


# --------------------------------------------------------------------------- #
# Plan
# --------------------------------------------------------------------------- #


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower() or "device"


def apple_language(locale: str) -> str:
    return locale


def apple_locale(locale: str) -> str:
    parts = locale.split("-")
    if len(parts) >= 2 and len(parts[-1]) == 2 and parts[-1].isupper():
        return f"{parts[0]}_{parts[-1]}"
    return parts[0]


def load_plan(path: Path) -> Dict[str, object]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PlanError(f"cannot read plan {path}: {exc}") from exc
    if not isinstance(plan, dict):
        raise PlanError("plan must be a JSON object")

    bundle_id = plan.get("bundle_id")
    if not isinstance(bundle_id, str) or not re.match(r"^[A-Za-z0-9.-]+$", bundle_id):
        raise PlanError("plan.bundle_id must be a reverse-DNS bundle identifier")

    devices = plan.get("devices")
    if not isinstance(devices, list) or not devices or not all(isinstance(d, str) and d.strip() for d in devices):
        raise PlanError("plan.devices must be a non-empty list of simulator names or slot ids")

    locales = plan.get("locales") or ["en-US"]
    if not all(isinstance(l, str) and LOCALE.match(l) for l in locales):
        raise PlanError("plan.locales must look like 'en-US', 'tr-TR', 'zh-Hans-CN' or 'de'")

    appearances = plan.get("appearances") or ["light"]
    if not all(a in APPEARANCES for a in appearances):
        raise PlanError("plan.appearances accepts 'light' and 'dark'")

    screens = plan.get("screens") or [{"name": "01-launch"}]
    for screen in screens:
        if not isinstance(screen, dict) or not SAFE_NAME.match(str(screen.get("name", ""))):
            raise PlanError("each screen needs a file-safe 'name' such as '01-home'")
        if "arguments" in screen and not all(isinstance(a, str) for a in screen["arguments"]):
            raise PlanError(f"screen {screen['name']}: arguments must be strings")
        if "url" in screen and not isinstance(screen["url"], str):
            raise PlanError(f"screen {screen['name']}: url must be a string")
        if "env" in screen and not (isinstance(screen["env"], dict) and all(
                re.match(r"^[A-Z][A-Z0-9_]*$", key) and isinstance(value, (str, int)) for key, value in screen["env"].items())):
            raise PlanError(f"screen {screen['name']}: env must map UPPER_CASE names to strings")

    status_bar = dict(DEFAULT_STATUS_BAR)
    custom = plan.get("status_bar")
    if custom is False:
        status_bar = {}
    elif isinstance(custom, dict):
        unknown = set(custom) - STATUS_BAR_FLAGS
        if unknown:
            raise PlanError(f"unknown status_bar keys: {', '.join(sorted(unknown))}")
        status_bar.update(custom)

    launch_arguments = plan.get("launch_arguments") or []
    if not all(isinstance(a, str) for a in launch_arguments):
        raise PlanError("plan.launch_arguments must be strings")

    total = len(devices) * len(locales) * len(appearances) * len(screens)
    if total > MAX_CAPTURES:
        raise PlanError(f"plan expands to {total} captures; split it (limit {MAX_CAPTURES})")

    return {
        "bundle_id": bundle_id,
        "app": plan.get("app"),
        "devices": [d.strip() for d in devices],
        "locales": locales,
        "appearances": appearances,
        "screens": screens,
        "status_bar": status_bar,
        "launch_arguments": launch_arguments,
        "settle_seconds": float(plan.get("settle_seconds", 3)),
        "shutdown_after": bool(plan.get("shutdown_after", False)),
        "flatten": bool(plan.get("flatten", True)),
        "env": {key: str(value) for key, value in (plan.get("env") or {}).items()},
    }


def device_name_for(entry: str) -> str:
    """Accept a slot id (``iphone-6.9``) or a simulator name (``iPhone 18 Pro``)."""

    for slot in screenshot_slots():
        if entry == slot["id"]:
            if not slot.get("simulator"):
                raise PlanError(f"slot {entry} has no current simulator; capture on a physical device instead")
            return slot["simulator"]
    return entry


# --------------------------------------------------------------------------- #
# Simulator access
# --------------------------------------------------------------------------- #


Runner = Callable[[Sequence[str], float], subprocess.CompletedProcess]


def default_runner(command: Sequence[str], timeout: float,
                   env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    merged = None
    if env:
        import os
        merged = {**os.environ, **env}
    return subprocess.run(list(command), capture_output=True, text=True, timeout=timeout, env=merged)


class Simulator:
    def __init__(self, runner: Runner, log: List[Dict[str, object]], dry_run: bool) -> None:
        self.runner = runner
        self.log = log
        self.dry_run = dry_run
        self._inventory: Optional[Dict[str, object]] = None

    def run(self, *args: str, timeout: float = 120, mutate: bool = True,
            check: bool = True, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        command = ["xcrun", "simctl", *args]
        if env:
            # simctl forwards SIMCTL_CHILD_<NAME> to the launched app as <NAME>.
            command_env = {f"SIMCTL_CHILD_{key}": str(value) for key, value in env.items()}
            prefix = [f"{key}={value}" for key, value in command_env.items()]
        else:
            command_env, prefix = None, []
        if self.dry_run and mutate:
            self.log.append({"command": ["env", *prefix, *command] if prefix else command, "executed": False})
            return subprocess.CompletedProcess(command, 0, "", "")
        result = self.runner(command, timeout, command_env) if command_env else self.runner(command, timeout)
        if mutate:
            self.log.append({"command": command, "executed": True, "exit": result.returncode})
        if result.returncode != 0 and check:
            raise RuntimeError(f"{' '.join(command)} failed: {(result.stderr or result.stdout).strip()[:400]}")
        return result

    def inventory(self) -> Dict[str, object]:
        if self._inventory is None:
            try:
                # A dry run must stay fast: CoreSimulator can take minutes to start on a cold machine (CI).
                payload = json.loads(self.run("list", "--json", mutate=False,
                                              timeout=15 if self.dry_run else 300).stdout or "{}")
            except (subprocess.TimeoutExpired, RuntimeError, ValueError):
                if not self.dry_run:
                    raise
                payload = {"devices": {}, "devicetypes": [], "runtimes": []}
            self._inventory = payload
        return self._inventory

    def resolve(self, name: str) -> Dict[str, str]:
        payload = self.inventory()
        device_types = {t["name"]: t["identifier"] for t in payload.get("devicetypes", [])}
        runtimes = [r for r in payload.get("runtimes", []) if r.get("isAvailable")]
        candidates = []
        for runtime_id, entries in payload.get("devices", {}).items():
            for entry in entries:
                # Reuse a simulator this tool created earlier ("ANE <name>") instead of adding another.
                if entry.get("name") in (name, f"ANE {name}") and entry.get("isAvailable", True):
                    candidates.append((runtime_id, entry))
        if candidates:
            candidates.sort(key=lambda item: (item[1].get("state") == "Booted", item[1].get("name") == name, item[0]),
                            reverse=True)
            runtime_id, entry = candidates[0]
            return {"udid": entry["udid"], "name": name, "runtime": runtime_id, "created": "no",
                    "state": entry.get("state", "Shutdown")}

        type_id = device_types.get(name)
        if not type_id:
            close = [n for n in device_types if name.lower().split(" (")[0] in n.lower()][:5]
            raise PlanError(f"no simulator device type named {name!r}" + (f"; did you mean {close}?" if close else ""))
        family = name.split(" ")[0].lower()
        family_runtime = {"iphone": "iOS", "ipad": "iOS", "apple": None}.get(family)
        if name.startswith("Apple TV"):
            family_runtime = "tvOS"
        elif name.startswith("Apple Watch"):
            family_runtime = "watchOS"
        elif name.startswith("Apple Vision"):
            family_runtime = "visionOS"
        matching = [r for r in runtimes if family_runtime and r.get("platform", r.get("name", "")).startswith(family_runtime)]
        supported = [r for r in matching if not r.get("supportedDeviceTypes")
                     or any(t.get("identifier") == type_id for t in r.get("supportedDeviceTypes", []))]
        if not supported:
            raise PlanError(f"no installed {family_runtime or 'matching'} runtime supports {name!r}; "
                            "install one in Xcode › Settings › Components")
        runtime = sorted(supported, key=lambda r: [int(p) for p in re.findall(r"\d+", r.get("version", "0"))])[-1]
        label = f"ANE {name}"
        created = self.run("create", label, type_id, runtime["identifier"], timeout=120)
        udid = created.stdout.strip() or f"<new {name}>"
        return {"udid": udid, "name": name, "runtime": runtime["identifier"], "created": "yes", "state": "Shutdown"}


# --------------------------------------------------------------------------- #
# Capture
# --------------------------------------------------------------------------- #


def capture(plan: Dict[str, object], out: Path, report: Report, *, dry_run: bool,
            runner: Runner = default_runner, sleep: Callable[[float], None] = time.sleep) -> None:
    log: List[Dict[str, object]] = []
    simulator = Simulator(runner, log, dry_run)
    files: List[Dict[str, object]] = []
    devices_used: List[Dict[str, str]] = []

    if dry_run and shutil.which("xcrun") is None:
        simulator.inventory = lambda: {"devices": {}, "devicetypes": [], "runtimes": []}  # type: ignore[assignment]

    for entry in plan["devices"]:
        name = device_name_for(entry)
        try:
            device = simulator.resolve(name)
        except PlanError as exc:
            if dry_run:
                device = {"udid": f"<{name}>", "name": name, "runtime": "<newest installed>", "created": "planned",
                          "state": "Shutdown"}
                report.info("CAP011", f"Dry run: {exc}")
            else:
                report.error("CAP010", str(exc), hint="List device types with: xcrun simctl list devicetypes")
                continue
        udid = device["udid"]
        devices_used.append(device)
        device_dir = slug(name)

        if device.get("state") != "Booted":
            simulator.run("boot", udid, timeout=300)
        simulator.run("bootstatus", udid, "-b", timeout=600)
        if plan["status_bar"]:
            flags: List[str] = []
            for key, value in plan["status_bar"].items():
                flags += [f"--{key}", str(value)]
            try:
                simulator.run("status_bar", udid, "override", *flags)
            except RuntimeError as exc:  # watchOS and older runtimes reject some flags
                report.warn("CAP020", f"{name}: status bar override not applied ({exc}).",
                            hint="Captures continue with the live status bar; check them before upload.")
        if plan.get("app"):
            simulator.run("install", udid, str(plan["app"]), timeout=600)

        for appearance in plan["appearances"]:
            try:
                simulator.run("ui", udid, "appearance", appearance)
            except RuntimeError as exc:
                report.warn("CAP021", f"{name}: appearance '{appearance}' not supported ({exc}).")
                continue
            for locale in plan["locales"]:
                for screen in plan["screens"]:
                    # A fresh launch per locale: the argument domain is read at launch.
                    simulator.run("terminate", udid, plan["bundle_id"], timeout=60, check=False)
                    arguments = ["-AppleLanguages", f"({apple_language(locale)})", "-AppleLocale", apple_locale(locale)]
                    arguments += list(plan["launch_arguments"]) + list(screen.get("arguments", []))
                    environment = {**plan["env"], **(screen.get("env") or {}), "APPLE_LOCALE": locale}
                    simulator.run("launch", udid, plan["bundle_id"], *arguments, timeout=120, env=environment)
                    if screen.get("url"):
                        simulator.run("openurl", udid, screen["url"], timeout=60)
                    if not dry_run:
                        sleep(plan["settle_seconds"])
                    suffix = f"-{appearance}" if len(plan["appearances"]) > 1 else ""
                    target = out / locale / device_dir / f"{screen['name']}{suffix}.png"
                    if not dry_run:
                        target.parent.mkdir(parents=True, exist_ok=True)
                    simulator.run("io", udid, "screenshot", "--type=png", str(target), timeout=120)
                    record: Dict[str, object] = {"file": str(target.relative_to(out)), "device": name,
                                                 "locale": locale, "appearance": appearance, "screen": screen["name"]}
                    if not dry_run:
                        try:
                            info = image_info(target)
                            record["size"] = f"{info.width}x{info.height}"
                            record["alpha"] = info.has_alpha
                        except (UnsupportedImage, OSError) as exc:
                            report.error("CAP030", f"Capture unreadable: {target.name}: {exc}")
                    files.append(record)
        if plan["status_bar"]:
            try:
                simulator.run("status_bar", udid, "clear")
            except RuntimeError:
                pass
        if plan["shutdown_after"]:
            simulator.run("shutdown", udid, timeout=120)

    custom = sorted({screen["url"].split(":")[0] for screen in plan["screens"]
                     if screen.get("url") and not screen["url"].startswith(("http://", "https://"))})
    if custom:
        report.warn("CAP040", f"Deep links with custom schemes ({', '.join(custom)}) make iOS show an "
                    "\"Open in …?\" confirmation that can appear in the capture.",
                    hint="Prefer launch arguments (-screen <name>) read from UserDefaults / Settings.get / "
                         "SharedPreferencesAsync, or universal links.")

    report.data.update({
        "dry_run": dry_run,
        "output": str(out),
        "devices": devices_used,
        "captures": files,
        "capture_count": len(files),
        "commands": [shlex.join(entry["command"]) for entry in log],
    })

    if dry_run:
        report.info("CAP001", f"Dry run: {len(files)} capture(s) planned across {len(devices_used)} device(s); "
                    "nothing was executed.", hint="Re-run without --dry-run to capture.")
        return

    if plan["flatten"]:
        flatten_captures(out, files, report)

    manifest = {
        "tool": "capture-batch",
        "tool_version": __version__,
        "captured_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "bundle_id": plan["bundle_id"],
        "devices": devices_used,
        "captures": files,
        "status_bar": plan["status_bar"],
        "scope": "Real Simulator captures. Each file is what the app rendered; nothing was drawn or edited.",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report.info("CAP002", f"Captured {len(files)} screenshot(s); manifest written to {out / 'manifest.json'}.",
                hint="Next: audit_screenshots on this folder, then compose_marketing_screenshots.")

    slots = {tuple(size) for slot in screenshot_slots() for key in ("portrait", "landscape") for size in slot[key]}
    for record in files:
        size = record.get("size")
        if size and tuple(int(v) for v in size.split("x")) not in slots:
            report.warn("CAP031", f"{record['file']} is {size}, not an App Store slot.",
                        hint="Use a device listed in data/app-store-specs.json (field 'simulator').")
        if record.get("alpha"):
            report.error("CAP032", f"{record['file']} has an alpha channel; App Store Connect rejects it.")


def flatten_captures(out: Path, files: List[Dict[str, object]], report: Report) -> None:
    """Simulator PNGs carry an alpha channel; App Store Connect rejects alpha."""

    targets = [out / str(record["file"]) for record in files if record.get("alpha")]
    if not targets:
        return
    try:
        result = native.flatten(targets)
    except (native.NativeError, OSError, subprocess.TimeoutExpired) as exc:
        report.warn("CAP033", f"Could not flatten captures to opaque RGB: {exc}",
                    hint="Flatten before upload, or compose them with compose_marketing_screenshots.")
        return
    for record in files:
        if record.get("alpha"):
            info = image_info(out / str(record["file"]))
            record["alpha"] = info.has_alpha
            record["flattened"] = not info.has_alpha
    report.info("CAP034", f"Flattened {len(targets) - len(result.get('errors', []))} capture(s) to opaque RGB PNG "
                "(Simulator screenshots include an alpha channel App Store Connect rejects).")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="capture-batch",
        description="Capture App Store screenshots in the Simulator across devices, locales and appearances.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("plan", help="Capture plan JSON (see the module docstring)")
    parser.add_argument("--out", required=True, help="Output root: <out>/<locale>/<device>/<screen>.png")
    parser.add_argument("--dry-run", action="store_true", help="Print the simctl commands; execute nothing")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    args = parser.parse_args(argv)

    plan_path = Path(args.plan).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    report = Report(tool="capture-batch", target=str(plan_path), version=__version__)

    try:
        plan = load_plan(plan_path)
    except PlanError as exc:
        report.error("CAP100", str(exc), hint="See tools/screenshot-studio/capture_batch.py for the plan format.")
        return emit(report, args, title="Apple Native Engineer — Screenshot capture")

    if plan.get("app"):
        app = Path(str(plan["app"])).expanduser()
        if not app.is_absolute():
            app = (plan_path.parent / app).resolve()
        if not args.dry_run and not app.exists():
            report.error("CAP101", f"App bundle not found: {app}",
                         hint="Build for the Simulator first. Swift: xcodebuild -scheme <App> -destination "
                              "'generic/platform=iOS Simulator' -derivedDataPath build build · Flutter: flutter build "
                              "ios --simulator (build/ios/iphonesimulator/Runner.app) · React Native/Expo: "
                              "npx expo run:ios --configuration Release, or xcodebuild on ios/<App>.xcworkspace "
                              "with -sdk iphonesimulator · Capacitor: npx cap sync ios, then xcodebuild on ios/App.")
            return emit(report, args, title="Apple Native Engineer — Screenshot capture")
        plan["app"] = str(app)

    if not args.dry_run and shutil.which("xcrun") is None:
        report.error("CAP003", "xcrun is not available; capture requires macOS with Xcode.",
                     hint="Use --dry-run to review the plan on this machine.")
        return emit(report, args, title="Apple Native Engineer — Screenshot capture")

    try:
        capture(plan, out, report, dry_run=args.dry_run)
    except (RuntimeError, subprocess.TimeoutExpired, PlanError) as exc:
        report.error("CAP004", f"Capture stopped: {exc}",
                     hint="Fix the failing step; files already captured are kept.")
    return emit(report, args, title="Apple Native Engineer — Screenshot capture")


if __name__ == "__main__":
    raise SystemExit(main())
