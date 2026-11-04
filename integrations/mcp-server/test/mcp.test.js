/**
 * Protocol-level conformance tests.
 *
 * These drive the real McpServer through the SDK's in-memory transport and a
 * real Client, so they fail if the protocol surface regresses — not just if a
 * helper function changes.
 */

import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { after, before, describe, it } from "node:test";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

import { createServer } from "../src/server.js";
import { TOOL_SPECS } from "../src/tools.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(HERE, "..", "..", "..");
const FIXTURE = path.join(REPO_ROOT, "tests", "fixtures", "legacy-app");

async function connect() {
  const server = createServer();
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: "test-client", version: "1.0.0" }, { capabilities: {} });
  await Promise.all([server.connect(serverTransport), client.connect(clientTransport)]);
  return { client, server };
}

describe("apple-native-engineer MCP server", () => {
  let client;

  before(async () => {
    ({ client } = await connect());
  });

  after(async () => {
    await client?.close();
  });

  it("advertises a complete tool inventory", async () => {
    const { tools } = await client.listTools();
    const names = tools.map((tool) => tool.name).sort();
    assert.deepEqual(names, TOOL_SPECS.map((spec) => spec.name).sort());
    for (const tool of tools) {
      assert.ok(tool.description && tool.description.length > 40, `${tool.name} needs a description`);
      assert.ok(tool.inputSchema, `${tool.name} needs an input schema`);
    }
  });

  it("marks audit tools read-only", async () => {
    const { tools } = await client.listTools();
    const inspector = tools.find((tool) => tool.name === "inspect_apple_project");
    assert.equal(inspector.annotations?.readOnlyHint, true);
    assert.equal(inspector.annotations?.destructiveHint, false);
  });

  it("exposes the knowledge base as resources", async () => {
    const { resources } = await client.listResources();
    assert.ok(resources.length >= 40, `expected the full knowledge base, got ${resources.length}`);
    const skill = resources.find((resource) => resource.uri === "apple-native://skill");
    assert.ok(skill, "SKILL.md must be exposed as a resource");

    const { contents } = await client.readResource({ uri: "apple-native://references/liquid-glass" });
    assert.equal(contents.length, 1);
    assert.match(contents[0].text, /Liquid Glass/i);
  });

  it("exposes every command as a prompt", async () => {
    const { prompts } = await client.listPrompts();
    assert.ok(prompts.length >= 10, `expected at least 10 prompts, got ${prompts.length}`);
    assert.ok(prompts.some((prompt) => prompt.name === "apple-native-release"));
  });

  it("runs a real audit and returns a structured envelope", async () => {
    const result = await client.callTool({
      name: "inspect_apple_project",
      arguments: { path: FIXTURE },
    });
    assert.ok(Array.isArray(result.content) && result.content.length >= 1);
    const envelope = result.structuredContent;
    assert.equal(envelope.schema_version, "2.0");
    assert.equal(envelope.tool, "project-inspector");
    assert.equal(envelope.target, FIXTURE);
    assert.ok(["pass", "warn", "fail"].includes(envelope.status));
    assert.ok(envelope.summary && typeof envelope.summary.total === "number");
  });

  it("reports a lint failure with finding codes", async () => {
    const result = await client.callTool({ name: "lint_swiftui", arguments: { path: FIXTURE } });
    const envelope = result.structuredContent;
    assert.equal(envelope.status, "fail");
    assert.ok(envelope.findings.length > 0);
    assert.match(envelope.findings.map((finding) => finding.code).join(","), /SWU/);
  });

  it("surfaces a missing path as an MCP error instead of crashing", async () => {
    const result = await client.callTool({
      name: "inspect_apple_project",
      arguments: { path: path.join(REPO_ROOT, "definitely-not-here") },
    });
    assert.equal(result.isError, true);
    assert.match(result.content[0].text, /Path does not exist/);
  });

  it("validates a single SF Symbol against the real catalogue", async () => {
    const result = await client.callTool({
      name: "validate_sf_symbols",
      arguments: { name: "square.and.pencil", ios_target: "17.0", path: FIXTURE },
    });
    assert.equal(result.structuredContent.status, "pass");
  });
});
