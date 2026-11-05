/**
 * Capability module tests.
 *
 * The rule these protect: a disabled module must be invisible to the client,
 * and an unknown module id must stop startup instead of being ignored.
 */

import assert from "node:assert/strict";
import { after, before, describe, it } from "node:test";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

import {
  CORE_MODULE,
  MODULES,
  moduleFor,
  moduleIds,
  resolveModules,
  toolsFor,
} from "../src/modules.js";
import { createServer } from "../src/server.js";
import { TOOL_SPECS } from "../src/tools.js";

async function connect(options) {
  const server = createServer(options);
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: "module-test", version: "1.0.0" }, { capabilities: {} });
  await Promise.all([server.connect(serverTransport), client.connect(clientTransport)]);
  return { client, server };
}

describe("module registry", () => {
  it("assigns every tool to exactly one module", () => {
    for (const spec of TOOL_SPECS) {
      const matches = MODULES.filter((module) => module.tools.includes(spec.name));
      assert.equal(matches.length, 1, `${spec.name} must belong to exactly one module`);
    }
  });

  it("has no module shadows a tool that does not exist", () => {
    const known = new Set(TOOL_SPECS.map((spec) => spec.name));
    for (const module of MODULES) {
      for (const tool of module.tools) {
        assert.ok(known.has(tool), `${module.id} references unknown tool ${tool}`);
      }
    }
  });

  it("enables everything by default", () => {
    const resolved = resolveModules({});
    assert.equal(resolved.disabled.length, 0);
    assert.equal(toolsFor(resolved.enabled).length, TOOL_SPECS.length);
    assert.equal(resolved.source, "default");
  });

  it("supports explicit module selection and always keeps core", () => {
    const resolved = resolveModules({ APPLE_NATIVE_MODULES: "swift-engineering" });
    assert.ok(resolved.enabled.includes(CORE_MODULE));
    assert.ok(resolved.enabled.includes("swift-engineering"));
    assert.ok(resolved.disabled.includes("app-store-connect"));
    assert.ok(!toolsFor(resolved.enabled).includes("app_store_connect"));
  });

  it("treats 'all' as everything", () => {
    const resolved = resolveModules({ APPLE_NATIVE_MODULES: "all" });
    assert.equal(resolved.disabled.length, 0);
  });

  it("rejects an unknown module id with the valid list", () => {
    assert.throws(
      () => resolveModules({ APPLE_NATIVE_MODULES: "core,not-a-module" }),
      (error) => error.message.includes("not-a-module") && error.message.includes(moduleIds()[0]),
    );
  });

  it("maps tools back to their module", () => {
    assert.equal(moduleFor("lint_swiftui").id, "swift-engineering");
    assert.equal(moduleFor("app_store_connect").id, "app-store-connect");
    assert.equal(moduleFor("nonexistent"), undefined);
  });
});

describe("module isolation over the protocol", () => {
  let client;

  before(async () => {
    ({ client } = await connect({ modules: resolveModules({ APPLE_NATIVE_MODULES: "core" }) }));
  });

  after(async () => {
    await client?.close();
  });

  it("only advertises the enabled module's tools", async () => {
    const { tools } = await client.listTools();
    const names = tools.map((tool) => tool.name).sort();
    assert.deepEqual(names, ["audit_project", "check_environment", "inspect_apple_project", "review_diff"]);
  });

  it("keeps the knowledge base available", async () => {
    const { resources } = await client.listResources();
    assert.ok(resources.length > 40, "resources are knowledge, not a capability to gate");
  });

  it("refuses a disabled tool instead of pretending", async () => {
    const result = await client.callTool({ name: "lint_swiftui", arguments: { path: "." } });
    assert.equal(result.isError, true, "a disabled tool must not run");
    const text = result.content.map((part) => part.text ?? "").join(" ");
    assert.match(text, /unknown tool|not found|invalid|tool/i);
  });
});
