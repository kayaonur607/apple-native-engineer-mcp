# apple-native-engineer — MCP server

Every audit in this repository, exposed to any Model Context Protocol client, plus the reference library as
resources and the review workflows as prompts.

The point is not that an agent can *write* SwiftUI. It is that an agent can **check** what it wrote against
the same rules a senior Apple engineer applies, with finding codes you can quote in a code review. Nothing
here is generated from memory: each tool is a Python auditor in `tools/`, each guide is verified against the
installed SDK, and the server is a thin, honest shell over both.

```
Claude Desktop · Cursor · Codex · Cline · Zed · any MCP client
        │  stdio (default) or Streamable HTTP (POST /mcp)
        ▼
  apple-native-engineer  ──►  python3 tools/<auditor>/<script>.py --json
        │                          │
        │                          └── stable envelope (schema_version 2.0)
        ├── 16 tools        (a whole-project sweep, a diff-scoped review, and 14 auditors)
        ├── 53 resources    (references, checklists, examples, SKILL.md)
        └── 12 prompts      (the review workflows, parameterised)
```

## Why this exists

An agent asked to "make this screen look native" will happily invent `.glassBackground()` and ship code that
does not compile. An agent asked to "prepare for App Store submission" will miss the privacy manifest, the
1,024 px icon alpha channel, or the fact that the app still calls `NavigationView`.

This server replaces opinion with evidence:

| Question | Tool | Answer it returns |
| :--- | :--- | :--- |
| What is this project? | `inspect_apple_project` | targets, deployment floor, Swift version, architecture |
| Is any of this wrong? | `audit_project` | 8 audits at once, merged and attributed |
| Did *my change* break something? | `review_diff` | only the files in `git diff`, audited |
| Will Apple reject it? | `generate_release_report` | a gate verdict with the blocking findings |
| Does it look native? | `lint_swiftui`, `audit_liquid_glass` | `SWU*` / `GLASS*` finding codes |
| Is it accessible? | `audit_accessibility` | `A11Y*` codes with contrast ratios |
| Is the privacy manifest valid? | `audit_privacy_manifest` | required-reason APIs and their declared codes |
| Why is a tool failing? | `check_environment` | Node, Python, auditors, git, Xcode, credentials |

## Install

### npx — no clone, no install

```bash
npx -y apple-native-engineer-mcp --selftest
```

Then point the client at it:

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "npx",
      "args": ["-y", "apple-native-engineer-mcp"]
    }
  }
}
```

Requires Node 20+ and `python3` on `PATH`. The npm artifact vendors the auditors and the reference library,
so it does not need the repository checkout.

### From this repository

```bash
cd integrations/mcp-server
npm install
node src/index.js --selftest
```

`npm install` is the only build step; there is no compilation and no bundling.

### Docker — for a shared or hosted endpoint

```bash
# build from the repository root: the image vendors tools/ and references/
docker build -f integrations/mcp-server/Dockerfile -t apple-native-engineer .
docker run --rm -p 3927:3927 apple-native-engineer
curl -s http://127.0.0.1:3927/health
```

### Install matrix

| Client | Where the config lives | Transport |
| :--- | :--- | :--- |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` | stdio |
| Claude Code | `claude mcp add` or `.mcp.json` | stdio |
| Cursor | `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global) | stdio |
| OpenAI Codex | `~/.codex/config.toml` → `[mcp_servers.<name>]` | stdio |
| Gemini CLI | `~/.gemini/settings.json` → `mcpServers` | stdio |
| VS Code / Copilot | `.vscode/mcp.json` → `servers` (portable: `.mcp.json` → `mcpServers`) | stdio |
| OpenCode | `opencode.jsonc` → `mcp.servers` | stdio |
| Cline / Zed / Windsurf | their own `mcpServers` block, same shape | stdio |
| Anything that speaks HTTP | POST `http://127.0.0.1:3927/mcp` | Streamable HTTP |
| A container platform | the image above, `--http` | Streamable HTTP |

Per-client walkthroughs — including how each one surfaces the prompts and resources — are in the guides one
directory up: [`integrations/`](../README.md).

