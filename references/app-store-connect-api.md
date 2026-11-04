# App Store Connect API Integration Reference

The official **Apple App Store Connect REST API** enables programmatic automation of application management, metadata updates, TestFlight distribution, provisioning profiles, and review submissions.

> **Disclaimer**: This documentation provides technical guidance on using Apple's published REST API endpoints. It does not replace Apple Developer terms and agreements.

---

## 1. Authentication & Security (JSON Web Tokens)

All requests to `https://api.appstoreconnect.apple.com/v1/` require an authorization header containing a signed JSON Web Token (JWT) with **ES256** (ECDSA with P-256 curve and SHA-256):

```http
Authorization: Bearer <JWT_TOKEN>
```

### JWT Structure
- **Header**:
  - `alg`: `"ES256"`
  - `kid`: 10-character Key ID from App Store Connect.
  - `typ`: `"JWT"`
- **Payload**:
  - `iss`: 36-character Issuer ID UUID.
  - `iat`: Current Unix epoch timestamp in seconds.
  - `exp`: Expiration timestamp (maximum 20 minutes from `iat`).
  - `aud`: `"appstoreconnect-v1"`

---

## 2. Core API Endpoints

### A. Applications
- `GET /v1/apps`: Lists all registered applications in the developer account.
- `GET /v1/apps/{id}`: Fetches detailed attributes (bundleId, name, sku, primaryLocale).

### B. App Store Versions & State
- `GET /v1/apps/{id}/appStoreVersions`: Fetches version numbers, release types, and states (`PREPARE_FOR_SUBMISSION`, `WAITING_FOR_REVIEW`, `IN_REVIEW`, `READY_FOR_SALE`).
- `GET /v1/appStoreVersions/{id}/appStoreVersionLocalizations`: Reads localized metadata (description, keywords, promo text, URLs).

### C. Builds & TestFlight
- `GET /v1/apps/{id}/builds`: Lists builds with processing states (`PROCESSING`, `VALID`, `INVALID`).
- `PATCH /v1/builds/{id}`: Updates export compliance and beta testing notes.

### D. App Store Screenshots
- `GET /v1/appStoreVersionLocalizations/{id}/appScreenshotSets`: Lists screenshot sets grouped by display type (`APP_IPHONE_67`, `APP_IPAD_PRO_3GEN_129`).
- `POST /v1/appScreenshots`: Reserves an asset upload slot and receives chunked upload URLs.

---

## 3. Rate Limits & Error Handling

- **Rate Limits**: Apple enforces a token-bucket rate limiter. If exceeded, the API returns HTTP status `429 Too Many Requests`.
- **Error Response Format**:
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
