#!/usr/bin/env python3
"""Cross-platform auditor — Apple-native quality for Flutter, React Native, Expo, Capacitor, .NET MAUI and KMP apps.

A cross-platform app reaches the App Store through a native host project, and
App Review, VoiceOver and Dynamic Type judge it exactly like a Swift app. This
auditor finds the framework, then checks what typically separates "runs on
iPhone" from "feels made for iPhone":

* **Dynamic Type** — text scaling disabled (``TextScaler.noScaling``,
  ``allowFontScaling={false}``),
* **VoiceOver** — icon-only buttons without labels, images without descriptions,
* **Dark Mode** — Flutter ``MaterialApp`` without ``darkTheme``, Expo's
  ``userInterfaceStyle`` (which defaults to ``light``),
* **iOS conventions** — Material controls without ``.adaptive()``, Android-style
  bottom navigation, deprecated ``SafeAreaView``, ``Dimensions.get`` on resizable
  iPad/iPhone Duo windows, left/right instead of start/end for right-to-left,
* **App Store blockers** in the host — usage descriptions for the permission
  plugins in ``pubspec.yaml``/``package.json``, iOS localizations missing from
  Xcode, Expo bundle identifier, export compliance and privacy manifest,
* **Native-UI opportunities** — real SwiftUI (``@expo/ui``), Liquid Glass
  (``expo-glass-effect``), SF Symbols (``expo-symbols``), and the limits of
  Flutter's self-drawn UI.

Every rule is a heuristic over source text, reported with file and line. Rule
sources: Flutter platform-adaptation and internationalization docs, React
Native docs, Expo app-config reference, and Apple's HIG.

Usage::

    python3 tools/cross-platform-auditor/audit_cross_platform.py [PATH] [--json]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit, guard_directory
from apple_native.frameworks import FrameworkInfo, detect, read_json, source_files, xcode_containers
from apple_native.report import Report
from apple_native.xcode import discover, parse_version, read_plist, sdk_minimum_deployment

DOCS = {
    "flutter-adaptive": "https://docs.flutter.dev/ui/adaptive-responsive/platform-adaptations",
    "flutter-l10n": "https://docs.flutter.dev/ui/internationalization",
    "flutter-a11y": "https://docs.flutter.dev/ui/accessibility",
    "rn-a11y": "https://reactnative.dev/docs/accessibility",
    "rn-safearea": "https://reactnative.dev/docs/safeareaview",
    "expo-config": "https://docs.expo.dev/versions/latest/config/app/",
    "hig-dark": "https://developer.apple.com/design/human-interface-guidelines/dark-mode",
    "hig-type": "https://developer.apple.com/design/human-interface-guidelines/typography",
    "hig-tabs": "https://developer.apple.com/design/human-interface-guidelines/tab-bars",
    "privacy-keys": "https://developer.apple.com/documentation/bundleresources/information-property-list",
    "review-5-1-1": "https://developer.apple.com/app-store/review/guidelines/#data-collection-and-storage",
    "review-4-2": "https://developer.apple.com/app-store/review/guidelines/#minimum-functionality",
}

#: Package → Info.plist usage-description keys it needs on iOS (documented by each package).
PERMISSION_PACKAGES: Dict[str, Tuple[str, ...]] = {
    # Flutter (pub.dev)
    "camera": ("NSCameraUsageDescription", "NSMicrophoneUsageDescription"),
    "image_picker": ("NSPhotoLibraryUsageDescription", "NSCameraUsageDescription"),
    "mobile_scanner": ("NSCameraUsageDescription",),
    "geolocator": ("NSLocationWhenInUseUsageDescription",),
    "location": ("NSLocationWhenInUseUsageDescription",),
    "local_auth": ("NSFaceIDUsageDescription",),
    "flutter_contacts": ("NSContactsUsageDescription",),
    "contacts_service": ("NSContactsUsageDescription",),
    "speech_to_text": ("NSSpeechRecognitionUsageDescription", "NSMicrophoneUsageDescription"),
    "record": ("NSMicrophoneUsageDescription",),
    "photo_manager": ("NSPhotoLibraryUsageDescription",),
    "device_calendar": ("NSCalendarsFullAccessUsageDescription",),
    "flutter_blue_plus": ("NSBluetoothAlwaysUsageDescription",),
    "app_tracking_transparency": ("NSUserTrackingUsageDescription",),
    "health": ("NSHealthShareUsageDescription",),
    # React Native / Expo (npm)
    "expo-camera": ("NSCameraUsageDescription",),
    "react-native-vision-camera": ("NSCameraUsageDescription",),
    "expo-image-picker": ("NSPhotoLibraryUsageDescription",),
    "react-native-image-picker": ("NSPhotoLibraryUsageDescription", "NSCameraUsageDescription"),
    "expo-location": ("NSLocationWhenInUseUsageDescription",),
    "@react-native-community/geolocation": ("NSLocationWhenInUseUsageDescription",),
    "react-native-geolocation-service": ("NSLocationWhenInUseUsageDescription",),
    "expo-local-authentication": ("NSFaceIDUsageDescription",),
    "react-native-biometrics": ("NSFaceIDUsageDescription",),
    "expo-contacts": ("NSContactsUsageDescription",),
    "react-native-contacts": ("NSContactsUsageDescription",),
    "expo-media-library": ("NSPhotoLibraryUsageDescription",),
    "expo-calendar": ("NSCalendarsFullAccessUsageDescription",),
    "expo-tracking-transparency": ("NSUserTrackingUsageDescription",),
    "react-native-ble-plx": ("NSBluetoothAlwaysUsageDescription",),
    "@capacitor/camera": ("NSCameraUsageDescription", "NSPhotoLibraryUsageDescription"),
    "@capacitor/geolocation": ("NSLocationWhenInUseUsageDescription",),
}

FLUTTER_ADAPTIVE = ("Switch", "Slider", "CircularProgressIndicator", "Checkbox", "Radio", "AlertDialog",
                    "RefreshIndicator")
RTL_LANGUAGES = {"ar", "he", "fa", "ur"}


# --------------------------------------------------------------------------- #
# Source helpers
# --------------------------------------------------------------------------- #


def strip_comments(source: str) -> str:
    """Blank // and /* */ comments, keeping offsets (Dart, JS, TS, Kotlin, C#)."""

    def blank(match: re.Match) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return re.sub(r"/\*.*?\*/|//[^\n]*", blank, source, flags=re.DOTALL)


