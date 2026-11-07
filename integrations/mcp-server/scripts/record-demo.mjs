#!/usr/bin/env node
/** Record real stdio MCP requests and responses from public fixtures. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
const root = fileURLToPath(new URL('../../../', import.meta.url));
const output = path.join(root, 'assets/demo');
const scratch = path.join(root, '.swiftwork/video-demo');
await fs.mkdir(output, { recursive: true });
await fs.mkdir(path.join(scratch, 'AppIcon.appiconset'), { recursive: true });
const client = new Client({ name: 'readme-demo-recorder', version: '1.0.0' });
const transport = new StdioClientTransport({ command: process.execPath, args: [path.join(root, 'integrations/mcp-server/src/index.js')],
  env: { ...process.env, APPLE_NATIVE_ROOT: root }, stderr: 'pipe' });
transport.stderr?.on('data', () => {});
const events = [];
const portable = value => JSON.parse(JSON.stringify(value).replaceAll(root, '<repository>/'));
async function step(title, method, params, action) {
  const started = performance.now();
  const response = await action();
  events.push({ title, method, params: portable(params), duration_ms: Math.round(performance.now() - started), response: portable(response) });
  console.log(`${events.length}. ${title} (${events.at(-1).duration_ms}ms)`);
  return response;
}
try {
  await step('Connect a real MCP client', 'initialize', { transport: 'stdio', command: 'node integrations/mcp-server/src/index.js' }, async () => {
    await client.connect(transport);
    const tools = await client.listTools(), resources = await client.listResources(), prompts = await client.listPrompts();
    return { server: client.getServerVersion(), tools: tools.tools.length, resources: resources.resources.length, prompts: prompts.prompts.length };
  });
  await step('Start as a developer or designer', 'prompts/get', { name: 'apple-native-start', arguments: { focus: 'Review a native Apple interface' } }, () => client.getPrompt({ name: 'apple-native-start', arguments: { focus: 'Review a native Apple interface' } }));
  const legacy = path.join(root, 'tests/fixtures/legacy-app');
  await step('Inspect the project before giving advice', 'tools/call', { name: 'inspect_apple_project', arguments: { path: legacy } }, () => client.callTool({ name: 'inspect_apple_project', arguments: { path: legacy } }));
  const before = await step('Find concrete SwiftUI issues', 'tools/call', { name: 'lint_swiftui', arguments: { path: legacy } }, () => client.callTool({ name: 'lint_swiftui', arguments: { path: legacy } }));
  const clean = path.join(root, 'tests/fixtures/clean-app');
  const after = await step('Check the clean reference implementation', 'tools/call', { name: 'lint_swiftui', arguments: { path: clean } }, () => client.callTool({ name: 'lint_swiftui', arguments: { path: clean } }));
  const master = path.join(clean, 'Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png');
  const iconOut = path.join(scratch, 'AppIcon.appiconset');
  const prepared = await step('Convert one master into Xcode icon assets', 'tools/call', { name: 'prepare_icon_assets', arguments: { source: master, out: iconOut } }, () => client.callTool({ name: 'prepare_icon_assets', arguments: { source: master, out: iconOut } }));
  await step('Verify the generated icon set', 'tools/call', { name: 'verify_icon_set', arguments: { path: iconOut } }, () => client.callTool({ name: 'verify_icon_set', arguments: { path: iconOut } }));
  await step('Read the installed version and changes', 'resources/read', { uri: 'apple-native://release' }, () => client.readResource({ uri: 'apple-native://release' }));
  if (before.structuredContent?.status !== 'fail' || after.structuredContent?.status !== 'pass' || prepared.isError) throw new Error('Demo acceptance failed');
  const iconFiles = await fs.readdir(iconOut);
  const evidence = { recorded_at: new Date().toISOString(), fixture_only: true,
    format: 'Real MCP stdio session; rendered transcript playback, not a desktop screen recording.',
    comparison: 'Legacy and clean are separate fixtures. This session does not automatically rewrite Swift code.',
    events, generated_icon_files: iconFiles };
  const payload = JSON.stringify(evidence, null, 2) + '\n';
  await fs.writeFile(path.join(output, 'session.json'), payload);
  await fs.writeFile(path.join(output, 'session.sha256'), `${createHash('sha256').update(payload).digest('hex')}  session.json\n`);
} finally { await client.close(); }
