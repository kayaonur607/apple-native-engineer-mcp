#!/usr/bin/env python3
"""Distribution planner — archive, export, TestFlight / App Store upload, Developer ID notarization.

Reads the project (``project.pbxproj``, Info.plist, entitlements, shared schemes)
and produces:

* preflight findings that commonly stop a build at upload or review time —
  missing team, version or build number, export-compliance key, hardened
  runtime for Developer ID, App Sandbox for the Mac App Store, debug
  entitlements, missing privacy manifest or app icon,
* an ``ExportOptions.plist`` for the chosen method, using the keys
  ``xcodebuild -help`` documents (written only with ``--write-export-options``),
* the exact, ordered command sequence for the method: archive, export or upload,
  validation, notarization, stapling and Gatekeeper assessment.

It never runs ``xcodebuild``, uploads a build or contacts Apple. Signing and
uploading change account state, so the host AI shows the plan and runs each
step only with the developer's approval.

Methods::

    app-store         App Store / TestFlight (xcodebuild method app-store-connect)
    testflight-internal  App Store Connect, internal TestFlight only
    release-testing   Ad hoc devices (formerly ad-hoc)
    enterprise        In-house distribution (Enterprise Program)
    debugging         Development-signed build (formerly development)
    developer-id      macOS outside the Mac App Store, notarized
    mac-app-store     macOS App Store (app-store-connect, sandbox required)

Usage::

    python3 tools/distribution/plan_distribution.py . --method app-store --scheme Planner
    python3 tools/distribution/plan_distribution.py . --method developer-id --write-export-options build/ExportOptions.plist
"""

from __future__ import annotations

import plistlib
import re
import shlex
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit, guard_directory
from apple_native.report import Report
from apple_native.frameworks import detect as detect_framework, xcode_containers
from apple_native.xcode import discover, read_plist

METHODS = {
    "app-store": {"export": "app-store-connect", "platforms": {"iOS", "tvOS", "visionOS", "watchOS"}},
    "testflight-internal": {"export": "app-store-connect", "platforms": {"iOS", "tvOS", "visionOS", "watchOS", "macOS"}},
    "release-testing": {"export": "release-testing", "platforms": {"iOS", "tvOS", "visionOS", "watchOS"}},
    "enterprise": {"export": "enterprise", "platforms": {"iOS", "tvOS", "visionOS", "watchOS"}},
    "debugging": {"export": "debugging", "platforms": {"iOS", "tvOS", "visionOS", "watchOS", "macOS"}},
    "developer-id": {"export": "developer-id", "platforms": {"macOS"}},
    "mac-app-store": {"export": "app-store-connect", "platforms": {"macOS"}},
}
DESTINATIONS = {
    "iOS": "generic/platform=iOS",
    "macOS": "generic/platform=macOS",
    "tvOS": "generic/platform=tvOS",
    "visionOS": "generic/platform=visionOS",
    "watchOS": "generic/platform=watchOS",
}
SDKROOT_PLATFORM = {"iphoneos": "iOS", "macosx": "macOS", "appletvos": "tvOS", "xros": "visionOS", "watchos": "watchOS"}
DOCS = {
    "export": "https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases",
    "notarize": "https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution",
    "encryption": "https://developer.apple.com/documentation/security/complying-with-encryption-export-regulations",
    "sandbox": "https://developer.apple.com/documentation/security/app-sandbox",
    "hardened": "https://developer.apple.com/documentation/security/hardened-runtime",
}


def build_settings(root: Path) -> Dict[str, List[str]]:
    """Every value assigned to the build settings we care about, across all configurations."""

    keys = ("DEVELOPMENT_TEAM", "CODE_SIGN_STYLE", "MARKETING_VERSION", "CURRENT_PROJECT_VERSION",
            "ENABLE_HARDENED_RUNTIME", "INFOPLIST_KEY_ITSAppUsesNonExemptEncryption", "CODE_SIGN_ENTITLEMENTS",
            "ASSETCATALOG_COMPILER_APPICON_NAME", "SDKROOT", "SUPPORTED_PLATFORMS", "PRODUCT_BUNDLE_IDENTIFIER",
            "VERSIONING_SYSTEM", "ENABLE_APP_SANDBOX")
    found: Dict[str, List[str]] = {key: [] for key in keys}
    for pbx in sorted(path / "project.pbxproj" for path in xcode_containers(root) if path.suffix == ".xcodeproj"):
        text = pbx.read_text(encoding="utf-8", errors="ignore")
        for key in keys:
            for value in re.findall(rf"\b{key}\s*=\s*\"?([^\";\n]*)\"?\s*;", text):
                value = value.strip()
                if value and value not in found[key]:
                    found[key].append(value)
    return found


