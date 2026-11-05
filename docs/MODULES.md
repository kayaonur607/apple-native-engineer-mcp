# Capability modules

The MCP server is a thin protocol shell around sixteen tools. Those tools are grouped into nine **capability
modules**, so a user can install one artefact and enable only what their project needs.

```
core                      audit_project · inspect_apple_project · review_diff · check_environment
swift-engineering         lint_swiftui · audit_accessibility · audit_liquid_glass
                          check_localization · validate_widgets
apple-docs-research       search_apple_documentation · read_apple_documentation
                          inspect_apple_api_availability · find_apple_guidelines
sf-symbols                validate_sf_symbols
design-tokens             forge_design_tokens
privacy-security-audit    audit_privacy_manifest
app-store-review          validate_app_metadata · audit_app_store_review
app-store-assets          validate_app_icon · prepare_icon_assets · verify_icon_set
                          compose_marketing_screenshots
release-readiness         generate_release_report
app-store-connect         app_store_connect
```

## Configuration

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "npx",
      "args": ["-y", "apple-native-engineer-mcp"],
      "env": {
        "APPLE_NATIVE_MODULES": "core,swift-engineering,privacy-security-audit"
      }
    }
  }
}
```

| Value | Effect |
| :--- | :--- |
| unset | every module enabled (the default; nothing changes for existing users) |
| `all` | same as unset, explicit |
| `core` | four tools: inspect, audit, diff review, environment diagnostics |
| `core,swift-engineering` | adds lint, accessibility, Liquid Glass, localisation, widgets |

Inspect the state at any time:

```bash
npx -y apple-native-engineer-mcp --modules   # registry + what is enabled
npx -y apple-native-engineer-mcp --selftest  # enabled tools, resources, prompts
```

## Rules the implementation guarantees

These are enforced by `integrations/mcp-server/test/modules.test.js`, not by convention:

1. **Every tool belongs to exactly one module.** A tool that is added without a module fails the suite.
2. **`core` cannot be disabled.** It contains the four tools that explain the rest; a server with no discovery is
   useless.
3. **An unknown module id is a startup error** that lists the valid ids — never a silent no-op.
4. **A disabled tool is invisible.** It is not listed by `tools/list` and calling it returns an error result, so an
   agent cannot mistake "not installed" for "nothing to report".
5. **Resources and prompts stay available.** They are knowledge and instructions, not capabilities; gating them
   would make the server harder to use without improving privacy.
6. **No credentials are requested for disabled modules.** The App Store Connect tool is the only one that reads
   `ASC_*`; if its module is off, those variables are never touched.

## Why this exists

Without modules, installing the toolkit means installing the ability to call App Store Connect — a capability most
users never want, and one that implies holding a private key. Modules let the same package be:

- a **design and Swift reviewer** for a team that never ships (core + swift-engineering + sf-symbols),
- a **privacy auditor** for a client project (core + privacy-security-audit),
- a **release tool** for the person who actually submits (add release-readiness + app-store-*),
- and nothing else, if that is all they want.

The core also stays honest about what it is not: there is no image generation, no browser automation, no telemetry
by default. Adding a module is the only way to add a capability, and every module has to justify its dependencies
in review.
