/**
 * Streamable HTTP transport tests.
 *
 * These bind a real socket on port 0 and speak to it with `fetch`, because the
 * interesting failures in an HTTP transport are the ones an in-memory pair
 * cannot reproduce: header handling, body limits, origin checks, clean shutdown.
 */

import http from "node:http";
import assert from "node:assert/strict";
import { after, before, describe, it } from "node:test";

import { startHttpServer } from "../src/http.js";

const INITIALIZE = {
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "2025-06-18",
    capabilities: {},
    clientInfo: { name: "http-test", version: "1.0.0" },
  },
};

const ACCEPT = "application/json, text/event-stream";

describe("streamable HTTP transport", () => {
  let handle;

  before(async () => {
    handle = await startHttpServer({ port: 0, log: () => {} });
  });

  after(async () => {
    await handle?.close();
  });

  it("binds a real port and reports its own URL", () => {
    assert.ok(handle.port > 0);
    assert.match(handle.url, /^http:\/\/127\.0\.0\.1:\d+$/);
  });

  it("answers /health without touching the protocol layer", async () => {
    const response = await fetch(`${handle.url}/health`);
    assert.equal(response.status, 200);
    const body = await response.json();
    assert.equal(body.name, "apple-native-engineer");
    assert.equal(body.transport, "streamable-http");
    assert.equal(body.status, "ok");
    assert.ok(body.tools >= 14);
    assert.equal(body.telemetry, "off");
  });

  it("completes an MCP initialize handshake over POST /mcp", async () => {
    const response = await fetch(`${handle.url}/mcp`, {
      method: "POST",
      headers: { "content-type": "application/json", accept: ACCEPT },
      body: JSON.stringify(INITIALIZE),
    });
    assert.equal(response.status, 200);
    const text = await response.text();
    // The transport may answer as JSON or as a single SSE event; both are valid.
    const payload = text.startsWith("event:")
      ? JSON.parse(text.split("\ndata: ")[1].split("\n")[0])
      : JSON.parse(text);
    assert.equal(payload.result.serverInfo.name, "apple-native-engineer");
    assert.ok(payload.result.protocolVersion);
  });

  it("rejects a cross-origin browser request", async () => {
    const response = await fetch(`${handle.url}/mcp`, {
      method: "POST",
      headers: { "content-type": "application/json", accept: ACCEPT, origin: "https://evil.example" },
      body: JSON.stringify(INITIALIZE),
    });
    assert.equal(response.status, 403);
    const body = await response.json();
    assert.equal(body.error, "origin_not_allowed");
  });

  it("rejects a foreign Host even without Origin", async () => {
    const result = await new Promise((resolve, reject) => {
      const request = http.request(`${handle.url}/mcp`, {
        method: "POST",
        headers: { host: "attacker.example", "content-type": "application/json", accept: ACCEPT },
      }, response => {
        let body = "";
        response.on("data", chunk => { body += chunk; });
        response.on("end", () => resolve({ status: response.statusCode, body: JSON.parse(body) }));
      });
      request.on("error", reject);
      request.end(JSON.stringify(INITIALIZE));
    });
    assert.equal(result.status, 403);
    assert.equal(result.body.error, "host_not_allowed");
  });

  it("accepts the actual ephemeral loopback Origin", async () => {
    const response = await fetch(`${handle.url}/mcp`, {
      method: "POST",
      headers: { origin: handle.url, "content-type": "application/json", accept: ACCEPT },
      body: JSON.stringify(INITIALIZE),
    });
    assert.equal(response.status, 200);
    await response.text();
  });

  it("rejects cross-site requests that omit Origin", async () => {
    const response = await fetch(`${handle.url}/mcp`, {
      method: "POST",
      headers: { "sec-fetch-site": "cross-site", "content-type": "application/json", accept: ACCEPT },
      body: JSON.stringify(INITIALIZE),
    });
    assert.equal(response.status, 403);
  });

  it("rejects a non-JSON content type", async () => {
    const response = await fetch(`${handle.url}/mcp`, {
      method: "POST",
      headers: { "content-type": "text/plain", accept: ACCEPT },
      body: "{}",
    });
    assert.equal(response.status, 415);
  });

  it("rejects an unparseable body with 400 rather than crashing", async () => {
    const response = await fetch(`${handle.url}/mcp`, {
      method: "POST",
      headers: { "content-type": "application/json", accept: ACCEPT },
      body: "{not json",
    });
    assert.equal(response.status, 400);
  });

  it("refuses GET /mcp in stateless mode", async () => {
    const response = await fetch(`${handle.url}/mcp`, { headers: { accept: ACCEPT } });
    assert.equal(response.status, 405);
    assert.equal(response.headers.get("allow"), "POST");
  });

  it("documents the endpoint on an unknown path", async () => {
    const response = await fetch(`${handle.url}/nope`);
    assert.equal(response.status, 404);
    const body = await response.json();
    assert.match(body.hint, /POST \/mcp/);
  });
});

describe("network exposure", () => {
  it("refuses a non-loopback bind without --allow-remote", () => {
    assert.throws(
      () => startHttpServer({ port: 0, host: "0.0.0.0" }),
      /Refusing to bind 0\.0\.0\.0/,
    );
  });
});
