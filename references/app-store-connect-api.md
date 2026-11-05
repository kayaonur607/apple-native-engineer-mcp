# App Store Connect API Integration Reference

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.
> **Authority**: [App Store Connect API](https://developer.apple.com/documentation/appstoreconnectapi), [App Store Connect Help — API](https://developer.apple.com/help/app-store-connect/get-started/app-store-connect-api)

This guide documents the surface the repository's client actually implements — `tools/app-store-connect/` — not the whole App Store Connect API. Everything below is checkable against `asc_client.py` and `cli.py`; anything not in those files is marked as unimplemented.

---

## 1. Authentication: JWT signed with ES256

Every request carries `Authorization: Bearer <jwt>` against `https://api.appstoreconnect.apple.com/v1`.

| Claim / header | Value | Notes |
| :--- | :--- | :--- |
| `alg` | `ES256` | ECDSA over P-256 with SHA-256 |
| `kid` | 10-character key ID | Must match the `.p8` file, or the API returns 401 |
| `typ` | `JWT` | |
| `iss` | Issuer ID (UUID) | From App Store Connect ▸ Users and Access ▸ Integrations |
| `iat` | issued-at, seconds | |
| `exp` | `iat + 1140` | Apple rejects anything older than 20 minutes; the client refreshes at 18 minutes |

Two details that break naive implementations:

1. **The signature is raw `r‖s`, not DER.** JWT ES256 wants two 32-byte big-endian integers concatenated and base64url-encoded. Sign with CryptoKit/`cryptography` and you get DER, so decode it and re-encode. The client does exactly that with `decode_dss_signature`, then `r.to_bytes(32, "big") + s.to_bytes(32, "big")`.
2. **A JWT is not a session.** There is no refresh token. Sign a new token when the old one nears expiry; the client caches one for `TOKEN_LIFETIME - 60` seconds.

```json
{
  "alg": "ES256",
  "kid": "ABCD123456",
  "typ": "JWT"
}
```

```json
{
  "iss": "69a6de7c-0000-4000-9000-000000000000",
  "iat": 1790000000,
  "exp": 1790001140,
  "aud": "appstoreconnect-v1"
}
```

The client refuses to send an unsigned request: if the `cryptography` package is missing it raises with the install command instead of shipping an invalid token. A release audit that invents data is worse than one that fails.

---

## 2. Endpoints the client calls

Read-only by construction — every request is a `GET`, so a misconfigured key cannot mutate store state.

| Method and path | Query | Attributes read | Command |
| :--- | :--- | :--- | :--- |
| `GET /v1/apps` | `limit` | `name`, `bundleId`, `sku`, `primaryLocale` | `list-apps`, `verify` |
| `GET /v1/apps/{id}/appStoreVersions` | `limit` | `versionString`, `appStoreState`, `platform`, `createdDate` | `versions --app <id>` |
| `GET /v1/apps/{id}/builds` | `limit` | `version`, `processingState`, `uploadedDate`, `expired` | `builds --app <id>` |

`verify` issues `GET /v1/apps?limit=1` and reports `apps_visible`, which proves both the signature and the key's role in one call.

Not implemented, despite being commonly described as part of "the API": `appStoreVersionLocalizations` (so no metadata reads or writes), `appScreenshotSets` / `appScreenshots` (no screenshot upload), `PATCH /v1/builds/{id}` (no export-compliance edits), and any submission endpoint. Use the App Store Connect UI or a full client for those; do not assume this tool will grow them.

---

## 3. Running the client

Credentials come from the environment, with flags as an override:

| Variable | Meaning |
| :--- | :--- |
| `ASC_KEY_ID` | 10-character key ID (the `.p8` filename) |
| `ASC_ISSUER_ID` | Issuer ID UUID |
| `ASC_PRIVATE_KEY_PATH` | Path to the `.p8` file (preferred) |
| `ASC_PRIVATE_KEY` | Inline PEM, `\n` escapes accepted |
| `ASC_PRIVATE_KEY_BASE64` | Base64 of the PEM, for CI secret stores |

```bash
export ASC_KEY_ID=ABCD123456
export ASC_ISSUER_ID=69a6de7c-0000-4000-9000-000000000000
export ASC_PRIVATE_KEY_PATH=~/private_keys/AuthKey_ABCD123456.p8

python3 tools/app-store-connect/cli.py verify
python3 tools/app-store-connect/cli.py list-apps --limit 20
python3 tools/app-store-connect/cli.py versions --app 1234567890
python3 tools/app-store-connect/cli.py builds --app 1234567890 --json
```

Precedence is inline PEM, then base64, then path. Missing pieces are collected into one error message (`ASC001`) that names every variable it needs — the client never falls back to synthetic data on its own.

`--mock` is the only path to synthetic output, and it is explicit:

```bash
python3 tools/app-store-connect/cli.py --mock list-apps --json
```

Mock mode emits `ASC010`: *"Mock mode: results are synthetic and must not gate a release."* Treat that warning as a failure in CI.

---

## 4. Failure modes

| Condition | What the client does | Report code |
| :--- | :--- | :--- |
| Missing credentials | Raises before any request, listing the missing variables | `ASC001` |
| `cryptography` not installed | Raises with `python3 -m pip install cryptography` | `ASC001` |
| Key is not an EC P-256 key | Raises `The App Store Connect key must be an EC P-256 private key (.p8 file)` | `ASC001` |
| `--app` omitted for `versions` / `builds` | Errors without calling the API | `ASC002` |
| HTTP 401 or 403 | Raises with Apple's body (first 300 characters) and a role/key hint | `ASC020` |
| HTTP 429 | Sleeps `min(Retry-After, 30)` and retries, up to 3 attempts | `ASC020` after exhaustion |
| Network error or timeout | Exponential backoff (1 s, 2 s, 4 s), up to 3 attempts | `ASC020` after exhaustion |
| Key sees zero apps | Warns | `ASC011` |
| No versions returned | Warns | `ASC012` |
| Expired builds present | Warns, with "upload a new build before submitting" | `ASC013` |

Apple's error envelope is passed through, not paraphrased:

```json
{
  "errors": [
    {
      "status": "403",
      "code": "FORBIDDEN.REQUIRED_PERMISSIONS",
      "title": "Forbidden",
      "detail": "Your API key does not have sufficient role permissions to perform this operation."
    }
  ]
}
```

For 429 responses the client trusts `Retry-After` rather than a hard-coded quota. Apple's limit is a rolling-hour budget; if you are hitting it, batch fewer requests instead of tuning a constant.

---

## 5. Keys, roles and safety

- Create the key under **Users and Access ▸ Integrations ▸ App Store Connect API**. The `.p8` downloads **once**; store it in a secret manager, never in the repo.
- Give the key the narrowest role that does the job. A read-only audit does not need **Admin**.
- Keys are per-team, not per-app. `list-apps` returning fewer apps than you expect is a role problem, not a caching problem (`ASC011`).
- Revoke a leaked key in the same screen. Revocation is immediate; the JWT lifetime means a signed token can survive at most 20 minutes after revocation.

---

## 6. Evidence

| Claim | Where it is enforced |
| :--- | :--- |
| ES256, raw `r‖s`, 20-minute ceiling | `tools/app-store-connect/asc_client.py` — `sign_jwt`, `TOKEN_LIFETIME` |
| Read-only surface | every request is built with `method="GET"` in `AppStoreConnectClient.get` |
| No silent mock | `Credentials.from_env` raises `ASCError`; `--mock` warns `ASC010` |
| Rate-limit handling | `get()` retries on 429 with `Retry-After` |

## 7. Official references

- [App Store Connect API](https://developer.apple.com/documentation/appstoreconnectapi)
- [Generating tokens for API requests](https://developer.apple.com/documentation/appstoreconnectapi/generating-tokens-for-api-requests)
- [App Store Connect Help — API](https://developer.apple.com/help/app-store-connect/get-started/app-store-connect-api)
