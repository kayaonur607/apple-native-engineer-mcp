#!/usr/bin/env node
/**
 * apple-native-engineer-mcp — entry point.
 *
 * Everything the agent can do through this server is reproducible from a shell:
 * each tool shells out to a Python script in `tools/`. That single rule is why
 * the repository stays honest — there is no second implementation to drift.
 *
 * Usage:
 *   node src/index.js                       # speak MCP on stdio (default)
 *   node src/index.js --http                # speak MCP on POST /mcp, port 3927
 *   node src/index.js --http 8080           # … on a specific port
 *   node src/index.js --selftest            # print the inventory and exit
 *   node src/index.js --telemetry-preview   # show exactly what telemetry would record
 */

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createServer, SERVER_NAME, SERVER_VERSION } from "./server.js";
import { promptInventory } from "./prompts.js";
import { resourceInventory } from "./resources.js";
import { MODULES, resolveModules } from "./modules.js";
import { TOOL_SPECS } from "./tools.js";
import { DEFAULT_PORT, startHttpServer } from "./http.js";
import { checkEnvironment } from "./environment.js";
import { previewPayload, telemetryMode, usageFilePath } from "./telemetry.js";

const HELP = [
  `${SERVER_NAME} v${SERVER_VERSION}`,
  "",
  "Usage:",
  "  apple-native-engineer-mcp                 speak MCP on stdio",
  `  apple-native-engineer-mcp --http [port]   speak MCP on POST /mcp (default port ${DEFAULT_PORT})`,
  "  apple-native-engineer-mcp --selftest      print the tool/resource/prompt inventory",
  "  apple-native-engineer-mcp --modules       print the capability module registry",
  "  apple-native-engineer-mcp --doctor        check that this machine can run the server",
  "  apple-native-engineer-mcp --telemetry-preview  print the exact telemetry payload",
  "  apple-native-engineer-mcp --version       print the version",
  "  apple-native-engineer-mcp --help          this message",
  "",
  "HTTP flags:",
  "  --http-host <host>   bind address (default 127.0.0.1)",
  "  --allow-remote       required to bind a non-loopback address",
  "",
  "Environment:",
  "  APPLE_NATIVE_PYTHON       python interpreter (default: python3)",
  "  APPLE_NATIVE_ROOT         repository root override",
  "  APPLE_NATIVE_TIMEOUT_MS   tool timeout in milliseconds (default: 180000)",
  "  APPLE_NATIVE_TELEMETRY    off (default) | local | anonymous",
  "  APPLE_NATIVE_TELEMETRY_URL  HTTPS endpoint for anonymous aggregates",
  "  APPLE_NATIVE_USAGE_FILE   override the local usage file path",
  "  ASC_KEY_ID / ASC_ISSUER_ID / ASC_PRIVATE_KEY_PATH  App Store Connect credentials",
  "",
  "Privacy: telemetry is off unless you turn it on. When on, it records the tool",
  "name, the outcome, a duration bucket and a UTC day — never a path, file name,",
  "source text, prompt, finding, credential or identifier. Run",
  "--telemetry-preview to see the exact bytes.",
  "",
];

/** Read a flag that takes a value: `--flag value` or `--flag=value`. */
function flagValue(args, name) {
  const index = args.findIndex((arg) => arg === name || arg.startsWith(`${name}=`));
  if (index === -1) return undefined;
  const arg = args[index];
  if (arg.includes("=")) return arg.slice(arg.indexOf("=") + 1);
  const next = args[index + 1];
  return next && !next.startsWith("-") ? next : undefined;
}

async function main() {
  const args = process.argv.slice(2);

  if (args.includes("--version") || args.includes("-v")) {
    process.stdout.write(`${SERVER_VERSION}\n`);
    return;
  }

  if (args.includes("--help") || args.includes("-h")) {
    process.stdout.write(HELP.join("\n"));
    return;
  }

  if (args.includes("--modules")) {
    const resolved = resolveModules();
    process.stdout.write(JSON.stringify({ ...resolved, registry: MODULES }, null, 2) + "\n");
    return;
  }

  if (args.includes("--selftest")) {
    const resolved = resolveModules();
    const enabledTools = TOOL_SPECS.map((spec) => spec.name).filter((tool) =>
      MODULES.some((module) => resolved.enabled.includes(module.id) && module.tools.includes(tool)));
    const payload = {
      name: SERVER_NAME,
      version: SERVER_VERSION,
      transport: args.includes("--http") ? "streamable-http" : "stdio",
      modules: resolved,
      tools: enabledTools,
      resources: resourceInventory().length,
      prompts: promptInventory(),
      telemetry: telemetryMode(),
    };
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
    return;
  }

  if (args.includes("--telemetry-preview")) {
    const payload = {
      ...previewPayload(),
      usage_file_when_enabled: usageFilePath(),
    };
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
    return;
  }

  if (args.includes("--doctor")) {
    const run = await checkEnvironment();
    process.stdout.write(`${run.summary}\n`);
    // The tool result and the exit code must agree, or `--doctor` in CI is theatre.
    process.exitCode = run.exitCode;
    return;
  }

  if (args.includes("--http")) {
    const explicitPort = flagValue(args, "--http");
    const port = explicitPort ? Number(explicitPort) : DEFAULT_PORT;
    if (!Number.isInteger(port) || port < 0 || port > 65535) {
      throw new Error(`Invalid port: ${explicitPort}`);
    }
    const host = flagValue(args, "--http-host") ?? "127.0.0.1";
    const allowRemote = args.includes("--allow-remote");

    const { url } = await startHttpServer({ port, host, allowRemote });
    process.stderr.write(
      [
        `${SERVER_NAME} v${SERVER_VERSION} ready (streamable-http)`,
        `  MCP endpoint: POST ${url}/mcp`,
        `  health:       GET  ${url}/health`,
        host === "127.0.0.1" || host === "::1" || host === "localhost"
          ? "  bound to loopback only; other machines cannot reach it"
          : "  WARNING: reachable from the network and unauthenticated — put an authenticating proxy in front",
        "  stdout is not used; send diagnostics to stderr",
        "",
      ].join("\n"),
    );
    return;
  }

  const server = createServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // stdout is reserved for the protocol; diagnostics go to stderr.
  process.stderr.write(`${SERVER_NAME} v${SERVER_VERSION} ready (stdio)\n`);
}

main().catch((error) => {
  // Configuration mistakes deserve a sentence, not a stack trace.
  const message = error?.message ?? String(error);
  const expected = /^Refusing to bind|^Invalid port/.test(message);
  process.stderr.write(expected ? `error: ${message}\n` : `fatal: ${error?.stack ?? message}\n`);
  process.exit(expected ? 2 : 1);
});