def shared_schemes(root: Path) -> List[str]:
    schemes = []
    for container in xcode_containers(root):
        for scheme in sorted(container.glob("xcshareddata/xcschemes/*.xcscheme")):
            if scheme.stem not in schemes:
                schemes.append(scheme.stem)
    return schemes


def detect_platform(project, settings: Dict[str, List[str]]) -> str:
    for sdk in settings["SDKROOT"]:
        if sdk in SDKROOT_PLATFORM:
            return SDKROOT_PLATFORM[sdk]
    for platform in ("iOS", "macOS", "visionOS", "tvOS", "watchOS"):
        if platform in project.deployment_targets:
            return platform
    return "iOS"


def export_options(method: str, platform: str, team: Optional[str], style: Optional[str],
                   upload: bool) -> Dict[str, object]:
    spec = METHODS[method]
    options: Dict[str, object] = {"method": spec["export"]}
    if spec["export"] == "app-store-connect":
        options["destination"] = "upload" if upload else "export"
        options["uploadSymbols"] = True
        options["manageAppVersionAndBuildNumber"] = False
        if method == "testflight-internal":
            options["testFlightInternalTestingOnly"] = True
    else:
        options["destination"] = "export"
    if spec["export"] in ("release-testing", "enterprise", "debugging") and platform != "macOS":
        options["thinning"] = "<none>"
    if spec["export"] in ("release-testing", "enterprise", "debugging", "app-store-connect") and platform != "macOS":
        options["stripSwiftSymbols"] = True
    if team:
        options["teamID"] = team
    options["signingStyle"] = "manual" if (style or "").lower() == "manual" else "automatic"
    return options


def q(value: str) -> str:
    return shlex.quote(value)