def line_of(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def call_body(source: str, open_paren: int) -> str:
    """The text between ``(`` at *open_paren* and its matching ``)``."""

    depth = 0
    for index in range(open_paren, min(len(source), open_paren + 6000)):
        char = source[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[open_paren + 1:index]
    return source[open_paren + 1:open_paren + 6000]


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


# --------------------------------------------------------------------------- #
# Host project (shared by every framework)
# --------------------------------------------------------------------------- #


def host_plists(root: Path, info: FrameworkInfo) -> Dict[str, object]:
    keys: Dict[str, object] = {}
    host = info.hosts.get("iOS")
    if not host:
        return keys
    for plist in sorted((root / host).rglob("Info.plist")):
        parts = set(plist.relative_to(root).parts)
        if parts & {"Pods", ".symlinks", "build", "Tests", "RunnerTests", "Flutter"}:
            continue
        data = read_plist(plist) or {}
        for key, value in data.items():
            keys.setdefault(key, value)
    return keys


def check_permissions(root: Path, info: FrameworkInfo, report: Report) -> List[str]:
    needed: Dict[str, List[str]] = {}
    for package in info.dependencies:
        for key in PERMISSION_PACKAGES.get(package, ()):
            needed.setdefault(key, []).append(package)
    if not needed:
        return []

    if info.framework == "expo":
        config = info.expo_config or {}
        plist = ((config.get("ios") or {}).get("infoPlist") or {})
        plugins = config.get("plugins") or []
        configured = {entry[0] for entry in plugins if isinstance(entry, list) and entry and isinstance(entry[-1], dict)}
        listed = {entry if isinstance(entry, str) else entry[0] for entry in plugins if entry}
        for key, packages in sorted(needed.items()):
            if plist.get(key):
                continue
            if any(package in configured for package in packages):
                continue
            if any(package in listed for package in packages):
                report.warn("XPL011", f"{key}: the {', '.join(packages)} config plugin supplies a generic default "
                            "permission message.", file="app.json",
                            hint="App Review (5.1.1) expects the purpose in your words: set the plugin's permission "
                                 "option or ios.infoPlist." + key + ".", docs=DOCS["review-5-1-1"])
            else:
                report.error("XPL010", f"{key} is missing for {', '.join(packages)}.", file="app.json",
                             hint=f"Add the config plugin with a permission message, or ios.infoPlist.{key}.",
                             docs=DOCS["privacy-keys"])
        return sorted(needed)

    if "iOS" not in info.hosts:
        return sorted(needed)
    keys = host_plists(root, info)
    for key, packages in sorted(needed.items()):
        value = keys.get(key)
        if not value:
            report.error("XPL010", f"{key} is missing from the iOS Info.plist, but {', '.join(packages)} "
                         "requests that permission.", file=info.hosts["iOS"],
                         hint="iOS terminates the app when it asks without this key, and App Review rejects the build. "
                              "Describe the specific purpose.", docs=DOCS["privacy-keys"])
        elif isinstance(value, str) and (len(value) < 12 or re.search(r"\$\(PRODUCT_NAME\) to access", value)):
            report.warn("XPL011", f"{key} is generic: {value!r}.", file=info.hosts["iOS"],
                        hint="State what the feature does with the data (Guideline 5.1.1).", docs=DOCS["review-5-1-1"])
    return sorted(needed)


def check_host(root: Path, info: FrameworkInfo, report: Report) -> None:
    host = info.hosts.get("iOS")
    if not host:
        return
    floor = discover(root).deployment_targets.get("iOS")
    supported = sdk_minimum_deployment("iOS")
    if floor and supported and parse_version(floor) < parse_version(supported[0]):
        report.error("XPL020", f"iOS deployment target {floor} is below {supported[0]}, the minimum the installed "
                     f"Xcode (iOS SDK {supported[1]}) can build.", file=host,
                     hint=f"Raise IPHONEOS_DEPLOYMENT_TARGET (and the Podfile platform) to {supported[0]} or later; "
                          "framework templates can lag behind Xcode.")
    if not list((root / host).rglob("PrivacyInfo.xcprivacy")):
        report.warn("XPL012", f"No PrivacyInfo.xcprivacy in the iOS host ({host}).",
                    hint="Plugins bring their own manifests; your app still needs one for the required-reason "
                         "APIs it uses. Run audit_privacy_manifest on the host.")


# --------------------------------------------------------------------------- #
# Flutter
# --------------------------------------------------------------------------- #


def known_regions(root: Path, info: FrameworkInfo) -> Optional[Set[str]]:
    host = info.hosts.get("iOS")
    if not host:
        return None
    for container in xcode_containers(root / host, max_depth=1):
        pbx = container / "project.pbxproj"
        if container.suffix == ".xcodeproj" and pbx.exists():
            match = re.search(r"knownRegions\s*=\s*\((.*?)\);", pbx.read_text(errors="ignore"), re.DOTALL)
            if match:
                return {item.strip().strip('"').lower() for item in match.group(1).split(",") if item.strip()}
    return None


def app_languages(root: Path, sources: Dict[Path, str]) -> Set[str]:
    languages: Set[str] = set()
    for arb in list((root / "lib").rglob("*.arb")) if (root / "lib").is_dir() else []:
        match = re.search(r"_([a-z]{2,3})(?:_[A-Za-z]{2,4})?\.arb$", arb.name)
        if match:
            languages.add(match.group(1))
    for source in sources.values():
        for language in re.findall(r"Locale\(\s*'([a-z]{2,3})'", source):
            languages.add(language)
    return languages


def audit_flutter(root: Path, info: FrameworkInfo, sources: Dict[Path, str], report: Report) -> None:
    targets_ios = "iOS" in info.hosts
    adaptive_hits: Dict[str, List[str]] = {}
    totals = {"material_only_nav": 0, "rtl": 0, "images": 0}

    for path, raw in sources.items():
        source = strip_comments(raw)
        name = rel(path, root)
        for match in re.finditer(r"TextScaler\.noScaling|textScaleFactor\s*:\s*1(?:\.0)?\b|TextScaler\.linear\(\s*1(?:\.0)?\s*\)",
                                 source):
            report.error("FLT001", "Text scaling is disabled; Dynamic Type sizes are ignored.", file=name,
                         line=line_of(source, match.start()),
                         hint="Remove the override. If a layout breaks, clamp with "
                              "textScaler.clamp(maxScaleFactor: 2.0) on that widget only.", docs=DOCS["hig-type"])
        for widget in FLUTTER_ADAPTIVE:
            for match in re.finditer(rf"(?<![\w.]){widget}\(", source):
                adaptive_hits.setdefault(widget, []).append(f"{name}:{line_of(source, match.start())}")
        for match in re.finditer(r"(?<![\w.])IconButton\(", source):
            body = call_body(source, match.end() - 1)
            if "tooltip:" not in body and "semanticLabel" not in body:
                report.warn("FLT004", "IconButton without a tooltip has no VoiceOver label.", file=name,
                            line=line_of(source, match.start()),
                            hint="Add tooltip: (it becomes the accessibility label) or wrap in Semantics(label:).",
                            docs=DOCS["flutter-a11y"])
        for match in re.finditer(r"(?<![\w.])GestureDetector\(", source):
            body = call_body(source, match.end() - 1)
            if "onTap" in body and re.search(r"child:\s*(const\s+)?Icon\(", body) and "Semantics" not in source[max(0, match.start() - 200):match.start()]:
                report.warn("FLT005", "Tappable icon built from GestureDetector is invisible to VoiceOver.", file=name,
                            line=line_of(source, match.start()),
                            hint="Use IconButton with a tooltip, or wrap in Semantics(button: true, label: …).",
                            docs=DOCS["flutter-a11y"])
        for match in re.finditer(r"Image\.(asset|network|file|memory)\(", source):
            body = call_body(source, match.end() - 1)
            if "semanticLabel" not in body and "excludeFromSemantics" not in body:
                totals["images"] += 1
        for match in re.finditer(r"(?<![\w.])MaterialApp(\.router)?\(", source):
            body = call_body(source, match.end() - 1)
            if "darkTheme:" not in body:
                report.warn("FLT007", "MaterialApp has no darkTheme, so the app stays light in Dark Mode.", file=name,
                            line=line_of(source, match.start()),
                            hint="Provide darkTheme: (e.g. ThemeData(brightness: Brightness.dark, colorSchemeSeed: …)) "
                                 "and leave themeMode on ThemeMode.system.", docs=DOCS["hig-dark"])
        if re.search(r"(?<![\w.])(BottomNavigationBar|NavigationBar)\(", source) and not re.search(
                r"CupertinoTabBar|CupertinoTabScaffold|Platform\.isIOS|TargetPlatform\.iOS|isCupertino", source):
            totals["material_only_nav"] += 1
            first = re.search(r"(?<![\w.])(BottomNavigationBar|NavigationBar)\(", source)
            report.warn("FLT003", "Material bottom navigation is used on iOS too.", file=name,
                        line=line_of(source, first.start()),
                        hint="Flutter's guidance: NavigationBar on Android, CupertinoTabBar on iOS (branch on "
                             "Platform.isIOS), matching the iOS tab bar's look and behaviour.", docs=DOCS["flutter-adaptive"])
        totals["rtl"] += len(re.findall(r"EdgeInsets\.only\([^)]*\b(left|right):|Alignment\.(centerLeft|centerRight|topLeft|topRight|bottomLeft|bottomRight)|TextAlign\.(left|right)\b", source))

    if targets_ios:
        for widget, places in sorted(adaptive_hits.items()):
            report.warn("FLT002", f"{widget}() renders the Material control on iOS ({len(places)}×).",
                        file=places[0].split(":")[0], line=int(places[0].split(":")[1]),
                        hint=f"Use {widget}.adaptive() so iPhone and iPad get the Cupertino control.",
                        docs=DOCS["flutter-adaptive"])
    if totals["images"]:
        report.info("FLT006", f"{totals['images']} image(s) without semanticLabel or excludeFromSemantics.",
                    hint="Describe meaningful images; mark decorative ones excludeFromSemantics: true.",
                    docs=DOCS["flutter-a11y"])
    if totals["rtl"]:
        report.info("FLT008", f"{totals['rtl']} left/right-specific insets, alignments or text alignments.",
                    hint="Use EdgeInsetsDirectional, AlignmentDirectional and TextAlign.start/end so Arabic and "
                         "Hebrew layouts mirror.")

    languages = app_languages(root, sources)
    regions = known_regions(root, info)
    if languages and regions is not None:
        missing = sorted(language for language in languages if language not in regions
                         and not any(region.startswith(language + "-") for region in regions))
        if missing:
            report.warn("FLT009", f"iOS localizations missing for: {', '.join(missing)} "
                        f"(app ships {', '.join(sorted(languages))}; Xcode knows {', '.join(sorted(regions))}).",
                        file=f"{info.hosts['iOS']}/Runner.xcodeproj/project.pbxproj",
                        hint="Flutter docs: add each language under Runner › Info › Localizations in Xcode so the "
                             "App Store lists it and system UI follows the language.", docs=DOCS["flutter-l10n"])
    podfile = root / info.hosts.get("iOS", "ios") / "Podfile"
    if podfile.exists():
        match = re.search(r"platform\s*:ios,\s*'([\d.]+)'", podfile.read_text(errors="ignore"))
        if match:
            report.info("FLT010", f"iOS deployment target in Podfile: {match.group(1)}.",
                        hint="Raise it deliberately if plugins or native code need newer APIs; keep the Xcode "
                             "build setting in sync.")
    report.info("FLT020", "Flutter draws its own UI, so system Liquid Glass, native tab bars and SF Symbols do not "
                "apply automatically.",
                hint="Shader packages imitate glass; real system materials need native platform views or native "
                     "host chrome. Keep Cupertino widgets and adaptive constructors for iOS conventions.")


# --------------------------------------------------------------------------- #
# React Native / Expo
# --------------------------------------------------------------------------- #


def audit_react_native(root: Path, info: FrameworkInfo, sources: Dict[Path, str], report: Report) -> None:
    color_scheme_used = False
    hardcoded_colors = 0
    rtl = images = 0
    vector_icons = False

    for path, raw in sources.items():
        source = strip_comments(raw)
        name = rel(path, root)
        for match in re.finditer(r"allowFontScaling\s*=\s*\{\s*false\s*\}|allowFontScaling\s*:\s*false|maxFontSizeMultiplier\s*=\s*\{\s*1(?:\.0)?\s*\}",
                                 source):
            report.error("RNA001", "Font scaling is disabled; Dynamic Type sizes are ignored.", file=name,
                         line=line_of(source, match.start()),
                         hint="Remove allowFontScaling={false}; cap extreme sizes with maxFontSizeMultiplier ≥ 1.5 "
                              "where a layout truly cannot grow.", docs=DOCS["hig-type"])
        for match in re.finditer(r"<(Pressable|TouchableOpacity|TouchableHighlight|TouchableWithoutFeedback)\b([^>]*)>(.*?)</\1>",
                                 source, re.DOTALL):
            attributes, inner = match.group(2), match.group(3)
            if re.search(r"accessibilityLabel|aria-label", attributes):
                continue
            if "<Text" not in inner:
                report.warn("RNA002", f"<{match.group(1)}> with only an icon or image has no VoiceOver label.",
                            file=name, line=line_of(source, match.start()),
                            hint='Add accessibilityLabel="…" and accessibilityRole="button".', docs=DOCS["rn-a11y"])
        for match in re.finditer(r"import\s*\{[^}]*\bSafeAreaView\b[^}]*\}\s*from\s*['\"]react-native['\"]", source):
            report.warn("RNA003", "SafeAreaView from react-native is deprecated.", file=name,
                        line=line_of(source, match.start()),
                        hint="Use react-native-safe-area-context, or ScrollView contentInsetAdjustmentBehavior=\"automatic\".",
                        docs=DOCS["rn-safearea"])
        for match in re.finditer(r"Dimensions\.get\(", source):
            report.warn("RNA004", "Dimensions.get() does not update when the window resizes.", file=name,
                        line=line_of(source, match.start()),
                        hint="Use useWindowDimensions(): iPad multitasking, Stage Manager and iPhone Duo resize the "
                             "window at runtime.")
        if re.search(r"useColorScheme|Appearance\.|PlatformColor|DynamicColorIOS|from ['\"]expo-router['\"].*\bColor\b", source):
            color_scheme_used = True
        hardcoded_colors += len(re.findall(r"['\"]#[0-9A-Fa-f]{3,8}['\"]", source))
        rtl += len(re.findall(r"\b(marginLeft|marginRight|paddingLeft|paddingRight)\b|textAlign\s*:\s*['\"](left|right)['\"]", source))
        images += sum(1 for match in re.finditer(r"<Image\b([^>]*)/?>", source)
                      if not re.search(r"accessibilityLabel|alt=|accessible=\{false\}|accessibilityElementsHidden", match.group(1)))
        if "@expo/vector-icons" in source or "react-native-vector-icons" in source:
            vector_icons = True

    if hardcoded_colors and not color_scheme_used:
        report.warn("RNA005", f"{hardcoded_colors} hard-coded colour literal(s) and no useColorScheme/PlatformColor.",
                    hint="Dark Mode needs colours that change with the appearance: useColorScheme(), "
                         "PlatformColor('label') / DynamicColorIOS, or expo-router's Color.", docs=DOCS["hig-dark"])
    if rtl:
        report.info("RNA006", f"{rtl} left/right style properties.",
                    hint="Use marginStart/paddingStart/marginEnd and textAlign: 'auto' so right-to-left layouts mirror.")
    if images:
        report.info("RNA007", f"{images} <Image> element(s) without an accessibility label.",
                    hint="Describe meaningful images (accessibilityLabel / alt); hide decorative ones.",
                    docs=DOCS["rn-a11y"])
    if info.framework == "expo":
        native = {name for name in ("@expo/ui", "expo-glass-effect", "expo-symbols") if name in info.dependencies}
        missing = [name for name in ("@expo/ui", "expo-glass-effect", "expo-symbols") if name not in native]
        if missing:
            report.info("RNA020", "Native iOS building blocks not installed: " + ", ".join(missing) + ".",
                        hint="@expo/ui renders real SwiftUI controls (sheets, pickers, menus, toggles); "
                             "expo-glass-effect gives system Liquid Glass; expo-symbols gives SF Symbols."
                             + (" @expo/vector-icons are drawn glyphs, not SF Symbols." if vector_icons else ""))


def audit_expo_config(root: Path, info: FrameworkInfo, report: Report) -> None:
    config = info.expo_config
    if config is None:
        if (root / "app.config.js").exists() or (root / "app.config.ts").exists():
            report.info("EXP000", "Dynamic app.config.js/ts is not executed; Expo config checks were skipped.",
                        hint="Run `npx expo config --json > expo-config.json` and keep a static app.json for audits.")
        return
    ios = config.get("ios") or {}
    if not ios.get("bundleIdentifier"):
        report.error("EXP001", "expo.ios.bundleIdentifier is missing.", file="app.json",
                     hint="Set the reverse-DNS bundle ID registered in App Store Connect.", docs=DOCS["expo-config"])
    encryption = (ios.get("config") or {}).get("usesNonExemptEncryption")
    if encryption is None and "ITSAppUsesNonExemptEncryption" not in (ios.get("infoPlist") or {}):
        report.warn("EXP002", "Export compliance is not declared.", file="app.json",
                    hint="Set ios.config.usesNonExemptEncryption (false when only HTTPS/Apple crypto is used); "
                         "otherwise every TestFlight build waits for a manual answer.", docs=DOCS["expo-config"])
    style = ios.get("userInterfaceStyle") or config.get("userInterfaceStyle")
    if style in (None, "light"):
        report.warn("EXP003", "Dark Mode is off: userInterfaceStyle " + ("defaults to 'light'." if style is None else "is 'light'."),
                    file="app.json", hint='Set "userInterfaceStyle": "automatic" and provide dark colours.',
                    docs=DOCS["expo-config"])
    if not ios.get("privacyManifests") and not list((root / "ios").rglob("PrivacyInfo.xcprivacy") if (root / "ios").is_dir() else []):
        report.warn("EXP004", "No ios.privacyManifests in app config.", file="app.json",
                    hint="Declare required-reason API use (NSPrivacyAccessedAPITypes) in ios.privacyManifests.",
                    docs=DOCS["expo-config"])
    eas = read_json(root / "eas.json") or {}
    auto_increment = any((profile or {}).get("autoIncrement") for profile in ((eas.get("build") or {}).values())
                         if isinstance(profile, dict)) or (eas.get("cli") or {}).get("appVersionSource") == "remote"
    if not ios.get("buildNumber") and not auto_increment:
        report.info("EXP005", "No ios.buildNumber and no EAS autoIncrement.", file="app.json",
                    hint="Each upload needs a higher CFBundleVersion: set ios.buildNumber or autoIncrement in eas.json.")
    if ios.get("supportsTablet"):
        report.info("EXP006", "supportsTablet is true: iPad 13\" screenshots are required.", file="app.json",
                    hint="Plan captures with get_app_store_specs platforms=[\"iPadOS\"].")
    icon = ios.get("icon") or config.get("icon")
    if not icon:
        report.warn("EXP007", "No app icon in app config.", file="app.json", hint="Set ios.icon (1024×1024) or an Icon Composer .icon.")
    elif isinstance(icon, str) and not icon.endswith(".icon"):
        report.info("EXP008", "Icon is a single image.", file="app.json",
                    hint="ios.icon accepts an Icon Composer .icon or {light, dark, tinted} for iOS 26 appearances.",
                    docs=DOCS["expo-config"])


# --------------------------------------------------------------------------- #
# Capacitor, MAUI, KMP
# --------------------------------------------------------------------------- #


def audit_capacitor(root: Path, info: FrameworkInfo, report: Report) -> None:
    config = read_json(root / "capacitor.config.json") or {}
    text = "".join((root / name).read_text(errors="ignore") for name in ("capacitor.config.ts", "capacitor.config.js")
                   if (root / name).exists())
    url = (config.get("server") or {}).get("url") or (re.search(r"url\s*:\s*['\"](https?://[^'\"]+)", text) or [None, None])[1]
    if url:
        report.error("CPC001", f"server.url loads remote content ({url}).",
                     hint="Shipping a remote website in a native shell risks Guideline 4.2 (minimum functionality) "
                          "and 2.5.2. Bundle the web assets; use server.url only for development.",
                     docs=DOCS["review-4-2"])
    report.info("CPC010", "Web UI renders in WKWebView; native feel depends on the web layer.",
                hint="Respect safe areas (env(safe-area-inset-*)), disable tap highlights, avoid 100vh, and use "
                     "native plugins for share sheets, haptics and status bar.")


def audit_other(info: FrameworkInfo, report: Report) -> None:
    if info.framework == "maui":
        report.info("MAU010", ".NET MAUI maps controls to UIKit; iOS specifics live in Platforms/iOS.",
                    hint="Use SemanticProperties.Description/Hint for VoiceOver, FontAutoScalingEnabled stays true, "
                         "AppThemeBinding for Dark Mode; Info.plist and PrivacyInfo.xcprivacy belong in Platforms/iOS.")
    if info.framework == "kmp":
        report.info("KMP010", "Compose Multiplatform draws its own UI on iOS; SwiftUI screens in iosApp are native.",
                    hint="Keep system chrome (navigation, tab bars, sheets) in SwiftUI where it matters and share "
                         "logic in Kotlin; Info.plist and the privacy manifest live in iosApp.")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv=None) -> int:
    parser = build_parser("cross-platform-auditor",
                          "Apple-native quality checks for Flutter, React Native, Expo, Capacitor, .NET MAUI and KMP apps.",
                          epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.")
    args = parser.parse_args(argv)
    guard = guard_directory("cross-platform-auditor", args.path)
    if guard:
        return emit(guard, args)
    root = Path(args.path).expanduser().resolve()
    report = Report(tool="cross-platform-auditor", target=str(root), version=__version__)
    info = detect(root)
    report.data = info.as_dict()

    if info.framework == "native":
        report.info("XPL000", "No cross-platform framework detected; use the Swift auditors for this project.")
        return emit(report, args, title="Apple Native Engineer — Cross-platform audit")

    files = source_files(root, info)
    sources: Dict[Path, str] = {}
    for path in files:
        try:
            sources[path] = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    report.data["files_scanned"] = len(sources)
    report.info("XPL001", f"{info.label} app" + (f" ({info.version})" if info.version else "")
                + (f"; iOS host: {info.hosts['iOS']}" if "iOS" in info.hosts else "; no checked-in iOS host"
                   + (" (Expo prebuild/EAS generates it)" if info.managed else "")) + ".")

    if info.framework == "flutter":
        audit_flutter(root, info, sources, report)
    elif info.framework in ("react-native", "expo"):
        audit_react_native(root, info, sources, report)
        if info.framework == "expo":
            audit_expo_config(root, info, report)
    elif info.framework == "capacitor":
        audit_capacitor(root, info, report)
    else:
        audit_other(info, report)

    report.data["permissions_checked"] = check_permissions(root, info, report)
    check_host(root, info, report)
    report.data["next_steps"] = [
        "inspect_apple_project and audit_privacy_manifest run on the iOS host" if info.hosts.get("iOS") else
        "Generate the iOS host (npx expo prebuild -p ios) to run host-level audits, or rely on EAS",
        "capture_screenshots with the simulator build of this app (see references/cross-platform-apple.md)",
        "plan_distribution for the framework-specific build and upload commands",
    ]
    return emit(report, args, title="Apple Native Engineer — Cross-platform audit")


if __name__ == "__main__":
    raise SystemExit(main())
