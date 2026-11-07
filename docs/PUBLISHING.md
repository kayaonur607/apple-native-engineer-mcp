# GitHub release procedure

GitHub is the sole product distribution channel. `package.json` is private to block accidental npm publication. npm installs the locked MCP runtime dependencies; no `NPM_TOKEN`, npm publication, Smithery submission or hosted server is needed.

## Prepare a version

Choose a SemVer patch/minor/major according to compatibility. Keep these versions synchronized:

- `integrations/mcp-server/package.json` and `package-lock.json` (root and root package)
- `integrations/mcp-server/src/constants.js`
- `integrations/mcp-server/server.json` (repository metadata; no registry package)
- `SKILL.md` metadata

Add a dated `## [VERSION]` section to [CHANGELOG.md](../CHANGELOG.md) with user-visible additions, fixes and breaking changes. Update the README counts if the inventory or test count changed.

```bash
./scripts/verify.sh
node integrations/mcp-server/scripts/demo-evidence.mjs
node scripts/release-notes.mjs mcp-v2.2.1
```

## Publish

Commit the verified changes, then push the release commit and tag:

```bash
git tag -a mcp-v2.2.1 -m "Apple Native Engineer v2.2.1"
git push origin HEAD
git push origin mcp-v2.2.1
```

`.github/workflows/publish.yml` runs all verification gates on macOS, checks that tag and package version agree, extracts the exact changelog section, then creates a GitHub Release. A tag alone is not an update: clients discover only published stable Releases.

Before the first release, enable [immutable releases](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes) in the repository settings and ensure the Actions token can create releases. Do not move or reuse published tags. CI does not claim to verify publisher signatures or install an authorization/billing service.

Watch the release workflow and confirm the public artifact:

```bash
gh run list --workflow publish.yml --limit 3
gh release view mcp-v2.2.1
```

Then test the public path using a fresh temporary `APPLE_NATIVE_UPDATE_DIR` and the GitHub launcher. Confirm its `--version`, `--selftest` and `apple-native://release` report the published version. Customer auto-update is live only after this succeeds.

## Rollback and repair

Users can pin a known version with `APPLE_NATIVE_VERSION=mcp-v2.2.1` and reconnect. A failed installation preserves the cached working version. For a bad published release, publish a new patch and explain the regression; do not edit a tag's source. A runtime regression can pass the startup smoke test, so report it transparently and provide a pin immediately.

Details: [installation and update policy](UPDATES.md).
