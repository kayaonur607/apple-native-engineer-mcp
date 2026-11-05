/**
 * MCP prompts: the slash commands, available to any MCP client.
 *
 * A prompt is a reusable, parameterised instruction. Exposing the repository's
 * command specifications as prompts means a Claude Desktop or Cursor user gets
 * the same workflows as someone using the Claude Code slash commands, without
 * copying markdown into the chat by hand.
 *
 * Naming rule: the umbrella command `commands/apple-native.md` becomes the
 * prompt `apple-native`; every other command `commands/<slug>.md` becomes
 * `apple-native-<slug>`. The previous implementation prefixed unconditionally,
 * which produced the duplicated id `apple-native-apple-native` — fixed here and
 * covered by a test so it cannot regress.
 */

import fs from "node:fs";
import path from "node:path";
import { z } from "zod";
import { REPO_ROOT } from "./runner.js";

const COMMANDS_DIR = path.join(REPO_ROOT, "commands");

/** The umbrella command; its prompt id has no extra suffix. */
const UMBRELLA = "apple-native";

/** Fallback descriptions when the command file has no frontmatter description. */
const FALLBACK = {
  [UMBRELLA]: "Full end-to-end Apple engineering audit of the current project.",
  design: "Review and improve HIG design quality: typography, spacing, materials, colour semantics.",
  code: "Review Swift architecture: state management, concurrency, modularisation.",
  review: "Audit against App Store Review Guidelines sections 1-5 before submission.",
  privacy: "Audit PrivacyInfo.xcprivacy and Required-Reason API usage.",
  icon: "Validate the App Store marketing icon.",
  screenshots: "Capture and validate App Store screenshots.",
  connect: "Inspect App Store Connect: apps, versions, builds.",
  metadata: "Validate App Store listing metadata.",
  widgets: "Audit WidgetKit widgets, Live Activities and Dynamic Island.",
  localization: "Audit localisation, String Catalogs and RTL mirroring.",
  release: "Run the full release readiness gate.",
};

/** `apple-native` → `apple-native`; `design` → `apple-native-design`. */
export function promptIdForSlug(slug) {
  return slug === UMBRELLA ? UMBRELLA : `${UMBRELLA}-${slug}`;
}

/** `apple-native` → `/apple-native`; `design` → `/apple-native-design`. */
export function promptTitleForSlug(slug) {
  return `/${promptIdForSlug(slug)}`;
}

function readFrontmatterDescription(markdown) {
  const match = markdown.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  const line = match[1].split("\n").find((entry) => entry.trim().startsWith("description:"));
  if (!line) return null;
  return line.slice(line.indexOf(":") + 1).trim().replace(/^["']|["']$/g, "");
}

function stripFrontmatter(markdown) {
  return markdown.replace(/^---\n[\s\S]*?\n---\n/, "").trim();
}

/** @param {import('@modelcontextprotocol/sdk/server/mcp.js').McpServer} server */
export function registerPrompts(server) {
  if (!fs.existsSync(COMMANDS_DIR)) return;

  for (const filename of fs.readdirSync(COMMANDS_DIR).filter((name) => name.endsWith(".md")).sort()) {
    const slug = path.basename(filename, ".md");
    const markdown = fs.readFileSync(path.join(COMMANDS_DIR, filename), "utf8");
    const body = stripFrontmatter(markdown);
    const description = readFrontmatterDescription(markdown) ?? FALLBACK[slug] ?? `Run the ${slug} workflow.`;

    server.registerPrompt(
      promptIdForSlug(slug),
      {
        title: promptTitleForSlug(slug),
        description,
        argsSchema: {
          project: z
            .string()
            .optional()
            .describe("Absolute path to the Apple project. Defaults to the client's working directory."),
          focus: z
            .string()
            .optional()
            .describe("Optional emphasis for this run, e.g. 'only the settings screen' or 'Swift 6 concurrency'."),
        },
      },
      ({ project, focus }) => {
        const target = project?.trim() || "the current working directory";
        const emphasis = focus?.trim();
        return {
          description,
          messages: [
            {
              role: "user",
              content: {
                type: "text",
                text: [
                  `Apply the following Apple Native Engineer workflow to ${target}.`,
                  emphasis ? `\nEmphasis for this run: ${emphasis}.` : "",
                  "Use the apple-native-engineer MCP tools to gather evidence before advising;",
                  "quote the finding codes you relied on and end with concrete next steps.",
                  "",
                  "---",
                  "",
                  body,
                ]
                  .filter(Boolean)
                  .join("\n"),
              },
            },
          ],
        };
      },
    );
  }
}

export function promptInventory() {
  if (!fs.existsSync(COMMANDS_DIR)) return [];
  return fs
    .readdirSync(COMMANDS_DIR)
    .filter((name) => name.endsWith(".md"))
    .sort()
    .map((name) => promptIdForSlug(path.basename(name, ".md")));
}
