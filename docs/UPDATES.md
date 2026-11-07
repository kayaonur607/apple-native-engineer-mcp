# GitHub installation, versions and automatic updates

Apple Native Engineer v2.2.1 is distributed from [GitHub](https://github.com/kayaonur607/apple-native-engineer-mcp). GitHub Releases is the only product release channel. There is no hosted service or npm product publication. The MCP runs locally; it reads your local project and uses Apple documentation tools when requested. npm is still required to download the SDK dependencies pinned in `package-lock.json`.

## Install once

Requires Git, Node 20+, npm and Python 3.10+. Xcode is needed for Apple builds, not for static audits.

```bash
git clone https://github.com/kayaonur607/apple-native-engineer-mcp.git "$HOME/apple-native-engineer-mcp"
cd "$HOME/apple-native-engineer-mcp/integrations/mcp-server"
npm ci --ignore-scripts --no-audit --no-fund
node scripts/github-launcher.mjs --selftest
```

This bootstrap checkout contains the launcher. Keep it installed. No `curl | sh` step or global package installation is needed.

Configure the client with the **absolute path** to this launcher (replace `/absolute/path`):

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "node",
      "args": ["/absolute/path/apple-native-engineer-mcp/integrations/mcp-server/scripts/github-launcher.mjs"],
      "env": { "APPLE_NATIVE_PYTHON": "python3" }
    }
  }
}
```

Allow up to ten minutes for the first installation/update in clients with startup timeouts. Normal cached startups perform a GitHub API check with a five-second timeout. Some clients have fixed startup deadlines: run `node scripts/github-launcher.mjs --selftest` from `integrations/mcp-server` first to prewarm the release cache, then reconnect the client.

## What updates automatically

Every launcher startup checks up to the latest 100 GitHub Releases, ignores drafts/prereleases/non-version tags, and chooses the numerically newest stable version newer than the active version. All stable versions, including new major versions, are eligible; pin a version if compatibility must remain fixed. Only maintainers who can publish releases in this repository control this channel.

The launcher clones the release tag into a staging directory, records its commit, checks that the tag and package version agree, runs `npm ci --ignore-scripts` and the MCP inventory smoke test, then atomically changes the active pointer. npm integrity checks follow the lockfile. This is not a cryptographic publisher-signature verification system: GitHub/repository ownership and TLS remain the trust boundary. Maintainers should enable [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases).

A running MCP session keeps its existing version. A new version becomes active on the next client reconnect/restart, not mid-tool call. The launcher does not edit the bootstrap checkout, client configuration or customer source code. Server code, resources, prompts and its bundled skill document update together; separately copied skills must be refreshed separately.

Logs go to stderr so stdout remains valid MCP protocol. The server provides `apple-native://release` with the current version and changelog. Initialization instructions ask the AI to state the version and relevant changes in the user's language. The client/model controls whether it displays that guidance; the server cannot force a UI notification.

## Failure behaviour

- GitHub unreachable, rate-limited or no newer release: retain the active cached version.
- Dependency install or inventory smoke test fails: do not activate the candidate; retain the previous version.
- First startup with no cached release: use the bootstrap checkout if updates cannot complete. Its dependencies must have been installed above.
- Another client is updating: use the active version; if none exists, use the bootstrap checkout. A crashed install lock expires after ten minutes.
- Pinned version unavailable: fail visibly rather than silently run a different version.

The smoke test proves importability, version and core inventory; it is not a guarantee that every future tool call will work. Old installations remain cached so active sessions are not deleted. Cache cleanup is manual while clients are stopped. The launcher itself is a stable bootstrap: changes to its update algorithm require updating the bootstrap checkout explicitly, then reviewing the new launcher.

## Controls and rollback

Set these in the MCP client's `env` block:

| Variable | Default | Effect |
| --- | --- | --- |
| `APPLE_NATIVE_AUTO_UPDATE` | on | `off` skips the GitHub check and uses the active installation, or bootstrap if none |
| `APPLE_NATIVE_VERSION` | unset | Exact stable tag, e.g. `mcp-v2.2.1`; explicitly permits rollback to that published version |
| `APPLE_NATIVE_UPDATE_DIR` | `~/.cache/apple-native-engineer` | Isolated release cache and atomic active pointer |

To roll back, set `APPLE_NATIVE_VERSION` to a known published tag and reconnect. Leave auto-update on for the rollback installation. Once cached, it can run with updates off. Remove the pin to return to automatic stable updates.

Do not set `APPLE_NATIVE_ROOT` with the launcher: the launcher binds it to the selected installation to keep code and resources consistent. Audit paths are still provided through MCP tool arguments.

## Version history

Read [CHANGELOG.md](../CHANGELOG.md) or the [GitHub Releases page](https://github.com/kayaonur607/apple-native-engineer-mcp/releases). Tags use `mcp-vMAJOR.MINOR.PATCH`: patch for compatible fixes, minor for additions, major for breaking changes. A release is available to automatic updates only after it is published, not when its tag or changelog exists locally.

## v2.3.0 bootstrap safety fix

Existing users must refresh their original bootstrap checkout with `git pull --ff-only` to receive launcher fixes, then restart the MCP client. Updating only the cached server does not replace the bootstrap launcher. A damaged existing cache now fails validation and preserves the active pointer; a valid cached release can still be reactivated for rollback. Use a fresh `APPLE_NATIVE_UPDATE_DIR` if a damaged directory blocks recovery.

GitHub immutable release protection was enabled on 2026-11-07. This applies to newly published releases; it does not retroactively make old releases immutable. Publisher-signature verification is still not implemented.