Project-local Cursor config:

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "node",
      "args": ["./integrations/mcp-server/src/index.js"]
    }
  }
}
```

## HTTP mode

stdio is right when the client launches the server. HTTP is right when the server lives somewhere else — a
container, a shared dev box, a browser-based client that cannot spawn processes.

```bash
node src/index.js --http            # POST http://127.0.0.1:3927/mcp
node src/index.js --http 8080       # a specific port
node src/index.js --http --http-host 127.0.0.1 --allow-remote
```

```
GET  /health   → {"name":…,"version":…,"status":"ok","tools":16,"telemetry":"off"}
POST /mcp      → MCP Streamable HTTP (stateless)
```

Stateless means no session bookkeeping: every request is independent, so a crashed call cannot poison the
next one and the server scales by adding processes rather than by sharing memory.

**The defaults are deliberately unfriendly, because a local server that reads your source tree is an attack
surface:**

- binds `127.0.0.1` only; a non-loopback bind fails unless you pass `--allow-remote`;
- rejects any request whose `Origin` is not the loopback origin — that is the DNS-rebinding defence, not an
  oversight;
- accepts `application/json` only, with a 4 MiB body cap;
- **has no authentication of its own.** Exposing it beyond loopback means putting an authenticating reverse
  proxy in front. That is stated here rather than discovered later.

There is no CORS header and no CORS support by design. A web page has no legitimate reason to run audits
against your filesystem.

## Tools

Sixteen tools: fourteen 1:1 wrappers over a script you can run yourself. If the MCP tool and the CLI ever
disagree, the CLI wins — that rule is why the server cannot drift.

| Tool | What it answers | Backing script |
| :--- | :--- | :--- |
| `audit_project` | **Start here.** Eight read-only audits in one call, merged and tagged | *composite* |
| `review_diff` | **Use in an edit loop.** Audits only the Swift files in `git diff` | *composite* |
| `check_environment` | Why is a tool failing: Node, Python, auditors, git, Xcode, credentials | *self-diagnostic* |
| `inspect_apple_project` | What is this project: targets, OS floor, Swift version, architecture | `tools/project-inspector/inspect_project.py` |
| `lint_swiftui` | 20 rules: deprecated API, hardcoded colour, identity churn, force unwraps | `tools/swiftui-linter/lint_swiftui.py` |
| `audit_accessibility` | VoiceOver, Dynamic Type, 44 pt targets, contrast ratios | `tools/accessibility-auditor/audit_accessibility.py` |
| `audit_liquid_glass` | iOS 26 glass adoption and the material stacks it replaced | `tools/liquid-glass-auditor/audit_liquid_glass.py` |
| `audit_privacy_manifest` | `PrivacyInfo.xcprivacy`, required-reason APIs, tracking domains | `tools/privacy-auditor/audit_privacy.py` |
| `check_localization` | Non-localisable literals, RTL mirroring, missing String Catalog keys | `tools/localization-checker/check_localization.py` |
| `validate_widgets` | WidgetKit families, Dynamic Island regions, `NSSupportsLiveActivities` | `tools/widget-validator/validate_widget.py` |
| `validate_sf_symbols` | A symbol name against the real 9,649-symbol catalogue | `tools/sf-symbols-catalog/check_symbols.py` |
| `validate_app_icon` | Size, format, alpha channel, corner mask | `tools/asset-validator/validate_assets.py` |
| `validate_app_metadata` | Name/subtitle/keyword/description limits and claim rules | `tools/metadata-validator/validate_metadata.py` |
| `forge_design_tokens` | Token JSON → SwiftUI source + `.xcassets` colour sets | `tools/design-token-forge/forge_tokens.py` |
| `generate_release_report` | The release gate: ship / fix / blocked, with reasons | `tools/release-readiness/generate_report.py` |
| `app_store_connect` | Real App Store Connect reads via JWT ES256 | `tools/app-store-connect/cli.py` |

`audit_project` is the one tool without a CLI equivalent, and it is not a second implementation: it runs
eight existing auditors concurrently and merges their envelopes. Every finding keeps a `tool` field naming
the audit that produced it, so an agent can route the fix without re-running the sweep.

`review_diff` exists because a full sweep is the wrong shape for an agent's edit loop. It reads
`git diff --name-only` (against `HEAD`, the index with `staged: true`, or any `base` revision), keeps the
`.swift` files, and runs the SwiftUI, accessibility and Liquid Glass auditors on each one. Findings are
grouped under `data.files`, and only the files you touched are audited — so a project that was already
non-compliant does not drown the review. This required the three auditors to accept a single file as their
target, which they now do (`lint_swiftui.py App/ContentView.swift` works from the CLI too).

## Results

Every tool returns three views of the same answer:

- a short human summary as text,
- the full envelope as text,
- the same envelope as `structuredContent`, validated against the declared `outputSchema`.

```json
{
  "schema_version": "2.0",
  "tool": "swiftui-linter",
  "target": "/Users/you/App",
  "status": "fail",
  "summary": { "critical": 0, "error": 3, "warning": 7, "info": 3, "total": 13 },
  "findings": [
    {
      "code": "SWU003",
      "severity": "error",
      "message": "NavigationView is deprecated in iOS 16 and does not support typed navigation.",
      "file": "App/ContentView.swift",
      "line": 12,
      "hint": "Use NavigationStack with a typed path."
    }
  ],
  "data": {}
}
```

Exit semantics, identical in the CLI and over MCP:

| `status` | CLI exit | MCP |
| :--- | :--- | :--- |
| `pass` | 0 | normal result |
| `warn` | 1 under `--strict` | normal result |
| `fail` | 2 | `isError: true`, envelope still attached |

A tool that crashes still returns a valid envelope with `status: "fail"` and an error code (`TOOL_MISSING`,
`TOOL_TIMEOUT`, `TOOL_CANCELLED`). The agent gets something to reason about instead of a stack trace.

## Resources

The knowledge base is exposed rather than pasted into prompts, so a client loads only what it needs.

- `apple-native://skill` — the operating standard (`SKILL.md`)
- `apple-native://references/<name>` — 31 guides, e.g. `apple-native://references/liquid-glass`
- `apple-native://checklists/<name>` — 12 review checklists
- `apple-native://examples/<name>` — 9 worked examples

