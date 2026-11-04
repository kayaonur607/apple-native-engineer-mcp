"""Xcode / Swift package introspection.

The tools must work on a checkout that has never been opened in Xcode, so this
module parses the artefacts that are always present in a repository:

* ``*.xcodeproj/project.pbxproj`` — old-style plist; we read the build settings
  we care about (deployment targets, Swift version, bundle identifiers) with a
  targeted parser rather than a full OpenStep plist implementation.
* ``*.xcworkspace/contents.xcworkspacedata`` — workspace membership.
* ``Package.swift`` — Swift tools version and platform declarations.
* ``Info.plist`` / ``*.entitlements`` — property lists (real plists).
"""

from __future__ import annotations

import plistlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class ProjectInfo:
    root: Path
    kind: str = "unknown"  # xcode-project | xcode-workspace | swift-package | unknown
    project_files: List[str] = field(default_factory=list)
    workspace_files: List[str] = field(default_factory=list)
    package_files: List[str] = field(default_factory=list)
    targets: List[str] = field(default_factory=list)
    deployment_targets: Dict[str, str] = field(default_factory=dict)
    swift_versions: List[str] = field(default_factory=list)
    bundle_ids: List[str] = field(default_factory=list)
    has_cocoapods: bool = False
    has_carthage: bool = False
    has_spm_dependencies: bool = False
    info_plists: List[Path] = field(default_factory=list)
    entitlements: List[Path] = field(default_factory=list)
    privacy_manifests: List[Path] = field(default_factory=list)


_PBXPROJ_SKIP = {"DerivedData", ".build", "Pods", "Carthage", ".git"}


def discover(root: Path) -> ProjectInfo:
    info = ProjectInfo(root=root)

    for pattern, bucket in (
        ("*.xcodeproj", info.project_files),
        ("*.xcworkspace", info.workspace_files),
    ):
        for found in sorted(root.glob(pattern)):
            if any(part in _PBXPROJ_SKIP for part in found.parts):
                continue
            bucket.append(found.name)

    for found in sorted(root.rglob("Package.swift")):
        if any(part in _PBXPROJ_SKIP for part in found.parts):
            continue
        info.package_files.append(str(found.relative_to(root)))

    info.has_cocoapods = (root / "Podfile").exists()
    info.has_carthage = (root / "Cartfile").exists()

    if info.workspace_files:
        info.kind = "xcode-workspace"
    elif info.project_files:
        info.kind = "xcode-project"
    elif info.package_files:
        info.kind = "swift-package"

    for pbx in root.glob("*.xcodeproj/project.pbxproj"):
        parse_pbxproj(pbx, info)

    for pkg in info.package_files:
        parse_package_swift(root / pkg, info)

    for found in root.rglob("Info.plist"):
        if any(part in _PBXPROJ_SKIP for part in found.parts):
            continue
        info.info_plists.append(found)

    for found in root.rglob("*.entitlements"):
        if any(part in _PBXPROJ_SKIP for part in found.parts):
            continue
        info.entitlements.append(found)

    for found in root.rglob("PrivacyInfo.xcprivacy"):
        if any(part in _PBXPROJ_SKIP for part in found.parts):
            continue
        info.privacy_manifests.append(found)

    if (root / "Package.resolved").exists() or any(
        "XCRemoteSwiftPackageReference" in p.read_text(errors="ignore")
        for p in root.glob("*.xcodeproj/project.pbxproj")
    ):
        info.has_spm_dependencies = True

    return info


def parse_pbxproj(path: Path, info: ProjectInfo) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return

    for match in re.finditer(r"IPHONEOS_DEPLOYMENT_TARGET\s*=\s*([0-9.]+)\s*;", text):
        info.deployment_targets.setdefault("iOS", match.group(1))
    for match in re.finditer(r"MACOSX_DEPLOYMENT_TARGET\s*=\s*([0-9.]+)\s*;", text):
        info.deployment_targets.setdefault("macOS", match.group(1))
    for match in re.finditer(r"WATCHOS_DEPLOYMENT_TARGET\s*=\s*([0-9.]+)\s*;", text):
        info.deployment_targets.setdefault("watchOS", match.group(1))
    for match in re.finditer(r"XROS_DEPLOYMENT_TARGET\s*=\s*([0-9.]+)\s*;", text):
        info.deployment_targets.setdefault("visionOS", match.group(1))
    for match in re.finditer(r"TVOS_DEPLOYMENT_TARGET\s*=\s*([0-9.]+)\s*;", text):
        info.deployment_targets.setdefault("tvOS", match.group(1))

    for match in re.finditer(r"SWIFT_VERSION\s*=\s*([0-9.]+)\s*;", text):
        if match.group(1) not in info.swift_versions:
            info.swift_versions.append(match.group(1))

    for match in re.finditer(r"PRODUCT_BUNDLE_IDENTIFIER\s*=\s*\"?([A-Za-z0-9._$-]+)\"?\s*;", text):
        value = match.group(1)
        if value not in info.bundle_ids and "$" not in value:
            info.bundle_ids.append(value)

    # Native target names live in the PBXNativeTarget section.
    for block in re.finditer(r"isa = PBXNativeTarget;.*?\};", text, re.DOTALL):
        name_match = re.search(r'name\s*=\s*"?([^";]+)"?\s*;', block.group(0))
        if name_match:
            name = name_match.group(1).strip()
            if name not in info.targets:
                info.targets.append(name)


def parse_package_swift(path: Path, info: ProjectInfo) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return

    tools_match = re.search(r"//\s*swift-tools-version:\s*([0-9.]+)", text)
    if tools_match and tools_match.group(1) not in info.swift_versions:
        info.swift_versions.append(tools_match.group(1))

    for platform, version in re.findall(
        r"\.(iOS|macOS|watchOS|tvOS|visionOS)\s*\(\s*\.v?[\"']?([0-9_]+)[\"']?\s*\)", text
    ):
        info.deployment_targets.setdefault(platform, version.replace("_", "."))

    for dependency in re.findall(r"\.package\s*\(\s*url:\s*\"([^\"]+)\"", text):
        info.has_spm_dependencies = True

    for target in re.findall(r"\.(?:target|executableTarget|testTarget)\s*\(\s*name:\s*\"([^\"]+)\"", text):
        if target not in info.targets:
            info.targets.append(target)


def read_plist(path: Path) -> Optional[dict]:
    try:
        with path.open("rb") as handle:
            return plistlib.load(handle)
    except Exception:  # noqa: BLE001 - malformed plists are reported by callers
        return None


def find_info_plist(root: Path, project: ProjectInfo) -> Optional[dict]:
    for candidate in project.info_plists:
        data = read_plist(candidate)
        if data and "CFBundleIdentifier" in data:
            return data
    for candidate in project.info_plists:
        data = read_plist(candidate)
        if data:
            return data
    return None


def deployment_floor(project: ProjectInfo, platform: str = "iOS") -> Optional[str]:
    value = project.deployment_targets.get(platform)
    if value:
        return value
    if project.swift_versions:
        # Swift tools version implies a minimum OS in modern packages.
        return None
    return None


def parse_version(value: str) -> Tuple[int, ...]:
    """Parse ``"17.4"`` / ``"17"`` / ``"17_4"`` into a comparable, zero-padded tuple.

    Zero padding matters: without it ``(17,) < (17, 0)`` is True in Python, which
    would make an iOS 17.0 project look older than an iOS 17 API.
    """

    parts: List[int] = []
    for chunk in re.split(r"[._]", value):
        if chunk.isdigit():
            parts.append(int(chunk))
        else:
            break
    if not parts:
        return (0, 0, 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])
