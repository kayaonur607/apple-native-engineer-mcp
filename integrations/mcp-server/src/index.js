#!/usr/bin/env node
/**
 * apple-native-engineer-mcp — stdio entry point.
 *
 * Everything the agent can do through this server is reproducible from a shell:
 * each tool shells out to a Python script in `tools/`. That single rule is why
 * the repository stays honest — there is no second implementation to drift.
 *
 * Usage:
 *   node src/index.js            # speak MCP on stdio
 *   node src/index.js --selftest # print the tool/resource inventory and exit
 */

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createServer, SERVER_NAME, SERVER_VERSION } from "./server.js";
import { promptInventory } from "./prompts.js";
import { resourceInventory } from "./resources.js";
import { TOOL_SPECS } from "./tools.js";

async function main() {
  const args = process.argv.slice(2);

  if (args.includes("--selftest")) {
    const payload = {
      name: SERVER_NAME,
      version: SERVER_VERSION,
      tools: TOOL_SPECS.map((spec) => spec.name),
      resources: resourceInventory().length,
      prompts: promptInventory(),
    };
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
    return;
  }

  if (args.includes("--help") || args.includes("-h")) {
    process.stdout.write(
      [
        `${SERVER_NAME} v${SERVER_VERSION}`,
        "",
        "Environment:",
        "  APPLE_NATIVE_PYTHON     python interpreter (default: python3)",
        "  APPLE_NATIVE_ROOT       repository root override",
        "  APPLE_NATIVE_TIMEOUT_MS tool timeout in milliseconds (default: 180000)",
        "  ASC_KEY_ID / ASC_ISSUER_ID / ASC_PRIVATE_KEY_PATH  App Store Connect credentials",
        "",
        "Flags:",
        "  --selftest   print the tool/resource/prompt inventory",
        "  --help       this message",
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
  process.stderr.write(`fatal: ${error?.stack ?? error}\n`);
  process.exit(1);
});
