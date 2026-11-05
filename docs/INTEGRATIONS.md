# Integrations and external projects

This repository builds its own tools. Where another project already solves a problem better, this document says so
and explains the decision — including when the decision is "do not depend on it".

Everything below was checked on **2026-11-06** through the GitHub API. Stars and dates are recorded because they
age; treat them as a snapshot, not a promise.

---

## What we depend on at runtime

| Dependency | Why | Failure mode |
| :--- | :--- | :--- |
| Python 3.10+ standard library | Every auditor | The MCP server reports `check_environment` failure with the interpreter it found |
| Node 20+ and `@modelcontextprotocol/sdk` | The MCP protocol layer | `--doctor` names the version it found |
| `developer.apple.com` | Live documentation research | Cached for 7 days; `--offline` refuses the network and reports what is missing |
| `api.appstoreconnect.apple.com` | Read-only App Store Connect | Only reached when the `app-store-connect` module is enabled **and** credentials exist |

Nothing else is required, and no optional dependency is installed automatically.

---

## Projects we inspected

### `mishafyi/Apple-Docs-2.0-MCP` — 26 ★, MIT, TypeScript, pushed 2026-10-18

The closest related project: an MCP server over Apple's documentation, including WWDC sessions and transcripts.

- **What it does better:** WWDC transcript search and a broader documentation index than our four research tools.
- **Why we did not wrap it:** it is a second server with its own transport and tool namespace, and the value we
  needed — "does this API exist on iOS 17, and what does Apple say about it" — is a single documented JSON endpoint
  that our tool already reads directly, with citation and cache control.
- **When to use it:** if you want transcript-level search, run both servers. They do not conflict; our
  `apple-docs-research` module can be disabled with `APPLE_NATIVE_MODULES` while you use it.

### `modelcontextprotocol/servers` — 91.8k ★, reference implementations, TypeScript

The canonical example set. Used here as a **convention reference** for README structure, transport behaviour and
tool-result shape — not as a dependency.

- **Adopted:** stdio plus Streamable HTTP, `isError` semantics, capability declaration, resource URIs.
- **Not adopted:** its filesystem/git servers. Our tools read the local repository directly, so an extra process
  and a permission surface would buy nothing.

### `github/github-mcp-server` — 34.3k ★, MIT, Go

Used as a reference for operational hygiene rather than code.

- **Adopted:** an explicit "Security" section in the README, environment-variable configuration with documented
  defaults, and tool configuration that can be narrowed by the user (our `APPLE_NATIVE_MODULES`).
- **Not adopted:** remote hosting. An audit tool that reads your source should run where your source is.

### `upstash/context7` — 64.2k ★, MIT, TypeScript

Documentation retrieval as a service.

- **Why it is not used:** it uploads the query and receives third-party documentation. This repository's privacy
  position is that documentation research goes to Apple's own domain and nowhere else.

---

## Deliberate non-dependencies

| Tempting dependency | Why we did not take it |
| :--- | :--- |
| An image library (Pillow) for icons | `icon-studio` needs one operation — box-filter downscale — plus a PNG codec. ~200 lines of standard library keeps the toolkit installable with nothing but `python3`. |
| A web-scraping framework for Apple docs | Apple serves JSON for every page; scraping HTML would be slower, brittle and less precise. |
| An LLM SDK inside the server | The server exposes tools and structured context. Reasoning belongs to the connected agent, which keeps provider choice and data flow under the user's control. |
| A screenshot composition service | Composition is deterministic geometry; `compose_marketing.py` writes SVG locally and rasterises only if a renderer is already installed. |
| Apple's `xcodebuild` as a hard requirement | Most checks must run before a build exists, on any machine. Xcode is used only where it is genuinely required (Swift type-checking, simulator capture). |

---

## How to evaluate an integration before adding it

The checklist this document itself followed:

1. Read the source, not the README.
2. Check the licence and whether it permits the intended use.
3. Check the last commit date — an unmaintained dependency is a liability.
4. Count the permissions it needs; anything that reads the filesystem or the network must justify itself.
5. Ask whether the capability can be a 200-line local tool instead.
6. If it is adopted, give it a module, an explicit enable switch, and a test that proves the server still works
   when it is absent.

An integration that cannot survive step 6 is not integrated; it is a hope.
