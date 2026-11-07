/**
 * Tool registry: every MCP tool maps 1:1 onto a CLI script in `tools/`.
 *
 * Keeping the mapping thin means the MCP server can never drift from the CLI:
 * whatever an agent can do through MCP, a human can reproduce with one command,
 * and the CI suite exercises exactly the same code path.
 */

import { z } from "zod";
import { errorResult, gitChangedFiles, resolveOutput, resolveTarget, runFileMatrix, runTool, runToolsParallel, toResult } from "./runner.js";
import { recordToolRun, sanitiseEvent } from "./telemetry.js";
import { checkEnvironment } from "./environment.js";

const READ_ONLY = {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
};

// Writers can overwrite existing destinations. Conservative, static annotations
// apply even when an optional output argument is omitted.
const LOCAL_WRITE = { ...READ_ONLY, readOnlyHint: false, destructiveHint: true };

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
    data: z.record(z.string(), z.unknown()).optional(),
  })
  .passthrough();

/**
 * Turn a client's `progressToken` into a callback, or into a no-op.
 *
 * Long composites (a whole-project sweep, a large diff) otherwise look frozen
 * for seconds. Clients that do not ask for progress never see a notification.
 */
function progressReporter(extra) {
  const token = extra?._meta?.progressToken;
  if (token === undefined || typeof extra?.sendNotification !== "function") return undefined;
  return ({ completed, total, label, status }) => {
    extra
      .sendNotification({
        method: "notifications/progress",
        params: { progressToken: token, progress: completed, total, message: `${label} → ${status}` },
      })
      .catch(() => {});
  };
}

/**
 * @typedef {Object} ToolSpec
 * @property {string} name
 * @property {string} title
 * @property {string} description
 * @property {import('zod').ZodRawShape} inputSchema
 * @property {(args: any, extra?: any) => Promise<any>} run
 */

/**
 * The read-only suite behind `audit_project`. Every entry takes only a target
 * path, so they can run concurrently without ordering constraints.
 */
export const AUDIT_SUITE = [
  { name: "project-inspector", script: "tools/project-inspector/inspect_project.py" },
  { name: "swiftui-linter", script: "tools/swiftui-linter/lint_swiftui.py" },
  { name: "accessibility-auditor", script: "tools/accessibility-auditor/audit_accessibility.py" },
  { name: "liquid-glass-auditor", script: "tools/liquid-glass-auditor/audit_liquid_glass.py" },
  { name: "privacy-auditor", script: "tools/privacy-auditor/audit_privacy.py" },
  { name: "localization-checker", script: "tools/localization-checker/check_localization.py" },
  { name: "widget-validator", script: "tools/widget-validator/validate_widget.py" },
  { name: "sf-symbols-catalog", script: "tools/sf-symbols-catalog/check_symbols.py" },
  { name: "cross-platform-auditor", script: "tools/cross-platform-auditor/audit_cross_platform.py" },
];

/**
 * The file-scoped auditors behind `review_diff`.
 *
 * These three accept a single `.swift` path, which is what makes a diff review
 * possible — each changed file is audited on its own instead of re-auditing the
 * whole project on every edit.
 */
export const FILE_AUDITORS = [
  { name: "swiftui-linter", script: "tools/swiftui-linter/lint_swiftui.py" },
  { name: "accessibility-auditor", script: "tools/accessibility-auditor/audit_accessibility.py" },
  { name: "liquid-glass-auditor", script: "tools/liquid-glass-auditor/audit_liquid_glass.py" },
];

/** Files the cross-platform auditor understands: Dart, JS/TS sources and their app configs. */
const CROSS_PLATFORM_FILE = /\.(dart|jsx?|tsx?)$|(^|\/)(app\.json|pubspec\.yaml|capacitor\.config\.json)$/;
const SEVERITIES = ["critical", "error", "warning", "info"];

