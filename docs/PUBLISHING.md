# Publishing

Everything a maintainer has to do by hand, in order, with the command that proves each step worked. The point of
writing it down is that a release has one path: if a step is not here, it is not part of releasing.

Nothing here is automated by choice. Two steps — the npm token and the registry submission — belong to a human
account, and pretending otherwise produces a workflow that fails halfway.

---

## 0. Preconditions, once per machine

| Requirement | Check |
| :--- | :--- |
| Node 20+ | `node --version` |
| Python 3.10+ | `python3 --version` |
| An npm account with publish rights to `apple-native-engineer-mcp` | `npm whoami` |
| `NPM_TOKEN` set as a repository secret | GitHub → Settings → Secrets → Actions |

`NPM_TOKEN` must be a **granular automation token** scoped to this package. A classic token works, but it carries
write access to every package you own, which is a larger blast radius than a release needs.

---

## 1. Decide the version

The MCP server versions independently of the reference library, and its tag prefix is `mcp-v`:

| Change | Bump |
| :--- | :--- |
| A new tool, transport, or flag | minor (`2.1.0` → `2.2.0`) |
| A fix inside an existing tool's behaviour | patch (`2.1.0` → `2.1.1`) |
| A removed tool, a renamed argument, an envelope change | major (`2.1.0` → `3.0.0`) |

The version lives in three files and a test fails if they disagree:

```
integrations/mcp-server/package.json     "version"
integrations/mcp-server/server.json      "version" and packages[0].version
integrations/mcp-server/src/constants.js SERVER_VERSION
```

Update all three, then:

```bash
cd integrations/mcp-server
npm install --package-lock-only     # the lockfile carries the version too
node --test test/metadata.test.js   # proves the three agree
```

---

## 2. Prove the release

```bash
cd <repository root>
./scripts/verify.sh                 # 5 stages, must print "passed: 5 failed: 0"
cd integrations/mcp-server && npm test
```

Then check the artifact itself, not the source tree. This is the step that catches a `vendor/` that did not stage:

```bash
cd integrations/mcp-server
npm pack --pack-destination /tmp
rm -rf /tmp/install-check && mkdir /tmp/install-check && cd /tmp/install-check
npm init -y > /dev/null
npm install /tmp/apple-native-engineer-mcp-<version>.tgz
./node_modules/.bin/apple-native-engineer-mcp --version      # must print the new version
./node_modules/.bin/apple-native-engineer-mcp --doctor       # must not report a missing auditor
./node_modules/.bin/apple-native-engineer-mcp --selftest     # 25 tools, 53 resources, 12 prompts
```

A run that only succeeds in the repository has proven nothing about what users install.

---

## 3. Tag and publish

The workflow at `.github/workflows/publish.yml` runs on an `mcp-v*` tag: it re-runs the tests, re-stages
`vendor/`, publishes with npm provenance, then installs the published tarball in a clean directory and runs
`--selftest` against it. If any of that fails, the release failed — even if npm already has the package.

```bash
git tag mcp-v2.1.0
git push origin mcp-v2.1.0
```

Watch it: **Actions → Publish**. Provenance is why `--provenance` is in the workflow: it attaches a signed
statement that the tarball was built from this commit by this workflow, which is the only supply-chain claim that
is worth anything to a user.

Emergency manual publish (only if Actions is down):

```bash
cd integrations/mcp-server
npm publish --access public --provenance
```

A published version cannot be unpublished after 72 hours. If the release is wrong, publish a patch — do not
`npm unpublish`.

---

## 4. Submit to the registries

Publishing to npm makes the package installable. It does not make it *findable*. These submissions are manual
and each has its own review.

| Registry | What to submit | Notes |
| :--- | :--- | :--- |
| Official MCP registry | `integrations/mcp-server/server.json` | `mcpName` in `package.json` must equal `server.json`'s `name`; a test enforces that |
| Smithery | `integrations/mcp-server/smithery.yaml` | The config schema exposes only the Python interpreter and the telemetry mode |
| Glama / mcp.so / PulseMCP | the repository URL and the package name | They index from npm; no manifest needed |
| Docker Hub | `docker build -f integrations/mcp-server/Dockerfile -t <user>/apple-native-engineer .` | Build context is the repository root |

For the official registry, the manifest is validated against
`https://static.modelcontextprotocol.io/schemas/2025-09-29/server.schema.json`; the `$schema` key in `server.json`
points at it. Re-read that schema before a major release rather than assuming it is stable.

---

## 5. After publishing

```bash
npx -y apple-native-engineer-mcp@latest --selftest
```

Then, and only then, move the `Unreleased` section of `CHANGELOG.md` into a dated release and update the version
in the README badge if the test count moved.

---

## Rollback

| Situation | Action |
| :--- | :--- |
| The tarball is broken | Publish a patch with the fix. Deprecate the bad version: `npm deprecate apple-native-engineer-mcp@<version> "broken vendored tools; use <fixed>"` |
| The registry manifest is wrong | Re-submit; the registry reads `server.json` from the tagged commit |
| The Docker image is wrong | Re-tag the image only. The npm artifact and the image share source, not version tags |
| A tool regressed | Revert the commit, bump a patch, publish. Never edit a published tarball |

`npm deprecate` is the honest tool for a bad release: it keeps the install working for anyone who pinned it, while
telling every new install what to use instead.
