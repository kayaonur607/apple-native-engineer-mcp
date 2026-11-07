/**
 * MCP resources: the knowledge base itself.
 *
 * Most MCP servers only expose tools. The references, checklists and examples in
 * this repository are the actual engineering standard, so they are exposed as
 * resources that the client can list and read on demand instead of being pushed
 * into every prompt.
 */

import fs from "node:fs";
import path from "node:path";
import { REPO_ROOT } from "./runner.js";
import { releaseInformation } from "./release-info.js";

const SECTIONS = [
  { dir: "references", prefix: "references", title: "Reference guide" },
  { dir: "checklists", prefix: "checklists", title: "Review checklist" },
  { dir: "examples", prefix: "examples", title: "Production example" },
];

const DATA_RESOURCES = [
  ["app-store-specs", "app-store-specs.json", "Apple App Store asset specifications",
    "Screenshot slots, app preview and icon specifications transcribed from Apple, with source URLs and date."],
  ["hig-catalog", "hig-catalog.json", "Human Interface Guidelines index",
    "Every HIG page with its section, title, abstract and URL, from Apple's table of contents."],
];

const CONTENT_TYPES = {
  ".md": "text/markdown",
  ".json": "application/json",
  ".swift": "text/x-swift",
};

function titleize(filename) {
  return filename
    .replace(/\.(md|json|swift)$/i, "")
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function firstHeading(filePath) {
  try {
    const text = fs.readFileSync(filePath, "utf8").slice(0, 4000);
    const match = text.match(/^#{1,2}\s+(.+)$/m);
    return match ? match[1].trim() : null;
  } catch {
    return null;
  }
}

function listMarkdown(dir) {
  const absolute = path.join(REPO_ROOT, dir);
  if (!fs.existsSync(absolute)) return [];
  return fs
    .readdirSync(absolute)
    .filter((name) => name.endsWith(".md"))
    .sort();
}

/** @param {import('@modelcontextprotocol/sdk/server/mcp.js').McpServer} server */
export function registerResources(server) {
  server.registerResource("release", "apple-native://release", {
    title: "Installed version and release notes",
    description: "Current MCP version, GitHub release notes and automatic update policy.",
    mimeType: "application/json",
  }, async uri => ({ contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(releaseInformation(), null, 2) }] }));
  // Apple's published specifications and HIG index, as data the client can read directly.
  for (const [name, file, title, description] of DATA_RESOURCES) {
    const absolute = path.join(REPO_ROOT, "data", file);
    if (!fs.existsSync(absolute)) continue;
    server.registerResource(`data-${name}`, `apple-native://data/${name}`, {
      title, description, mimeType: "application/json",
    }, async (uri) => ({ contents: [{ uri: uri.href, mimeType: "application/json", text: fs.readFileSync(absolute, "utf8") }] }));
  }
  // The skill document itself.
  const skillPath = path.join(REPO_ROOT, "SKILL.md");
  if (fs.existsSync(skillPath)) {
    server.registerResource(
      "skill",
      "apple-native://skill",
      {
        title: "Apple Native Engineer skill",
        description:
          "The canonical operating standard for Apple platform work: design rules, Swift architecture, " +
          "privacy, accessibility and release gates.",
        mimeType: "text/markdown",
      },
      async (uri) => ({
        contents: [{ uri: uri.href, mimeType: "text/markdown", text: fs.readFileSync(skillPath, "utf8") }],
      }),
    );
  }

  for (const section of SECTIONS) {
    for (const filename of listMarkdown(section.dir)) {
      const absolute = path.join(REPO_ROOT, section.dir, filename);
      const uri = `apple-native://${section.prefix}/${filename.replace(/\.md$/, "")}`;
      const heading = firstHeading(absolute) ?? titleize(filename);
      server.registerResource(
        `${section.prefix}-${filename.replace(/\.md$/, "")}`,
        uri,
        {
          title: `${section.title}: ${heading}`,
          description: `${section.title} shipped with apple-native-engineer-mcp (${filename}).`,
          mimeType: CONTENT_TYPES[".md"],
        },
        async (resourceUri) => ({
          contents: [
            {
              uri: resourceUri.href,
              mimeType: "text/markdown",
              text: fs.readFileSync(absolute, "utf8"),
            },
          ],
        }),
      );
    }
  }
}

/** Exposed for tests and for `--list-resources` diagnostics. */
export function resourceInventory() {
  const items = [{ uri: "apple-native://release", file: "CHANGELOG.md" }, { uri: "apple-native://skill", file: "SKILL.md" }];
  for (const [name, file] of DATA_RESOURCES) {
    if (fs.existsSync(path.join(REPO_ROOT, "data", file))) items.push({ uri: `apple-native://data/${name}`, file: `data/${file}` });
  }
  for (const section of SECTIONS) {
    for (const filename of listMarkdown(section.dir)) {
      items.push({
        uri: `apple-native://${section.prefix}/${filename.replace(/\.md$/, "")}`,
        file: `${section.dir}/${filename}`,
      });
    }
  }
  return items;
}
