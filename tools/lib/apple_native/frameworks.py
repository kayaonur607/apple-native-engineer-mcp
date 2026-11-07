"""Cross-platform framework detection.

Flutter, React Native, Expo, Capacitor, .NET MAUI and Kotlin/Compose
Multiplatform apps all ship to Apple platforms through a native host project
(``ios/Runner.xcodeproj``, ``ios/<App>.xcworkspace``, ``ios/App``, ``iosApp`` …).
Everything Apple checks — Info.plist, entitlements, privacy manifest, icons,
signing — lives in that host. This module finds the framework and its hosts so
the Apple-side tools can run on any of them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

#: Directories never worth walking: dependencies, generated code, build output.
SKIP_DIRS = {
    ".git", "node_modules", "Pods", "build", "DerivedData", ".build", ".dart_tool", ".symlinks",
    "ephemeral", ".expo", ".gradle", "android", "bin", "obj", ".swiftwork", "Carthage", "vendor",
}

SOURCE_SUFFIXES = {
    "flutter": (".dart",),
    "react-native": (".js", ".jsx", ".ts", ".tsx"),
    "expo": (".js", ".jsx", ".ts", ".tsx"),
    "capacitor": (".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".html"),
    "maui": (".cs", ".xaml"),
    "kmp": (".kt",),
}

LABELS = {
    "native": "Native (Swift/Objective-C)",
    "flutter": "Flutter",
    "react-native": "React Native",
    "expo": "Expo (React Native)",
    "capacitor": "Capacitor",
    "maui": ".NET MAUI",
    "kmp": "Kotlin Multiplatform / Compose Multiplatform",
}


@dataclass
class FrameworkInfo:
    framework: str = "native"
    label: str = LABELS["native"]
    version: Optional[str] = None
    app_version: Optional[str] = None
    managed: bool = False                     # Expo without a checked-in ios/ (Continuous Native Generation)
    hosts: Dict[str, str] = field(default_factory=dict)   # platform -> relative host directory
    dependencies: Dict[str, str] = field(default_factory=dict)
    config_files: List[str] = field(default_factory=list)
    expo_config: Optional[dict] = None

    def as_dict(self) -> Dict[str, object]:
        return {
            "framework": self.framework,
            "label": self.label,
            "version": self.version,
            "app_version": self.app_version,
            "managed": self.managed,
            "native_hosts": self.hosts,
            "config_files": self.config_files,
        }


def walk(root: Path, suffixes, limit: int = 4000):
    """Yield source files under *root*, skipping dependency and build folders."""

    count = 0
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = sorted(directory.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name not in SKIP_DIRS and not entry.name.startswith("."):
                    stack.append(entry)
            elif entry.suffix in suffixes:
                yield entry
                count += 1
                if count >= limit:
                    return


def xcode_containers(root: Path, max_depth: int = 3) -> List[Path]:
    """Every .xcworkspace / .xcodeproj up to *max_depth*, workspaces first, shallowest first."""

    found: List[Path] = []
    stack = [(root, 0)]
    while stack:
        directory, depth = stack.pop()
        try:
            entries = sorted(directory.iterdir())
        except OSError:
            continue
        for entry in entries:
            if not entry.is_dir() or entry.is_symlink():
                continue
            if entry.suffix in (".xcodeproj", ".xcworkspace"):
                if entry.suffix == ".xcworkspace" and entry.parent.suffix == ".xcodeproj":
                    continue  # the implicit project.xcworkspace
                found.append(entry)
            elif depth < max_depth and entry.name not in SKIP_DIRS and not entry.name.startswith("."):
                stack.append((entry, depth + 1))
    found.sort(key=lambda path: (len(path.relative_to(root).parts), path.suffix != ".xcworkspace", str(path)))
    return found


def read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _pubspec(root: Path) -> Optional[Dict[str, str]]:
    path = root / "pubspec.yaml"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not re.search(r"^\s*sdk:\s*flutter\b", text, re.MULTILINE) and not re.search(r"^flutter:\s*$", text, re.MULTILINE):
        return None
    deps: Dict[str, str] = {}
    block = None
    for line in text.splitlines():
        if re.match(r"^(dependencies|dev_dependencies):", line):
            block = line.split(":")[0]
            continue
        if line and not line.startswith(" "):
            block = None
        match = re.match(r"^  ([a-z0-9_]+):\s*(.*)$", line)
        if block == "dependencies" and match:
            deps[match.group(1)] = match.group(2).strip()
    version = re.search(r"^version:\s*([^\s#]+)", text, re.MULTILINE)
    deps["__app_version__"] = version.group(1) if version else ""
    return deps


def expo_config(root: Path) -> Optional[dict]:
    """The `expo` object from app.json (static config). Dynamic app.config.js is not executed."""

    for name in ("app.json", "app.config.json"):
        data = read_json(root / name)
        if isinstance(data, dict):
            return data.get("expo", data) if isinstance(data.get("expo", data), dict) else None
    return None


def detect(root: Path) -> FrameworkInfo:
    info = FrameworkInfo()

    pubspec = _pubspec(root)
    package = read_json(root / "package.json") or {}
    npm_deps: Dict[str, str] = {}
    for key in ("dependencies", "devDependencies"):
        if isinstance(package.get(key), dict):
            npm_deps.update(package[key])

    if pubspec is not None:
        info.framework = "flutter"
        info.app_version = pubspec.pop("__app_version__") or None
        info.dependencies = pubspec
        info.config_files.append("pubspec.yaml")
    elif "expo" in npm_deps:
        info.framework = "expo"
        info.version = npm_deps.get("expo")
        info.dependencies = npm_deps
        info.expo_config = expo_config(root)
        info.config_files += [name for name in ("app.json", "app.config.json", "app.config.js", "app.config.ts", "eas.json")
                              if (root / name).exists()]
        info.app_version = (info.expo_config or {}).get("version")
    elif "react-native" in npm_deps:
        info.framework = "react-native"
        info.version = npm_deps.get("react-native")
        info.dependencies = npm_deps
        info.config_files.append("package.json")
        info.app_version = package.get("version")
    elif "@capacitor/core" in npm_deps or any((root / f"capacitor.config.{ext}").exists() for ext in ("json", "ts", "js")):
        info.framework = "capacitor"
        info.version = npm_deps.get("@capacitor/core")
        info.dependencies = npm_deps
        info.config_files += [f"capacitor.config.{ext}" for ext in ("json", "ts", "js") if (root / f"capacitor.config.{ext}").exists()]
        info.app_version = package.get("version")
    else:
        for csproj in sorted(root.glob("*.csproj")) + sorted(root.glob("*/*.csproj")):
            text = csproj.read_text(encoding="utf-8", errors="ignore")
            if "<UseMaui>true</UseMaui>" in text or re.search(r"net\d+\.\d+-(ios|maccatalyst)", text):
                info.framework = "maui"
                info.config_files.append(str(csproj.relative_to(root)))
                frameworks = re.search(r"<TargetFrameworks?>([^<]+)<", text)
                info.version = frameworks.group(1) if frameworks else None
                display = re.search(r"<ApplicationDisplayVersion>([^<]+)<", text)
                info.app_version = display.group(1) if display else None
                break
        if info.framework == "native":
            gradle = [root / name for name in ("settings.gradle.kts", "settings.gradle", "build.gradle.kts")]
            if (root / "iosApp").is_dir() and any(path.exists() for path in gradle):
                info.framework = "kmp"
                info.config_files += [path.name for path in gradle if path.exists()]

    info.label = LABELS[info.framework]

    host_candidates = {
        "flutter": {"iOS": "ios", "macOS": "macos"},
        "react-native": {"iOS": "ios", "macOS": "macos"},
        "expo": {"iOS": "ios"},
        "capacitor": {"iOS": "ios/App"},
        "maui": {"iOS": "Platforms/iOS", "macOS": "Platforms/MacCatalyst"},
        "kmp": {"iOS": "iosApp"},
    }.get(info.framework, {})
    for platform, relative in host_candidates.items():
        candidate = root / relative
        if not candidate.is_dir() and info.framework == "maui":
            matches = sorted(root.glob(f"*/{relative}"))
            candidate = matches[0] if matches else candidate
        if candidate.is_dir():
            info.hosts[platform] = str(candidate.relative_to(root))
    if info.framework == "expo" and "iOS" not in info.hosts:
        info.managed = True
    return info


def source_files(root: Path, info: FrameworkInfo, limit: int = 4000) -> List[Path]:
    suffixes = SOURCE_SUFFIXES.get(info.framework)
    if not suffixes:
        return []
    if info.framework == "flutter":
        base = root / "lib"
        return list(walk(base, suffixes, limit)) if base.is_dir() else []
    files = []
    for path in walk(root, suffixes, limit):
        relative = path.relative_to(root).parts
        if relative[0] in ("ios", "macos", "android", "web-build", "dist", "coverage", "scripts", "__tests__", "e2e"):
            continue
        if any(part.endswith((".config.js", ".config.ts")) for part in relative[-1:]) and len(relative) == 1:
            continue
        files.append(path)
    return files
