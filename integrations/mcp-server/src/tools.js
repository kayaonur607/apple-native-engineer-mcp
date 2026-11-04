/**
 * Tool registry: every MCP tool maps 1:1 onto a CLI script in `tools/`.
 *
 * Keeping the mapping thin means the MCP server can never drift from the CLI:
 * whatever an agent can do through MCP, a human can reproduce with one command,
 * and the CI suite exercises exactly the same code path.
 */

import { z } from "zod";
import { errorResult, resolveTarget, runTool, toResult } from "./runner.js";

const READ_ONLY = {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
};

const OPTIONAL_PATH = z
  .string()
  .optional()
  .describe("Project directory to analyse. Relative paths resolve against the client's working directory; defaults to '.'");

/** Shared envelope schema so structuredContent validates on the client side. */
const ENVELOPE = z
  .object({
    schema_version: z.string(),
    tool: z.string(),
    tool_version: z.string().optional(),
    target: z.string(),
    status: z.enum(["pass", "warn", "fail"]),
    summary: z
      .object({
        critical: z.number(),
        error: z.number(),
        warning: z.number(),
        info: z.number(),
        total: z.number(),
      })
      .passthrough(),
    findings: z
      .array(
        z
          .object({
            code: z.string(),
            severity: z.string(),
            message: z.string(),
            file: z.string().optional(),
            line: z.number().optional(),
            hint: z.string().optional(),
            docs: z.string().optional(),
          })
          .passthrough(),
      )
      .optional(),
    data: z.record(z.unknown()).optional(),
  })
  .passthrough();

/**
 * @typedef {Object} ToolSpec
 * @property {string} name
 * @property {string} title
 * @property {string} description
 * @property {import('zod').ZodRawShape} inputSchema
 * @property {(args: any) => Promise<any>} run
 */

