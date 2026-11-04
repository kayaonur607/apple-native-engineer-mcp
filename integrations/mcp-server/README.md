# Apple Native Engineer — Model Context Protocol (MCP) Server

An optional Model Context Protocol (MCP) server that exposes executable Apple development, audit, and App Store Connect tools directly to MCP-compatible AI clients (Claude Desktop, Cursor, Zed, Windsurf).

---

## Exposed Tools

| Tool Name | Description |
| :--- | :--- |
| `inspect_apple_project` | Analyzes workspace structure, detected frameworks, and architecture. |
| `validate_app_icon` | Inspects 1024x1024 dimensions, PNG signature, and zero alpha transparency. |
| `validate_app_metadata` | Validates character limits, mandatory URLs, and keyword optimization. |
| `audit_privacy_manifest` | Scans for Required-Reason APIs and verifies `PrivacyInfo.xcprivacy`. |
| `generate_release_readiness_report` | Produces an end-to-end release readiness score (0-100) and audit report. |
| `connect_app_store_connect` | Verifies connection & credentials to App Store Connect REST API. |
| `list_applications` | Lists registered applications in App Store Connect. |
| `inspect_app_version` | Reads version submission states and localizations. |

---

## Configuration in Claude Desktop / Cursor

Add to your `claude_desktop_config.json` or Cursor MCP settings:

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "node",
      "args": [
        "/Users/onur/Desktop/apple-native-engineer/integrations/mcp-server/src/index.js"
      ],
      "env": {
        "ASC_KEY_ID": "YOUR_KEY_ID",
        "ASC_ISSUER_ID": "YOUR_ISSUER_ID",
        "ASC_PRIVATE_KEY_PATH": "/path/to/AuthKey_XXXX.p8"
      }
    }
  }
}
```
