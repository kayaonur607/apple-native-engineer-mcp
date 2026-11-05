# Architecture

How the pieces fit, and the rules that keep them honest.

```
┌────────────────────────────────────────────────────────────────────────────┐
│ MCP client: Claude · Cursor · Codex · Copilot · Gemini · any MCP host     │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │ stdio or Streamable HTTP
┌───────────────────────────────▼────────────────────────────────────────────┐
│ integrations/mcp-server                                                    │
│  modules.js   capability gating (11 modules, 25 tools)                     │
│  tools.js     tool registry, zod schemas, annotations, output schema       │
│  runner.js    spawns python3, parses the envelope, maps exit codes         │
│  resources.js 53 documents as apple-native:// URIs                         │
│  prompts.js   12 slash commands as MCP prompts                             │
│  telemetry.js opt-in, five-key schema, sanitiser-tested                    │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │ subprocess: python3 tools/<tool>/<script>.py --json
┌───────────────────────────────▼────────────────────────────────────────────┐
│ tools/  18 CLIs, standard library only                                     │
│  lib/apple_native/  report contract · Swift scanner · colour maths ·       │
│                     Xcode parsing · PNG codec (icon-studio) · imaging      │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │ reads
         ┌──────────────────────┼───────────────────────┐
         ▼                      ▼                       ▼
   Swift sources         Info.plist / xcprivacy    developer.apple.com
   xcstrings / assets    git history               App Store Connect (GET)
```

## The three contracts

1. **The envelope.** Every CLI prints one JSON object: `schema_version`, `tool`, `target`, `status`, `summary`,
   `findings[]`, `data{}`. The MCP server validates it against a declared `outputSchema`; the app decodes the same
   struct. A tool that cannot produce it has failed.
2. **Exit codes.** `0` pass, `1` warnings under `--strict`, `2` failure. The MCP layer maps `2` to `isError`, which
   is why an agent cannot mistake a failed audit for a clean one.
3. **One implementation.** The MCP tools shell out to the same scripts the README documents. There is no second
   code path to drift, and a bug reproduced in the terminal is the same bug the agent sees.

## Why the core is small

The MCP server owns protocol, module gating, process execution and telemetry — nothing else. Every capability lives
in a Python tool that can be run, tested and trusted on its own. Optional dependencies are not installed at all:
the icon studio has its own PNG codec precisely so that the toolkit never grows an image-library requirement.

## Where knowledge lives

- `SKILL.md` — the standard an agent loads first.
- `references/` — 31 guides; `whats-new-ios-27.md` is generated from the installed SDK.
- `data/sf-symbols.json` — 9,649 symbols extracted from `CoreGlyphs.bundle`.
- `docs/` — roadmap, modules, integrations, publishing, and the raw verification transcripts in `PROOF.md`.

## What is enforced in CI

`./scripts/verify.sh` runs five stages: repository validation (links, counts, frontmatter), Python tests, MCP
protocol tests, Swift compilation and snippet type-checking, and documentation claims against the SDK. The npm job
packs the package, installs it in a clean directory and runs it. If a claim in this repository is not exercised by
one of those, it is not a claim — it is a hope.