def plan_steps(method: str, platform: str, container: Optional[str], scheme: str, archive: str,
               export_dir: str, options_path: str, upload: bool, app_name: str) -> List[Dict[str, object]]:
    selector = []
    if container:
        selector = ["-workspace" if container.endswith(".xcworkspace") else "-project", container]
    auth = ("-allowProvisioningUpdates -authenticationKeyPath \"$ASC_PRIVATE_KEY_PATH\" "
            "-authenticationKeyID \"$ASC_KEY_ID\" -authenticationKeyIssuerID \"$ASC_ISSUER_ID\"")
    steps: List[Dict[str, object]] = [{
        "step": "archive",
        "purpose": "Build a Release archive for distribution.",
        "command": " ".join(["xcodebuild", "archive", *map(q, selector), "-scheme", q(scheme), "-configuration",
                             "Release", "-destination", q(DESTINATIONS[platform]), "-archivePath", q(archive),
                             auth]),
        "writes": archive, "network": "signing assets only (with -allowProvisioningUpdates)",
    }]
    export_cmd = " ".join(["xcodebuild", "-exportArchive", "-archivePath", q(archive), "-exportPath", q(export_dir),
                           "-exportOptionsPlist", q(options_path), auth])
    spec = METHODS[method]
    if spec["export"] == "app-store-connect" and upload:
        steps.append({"step": "upload", "purpose": "Re-sign for App Store Connect and upload in one step "
                      "(ExportOptions destination=upload).", "command": export_cmd, "writes": export_dir,
                      "network": "uploads the build to App Store Connect", "requires_approval": True})
    else:
        steps.append({"step": "export", "purpose": f"Export a signed {spec['export']} build.", "command": export_cmd,
                      "writes": export_dir, "network": "signing assets only"})

    if spec["export"] == "app-store-connect" and not upload:
        package = f"{export_dir}/{app_name}.{'pkg' if platform == 'macOS' else 'ipa'}"
        steps.append({"step": "validate", "purpose": "Ask App Store Connect to validate before uploading.",
                      "command": f"xcrun altool --validate-app {q(package)} "
                                 "--api-key \"$ASC_KEY_ID\" --api-issuer \"$ASC_ISSUER_ID\"",
                      "network": "contacts App Store Connect (read-only validation)"})
        steps.append({"step": "upload", "purpose": "Upload the exported package to App Store Connect.",
                      "command": f"xcrun altool --upload-package {q(package)} --api-key \"$ASC_KEY_ID\" "
                                 "--api-issuer \"$ASC_ISSUER_ID\" --wait",
                      "network": "uploads the build to App Store Connect", "requires_approval": True,
                      "note": "altool looks for AuthKey_<KEY_ID>.p8 in ~/.appstoreconnect/private_keys or "
                              "$API_PRIVATE_KEYS_DIR."})
    if spec["export"] == "app-store-connect":
        steps.append({"step": "confirm-processing", "purpose": "Confirm the build finished processing.",
                      "command": "app_store_connect operation=builds app_id=<APP_ID>  (this MCP, read-only)",
                      "network": "read-only App Store Connect query"})

    if method == "developer-id":
        app = f"{export_dir}/{app_name}.app"
        zip_path = f"{export_dir}/{app_name}.zip"
        steps += [
            {"step": "zip", "purpose": "Package the app for the notary service.",
             "command": f"ditto -c -k --keepParent {q(app)} {q(zip_path)}", "writes": zip_path},
            {"step": "notarize", "purpose": "Submit to Apple's notary service and wait for the verdict.",
             "command": f"xcrun notarytool submit {q(zip_path)} --key \"$ASC_PRIVATE_KEY_PATH\" --key-id \"$ASC_KEY_ID\" "
                        "--issuer \"$ASC_ISSUER_ID\" --wait",
             "network": "uploads the archive to the notary service", "requires_approval": True,
             "note": "On rejection: xcrun notarytool log <submission-id> --key … for the exact reasons."},
            {"step": "staple", "purpose": "Attach the ticket so Gatekeeper works offline.",
             "command": f"xcrun stapler staple {q(app)}", "writes": app},
            {"step": "assess", "purpose": "Confirm Gatekeeper accepts the notarized app.",
             "command": f"spctl --assess --type execute -vv {q(app)}"},
            {"step": "disk-image", "purpose": "Optional: ship a DMG; notarize and staple the DMG too.",
             "command": f"hdiutil create -volname {q(app_name)} -srcfolder {q(app)} -ov -format UDZO "
                        f"{q(export_dir + '/' + app_name + '.dmg')}", "optional": True},
        ]
    return steps