/** Run the cross-platform auditor on the project, keep findings in the changed files. */
async function crossPlatformReview(target, changed) {
  const run = await runTool("tools/cross-platform-auditor/audit_cross_platform.py", [target]);
  const keep = new Set(changed);
  const findings = (run.envelope.findings ?? []).filter((finding) => finding.file && keep.has(finding.file));
  const summary = Object.fromEntries(SEVERITIES.map((level) => [level, findings.filter((f) => f.severity === level).length]));
  summary.total = findings.length;
  const status = summary.critical || summary.error ? "fail" : summary.warning ? "warn" : "pass";
  return {
    envelope: { ...run.envelope, tool: "diff-review", status, summary, findings,
      data: { framework: run.envelope.data?.framework, note: "Cross-platform rules applied to the changed files." } },
    summary: `diff-review · ${status.toUpperCase()} · ${findings.length} finding(s) in ${changed.length} cross-platform file(s)`,
    exitCode: status === "fail" ? 2 : 0,
  };
}

function mergeFindings(result, findings, source) {
  if (!findings.length) return;
  const envelope = result.envelope;
  envelope.findings = [...(envelope.findings ?? []), ...findings.map((finding) => ({ ...finding, source }))];
  for (const level of SEVERITIES) envelope.summary[level] = envelope.findings.filter((f) => f.severity === level).length;
  envelope.summary.total = envelope.findings.length;
  envelope.status = envelope.summary.critical || envelope.summary.error ? "fail" : envelope.summary.warning ? "warn" : "pass";
}