## Prompts

Twelve workflows, available as slash commands in clients that support prompts. Each takes an optional
`project` path and an optional `focus` string.

`apple-native` (the umbrella audit), `apple-native-design`, `apple-native-code`, `apple-native-review`,
`apple-native-privacy`, `apple-native-icon`, `apple-native-screenshots`, `apple-native-connect`,
`apple-native-metadata`, `apple-native-widgets`, `apple-native-localization`, `apple-native-release`.

Naming is mechanical: `commands/apple-native.md` → `apple-native`, `commands/<slug>.md` → `apple-native-<slug>`.
A test enforces it so the doubled prefix cannot come back.

## Privacy

**This server does not want your data, and the code makes that checkable.**

- No network calls are made by any audit. The only outbound request in the entire server is the optional App
  Store Connect tool, which you must configure with your own credentials, and anonymous telemetry if you
  explicitly enable it.
- Nothing is uploaded, cached, or indexed. Findings are returned to the client and forgotten.
- Telemetry is **off by default**. When enabled it records a closed set of five fields — `schema`, `tool`,
  `outcome`, `duration_bucket`, `day` — and nothing else. No path, file name, source text, finding message,
  prompt, credential, hostname, user name or stable identifier. Unknown fields are dropped by an allowlist,
  not filtered by a denylist.
- `local` mode appends to a JSONL file you own (`~/.local/share/apple-native-engineer/usage.jsonl`) and can
  delete.
- `anonymous` mode also posts those aggregates to an HTTPS endpoint **you** supply. There is no default
  endpoint, so there is no phone-home to disable.
- A telemetry failure never fails a tool call.

You do not have to take any of that on trust:

```bash
node src/index.js --telemetry-preview
```

