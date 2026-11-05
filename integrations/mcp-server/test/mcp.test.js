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
import { ProgressNotificationSchema } from "@modelcontextprotocol/sdk/types.js";

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

  it("names the umbrella prompt once, without a duplicated prefix", async () => {
    const { prompts } = await client.listPrompts();
    const names = prompts.map((prompt) => prompt.name);
    assert.ok(names.includes("apple-native"), "the umbrella prompt must be `apple-native`");
    assert.ok(
      !names.includes("apple-native-apple-native"),
      "regression: the umbrella prompt regained its duplicated prefix",
    );
    // Every other prompt must be namespaced exactly once.
    for (const name of names.filter((entry) => entry !== "apple-native")) {
      assert.match(name, /^apple-native-[a-z0-9-]+$/);
      assert.ok(!name.startsWith("apple-native-apple-native-"), `${name} is double-prefixed`);
    }
  });

  it("renders a prompt with its workflow body and optional focus", async () => {
    const { messages } = await client.getPrompt({
      name: "apple-native-release",
      arguments: { project: "/tmp/Example", focus: "the paywall copy" },
    });
    assert.equal(messages.length, 1);
    const text = messages[0].content.text;
    assert.match(text, /\/tmp\/Example/);
    assert.match(text, /the paywall copy/);
    assert.match(text, /apple-native-engineer MCP tools/);
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

  it("audits the whole project in one call and merges every report", async () => {
    const result = await client.callTool({ name: "audit_project", arguments: { path: FIXTURE } });
    const envelope = result.structuredContent;
    assert.equal(envelope.tool, "suite");
    assert.equal(envelope.target, FIXTURE);
    assert.equal(envelope.status, "fail");
    assert.deepEqual(envelope.data.failures, []);

    const audited = Object.keys(envelope.data.tools).sort();
    assert.deepEqual(audited, [
      "accessibility-auditor",
      "liquid-glass-auditor",
      "localization-checker",
      "privacy-auditor",
      "project-inspector",
      "sf-symbols-catalog",
      "swiftui-linter",
      "widget-validator",
    ]);

    // Every merged finding names the audit that produced it, so an agent can
    // route a fix without re-running the suite.
    assert.ok(envelope.findings.length > 0);
    for (const finding of envelope.findings) {
      assert.ok(audited.includes(finding.tool), `finding has no attributable tool: ${finding.code}`);
    }
    // Merged counters must equal the sum of the children, not the last child.
    const summed = Object.values(envelope.data.tools).reduce(
      (total, entry) => total + Number(entry.summary?.total ?? 0),
      0,
    );
    assert.equal(envelope.summary.total, summed);
  });

  it("reports progress for a long composite instead of going silent", async () => {
    const updates = [];
    const { client: fresh } = await connect();
    fresh.setNotificationHandler(ProgressNotificationSchema, (notification) => {
      updates.push(notification.params);
    });
    try {
      const result = await fresh.callTool(
        { name: "audit_project", arguments: { path: FIXTURE }, _meta: { progressToken: "review-1" } },
        undefined,
      );
      assert.equal(result.structuredContent.tool, "suite");
    } finally {
      await fresh.close();
    }
    assert.equal(updates.length, 8, "one progress notification per audit");
    assert.equal(updates.at(-1).progress, 8);
    assert.equal(updates.at(-1).total, 8);
    assert.equal(updates[0].progressToken, "review-1");
  });
});