/** @type {ToolSpec[]} */
export const TOOL_SPECS = [
  {
    name: "review_diff",
    title: "Review only the files this change touched",
    description:
      "Reads `git diff` for the project, runs the SwiftUI, accessibility and Liquid Glass auditors on each changed " +
      "Swift file, and the cross-platform auditor on changed Dart, TypeScript/JavaScript and app-config files. Use this in an edit loop instead of audit_project: it costs seconds, " +
      "reports only what you just wrote, and groups findings by file. Set `staged` to review the index, or `base` " +
      "to review against a branch.",
    inputSchema: {
      path: OPTIONAL_PATH,
      base: z
        .string()
        .optional()
        .describe("Git revision to diff against, e.g. 'origin/main' or a commit SHA. Defaults to HEAD."),
      staged: z.boolean().optional().describe("Review staged changes only (git diff --cached). Defaults to false."),
      max_files: z
        .number()
        .int()
        .min(1)
        .max(500)
        .optional()
        .describe("Cap on files audited, because a 400-file diff is not a review. Defaults to 60."),
    },
    run: async (args, extra) => {
      const target = resolveTarget(args.path);
      const { selected, truncated, files } = await gitChangedFiles(target, {
        base: args.base || "HEAD",
        staged: Boolean(args.staged),
        maxFiles: args.max_files ?? 60,
      });
      const swiftFiles = selected.filter((file) => file.endsWith(".swift"));
      const crossFiles = selected.filter((file) => CROSS_PLATFORM_FILE.test(file));
      const cross = crossFiles.length ? await crossPlatformReview(target, crossFiles) : null;

      if (swiftFiles.length === 0 && cross) {
        cross.envelope.data = { ...cross.envelope.data, changed_files: files, audited: crossFiles, truncated };
        return cross;
      }

      if (swiftFiles.length === 0) {
        return {
          envelope: {
            schema_version: "2.0",
            tool: "diff-review",
            tool_version: "2.0.0",
            target,
            status: "pass",
            summary: { critical: 0, error: 0, warning: 0, info: 0, total: 0 },
            findings: [],
            data: {
              changed_files: files,
              audited: [],
              note:
                files.length === 0
                  ? "No changes to review."
                  : `${files.length} changed file(s), none of them Swift — nothing for the Swift auditors to read.`,
            },
          },
          summary: `diff-review · PASS · no Swift changes (${files.length} changed file(s))`,
          exitCode: 0,
        };
      }

      const result = await runFileMatrix({
        target,
        files: swiftFiles,
        auditors: FILE_AUDITORS,
        signal: extra?.signal,
        onProgress: progressReporter(extra),
      });
      result.envelope.data.truncated = truncated;
      result.envelope.data.changed_files = files;
      if (cross) mergeFindings(result, cross.envelope.findings, "cross-platform-auditor");
      return result;
    },
  },
  {
    name: "check_environment",
    title: "Diagnose the MCP server itself",
    description:
      "Checks the runtime this server depends on: Node and Python versions, whether the auditors and reference " +
      "guides are present, git and Xcode availability, App Store Connect credentials (presence only, never the " +
      "value), and the telemetry mode. Run this first when a tool behaves unexpectedly.",
    inputSchema: {},
    run: async () => checkEnvironment(),
  },
  {
    name: "audit_project",
    title: "Audit the whole project in one call",
    description:
      "Runs nine read-only audits concurrently — project structure, SwiftUI lint, accessibility, Liquid Glass, " +
      "privacy manifest, localisation, widgets, SF Symbols and the cross-platform auditor (Flutter, React Native, " +
      "Expo, Capacitor, .NET MAUI, KMP) — and returns one merged envelope with every " +
      "finding tagged by the audit that produced it. Use this first on an unfamiliar project; follow up with a " +
      "single audit when you need its full detail.",
    inputSchema: { path: OPTIONAL_PATH },
    run: async (args, extra) => {
      const target = resolveTarget(args.path);
      const specs = AUDIT_SUITE.map((entry) => ({ ...entry, args: [target], targetLabel: target }));
      return runToolsParallel(specs, { signal: extra?.signal, onProgress: progressReporter(extra) });
    },
  },
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
    name: "audit_cross_platform",
    title: "Audit a Flutter, React Native, Expo, Capacitor, MAUI or KMP app for Apple-native quality",
    description:
      "Detects the framework and its native iOS host, then checks what makes a cross-platform app feel made for " +
      "iPhone and pass review: Dynamic Type not disabled, VoiceOver labels on icon buttons, Dark Mode (Flutter " +
      "darkTheme, Expo userInterfaceStyle), Flutter .adaptive() controls and Cupertino tab bars, deprecated " +
      "SafeAreaView, resizable windows, right-to-left layout, usage descriptions for permission plugins, iOS " +
      "localizations in Xcode, Expo bundle ID/export compliance/privacy manifest, Capacitor remote URLs, and " +
      "native-UI options (@expo/ui SwiftUI, expo-glass-effect).",
    inputSchema: { path: OPTIONAL_PATH },
    run: async (args) => runTool("tools/cross-platform-auditor/audit_cross_platform.py", [resolveTarget(args.path)]),
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
    annotations: LOCAL_WRITE,
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
      if (args.out) cliArgs.push("--out", resolveOutput(args.out));
      if (args.xcassets) cliArgs.push("--xcassets", resolveOutput(args.xcassets));
      return runTool("tools/design-token-forge/forge_tokens.py", cliArgs);
    },
  },
  {
    name: "generate_release_report",
    annotations: LOCAL_WRITE,
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
      if (args.output) cliArgs.push("--output", resolveOutput(args.output));
      return runTool("tools/release-readiness/generate_report.py", cliArgs);
    },
  },
  {
    name: "search_apple_documentation",
    annotations: { ...READ_ONLY, openWorldHint: true },
    title: "Search Apple documentation",
    description:
      "Searches Apple's own symbol index for a framework (swiftui, uikit, appkit, foundation, …) and returns the " +
      "documentation paths that match. Use it before writing API you are not certain exists.",
    inputSchema: {
      query: z.string().describe("Symbol or phrase to look for, e.g. 'navigation stack'"),
      framework: z.string().optional().describe("Framework index to search (default: swiftui)"),
      limit: z.number().int().min(1).max(25).optional().describe("Maximum matches (default: 10)"),
    },
    run: async (args) => {
      const cliArgs = ["search", args.query];
      if (args.framework) cliArgs.push("--framework", args.framework);
      if (args.limit) cliArgs.push("--limit", String(args.limit));
      return runTool("tools/apple-docs-research/apple_docs.py", cliArgs);
    },
  },
  {
    name: "read_apple_documentation",
    annotations: { ...READ_ONLY, openWorldHint: true },
    title: "Read Apple documentation",
    description:
      "Fetches one developer.apple.com page through the JSON API the site itself uses and returns it as Markdown " +
      "with the source URL and fetch time. Refuses any host other than developer.apple.com.",
    inputSchema: {
      path: z.string().describe("Symbol path (swiftui/view/glassEffect(_:in:)) or a developer.apple.com URL"),
    },
    run: async (args) =>
      runTool("tools/apple-docs-research/apple_docs.py", ["read", args.path]),
  },
  {
    name: "inspect_apple_api_availability",
    annotations: { ...READ_ONLY, openWorldHint: true },
    title: "Inspect API availability",
    description:
      "Returns the per-platform availability table Apple publishes for a symbol: introduced version, deprecation, " +
      "beta status. Use it instead of guessing whether an API exists on the project's deployment target.",
    inputSchema: {
      path: z.string().describe("Symbol path, e.g. swiftui/view/glassEffect(_:in:)"),
    },
    run: async (args) =>
      runTool("tools/apple-docs-research/apple_docs.py", ["availability", args.path]),
  },
  {
    name: "find_apple_guidelines",
    annotations: { ...READ_ONLY, openWorldHint: true },
    title: "Read Human Interface Guidelines",
    description:
      "Fetches a Human Interface Guidelines page (buttons, navigation-and-search, materials, …) as Markdown with " +
      "its source URL, so design advice can cite Apple instead of an opinion.",
    inputSchema: {
      page: z.string().describe("HIG page slug, e.g. 'buttons' or 'materials'"),
    },
    run: async (args) =>
      runTool("tools/apple-docs-research/apple_docs.py", ["guidelines", args.page]),
  },
  {
    name: "search_apple_guidelines",
    title: "Search the Human Interface Guidelines",
    description:
      "Finds the right Human Interface Guidelines pages offline from Apple's HIG table of contents (158 pages: " +
      "platforms incl. iPhone Duo, foundations, patterns, components, inputs, technologies), ranked by relevance, " +
      "with titles, abstracts and URLs. Then call find_apple_guidelines with a slug to read the live page.",
    inputSchema: {
      query: z.string().optional().describe("Topic, e.g. 'tab bar', 'tvos focus', 'onboarding', 'widgets'"),
      section: z.string().optional().describe("Getting started, Foundations, Patterns, Components, Inputs or Technologies"),
      limit: z.number().int().min(1).max(50).optional(),
    },
    run: async (args) => {
      const cliArgs = ["guidelines-search", args.query ?? ""];
      if (args.section) cliArgs.push("--section", args.section);
      if (args.limit) cliArgs.push("--limit", String(args.limit));
      return runTool("tools/apple-docs-research/apple_docs.py", cliArgs);
    },
  },
  {
    name: "prepare_icon_assets",
    annotations: LOCAL_WRITE,
    title: "Prepare app icon assets",
    description:
      "Turns one 1024×1024 opaque PNG into a complete AppIcon.appiconset: 18 slots downscaled with a box filter, " +
      "plus the Contents.json Xcode expects. Refuses a master that is not 1024×1024, not PNG, or has alpha.",
    inputSchema: {
      source: z.string().describe("Path to the 1024×1024 master PNG"),
      out: z.string().describe("Destination .appiconset directory to write"),
    },
    run: async (args) =>
      runTool("tools/icon-studio/icon_studio.py", ["prepare", resolveTarget(args.source), "--out", resolveOutput(args.out)]),
  },
  {
    name: "verify_icon_set",
    title: "Verify app icon assets",
    description:
      "Checks an .appiconset against its Contents.json: every referenced file exists and has the pixel size the " +
      "slot declares.",
    inputSchema: {
      path: z.string().describe("Path to the .appiconset directory"),
    },
    run: async (args) =>
      runTool("tools/icon-studio/icon_studio.py", ["verify", resolveTarget(args.path)]),
  },
  {
    name: "audit_app_store_review",
    title: "Audit App Store Review risk",
    description:
      "Finds the specific conditions that appear in App Store rejection letters — missing usage descriptions, " +
      "placeholder copy, account creation without deletion, external payment links, web-wrapper apps, private " +
      "APIs — and names the guideline section for each. Never promises approval.",
    inputSchema: {
      path: OPTIONAL_PATH,
      metadata_path: z.string().optional().describe("Optional listing metadata JSON for 2.3.1 checks"),
    },
    run: async (args) => {
      const cliArgs = [resolveTarget(args.path)];
      if (args.metadata_path) cliArgs.push("--metadata", resolveTarget(args.metadata_path));
      return runTool("tools/app-store-review/review.py", cliArgs);
    },
  },
  {
    name: "get_app_store_specs",
    title: "Get Apple's App Store asset specifications",
    description:
      "Returns Apple's published screenshot slots (every iPhone, iPad, Mac, Apple TV, Vision Pro and Watch size, " +
      "with which sets are required and their fallbacks), app preview video rules and app icon sizes per platform, " +
      "with the source URLs and the date they were transcribed. Call this before planning captures or artwork.",
    inputSchema: {
      platforms: z
        .array(z.enum(["iOS", "iPadOS", "macOS", "tvOS", "visionOS", "watchOS"]))
        .optional()
        .describe("Limit screenshot slots to these platforms"),
    },
    run: async (args) => {
      const cliArgs = ["--specs"];
      if (args.platforms?.length) cliArgs.push("--platforms", args.platforms.join(","));
      return runTool("tools/screenshot-studio/screenshot_studio.py", cliArgs);
    },
  },
  {
    name: "capture_screenshots",
    annotations: { ...LOCAL_WRITE, idempotentHint: false },
    title: "Capture App Store screenshots in the Simulator",
    description:
      "Drives the iOS/iPadOS/tvOS/visionOS/watchOS Simulator from a JSON plan: for every device × locale × " +
      "appearance × screen it boots the simulator, sets the 9:41 status bar, applies light/dark, (re)installs the " +
      "app, launches it with -AppleLanguages/-AppleLocale plus the screen's launch arguments (read through " +
      "UserDefaults in Swift, Settings.get in React Native, SharedPreferencesAsync in Flutter), env or deep link, and " +
      "saves a PNG to <out>/<locale>/<device>/<screen>.png. Captures are flattened to opaque RGB and validated " +
      "against Apple's slots; manifest.json records provenance. Devices may be simulator names or slot ids from " +
      "get_app_store_specs (e.g. 'iphone-6.9'). Use dry_run first to show the exact commands. Real captures only.",
    inputSchema: {
      plan: z.string().describe("Path to the capture plan JSON (bundle_id, devices, locales, appearances, screens, app)"),
      out: z.string().describe("Output root directory"),
      dry_run: z.boolean().optional().describe("Print the simctl commands without executing anything"),
    },
    run: async (args) => {
      const cliArgs = [resolveTarget(args.plan), "--out", resolveOutput(args.out)];
      if (args.dry_run) cliArgs.push("--dry-run");
      return runTool("tools/screenshot-studio/capture_batch.py", cliArgs, { timeoutMs: 1_800_000 });
    },
  },
  {
    name: "audit_screenshots",
    title: "Audit App Store screenshots",
    description:
      "Validates a screenshot folder (locale subfolders allowed) against Apple's specification: exact slot sizes, " +
      "no alpha channel, 1–10 per device size, one orientation per set, one Apple Watch size across locales, and " +
      "— when platforms are given — the sets Apple requires for each platform.",
    inputSchema: {
      path: z.string().describe("Screenshots directory"),
      platforms: z
        .array(z.enum(["iOS", "iPadOS", "macOS", "tvOS", "visionOS", "watchOS"]))
        .optional()
        .describe("Platforms the app ships on, to check required sets"),
    },
    run: async (args) => {
      const cliArgs = ["--screenshots", resolveTarget(args.path)];
      if (args.platforms?.length) cliArgs.push("--platforms", args.platforms.join(","));
      return runTool("tools/screenshot-studio/screenshot_studio.py", cliArgs);
    },
  },
  {
    name: "compose_marketing_screenshots",
    annotations: LOCAL_WRITE,
    title: "Compose marketing screenshots",
    description:
      "Lays real screenshots into App Store marketing frames: background, localized headline and subheadline, " +
      "an optional drawn device frame (with Dynamic Island on iPhone), right-to-left layout for Arabic/Hebrew. " +
      "Always writes editable SVG; with render=true it also writes opaque RGB PNGs at the exact slot size, drawn " +
      "natively on macOS with CoreGraphics and the San Francisco system font. Locale subfolders are mirrored. " +
      "Refuses to invent screens: it only composes images you actually captured.",
    inputSchema: {
      screenshots: z.string().describe("Directory of real screenshots (e.g. the capture_screenshots output)"),
      out: z.string().describe("Directory to write compositions into"),
      captions: z
        .string()
        .optional()
        .describe('Captions JSON: {"en-US": {"01-home": {"headline": "…", "subhead": "…"}}, "*": {"*": {…}}}'),
      headline: z.string().optional().describe("Headline when no caption matches"),
      subhead: z.string().optional().describe("Supporting line when no caption matches"),
      theme: z.enum(["dark", "light", "warm", "blue", "graphite"]).optional().describe("Colour theme (default: dark)"),
      layout: z.enum(["caption-top", "caption-bottom"]).optional(),
      frame: z.enum(["auto", "device", "none"]).optional().describe("Device bezel (auto: iPhone/iPad portrait)"),
      align: z.enum(["center", "left"]).optional(),
      canvas: z.string().optional().describe("WxH override, e.g. 1290x2796"),
      render: z.boolean().optional().describe("Also write App Store-ready PNGs"),
    },
    run: async (args) => {
      const cliArgs = ["--screenshots", resolveTarget(args.screenshots), "--out", resolveOutput(args.out)];
      if (args.captions) cliArgs.push("--captions", resolveTarget(args.captions));
      if (args.headline) cliArgs.push("--headline", args.headline);
      if (args.subhead) cliArgs.push("--subhead", args.subhead);
      for (const key of ["theme", "layout", "frame", "align", "canvas"]) {
        if (args[key]) cliArgs.push(`--${key}`, args[key]);
      }
      if (args.render) cliArgs.push("--render");
      return runTool("tools/screenshot-studio/compose_marketing.py", cliArgs);
    },
  },
  {
    name: "plan_distribution",
    annotations: LOCAL_WRITE,
    title: "Plan archive, upload and notarization",
    description:
      "Preflights a project for distribution and returns the exact ordered commands: xcodebuild archive, export " +
      "or direct upload, altool validate/upload, and for Developer ID notarytool, stapler and spctl. Flags missing " +
      "team, version/build number, export-compliance key, Hardened Runtime, App Sandbox, debug entitlements, " +
      "privacy manifest and app icon. Generates ExportOptions.plist (written only when write_export_options is " +
      "set). Never builds, uploads or contacts Apple; run steps marked requires_approval only with the user's consent.",
    inputSchema: {
      path: OPTIONAL_PATH,
      method: z
        .enum(["app-store", "testflight-internal", "release-testing", "enterprise", "debugging", "developer-id", "mac-app-store"])
        .optional()
        .describe("Distribution method (default app-store)"),
      scheme: z.string().optional().describe("Scheme to archive"),
      platform: z.enum(["iOS", "macOS", "tvOS", "visionOS", "watchOS"]).optional().describe("Override detection"),
      upload: z.boolean().optional().describe("App Store methods: upload during export (destination=upload)"),
      write_export_options: z.string().optional().describe("Write ExportOptions.plist to this path"),
    },
    run: async (args) => {
      const cliArgs = [resolveTarget(args.path)];
      if (args.method) cliArgs.push("--method", args.method);
      if (args.scheme) cliArgs.push("--scheme", args.scheme);
      if (args.platform) cliArgs.push("--platform", args.platform);
      if (args.upload) cliArgs.push("--upload");
      if (args.write_export_options) cliArgs.push("--write-export-options", resolveOutput(args.write_export_options));
      return runTool("tools/distribution/plan_distribution.py", cliArgs);
    },
  },
  {
    name: "analyze_app_store_optimization",
    title: "Analyse App Store optimization",
    description:
      "Deterministic ASO pass over listing copy: character budgets, duplicated or wasted keywords, keyword coverage " +
      "against the visible copy, risky claims reviewers push back on, and candidate keywords extracted from your " +
      "own description. Uses no search-volume or competitor data and says so in its output.",
    inputSchema: {
      path: z.string().describe("Path to the listing metadata JSON"),
      locale: z.string().optional().describe("Analyse one locale only, e.g. en-US"),
    },
    run: async (args) => {
      const cliArgs = [resolveTarget(args.path)];
      if (args.locale) cliArgs.push("--locale", args.locale);
      return runTool("tools/aso-engine/aso.py", cliArgs);
    },
  },
  {
    name: "app_store_connect",
    title: "App Store Connect (read-only)",
    description:
      "Read-only App Store Connect access: verify credentials, list apps, list versions and builds. Requires " +
      "ASC_KEY_ID / ASC_ISSUER_ID / ASC_PRIVATE_KEY_PATH. Never falls back to mock data silently.",
    inputSchema: {
      operation: z
        .enum(["verify", "list_apps", "app_details", "versions", "builds", "localizations", "screenshots"])
        .describe("Which read-only operation to run"),
      app_id: z.string().optional().describe("App Store app ID (for app_details, versions, builds)"),
      version_id: z.string().optional().describe("App Store version ID (for localizations)"),
      localization_id: z.string().optional().describe("Version localization ID (for screenshots)"),
      mock: z.boolean().optional().describe("Use synthetic data instead of calling Apple (explicit opt-in)"),
      limit: z.number().int().min(1).max(100).optional().describe("Maximum records to return"),
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true },
    run: async (args) => {
      const cliArgs = [];
      if (args.mock) cliArgs.push("--mock");
      const command = {
        verify: "verify",
        list_apps: "list-apps",
        app_details: "app",
        versions: "versions",
        builds: "builds",
        localizations: "localizations",
        screenshots: "screenshots",
      }[args.operation];
      cliArgs.push(command);
      if (args.app_id) cliArgs.push("--app", args.app_id);
      if (args.version_id) cliArgs.push("--version", args.version_id);
      if (args.localization_id) cliArgs.push("--localization", args.localization_id);
      if (args.limit) cliArgs.push("--limit", String(args.limit));
      return runTool("tools/app-store-connect/cli.py", cliArgs);
    },
  },
];