```json
{
  "mode": "off",
  "local_file": null,
  "endpoint": null,
  "sample_event": {
    "schema": 1,
    "tool": "lint_swiftui",
    "outcome": "warn",
    "duration_bucket": "150-400ms",
    "day": "2026-11-05"
  },
  "event_keys": ["schema", "tool", "outcome", "duration_bucket", "day"],
  "note": "No path, file name, source text, finding, prompt, credential or identifier is ever recorded."
}
```

`test/telemetry.test.js` feeds the sanitiser a payload stuffed with paths, file names, prompts and
credentials, and fails if any of it survives.

## Configuration

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `APPLE_NATIVE_PYTHON` | `python3` | Interpreter for the auditors |
| `APPLE_NATIVE_ROOT` | detected | Point the server at a different checkout |
| `APPLE_NATIVE_TIMEOUT_MS` | `180000` | Per-tool timeout; the child is killed, not orphaned |
| `APPLE_NATIVE_TELEMETRY` | `off` | `local` or `anonymous`; anything else is treated as `off` |
| `APPLE_NATIVE_TELEMETRY_URL` | — | HTTPS collector for `anonymous`; unset means nothing is sent |
| `APPLE_NATIVE_USAGE_FILE` | XDG data dir | Where `local` writes `usage.jsonl` |
| `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_PRIVATE_KEY_PATH` | — | App Store Connect credentials |

`ASC_PRIVATE_KEY` (inline PEM) and `ASC_PRIVATE_KEY_BASE64` are supported for CI. Signing needs
`python3 -m pip install cryptography`; every other tool is standard library only.

## Verify the install

```bash
node src/index.js --selftest        # inventory: 16 tools, 53 resources, 12 prompts
node src/index.js --doctor          # Node, Python, auditors, git, Xcode, credentials
node src/index.js --telemetry-preview
npm test                            # 51 protocol, CLI, diff, HTTP, metadata and telemetry tests
```

`--doctor` exits 0 when the machine can run everything, 2 when something blocks it, and 1 when it can run but
degraded (no git, no reference guides). It is the same diagnostic the `check_environment` tool returns, so an
agent and a human see one answer.

Then, from any MCP client, call `audit_project` with no arguments — it audits the client's working directory.

## Development

```
src/server.js      createServer() — tools + resources + prompts, no transport
src/index.js       CLI entry: stdio, --http, --selftest, --doctor, --telemetry-preview
src/http.js        Streamable HTTP transport, health endpoint, origin defence
src/tools.js       tool registry, audit_project, review_diff, progress reporting
src/runner.js      child-process runner, timeout, cancellation, parallel and per-file merge
src/environment.js the self-diagnostic behind check_environment and --doctor
src/constants.js   server identity, shared to keep the module graph acyclic
src/resources.js   knowledge base indexing
src/prompts.js     command files → MCP prompts
src/telemetry.js   the closed event shape
scripts/           vendor staging for npm publish
test/              protocol tests via InMemoryTransport, real HTTP sockets, a throwaway git repo
```

`npm run vendor` stages the auditors and the reference library into `vendor/` so the published tarball is
self-contained. `runner.js` prefers the live repository during development and the staged copy in a published
package, so both run the same code path. `vendor/` is generated and gitignored.

Releasing is written down in [`docs/PUBLISHING.md`](../../docs/PUBLISHING.md): which files carry the version, how
to verify the packed tarball rather than the source tree, the `mcp-v*` tag that publishes with provenance, and the
registry submissions that npm does not do for you.

## Limits, stated plainly

- The auditors are static analysis, not a compiler. They catch the mistakes reviewers actually flag; they do
  not type-check your project. `scripts/typecheck_snippets.py` covers the documented snippets, not your code.
- `app_store_connect` reads only. It never submits, uploads or mutates anything.
- The reference guides are verified against Xcode 27.2 / iOS 27.2 SDK. On an older SDK the claim checker
  skips rather than failing, so a green run means "verified here", not "verified everywhere".
- Framework behaviour that only appears at runtime — animation timing, memory under Instruments, App Review
  judgement — is out of scope for a static tool. The guides cover it; the tools do not pretend to.

## License

MIT. See [LICENSE](LICENSE).
