/**
 * Server assembly.
 *
 * Split from `index.js` so the tests can build a server instance and drive it
 * through an in-memory transport without spawning a process.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerPrompts } from "./prompts.js";
import { registerResources } from "./resources.js";
import { registerTools } from "./tools.js";

export const SERVER_NAME = "apple-native-engineer";
export const SERVER_VERSION = "2.0.0";

/**
 * Build a fully configured McpServer (tools + resources + prompts).
 * @returns {McpServer}
 */
export function createServer({ name = SERVER_NAME, version = SERVER_VERSION } = {}) {
  const server = new McpServer(
    { name, version },
    {
      instructions: [
        "You are connected to apple-native-engineer, an Apple platform engineering toolkit.",
        "",
        "Core loop for any Apple task:",
        "1. inspect_apple_project first — understand targets, OS floor, Swift version and architecture.",
        "2. Before writing UI, read the apple-native://skill resource and the relevant references/ resource.",
        "3. After changing code, run lint_swiftui, audit_accessibility and audit_liquid_glass.",
        "4. Before claiming a feature is shippable, run generate_release_report and quote its verdict.",
        "",
        "Rules that override model preference:",
        "- Never introduce hardcoded colours, fixed font sizes or .frame(width:) on text.",
        "- Never hand-build glass effects; use Liquid Glass APIs on iOS 26+ with an availability guard.",
        "- Treat any tool result with status 'fail' as a blocker, and 'warn' as work you must resolve or justify.",
        "- Cite finding codes (for example SWU002, A11Y001, PRIV010) when you report problems.",
      ].join("\n"),
    },
  );

  registerTools(server);
  registerResources(server);
  registerPrompts(server);

  return server;
}
