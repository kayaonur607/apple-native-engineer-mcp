# Commercial launch and demonstration plan

## Product positioning

**Apple Native Engineer — evidence-backed Apple development and design workflows for your AI assistant.**

Inspect an existing project, research official Apple APIs and design guidance, review SwiftUI changes, and prepare App Store assets with structured findings. Works through a compatible MCP client; the client supplies the AI model. Independent software, not affiliated with or endorsed by Apple.

Suggested first message: “Apple geliştiricisiyim ve tasarımcıyım. Bu projedeki ana ekranı yerel Apple tasarımına uygun geliştir; önce hedef sürümü ve HIG kaynaklarını kontrol et, sonra değişiklikleri doğrula.” The client can also invoke `/apple-native-start` explicitly. Prompt discovery alone does not guarantee that every client will invoke it automatically.

## Initial commercial offer

Start with a paid setup and project review service around the existing MIT toolkit. Deliver client configuration, an evidence-backed audit, prioritized fixes and a handover report. The license permits commercial reuse; preserve its notice. Do not sell exclusivity over MIT code. Revenue and willingness to pay remain unvalidated.

Validate demand with developer interviews and a small paid pilot before committing to subscription hosting. Track actual installation completion, useful findings, false positives, repeat usage and support time with customer consent. Set pricing from observed delivery cost and pilot feedback; there is no measured ROI claim yet.

A later team subscription can fund maintained rules, private CI workflows, support and versioned reports. Billing, accounts, entitlement checks and a hosted customer workspace are not implemented by this change. Do not advertise them as available.

## Server decision

No purchased server is needed for the local pilot. Use stdio: source remains on the customer's machine and Xcode tools remain available. The existing Docker/HTTP transport is useful for controlled environments, but it runs audits against the server filesystem, not a caller's local project path.

Before a public hosted launch, implement MCP-compatible authorization, HTTPS, per-customer isolated workspaces, bounded execution, deletion policy, rate limits and billing lifecycle verification. A reverse proxy alone does not isolate customer files. Do not expose the current filesystem-auditing process as a shared public service.

References: [MCP authorization specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization), [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/).

## Reproducible video evidence

From the repository root:

```bash
node integrations/mcp-server/scripts/demo-evidence.mjs
./scripts/verify.sh
```

The first command uses a real MCP SDK client/server pair with public fixtures, writes timestamped `evidence.json` and a SHA-256 checksum under `.swiftwork/demo-evidence/`, and fails if the expected legacy/clean comparison does not hold. This is protocol evidence, not a simulator or HTTP transport test. No customer code is recorded.

A 90–120 second recording:

| Segment | Show | Claim supported |
| --- | --- | --- |
| 0–15 s | Compatible client's actual connection and tool inventory | MCP tools available in this client |
| 15–30 s | Invoke `/apple-native-start` with developer/designer intent | Guided workflow and integration boundaries |
| 30–55 s | Execute documentation lookup and show its URL/timestamp | Live Apple provenance, only if lookup succeeds |
| 55–80 s | Run demo evidence; expand legacy finding codes and clean result | Reproducible static analysis on labeled fixtures |
| 80–105 s | Show an actual app build and simulator, if performed | Only the device, SDK and states actually observed |
| 105–120 s | Show remaining limitations and setup call to action | Accurate commercial expectations |

Keep commands and results visible. Show errors if a lookup fails. Avoid private project paths, credentials, personal notifications and account details. Label any edits or sped-up sequences. Archive the raw recording with evidence JSON, checksum, git revision and verification log. Never present static fixture output as a working customer application or imply an App Store approval guarantee.

A [64-second protocol walkthrough](../assets/demo/usage-demo.mp4) now exists, with a [raw stdio session](../assets/demo/session.json), rendered evidence cards and captions. It is an animated motion graphic based on real MCP responses, not a desktop or simulator screen recording. Actual application/device footage is still to be captured.