def lockfile_install(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm install --frozen-lockfile"
    if (root / "yarn.lock").exists():
        return "yarn install --frozen-lockfile"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        return "bun install --frozen-lockfile"
    return "npm ci"


def framework_steps(framework, root: Path, method: str, platform: str, options_path: str,
                    steps: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Adapt the native plan to Flutter, React Native, Expo, Capacitor, MAUI or KMP."""

    name = framework.framework
    host = framework.hosts.get(platform)
    pods = f"cd {q(host)} && pod install" if host and (root / host / "Podfile").exists() else None
    prepare: List[Dict[str, object]] = []
    if name == "flutter":
        prepare.append({"step": "prepare", "purpose": "Fetch Dart packages.", "command": "flutter pub get"})
        if platform == "iOS" and METHODS[method]["export"] != "developer-id":
            export_method = {"app-store-connect": "app-store", "release-testing": "ad-hoc", "enterprise": "enterprise",
                             "debugging": "development"}.get(METHODS[method]["export"], "app-store")
            build = {"step": "archive", "purpose": "Build the Flutter app, archive and export an IPA "
                     "(build/ios/archive, build/ios/ipa).",
                     "command": f"flutter build ipa --release --export-options-plist={q(options_path)}",
                     "writes": "build/ios/archive, build/ios/ipa", "network": "signing assets only",
                     "note": f"Without an options plist: --export-method {export_method}. Override version/build "
                             "with --build-name/--build-number (pubspec version is the default)."}
            rest = [step for step in steps if step["step"] not in ("archive", "export")]
            for step in rest:
                if isinstance(step.get("command"), str):
                    step["command"] = re.sub(r"build/export-[\w-]+/\S+\.ipa", "build/ios/ipa/*.ipa", step["command"])
            return prepare + [build] + rest
        prepare.append({"step": "prepare-macos", "purpose": "Build the Flutter macOS app once so the Xcode "
                        "workspace has its generated files.", "command": "flutter build macos --release"})
    elif name in ("react-native", "expo") and not framework.managed:
        prepare.append({"step": "prepare", "purpose": "Install JavaScript dependencies.", "command": lockfile_install(root)})
        if pods:
            prepare.append({"step": "pods", "purpose": "Install CocoaPods for the native host.", "command": pods})
        if name == "expo":
            prepare.append({"step": "note", "purpose": "Continuous Native Generation: `npx expo prebuild` regenerates "
                            "ios/. Keep native changes in config plugins or they are lost.", "command": "# informational"})
    elif name == "expo" and framework.managed:
        profile = "production"
        submit = [{"step": "build", "purpose": "Build in EAS (cloud; EAS plan limits apply) — or add --local to build "
                   "on this Mac.", "command": f"npx eas-cli@latest build -p ios --profile {profile}",
                   "network": "uploads the project to EAS Build"},
                  {"step": "upload", "purpose": "Submit the latest build to App Store Connect / TestFlight.",
                   "command": "npx eas-cli@latest submit -p ios --latest", "network": "uploads the build to App Store Connect",
                   "requires_approval": True},
                  {"step": "confirm-processing", "purpose": "Confirm the build finished processing.",
                   "command": "app_store_connect operation=builds app_id=<APP_ID>  (this MCP, read-only)"}]
        alternative = {"step": "alternative-local", "purpose": "Without EAS: generate the native host, then use the "
                       "Xcode steps (re-run plan_distribution after prebuild).", "command": "npx expo prebuild -p ios",
                       "optional": True}
        return [{"step": "prepare", "purpose": "Install JavaScript dependencies.", "command": lockfile_install(root)}] + submit + [alternative]
    elif name == "capacitor":
        prepare += [{"step": "prepare", "purpose": "Build the web assets and copy them into the iOS host.",
                     "command": f"{lockfile_install(root)} && npm run build && npx cap sync ios"}]
    elif name == "maui":
        tfm = "net10.0-ios" if platform == "iOS" else "net10.0-maccatalyst"
        if framework.version:
            match = re.search(r"net[\d.]+-(ios|maccatalyst)", framework.version)
            wanted = "ios" if platform == "iOS" else "maccatalyst"
            found = re.findall(rf"net[\d.]+-{wanted}", framework.version)
            tfm = found[0] if found else tfm
        project = framework.config_files[0] if framework.config_files else "App.csproj"
        build = {"step": "archive", "purpose": "Publish a signed, archived .NET MAUI app.",
                 "command": f"dotnet publish {q(project)} -f {tfm} -c Release -p:ArchiveOnBuild=true",
                 "writes": "bin/Release/<tfm>/<rid>/publish"}
        rest = [step for step in steps if step["step"] not in ("archive", "export")]
        return [build] + rest
    elif name == "kmp":
        prepare.append({"step": "prepare", "purpose": "Build the shared Kotlin framework (Xcode's build phase "
                        "also runs Gradle).", "command": "./gradlew :shared:assemble"})
    return prepare + steps


def main(argv=None) -> int:
    parser = build_parser("distribution-planner",
                          "Plan archive, export, upload and notarization for an Apple app, with preflight checks.",
                          epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.")
    parser.add_argument("--method", default="app-store", choices=sorted(METHODS))
    parser.add_argument("--scheme", help="Scheme to archive (default: the only shared scheme, else the first target)")
    parser.add_argument("--platform", choices=sorted(DESTINATIONS), help="Override the detected platform")
    parser.add_argument("--upload", action="store_true",
                        help="App Store methods: upload during export (ExportOptions destination=upload)")
    parser.add_argument("--build-dir", default="build", help="Where archives and exports go (default: build)")
    parser.add_argument("--write-export-options", metavar="PATH", help="Write the generated ExportOptions.plist here")
    args = parser.parse_args(argv)

    guard = guard_directory("distribution-planner", args.path)
    if guard:
        return emit(guard, args)
    root = Path(args.path).expanduser().resolve()
    report = Report(tool="distribution-planner", target=str(root), version=__version__)
    project = discover(root)
    settings = build_settings(root)
    framework = detect_framework(root)
    if framework.framework == "flutter" and any("FLUTTER_BUILD" in value for value in settings["CURRENT_PROJECT_VERSION"]):
        build_number = (framework.app_version or "").partition("+")[2]
        settings["CURRENT_PROJECT_VERSION"] = [f"{build_number} (pubspec.yaml)"] if build_number else []
    if framework.framework == "flutter" and any("FLUTTER_BUILD" in value for value in settings["MARKETING_VERSION"]):
        settings["MARKETING_VERSION"] = [f"{framework.app_version.partition('+')[0]} (pubspec.yaml)"] if framework.app_version else []

    container = (project.workspace_files or project.project_files or [None])[0]
    if container is None and framework.framework == "expo" and framework.managed:
        report.info("DST002", "Expo app without a checked-in ios/ host: EAS Build generates it, so Xcode-level "
                    "checks run on app.json instead (see audit_cross_platform).")
    elif container is None:
        report.error("DST001", "No .xcodeproj or .xcworkspace found; an app archive needs an Xcode project.",
                     hint="Swift packages are distributed as source. Add an app target in Xcode to archive an app.")
    platform = args.platform or ("iOS" if framework.framework != "native" and framework.hosts.get("iOS")
                                 else detect_platform(project, settings))
    if framework.framework == "expo" and framework.managed and not args.platform:
        platform = "iOS"
    if platform not in METHODS[args.method]["platforms"]:
        report.error("DST060", f"Method '{args.method}' does not apply to {platform}.",
                     hint="macOS uses developer-id or mac-app-store; other platforms use app-store, "
                          "testflight-internal, release-testing, enterprise or debugging.")

    schemes = shared_schemes(root)
    scheme = args.scheme or (schemes[0] if len(schemes) == 1 else (schemes or project.targets or ["<Scheme>"])[0])
    if container and not schemes:
        report.warn("DST012", "No shared schemes (xcshareddata/xcschemes).",
                    hint="Product › Scheme › Manage Schemes › Shared, so CI and other machines can archive.")

    team = settings["DEVELOPMENT_TEAM"][0] if settings["DEVELOPMENT_TEAM"] else None
    style = settings["CODE_SIGN_STYLE"][0] if settings["CODE_SIGN_STYLE"] else None
    if container and not team:
        report.warn("DST010", "No DEVELOPMENT_TEAM in the project; export needs a team.",
                    hint="Set the team in Signing & Capabilities, or pass teamID in ExportOptions.plist.")
    if len(settings["DEVELOPMENT_TEAM"]) > 1:
        report.warn("DST013", f"Several development teams are set: {', '.join(settings['DEVELOPMENT_TEAM'])}.",
                    hint="Every target in one upload must be signed by the same team.")

    if container and not settings["MARKETING_VERSION"]:
        report.warn("DST020", "No MARKETING_VERSION build setting (the version customers see).",
                    hint="Set Version in the target's General tab, or CFBundleShortVersionString in Info.plist.")
    if container and not settings["CURRENT_PROJECT_VERSION"]:
        report.warn("DST021", "No CURRENT_PROJECT_VERSION (build number).",
                    hint="Each upload needs a higher build number for the same version.")
    elif settings["CURRENT_PROJECT_VERSION"]:
        report.info("DST022", f"Build number(s): {', '.join(settings['CURRENT_PROJECT_VERSION'])}. "
                    "Increase it before every upload (agvtool next-version -all, or the target's Build field).")

    plists = [read_plist(path) or {} for path in project.info_plists]
    expo_ios = ((framework.expo_config or {}).get("ios") or {}) if framework.framework == "expo" else {}
    encryption_declared = bool(settings["INFOPLIST_KEY_ITSAppUsesNonExemptEncryption"]) or any(
        "ITSAppUsesNonExemptEncryption" in plist for plist in plists) or \
        "usesNonExemptEncryption" in (expo_ios.get("config") or {}) or \
        "ITSAppUsesNonExemptEncryption" in (expo_ios.get("infoPlist") or {})
    if framework.framework == "expo" and framework.managed and not expo_ios.get("bundleIdentifier"):
        report.error("DST003", "expo.ios.bundleIdentifier is missing; EAS cannot build or submit.",
                     hint="Set ios.bundleIdentifier in app.json to the App Store Connect bundle ID.")
    if METHODS[args.method]["export"] == "app-store-connect" and not encryption_declared:
        report.warn("DST030", "ITSAppUsesNonExemptEncryption is not declared.",
                    hint="Without it every build waits for an export-compliance answer in App Store Connect. "
                         "Set it to NO when the app uses only exempt encryption (HTTPS, Apple APIs).",
                    docs=DOCS["encryption"])

    entitlements = {path: read_plist(path) or {} for path in project.entitlements}
    if args.method == "developer-id" and "YES" not in settings["ENABLE_HARDENED_RUNTIME"]:
        report.error("DST040", "Hardened Runtime is not enabled; notarization requires it.",
                     hint="Signing & Capabilities › + Capability › Hardened Runtime (ENABLE_HARDENED_RUNTIME = YES).",
                     docs=DOCS["hardened"])
    if args.method == "mac-app-store":
        sandboxed = "YES" in settings["ENABLE_APP_SANDBOX"] or any(
            data.get("com.apple.security.app-sandbox") is True for data in entitlements.values())
        if not sandboxed:
            report.error("DST041", "App Sandbox is not enabled; the Mac App Store requires it.",
                         hint="Add the App Sandbox capability and only the entitlements the app needs.",
                         docs=DOCS["sandbox"])
    for path, data in entitlements.items():
        if data.get("get-task-allow") is True:
            report.warn("DST042", "Entitlements set get-task-allow = true (debugger attachment).",
                        file=str(path.relative_to(root)),
                        hint="Remove it from distribution entitlements; Xcode adds it for Debug automatically.")
        if data.get("aps-environment") == "development" and METHODS[args.method]["export"] in ("app-store-connect", "developer-id"):
            report.info("DST043", "aps-environment is 'development' in source; distribution signing sets production.",
                        file=str(path.relative_to(root)))

    needs_manifest = platform != "macOS" or args.method == "mac-app-store"
    if container and needs_manifest and not project.privacy_manifests:
        report.warn("DST050", "No PrivacyInfo.xcprivacy found.",
                    hint="App Store Connect flags apps and SDKs that use required-reason APIs without a privacy "
                         "manifest. Run audit_privacy_manifest.")
    if container and not list(root.rglob("AppIcon.appiconset")) and not list(root.rglob("*.icon")) and not settings["ASSETCATALOG_COMPILER_APPICON_NAME"]:
        report.warn("DST051", "No app icon (AppIcon.appiconset, Icon Composer .icon, or ASSETCATALOG_COMPILER_APPICON_NAME).",
                    hint="Uploads without a 1024 px App Store icon are rejected. See prepare_icon_assets.")

    options = export_options(args.method, platform, team, style, args.upload)
    build_dir = args.build_dir.rstrip("/")
    archive = f"{build_dir}/{scheme}.xcarchive"
    export_dir = f"{build_dir}/export-{args.method}"
    options_path = args.write_export_options or f"{build_dir}/ExportOptions-{args.method}.plist"
    if args.write_export_options:
        target = Path(args.write_export_options).expanduser()
        if not target.is_absolute():
            target = Path.cwd() / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(plistlib.dumps(options))
        report.info("DST070", f"Wrote ExportOptions.plist ({options['method']}) to {target}.")
        options_path = str(target)

    steps = plan_steps(args.method, platform, container, scheme, archive, export_dir, options_path,
                       args.upload, scheme)
    steps = framework_steps(framework, root, args.method, platform, options_path, steps)
    report.data = {
        "method": args.method,
        "framework": framework.as_dict(),
        "export_method": options["method"],
        "platform": platform,
        "container": container,
        "scheme": scheme,
        "shared_schemes": schemes,
        "team": team,
        "signing_style": style or "automatic (default)",
        "versions": settings["MARKETING_VERSION"],
        "build_numbers": settings["CURRENT_PROJECT_VERSION"],
        "export_options": options,
        "export_options_xml": plistlib.dumps(options).decode(),
        "steps": steps,
        "credentials": "Commands read ASC_KEY_ID, ASC_ISSUER_ID and ASC_PRIVATE_KEY_PATH from the environment "
                       "(the same variables app_store_connect uses). Nothing here stores or prints secrets.",
        "scope": "A plan. Nothing was built, signed, uploaded or notarized. Steps marked requires_approval "
                 "change App Store Connect or notary state; run them only when the developer approves.",
        "docs": DOCS["export"] if args.method != "developer-id" else DOCS["notarize"],
    }
    report.info("DST000", f"{len(steps)}-step {args.method} plan for {platform} ({scheme}).",
                hint="Show the plan, fix errors first, then run steps one at a time with approval.")
    return emit(report, args, title="Apple Native Engineer — Distribution plan")


if __name__ == "__main__":
    raise SystemExit(main())
