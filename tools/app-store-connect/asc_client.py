#!/usr/bin/env python3
"""App Store Connect API client — read-only inspection with explicit auth modes.

Design rules that this client follows deliberately:

* **No silent fallback.** If credentials are missing the client raises. A release
  audit that quietly invents data is worse than one that refuses to run.
* **No fake signatures.** ES256 signing requires ``cryptography``; without it the
  client reports exactly what to install instead of sending an invalid token.
* **Read-only.** Only GET requests are issued, so a misconfigured key can never
  mutate App Store state.
* **Rate-limit aware.** 429 responses honour ``Retry-After`` and are retried with
  exponential backoff (App Store Connect allows ~3600 requests/hour).

Usage (CLI wrapper)::

    python3 tools/app-store-connect/cli.py verify
    python3 tools/app-store-connect/cli.py --mock list-apps
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from apple_native.http import open_trusted

API_BASE = "https://api.appstoreconnect.apple.com/v1"
TOKEN_LIFETIME = 19 * 60  # Apple rejects tokens older than 20 minutes
MAX_RETRIES = 3


class ASCError(RuntimeError):
    """Raised for every configuration or API problem, never swallowed."""


@dataclass
class Credentials:
    key_id: str
    issuer_id: str
    private_key: str

    @classmethod
    def from_env(cls, private_key_path: Optional[str] = None) -> "Credentials":
        key_id = os.environ.get("ASC_KEY_ID", "").strip()
        issuer_id = os.environ.get("ASC_ISSUER_ID", "").strip()
        inline = os.environ.get("ASC_PRIVATE_KEY", "").strip()
        base64_key = os.environ.get("ASC_PRIVATE_KEY_BASE64", "").strip()
        path = private_key_path or os.environ.get("ASC_PRIVATE_KEY_PATH", "").strip()

        missing = [name for name, value in (
            ("ASC_KEY_ID", key_id),
            ("ASC_ISSUER_ID", issuer_id),
        ) if not value]

        private_key = ""
        if inline:
            private_key = inline.replace("\\n", "\n")
        elif base64_key:
            try:
                private_key = base64.b64decode(base64_key).decode("utf-8")
            except Exception as exc:  # noqa: BLE001 - reported to the user
                raise ASCError(f"ASC_PRIVATE_KEY_BASE64 could not be decoded: {exc}") from exc
        elif path:
            key_path = Path(path).expanduser()
            if not key_path.exists():
                raise ASCError(f"ASC_PRIVATE_KEY_PATH does not exist: {key_path}")
            private_key = key_path.read_text()

        if not private_key:
            missing.append("ASC_PRIVATE_KEY(_PATH|_BASE64)")

        if missing:
            raise ASCError(
                "Missing App Store Connect credentials: " + ", ".join(missing) +
                ". Create a key at https://appstoreconnect.apple.com/access/api and export "
                "ASC_KEY_ID / ASC_ISSUER_ID / ASC_PRIVATE_KEY_PATH. "
                "Use --mock only when you explicitly want synthetic data."
            )
        return cls(key_id=key_id, issuer_id=issuer_id, private_key=private_key)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def sign_jwt(credentials: Credentials) -> str:
    """Create an ES256 App Store Connect JWT."""

    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ASCError(
            "The 'cryptography' package is required to sign App Store Connect requests "
            "(ES256). Install it with: python3 -m pip install cryptography"
        ) from exc

    header = {"alg": "ES256", "kid": credentials.key_id, "typ": "JWT"}
    now = int(time.time())
    payload = {
        "iss": credentials.issuer_id,
        "iat": now,
        "exp": now + TOKEN_LIFETIME,
        "aud": "appstoreconnect-v1",
    }
    signing_input = f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}." \
                    f"{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"

    key = serialization.load_pem_private_key(credentials.private_key.encode(), password=None)
    if not isinstance(key, ec.EllipticCurvePrivateKey):
        raise ASCError("The App Store Connect key must be an EC P-256 private key (.p8 file).")

    der_signature = key.sign(signing_input.encode(), ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der_signature)
    raw = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return f"{signing_input}.{_b64url(raw)}"


class AppStoreConnectClient:
    """Read-only App Store Connect client."""

    def __init__(self, credentials: Optional[Credentials] = None, mock: bool = False,
                 timeout: float = 30.0) -> None:
        self.mock = mock
        self.timeout = timeout
        self._credentials = credentials
        self._token: Optional[str] = None
        self._token_issued = 0.0

    # -- auth -----------------------------------------------------------
    @property
    def credentials(self) -> Credentials:
        if self._credentials is None:
            raise ASCError(
                "No credentials configured. Export ASC_KEY_ID, ASC_ISSUER_ID and "
                "ASC_PRIVATE_KEY_PATH, or pass --mock for synthetic data."
            )
        return self._credentials

    def token(self) -> str:
        if self._token is None or time.time() - self._token_issued > TOKEN_LIFETIME - 60:
            self._token = sign_jwt(self.credentials)
            self._token_issued = time.time()
        return self._token

    # -- transport ------------------------------------------------------
    def get(self, path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        if self.mock:
            return self._mock(path, params)

        url = f"{API_BASE}/{path.lstrip('/')}"
        if params:
            query = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
            url = f"{url}?{query}"

        last_error: Optional[str] = None
        for attempt in range(MAX_RETRIES):
            request = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {self.token()}",
                    "Accept": "application/json",
                },
                method="GET",
            )
            try:
                with open_trusted(request, {"api.appstoreconnect.apple.com"}, timeout=self.timeout) as response:
                    return json.loads(response.read().decode())
            except urllib.error.HTTPError as exc:
                body = exc.read().decode(errors="replace")
                if exc.code == 429:
                    retry_after = int(exc.headers.get("Retry-After", "2"))
                    time.sleep(min(retry_after, 30))
                    last_error = "rate limited (429)"
                    continue
                if exc.code in (401, 403):
                    raise ASCError(
                        f"Authentication failed ({exc.code}). Check that the key is active, has "
                        f"the right role, and that ASC_KEY_ID matches the .p8 file. Apple said: {body[:300]}"
                    ) from exc
                raise ASCError(f"App Store Connect returned HTTP {exc.code}: {body[:300]}") from exc
            except urllib.error.URLError as exc:
                last_error = f"network error: {exc.reason}"
                time.sleep(2 ** attempt)
            except TimeoutError:
                last_error = "request timed out"
                time.sleep(2 ** attempt)

        raise ASCError(f"App Store Connect request failed after {MAX_RETRIES} attempts: {last_error}")

    # -- high level operations -------------------------------------------
    def verify(self) -> Dict[str, Any]:
        if self.mock:
            return {"status": "ok", "mode": "mock", "authenticated": False,
                    "note": "Synthetic data — no network call was made."}
        payload = self.get("apps", {"limit": "1"})
        return {
            "status": "ok",
            "mode": "live",
            "authenticated": True,
            "apps_visible": len(payload.get("data", [])),
        }

    def list_apps(self, limit: int = 20) -> List[Dict[str, Any]]:
        payload = self.get("apps", {"limit": str(limit)})
        apps = []
        for item in payload.get("data", []):
            attributes = item.get("attributes", {})
            apps.append({
                "id": item.get("id"),
                "name": attributes.get("name"),
                "bundle_id": attributes.get("bundleId"),
                "sku": attributes.get("sku"),
                "primary_locale": attributes.get("primaryLocale"),
            })
        return apps

    def app_versions(self, app_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        payload = self.get(f"apps/{app_id}/appStoreVersions", {"limit": str(limit)})
        versions = []
        for item in payload.get("data", []):
            attributes = item.get("attributes", {})
            versions.append({
                "id": item.get("id"),
                "version": attributes.get("versionString"),
                "state": attributes.get("appStoreState"),
                "platform": attributes.get("platform"),
                "created": attributes.get("createdDate"),
            })
        return versions

    def builds(self, app_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        payload = self.get(f"apps/{app_id}/builds", {"limit": str(limit)})
        builds = []
        for item in payload.get("data", []):
            attributes = item.get("attributes", {})
            builds.append({
                "id": item.get("id"),
                "version": attributes.get("version"),
                "processing_state": attributes.get("processingState"),
                "uploaded": attributes.get("uploadedDate"),
                "expired": attributes.get("expired"),
            })
        return builds


    def app_details(self, app_id: str) -> Dict[str, Any]:
        """Attributes of one app: identity, locale, content-rights declaration."""
        payload = self.get(f"apps/{app_id}")
        attributes = (payload.get("data") or {}).get("attributes", {})
        return {
            "id": (payload.get("data") or {}).get("id", app_id),
            "name": attributes.get("name"),
            "bundle_id": attributes.get("bundleId"),
            "sku": attributes.get("sku"),
            "primary_locale": attributes.get("primaryLocale"),
            "content_rights": attributes.get("contentRightsDeclaration"),
            "available_in_new_territories": attributes.get("availableInNewTerritories"),
        }

    def version_localizations(self, version_id: str) -> List[Dict[str, Any]]:
        """Listing copy per locale for one App Store version."""
        payload = self.get(f"appStoreVersions/{version_id}/appStoreVersionLocalizations",
                           {"limit": "50"})
        localisations = []
        for item in payload.get("data", []):
            attributes = item.get("attributes", {})
            localisations.append({
                "id": item.get("id"),
                "locale": attributes.get("locale"),
                "description": attributes.get("description"),
                "keywords": attributes.get("keywords"),
                "promotional_text": attributes.get("promotionalText"),
                "support_url": attributes.get("supportUrl"),
                "marketing_url": attributes.get("marketingUrl"),
                "whats_new": attributes.get("whatsNew"),
            })
        return localisations

    def screenshot_sets(self, version_localization_id: str) -> List[Dict[str, Any]]:
        """Screenshot sets attached to one locale of one version."""
        payload = self.get(
            f"appStoreVersionLocalizations/{version_localization_id}/appScreenshotSets",
            {"limit": "10", "include": "appScreenshots"},
        )
        included = {item.get("id"): item for item in payload.get("included", []) or []}
        sets = []
        for item in payload.get("data", []):
            attributes = item.get("attributes", {})
            screenshots = []
            for relationship in item.get("relationships", {}).get("appScreenshots", {}).get("data", []) or []:
                shot = included.get(relationship.get("id"), {})
                shot_attributes = shot.get("attributes", {})
                screenshots.append({
                    "id": shot.get("id", relationship.get("id")),
                    "file_name": shot_attributes.get("fileName"),
                    "state": shot_attributes.get("assetDeliveryState", {}).get("state")
                    if isinstance(shot_attributes.get("assetDeliveryState"), dict) else None,
                    "width": shot_attributes.get("imageAsset", {}).get("width")
                    if isinstance(shot_attributes.get("imageAsset"), dict) else None,
                    "height": shot_attributes.get("imageAsset", {}).get("height")
                    if isinstance(shot_attributes.get("imageAsset"), dict) else None,
                })
            sets.append({
                "id": item.get("id"),
                "display_type": attributes.get("screenshotDisplayType"),
                "count": len(screenshots),
                "screenshots": screenshots,
            })
        return sets

    # -- mock ------------------------------------------------------------
    def _mock(self, path: str, params: Optional[Dict[str, str]]) -> Dict[str, Any]:
        if path == "apps":
            return {"data": [{
                "id": "0000000000",
                "type": "apps",
                "attributes": {
                    "name": "Mock App",
                    "bundleId": "com.example.mock",
                    "sku": "MOCK001",
                    "primaryLocale": "en-US",
                },
            }], "mock": True}
        if path.startswith("apps/") and path.count("/") == 1:
            return {"data": {
                "id": "0000000000",
                "type": "apps",
                "attributes": {
                    "name": "Mock App",
                    "bundleId": "com.example.mock",
                    "sku": "MOCK001",
                    "primaryLocale": "en-US",
                    "contentRightsDeclaration": "USES_THIRD_PARTY_CONTENT",
                },
            }, "mock": True}
        if path.endswith("/appStoreVersionLocalizations"):
            return {"data": [{
                "id": "loc-en",
                "attributes": {
                    "locale": "en-US",
                    "description": "Mock description for the listing.",
                    "keywords": "mock,app,listing",
                    "promotionalText": "Mock promotional text.",
                    "supportUrl": "https://example.com/support",
                    "marketingUrl": "https://example.com",
                    "whatsNew": "Initial release.",
                },
            }], "mock": True}
        if path.endswith("/appScreenshotSets"):
            return {
                "data": [{
                    "id": "set-1",
                    "type": "appScreenshotSets",
                    "attributes": {"screenshotDisplayType": "APP_IPHONE_69"},
                    "relationships": {"appScreenshots": {"data": [{"id": "shot-1", "type": "appScreenshots"}]}},
                }],
                "included": [{
                    "id": "shot-1",
                    "type": "appScreenshots",
                    "attributes": {
                        "fileName": "home.png",
                        "assetDeliveryState": {"state": "COMPLETE"},
                        "imageAsset": {"width": 1320, "height": 2868},
                    },
                }],
                "mock": True,
            }
        if path.endswith("/appStoreVersions"):
            return {"data": [{
                "id": "v1",
                "attributes": {
                    "versionString": "1.0.0",
                    "appStoreState": "PREPARE_FOR_SUBMISSION",
                    "platform": "IOS",
                },
            }], "mock": True}
        if path.endswith("/builds"):
            return {"data": [{
                "id": "b1",
                "attributes": {
                    "version": "1",
                    "processingState": "VALID",
                    "expired": False,
                },
            }], "mock": True}
        return {"data": [], "mock": True, "path": path}

