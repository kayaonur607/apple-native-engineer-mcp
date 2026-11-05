# Security Policy

## Supported Versions

| Version | Supported |
| :--- | :--- |
| 2.1.x | :white_check_mark: |
| 2.0.x | :white_check_mark: |
| < 2.0 | :x: |

Only the latest patch of a supported minor receives fixes. Version 2 is a rewrite: the 1.x line shipped a
hand-rolled JSON-RPC server and is not maintained.

---

## Reporting a Vulnerability

We take the security and integrity of this toolkit seriously. If you discover a vulnerability, an unsafe code
generation pattern, or a prompt-injection vector in the guides that the audits do not catch, please follow these
guidelines:

1. **Do not create a public GitHub issue.**
2. Use GitHub's private security advisory reporting on the repository, or email the maintainers.
3. Include:
   - a description of the issue and its impact,
   - steps to reproduce, ideally with the smallest project or prompt that triggers it,
   - the server version (`apple-native-engineer-mcp --version`) and the client you used,
   - the affected tool, if any.

Maintainers acknowledge receipt within 48 hours and provide a remediation timeline.

---

## Scope

This repository ships three things that can receive untrusted input: Python auditors that read a project
directory, an MCP server that exposes them, and reference guides that an agent may follow as instructions.
Anything that lets input escape its intended effect is in scope.

**In scope**

- Path traversal or symlink tricks that make an auditor read or write outside the target directory.
- A tool that mutates a project or an App Store Connect account. Every tool is declared read-only and must stay
  that way.
- Command injection through a path, a symbol name, a metadata field or a git revision.
- A way to make the server emit data it promised not to: file contents, credentials, environment variables.
- Telemetry fields outside the documented five-key shape, or a network request the user did not enable.
- Guide content that instructs an agent to exfiltrate data, disable a safety check or run an untrusted command.

**Out of scope**

- Findings the auditors miss. Static analysis is deliberately incomplete — that is documented, not a
  vulnerability. A false negative is a bug; report it as an issue.
- A deliberately hostile project that the auditors merely describe.
- Anything that requires an attacker to already have write access to the checkout or to the client configuration.

---

## The HTTP transport is unauthenticated by design

`node src/index.js --http` starts a server with **no authentication of its own**. That is a documented property,
not a defect, and the defaults are built around it:

- it binds `127.0.0.1` only; binding any other address requires `--allow-remote` and fails loudly without it;
- browser requests from a non-loopback `Origin` are rejected, which is the DNS-rebinding defence;
- only `application/json` is accepted, with a 4 MiB body cap;
- no CORS headers are sent, because a web page has no business running audits against your filesystem.

If you expose the port beyond loopback, put an authenticating reverse proxy in front of it. An unauthenticated
instance reachable from a network lets anyone who reaches it read findings about your source tree and your App
Store metadata. That is a deployment mistake, not an exploitable bug in the server — but report it anyway if the
flags do not behave as described above.

The Docker image passes `--allow-remote` because a container is only reachable through its published port. Treat
that image as a service you are exposing, and front it accordingly.

---

## Telemetry and data handling

- **No audit makes a network call.** The only outbound requests in the codebase are `app_store_connect`, which
  uses credentials you configure, and telemetry when you explicitly enable it.
- **Telemetry is off unless `APPLE_NATIVE_TELEMETRY` is `local` or `anonymous`.** Any other value is treated as
  `off`.
- **The event shape is closed and enforced by an allowlist.** Five fields: `schema`, `tool`, `outcome`,
  `duration_bucket`, `day`. No path, file name, source text, finding message, prompt, credential, hostname, user
  name or stable identifier — and `test/telemetry.test.js` feeds the sanitiser exactly those and fails if any
  survives.
- **`anonymous` mode requires an HTTPS endpoint that you supply.** There is no default collector, so there is
  nothing to opt out of. `--telemetry-preview` prints the exact bytes first.
- **Local mode writes one JSONL line per tool call** to `~/.local/share/apple-native-engineer/usage.jsonl`
  (override with `APPLE_NATIVE_USAGE_FILE`) and never leaves the machine.

## Credentials

App Store Connect credentials are read from the environment and used to sign a JWT in memory. They are never
written to disk, never logged, and never included in a tool result — `check_environment` reports only whether they
are present. `.p8` keys are gitignored at the repository root.

## Dependencies

The server has two runtime dependencies (`@modelcontextprotocol/sdk`, `zod`) and the auditors use the Python
standard library only; `cryptography` is required solely for `app_store_connect`. That is the whole supply chain,
by design — every additional dependency is an auditor that cannot run offline.
