/**
 * Publish-metadata consistency.
 *
 * A published MCP server is described in four places — package.json, server.json
 * (the registry manifest), smithery.yaml and the Dockerfile — and each one is
 * read by a different pipeline. They drift silently: the registry advertises a
 * version that npm never received, or the image copies a directory that was
 * renamed. Nothing at runtime notices, which is why this test exists.
 *
 * It runs offline and touches only files, so it is safe in CI and fast.
 */

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const PACKAGE_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const REPO_ROOT = path.resolve(PACKAGE_ROOT, "..", "..");

const read = (...parts) => fs.readFileSync(path.join(PACKAGE_ROOT, ...parts), "utf8");
const json = (...parts) => JSON.parse(read(...parts));

const pkg = json("package.json");
const server = json("server.json");
const constants = read("src", "constants.js");

describe("publish metadata", () => {
  it("uses one version everywhere", () => {
    const fromSource = constants.match(/SERVER_VERSION\s*=\s*"([^"]+)"/)?.[1];
    assert.ok(fromSource, "constants.js must declare SERVER_VERSION");
    assert.equal(pkg.version, fromSource, "package.json version drifted from the server");
    assert.equal(server.version, fromSource, "server.json version drifted from the server");
    assert.deepEqual(server.packages, [], "GitHub-only releases must not advertise an npm package");
  });

  it("names the package the registry points at", () => {
    assert.deepEqual(server.packages, []);
    assert.match(server.name ?? "", /^[a-z0-9.-]+\/[a-z0-9.-]+$/);
    assert.equal(pkg.mcpName, server.name, "package.json mcpName must match the registry name");
  });

  it("points every URL at the repository that actually exists", () => {
    const repoUrl = pkg.repository?.url ?? "";
    const slug = repoUrl.replace(/^git\+/, "").replace(/\.git$/, "");
    assert.equal(server.repository?.url, slug);
    assert.ok((pkg.homepage ?? "").startsWith(`${slug}#`), "homepage must be the repository README");
    assert.ok((pkg.bugs?.url ?? "").startsWith(`${slug}/issues`));
  });

  it("ships the runtime it needs and nothing more", () => {
    for (const entry of ["src/", "vendor/", "README.md", "LICENSE"]) {
      assert.ok(pkg.files?.includes(entry), `the published tarball must include ${entry}`);
    }
    assert.equal(pkg.private, true, "GitHub-only distribution must prevent accidental npm publication");
    assert.ok(pkg.bin?.["apple-native-engineer-mcp"], "the bin entry is how npx finds the server");
    assert.match(pkg.engines?.node ?? "", />=\s*20/);
    assert.ok(pkg.scripts?.prepack, "vendor/ must be staged on prepack, or the tarball cannot run");
  });

  it("declares the same tools the server registers", async () => {
    const { TOOL_SPECS } = await import("../src/tools.js");
    const description = `${pkg.description} ${server.description}`.toLowerCase();
    assert.ok(TOOL_SPECS.length >= 16);
    // No hard-coded tool count: the description must not contradict the code.
    const claimed = description.match(/(\d+)\s+(?:verifiable\s+)?(?:audits|tools)/);
    if (claimed) {
      assert.ok(
        Number(claimed[1]) <= TOOL_SPECS.length,
        `metadata claims ${claimed[1]} tools but the server registers ${TOOL_SPECS.length}`,
      );
    }
  });

  it("has a Dockerfile that copies paths that exist", () => {
    const dockerfile = read("Dockerfile");
    const copies = [...dockerfile.matchAll(/^COPY\s+(?:--from=\S+\s+)?(\S+)\s+\.\/(\S+)/gm)];
    assert.ok(copies.length > 0, "the Dockerfile must copy the runtime in");
    for (const [, source] of copies) {
      // `COPY --from=<stage> /app/...` names a path inside another stage, not
      // one on disk: only local sources can be checked here.
      if (source.startsWith("/")) continue;
      // The build context is the repository root, so a source is either
      // integrations/mcp-server/... or a repository-root path.
      const candidates = [path.join(PACKAGE_ROOT, source), path.join(REPO_ROOT, source)];
      assert.ok(
        candidates.some((candidate) => fs.existsSync(candidate)),
        `Dockerfile COPY source does not exist (context is the repo root): ${source}`,
      );
    }
    assert.match(dockerfile, /HEALTHCHECK[\s\S]*?\/health/, "the image must probe /health");
    assert.match(dockerfile, /USER\s+\w+/, "the image must not run as root");
  });

  it("publishes through GitHub Releases without npm credentials", () => {
    const workflow = fs.readFileSync(path.join(REPO_ROOT, ".github/workflows/publish.yml"), "utf8");
    assert.match(workflow, /gh release create/);
    assert.doesNotMatch(workflow, /npm publish|NPM_TOKEN|NODE_AUTH_TOKEN/);
    assert.ok(fs.existsSync(path.join(PACKAGE_ROOT, "scripts/github-launcher.mjs")));
  });
});
