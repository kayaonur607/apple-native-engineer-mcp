#!/usr/bin/env node
/**
 * Stage a self-contained package before `npm publish`.
 *
 * The server is a thin JSON-RPC shell over Python auditors that live at the
 * repository root. Publishing only `src/` would produce an npm package that
 * cannot run — the first tool call would fail with "script is missing". So the
 * published tarball carries a copy of exactly the directories the server reads,
 * produced here from the single source of truth rather than checked in.
 *
 * `vendor/` is generated, gitignored, and never edited by hand: run
 * `npm run vendor` and it is rebuilt from the repository. `runner.js` prefers
 * `vendor/` when it exists and falls back to the repository layout otherwise,
 * so development and the published artifact run the same code path.
 *
 * Usage:
 *   node scripts/pack-vendor.mjs          # stage vendor/
 *   node scripts/pack-vendor.mjs --check  # exit 1 if vendor/ is stale or missing
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = path.resolve(HERE, "..");
const REPO_ROOT = path.resolve(PACKAGE_ROOT, "..", "..");
const VENDOR = path.join(PACKAGE_ROOT, "vendor");

/** Everything the server reads at runtime, relative to the repository root. */
export const VENDORED = [
  "tools",
  "data",
  "references",
  "checklists",
  "examples",
  "commands",
  "SKILL.md",
  "LICENSE",
  "README.md",
];

/** Files that must never be copied into a published tarball. */
const EXCLUDE_DIRS = new Set(["__pycache__", ".pytest_cache", "node_modules", ".git"]);
const EXCLUDE_SUFFIXES = [".pyc", ".pyo", ".DS_Store"];

function copyTree(source, destination) {
  const stat = fs.statSync(source);
  if (stat.isFile()) {
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.copyFileSync(source, destination);
    return 1;
  }
  let count = 0;
  fs.mkdirSync(destination, { recursive: true });
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    if (EXCLUDE_DIRS.has(entry.name)) continue;
    if (EXCLUDE_SUFFIXES.some((suffix) => entry.name.endsWith(suffix))) continue;
    count += copyTree(path.join(source, entry.name), path.join(destination, entry.name));
  }
  return count;
}

function listVendored(dir = VENDOR, base = VENDOR) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...listVendored(full, base));
    else out.push(path.relative(base, full));
  }
  return out.sort();
}

export function buildVendor() {
  fs.rmSync(VENDOR, { recursive: true, force: true });
  fs.mkdirSync(VENDOR, { recursive: true });
  let files = 0;
  for (const entry of VENDORED) {
    const source = path.join(REPO_ROOT, entry);
    if (!fs.existsSync(source)) continue;
    files += copyTree(source, path.join(VENDOR, entry));
  }
  // A tarball has no repository metadata; record what was staged so `--check`
  // can tell a stale tree from a complete one without trusting timestamps.
  const manifest = {
    generated_by: "integrations/mcp-server/scripts/pack-vendor.mjs",
    source: "repository root",
    directories: VENDORED,
    files,
  };
  fs.writeFileSync(path.join(VENDOR, ".vendor-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  return manifest;
}

function main() {
  const check = process.argv.includes("--check");
  if (check) {
    const manifestPath = path.join(VENDOR, ".vendor-manifest.json");
    if (!fs.existsSync(manifestPath)) {
      process.stderr.write("vendor/ is missing — run `npm run vendor` before publishing\n");
      process.exit(1);
    }
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    const present = listVendored().filter((file) => !file.startsWith(".vendor-manifest"));
    const missing = VENDORED.filter((entry) => !fs.existsSync(path.join(VENDOR, entry)));
    if (missing.length > 0 || present.length !== manifest.files) {
      process.stderr.write(
        `vendor/ is stale (${present.length} files present, manifest claims ${manifest.files}; missing: ${
          missing.join(", ") || "none"
        }) — run \`npm run vendor\`\n`,
      );
      process.exit(1);
    }
    process.stdout.write(`vendor/ is current: ${present.length} files\n`);
    return;
  }

  const manifest = buildVendor();
  process.stdout.write(`staged ${manifest.files} files into vendor/ (${manifest.directories.length} top-level entries)\n`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
