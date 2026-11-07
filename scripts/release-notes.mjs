#!/usr/bin/env node
import fs from 'node:fs';
const pkg = JSON.parse(fs.readFileSync(new URL('../integrations/mcp-server/package.json', import.meta.url), 'utf8'));
const tag = process.argv[2];
if (tag !== `mcp-v${pkg.version}`) throw new Error(`Tag must be mcp-v${pkg.version}; received ${tag}`);
const changelog = fs.readFileSync(new URL('../CHANGELOG.md', import.meta.url), 'utf8');
const section = changelog.split(/^## /m).slice(1).find(s => s.startsWith(`[${pkg.version}]`));
if (!section) throw new Error('Missing changelog entry');
process.stdout.write(`## ${section.trim()}\n\nInstall and update instructions: https://github.com/kayaonur607/apple-native-engineer-mcp/blob/${tag}/docs/UPDATES.md\n`);