/** @type {ToolSpec[]} */
export const TOOL_SPECS = [
  {
    name: "inspect_apple_project",
    title: "Inspect Apple project",
    description:
      "Structural analysis of an Xcode project or Swift package: targets, deployment targets, Swift version, " +
      "frameworks in use, architecture signals and structural debt. Start here on an unfamiliar repository.",
    inputSchema: { path: OPTIONAL_PATH },
    run: async (args) => {
      const target = resolveTarget(args.path);
      return runTool("tools/project-inspector/inspect_project.py", [target]);
    },
  },
  {
    name: "audit_privacy_manifest",
    title: "Audit privacy manifest",
    description:
      "Detects Required-Reason API usage in Swift sources and validates PrivacyInfo.xcprivacy: undeclared " +
      "categories, invalid reason codes, tracking domains and collected-data declarations.",
    inputSchema: { path: OPTIONAL_PATH },
    run: async (args) => runTool("tools/privacy-auditor/audit_privacy.py", [resolveTarget(args.path)]),
  },
  {
    name: "validate_app_icon",
    title: "Validate App Store icon",
    description:
      "Validates the 1024x1024 marketing icon: exact dimensions, PNG format, zero alpha channel, bit depth. " +
      "These are the four reasons App Store Connect rejects an icon at upload.",
    inputSchema: {
      path: OPTIONAL_PATH,
      icon_path: z.string().describe("Path to the 1024x1024 marketing icon PNG"),
    },
    run: async (args) =>
      runTool("tools/asset-validator/validate_assets.py", [
        resolveTarget(args.path),
        "--icon",
        resolveTarget(args.icon_path),
      ]),
  },
  {
    name: "validate_app_metadata",
    title: "Validate App Store metadata",
    description:
      "Checks App Store listing copy against App Store Connect limits (name 30, subtitle 30, keywords 100, " +
      "promotional text 170, description 4000), required https URLs and screenshot counts.",
    inputSchema: {
      path: z.string().describe("Path to the metadata JSON file"),
    },
    run: async (args) => runTool("tools/metadata-validator/validate_metadata.py", [resolveTarget(args.path)]),
  },
  {
    name: "check_localization",
    title: "Check localisation and RTL",
    description:
      "Finds user-visible string literals that are not localisable, left/right layout that fails to mirror in " +
      "RTL, and String Catalog keys with missing translations.",
    inputSchema: { path: OPTIONAL_PATH },
    run: async (args) => runTool("tools/localization-checker/check_localization.py", [resolveTarget(args.path)]),
  },
  {
    name: "validate_widgets",
    title: "Validate widgets and Live Activities",
    description:
      "Audits WidgetKit and ActivityKit: Dynamic Island presentation regions, NSSupportsLiveActivities, " +
      "supported families, timeline providers and App Group wiring.",
    inputSchema: { path: OPTIONAL_PATH },
    run: async (args) => runTool("tools/widget-validator/validate_widget.py", [resolveTarget(args.path)]),
  },
  {
    name: "lint_swiftui",
    title: "Lint SwiftUI",
    description:
      "20 opinionated SwiftUI rules: deprecated APIs (foregroundColor, NavigationView, onChange), hardcoded " +
      "colours and font sizes, view-identity churn, AnyView, scaleEffect(0) and body-side effects.",
    inputSchema: { path: OPTIONAL_PATH },
    run: async (args) => runTool("tools/swiftui-linter/lint_swiftui.py", [resolveTarget(args.path)]),
  },
  {
    name: "audit_accessibility",
    title: "Audit accessibility",
    description:
      "Computes WCAG contrast for detected text colours in both appearances, and flags fixed font sizes, " +
      "single-line limits, sub-44pt tap targets and unlabelled icon-only buttons.",
    inputSchema: { path: OPTIONAL_PATH },
    run: async (args) => runTool("tools/accessibility-auditor/audit_accessibility.py", [resolveTarget(args.path)]),
  },
  {
    name: "audit_liquid_glass",
    title: "Audit Liquid Glass adoption",
    description:
      "Checks iOS 26 Liquid Glass usage (.glassEffect, GlassEffectContainer, .buttonStyle(.glass), " +
      "scrollEdgeEffect) against the deployment target, and flags hand-rolled 'fake glass' stacks.",
    inputSchema: { path: OPTIONAL_PATH },
    run: async (args) => runTool("tools/liquid-glass-auditor/audit_liquid_glass.py", [resolveTarget(args.path)]),
  },
  {
    name: "validate_sf_symbols",
    title: "Validate SF Symbols",
    description:
      "Validates every Image(systemName:) against a catalogue of 9,000+ real SF Symbols extracted from the " +
      "system, including the OS release that introduced each symbol, with typo suggestions.",
    inputSchema: {
      path: OPTIONAL_PATH,
      name: z.string().optional().describe("Check a single symbol name instead of scanning a project"),
      ios_target: z.string().optional().describe("Override the iOS deployment target, e.g. '17.0'"),
    },
    run: async (args) => {
      const cliArgs = args.name
        ? ["--name", args.name, "."]
        : [resolveTarget(args.path)];
      if (args.ios_target) cliArgs.push("--ios", args.ios_target);
      return runTool("tools/sf-symbols-catalog/check_symbols.py", cliArgs);
    },
  },
  {
    name: "forge_design_tokens",
    title: "Forge design tokens",
    description:
      "Compiles a design token JSON (colours with light/dark pairs, spacing, radius, typography) into idiomatic " +
      "SwiftUI tokens, optionally emitting .xcassets colour sets, and warns on failing contrast pairs.",
    inputSchema: {
      path: z.string().describe("Path to the token JSON file"),
      out: z.string().optional().describe("Write the generated Swift file here"),
      xcassets: z.string().optional().describe("Also emit a .xcassets colour set directory here"),
    },
    run: async (args) => {
      const cliArgs = [resolveTarget(args.path)];
      if (args.out) cliArgs.push("--out", resolveTarget(args.out));
      if (args.xcassets) cliArgs.push("--xcassets", resolveTarget(args.xcassets));
      return runTool("tools/design-token-forge/forge_tokens.py", cliArgs);
    },
  },
  {
    name: "generate_release_report",
    title: "Generate release readiness report",
    description:
      "Runs every audit and produces a weighted App Store readiness verdict. Gates that cannot be inspected " +
      "(no metadata, no icon) block the release rather than being silently skipped.",
    inputSchema: {
      path: OPTIONAL_PATH,
      metadata_path: z.string().optional().describe("Path to App Store metadata JSON"),
      icon_path: z.string().optional().describe("Path to the 1024x1024 icon"),
      screenshots_path: z.string().optional().describe("Directory of App Store screenshots"),
      output: z.string().optional().describe("Write the Markdown report to this path"),
    },
    run: async (args) => {
      const cliArgs = [resolveTarget(args.path)];
      if (args.metadata_path) cliArgs.push("--metadata", resolveTarget(args.metadata_path));
      if (args.icon_path) cliArgs.push("--icon", resolveTarget(args.icon_path));
      if (args.screenshots_path) cliArgs.push("--screenshots", resolveTarget(args.screenshots_path));
      if (args.output) cliArgs.push("--output", resolveTarget(args.output));
      return runTool("tools/release-readiness/generate_report.py", cliArgs);
    },
  },
  {
    name: "app_store_connect",
    title: "App Store Connect (read-only)",
    description:
      "Read-only App Store Connect access: verify credentials, list apps, list versions and builds. Requires " +
      "ASC_KEY_ID / ASC_ISSUER_ID / ASC_PRIVATE_KEY_PATH. Never falls back to mock data silently.",
    inputSchema: {
      operation: z.enum(["verify", "list_apps", "versions", "builds"]).describe("Which read-only operation to run"),
      app_id: z.string().optional().describe("App Store app ID (required for versions/builds)"),
      mock: z.boolean().optional().describe("Use synthetic data instead of calling Apple (explicit opt-in)"),
      limit: z.number().int().min(1).max(100).optional().describe("Maximum records to return"),
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true },
    run: async (args) => {
      const cliArgs = [];
      if (args.mock) cliArgs.push("--mock");
      const command = args.operation.replace("_", "-");
      cliArgs.push(command);
      if (args.app_id) cliArgs.push("--app", args.app_id);
      if (args.limit) cliArgs.push("--limit", String(args.limit));
      return runTool("tools/app-store-connect/cli.py", cliArgs);
    },
  },
];

/**
 * Register every tool on an McpServer instance.
 * @param {import('@modelcontextprotocol/sdk/server/mcp.js').McpServer} server
 */
export function registerTools(server) {
  for (const spec of TOOL_SPECS) {
    server.registerTool(
      spec.name,
      {
        title: spec.title,
        description: spec.description,
        inputSchema: spec.inputSchema,
        outputSchema: ENVELOPE,
        annotations: spec.annotations ?? READ_ONLY,
      },
      async (args) => {
        try {
          const run = await spec.run(args ?? {});
          return toResult(run);
        } catch (error) {
          return errorResult(error);
        }
      },
    );
  }
}
