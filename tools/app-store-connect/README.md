# App Store Connect Toolkit

CLI and Python client for interacting with the official Apple App Store Connect REST API:
- **Connection Diagnostics**: Verifies API keys, Issuer ID, and ES256 authentication.
- **Application & Version Inspection**: Lists registered applications, inspects submission states, and reads localizations.
- **Build Monitoring**: Inspects TestFlight and App Store build processing status.
- **Mock Mode**: Supports `--mock` for local developer testing and CI environments without live API credentials.

---

## Configuration

Copy `.env.example` to `.env` or set environment variables:
```bash
cp .env.example .env
```
Populate:
- `ASC_KEY_ID`: Your 10-character Key ID from App Store Connect.
- `ASC_ISSUER_ID`: Your Issuer ID UUID.
- `ASC_PRIVATE_KEY_PATH`: Path to your downloaded `AuthKey_XXXX.p8` private key file.

---

## Usage

```bash
# Verify connection
./tools/app-store-connect/cli.py verify

# List applications
./tools/app-store-connect/cli.py list-apps

# Inspect version status for an app
./tools/app-store-connect/cli.py inspect-version --app 1672348910

# Run in mock mode (safe for testing without real credentials)
./tools/app-store-connect/cli.py --mock list-apps
```
