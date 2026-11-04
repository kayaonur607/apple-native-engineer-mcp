# `/apple-native-connect` — App Store Connect API Integration

Manages App Store Connect API authentication, application status inspection, and build monitoring.

---

## Agent Execution Steps

1. **Verify Credentials**:
   Validate API key, Issuer ID, and ES256 authentication:
   ```bash
   python3 tools/app-store-connect/cli.py verify
   ```

2. **List Applications**:
   List registered applications in the account:
   ```bash
   python3 tools/app-store-connect/cli.py list-apps
   ```

3. **Inspect Version & Submission State**:
   Inspect version metadata, review state, and localizations:
   ```bash
   python3 tools/app-store-connect/cli.py inspect-version --app <APP_ID>
   ```

4. **Inspect Builds**:
   Monitor TestFlight and App Store build processing status:
   ```bash
   python3 tools/app-store-connect/cli.py inspect-builds --app <APP_ID>
   ```
