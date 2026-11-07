import fs from 'node:fs';
import path from 'node:path';
import { REPO_ROOT } from './runner.js';
import { SERVER_VERSION } from './constants.js';

export function releaseInformation() {
  let changelog = 'Release notes are not available in this checkout.';
  try { changelog = fs.readFileSync(path.join(REPO_ROOT, 'CHANGELOG.md'), 'utf8'); } catch {}
  const section = changelog.split(/^## /m).slice(1).find(part => part.startsWith(`[${SERVER_VERSION}]`));
  return { version: SERVER_VERSION,
    release_url: `https://github.com/kayaonur607/apple-native-engineer-mcp/releases/tag/mcp-v${SERVER_VERSION}`,
    notes: section ? `## ${section.trim()}` : changelog,
    update_policy: 'GitHub launcher checks published stable releases on MCP restart. Running sessions keep their current version. Direct src/index.js runs do not auto-update.',
  };
}
