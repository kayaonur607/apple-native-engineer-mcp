#!/usr/bin/env node
// Exercise the real MCP protocol against public fixtures; never reads customer projects.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { createServer } from '../src/server.js';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const output = path.resolve(process.argv[2] ?? path.join(root, '.swiftwork/demo-evidence'));
const client = new Client({ name: 'demo-evidence', version: '1.0.0' });
const server = createServer();
const [a, b] = InMemoryTransport.createLinkedPair();
const startedAt = new Date().toISOString();
try {
  await Promise.all([server.connect(b), client.connect(a)]);
  const inventory = {
    tools: (await client.listTools()).tools.map(t => t.name),
    resources: (await client.listResources()).resources.map(r => r.uri),
    prompts: (await client.listPrompts()).prompts.map(p => p.name),
  };
  const onboarding = await client.getPrompt({ name: 'apple-native-start', arguments: { focus: 'Apple geliştiricisiyim ve tasarımcıyım' } });
  const checks = [];
  for (const fixture of ['legacy-app', 'clean-app']) {
    const result = await client.callTool({ name: 'lint_swiftui', arguments: { path: path.join(root, 'tests/fixtures', fixture) } });
    const report = result.structuredContent;
    if (!report) throw new Error(`No structured report for ${fixture}`);
    // Public demo reports use portable fixture paths.
    checks.push({ fixture, isError: result.isError ?? false, report: JSON.parse(JSON.stringify(report).replaceAll(root, '<repository>/')) });
  }
  if (checks[0].report.status !== 'fail' || checks[1].report.status === 'fail') {
    throw new Error('Demo acceptance failed: legacy must fail and clean must not fail');
  }
  await fs.mkdir(output, { recursive: true });
  const payload = JSON.stringify({ startedAt, recordedAt: new Date().toISOString(), transport: 'SDK in-memory MCP client/server', fixtureOnly: true, inventory, onboarding, checks }, null, 2) + '\n';
  await fs.writeFile(path.join(output, 'evidence.json'), payload);
  await fs.writeFile(path.join(output, 'SHA256SUMS'), `${createHash('sha256').update(payload).digest('hex')}  evidence.json\n`);
  console.log(`Recorded ${inventory.tools.length} tools, ${inventory.resources.length} resources, ${inventory.prompts.length} prompts`);
  for (const check of checks) console.log(`${check.fixture}: ${check.report.status} (${check.report.summary.total} findings)`);
  console.log(`Evidence: ${output}`);
} finally {
  await client.close();
  await server.close();
}
