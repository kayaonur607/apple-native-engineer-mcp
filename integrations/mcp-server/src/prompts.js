/**
 * MCP prompts: the slash commands, available to any MCP client.
 *
 * A prompt is a reusable, parameterised instruction. Exposing the repository's
 * command specifications as prompts means a Claude Desktop or Cursor user gets
 * the same workflows as someone using the Claude Code slash commands, without
 * copying markdown into the chat by hand.
 */

import fs from "node:fs";
import path from "node:path";
import { z } from "zod";
import { REPO_ROOT } from "./runner.js";

const COMMANDS_DIR = path.join(REPO_ROOT, "commands");

/** Fallback descriptions when the command file has no frontmatter description. */
const FALLBACK = {
  "apple-native": "Full end-to-end Apple engineering audit of the current project.",
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
      `apple-native-${slug}`,
      {
        title: `/${slug === "apple-native" ? "apple-native" : "apple-native-" + slug}`,
        description,
        argsSchema: {
          project: z
            .string()
            .optional()
            .describe("Absolute path to the Apple project. Defaults to the client's working directory."),
        },
      },
      ({ project }) => {
        const target = project?.trim() || "the current working directory";
        return {
          description,
          messages: [
            {
              role: "user",
              content: {
                type: "text",
                text: [
                  `Apply the following Apple Native Engineer workflow to ${target}.`,
                  "Use the apple-native-engineer MCP tools to gather evidence before advising;",
                  "quote the finding codes you relied on and end with concrete next steps.",
                  "",
                  "---",
                  "",
                  body,
                ].join("\n"),
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
    .map((name) => `apple-native-${path.basename(name, ".md")}`);
}
