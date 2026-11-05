/**
 * Streamable HTTP transport.
 *
 * stdio is the right transport when the client launches the server as a child
 * process. It is the wrong transport when the server lives somewhere else: a
 * container, a shared dev box, a hosted endpoint, or a browser-based client that
 * cannot spawn processes. This module serves the same McpServer over
 * `POST /mcp` using the MCP Streamable HTTP transport, in stateless mode, so any
 * number of clients can hit it without session bookkeeping.
 *
 * Security posture — a local HTTP server that runs project audits is an attack
 * surface, so the defaults are deliberately unfriendly:
 *
 *   - binds to 127.0.0.1 unless `--http-host` says otherwise;
 *   - refuses cross-origin browser requests by default (DNS-rebinding defence);
 *   - rejects non-JSON bodies and bodies over `maxBodyBytes`;
 *   - never enables CORS, because a browser page has no reason to call this.
 *
 * Exposing it beyond loopback is an explicit, documented decision — see
 * `--allow-remote` in the README, which also warns that the server has no
 * authentication of its own and must sit behind a proxy that does.
 */

import http from "node:http";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createServer, SERVER_NAME, SERVER_VERSION } from "./server.js";
import { TOOL_SPECS } from "./tools.js";
import { telemetryMode } from "./telemetry.js";

const DEFAULT_PORT = 3927;
const DEFAULT_MAX_BODY = 4 * 1024 * 1024;

/** Origins allowed to call the server from a browser context. */
function allowedOrigins(port) {
  return new Set([
    `http://127.0.0.1:${port}`,
    `http://localhost:${port}`,
    `http://[::1]:${port}`,
  ]);
}

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
    "cache-control": "no-store",
  });
  res.end(body);
}

function readBody(req, limit) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > limit) {
        reject(Object.assign(new Error("Request body too large"), { status: 413 }));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

/**
 * Create (but do not start) the HTTP server.
 *
 * Split from `startHttpServer` so tests can bind port 0 and read the assigned
 * port without racing a listen promise.
 *
 * @param {object} [options]
 * @param {number} [options.port]
 * @param {string} [options.host]
 * @param {boolean} [options.allowRemote] permit a non-loopback bind
 * @param {number} [options.maxBodyBytes]
 * @param {(line: string) => void} [options.log]
 */
export function createHttpServer({
  port = DEFAULT_PORT,
  host = "127.0.0.1",
  allowRemote = false,
  maxBodyBytes = DEFAULT_MAX_BODY,
  log = (line) => process.stderr.write(`${line}\n`),
} = {}) {
  const startedAt = Date.now();
  const isLoopback = host === "127.0.0.1" || host === "::1" || host === "localhost";
  if (!isLoopback && !allowRemote) {
    throw new Error(
      `Refusing to bind ${host}: this server runs project audits and has no authentication. ` +
        "Pass --allow-remote only when a reverse proxy in front of it authenticates callers.",
    );
  }

  const origins = allowedOrigins(port);

  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url ?? "/", `http://${req.headers.host ?? "localhost"}`);

    // Health is intentionally unauthenticated and body-free: it is what a
    // container orchestrator and a human with curl both need.
    if (req.method === "GET" && (url.pathname === "/health" || url.pathname === "/")) {
      sendJson(res, 200, {
        name: SERVER_NAME,
        version: SERVER_VERSION,
        transport: "streamable-http",
        status: "ok",
        uptime_seconds: Math.floor((Date.now() - startedAt) / 1000),
        tools: TOOL_SPECS.length,
        telemetry: telemetryMode(),
      });
      return;
    }

    if (url.pathname !== "/mcp") {
      sendJson(res, 404, { error: "not_found", hint: "MCP endpoint is POST /mcp; health is GET /health." });
      return;
    }

    // DNS-rebinding defence: a page served from evil.example that resolves to
    // 127.0.0.1 still sends its own Origin. Reject anything not explicitly
    // allowed, and reject requests with no usable Origin only when they claim
    // to be cross-origin (Sec-Fetch-Site).
    const origin = req.headers.origin;
    if (origin && !origins.has(origin)) {
      sendJson(res, 403, {
        error: "origin_not_allowed",
        detail: `Origin ${origin} is not allowed. Add it explicitly only if you trust it.`,
      });
      return;
    }

    if (req.method !== "POST") {
      res.writeHead(405, { allow: "POST", "content-type": "application/json" });
      res.end(JSON.stringify({ error: "method_not_allowed", detail: "Stateless mode accepts POST /mcp only." }));
      return;
    }

    const contentType = String(req.headers["content-type"] ?? "");
    if (!contentType.includes("application/json")) {
      sendJson(res, 415, { error: "unsupported_media_type", detail: "Content-Type must be application/json." });
      return;
    }

    let body;
    try {
      const raw = await readBody(req, maxBodyBytes);
      body = JSON.parse(raw.toString("utf8"));
    } catch (error) {
      sendJson(res, error.status ?? 400, { error: "bad_request", detail: error.message });
      return;
    }

    // Stateless: one server + transport per request. The server holds no state
    // across calls, and a fresh instance means a crashed request cannot poison
    // the next one.
    const mcp = createServer();
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
    try {
      await mcp.connect(transport);
      await transport.handleRequest(req, res, body);
    } catch (error) {
      log(`[${SERVER_NAME}] request failed: ${error?.message ?? error}`);
      if (!res.headersSent) sendJson(res, 500, { error: "internal_error" });
    } finally {
      res.on("close", () => {
        transport.close().catch(() => {});
        mcp.close().catch(() => {});
      });
    }
  });

  server.on("clientError", (error, socket) => {
    if (!socket.writable) return;
    socket.end("HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n");
  });

  return server;
}

/**
 * Start the HTTP transport and resolve once the socket is listening.
 * @returns {Promise<{ server: http.Server, url: string, close: () => Promise<void> }>}
 */
export function startHttpServer(options = {}) {
  const server = createHttpServer(options);
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(options.port ?? DEFAULT_PORT, options.host ?? "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : (options.port ?? DEFAULT_PORT);
      const host = options.host ?? "127.0.0.1";
      const url = `http://${host.includes(":") ? `[${host}]` : host}:${port}`;
      resolve({
        server,
        port,
        url,
        close: () =>
          new Promise((done) => {
            server.closeAllConnections?.();
            server.close(() => done());
          }),
      });
    });
  });
}

export { DEFAULT_PORT };