/**
 * Register every tool on an McpServer instance.
 * @param {import('@modelcontextprotocol/sdk/server/mcp.js').McpServer} server
 */
export function registerTools(server, { enabledTools } = {}) {
  const knownTools = TOOL_SPECS.map((spec) => spec.name);
  const allowed = enabledTools ? new Set(enabledTools) : null;
  const registered = [];

  for (const spec of TOOL_SPECS) {
    if (allowed && !allowed.has(spec.name)) continue;
    registered.push(spec.name);
    server.registerTool(
      spec.name,
      {
        title: spec.title,
        description: spec.description,
        inputSchema: spec.inputSchema,
        outputSchema: ENVELOPE,
        annotations: spec.annotations ?? READ_ONLY,
      },
      async (args, extra) => {
        const started = Date.now();
        let outcome = "error";
        try {
          const run = await spec.run(args ?? {}, extra);
          outcome = sanitiseEvent({ outcome: run?.envelope?.status }).outcome;
          return toResult(run);
        } catch (error) {
          return errorResult(error);
        } finally {
          // Fire-and-forget, aggregate-only, and a no-op unless explicitly enabled.
          recordToolRun({ tool: spec.name, outcome, durationMs: Date.now() - started, knownTools });
        }
      },
    );
  }
  return registered;
}
