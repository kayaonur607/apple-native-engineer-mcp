import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { it } from 'node:test';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { createServer } from '../src/server.js';
import { REPO_ROOT, resolveOutput, resolveTarget } from '../src/runner.js';

it('distinguishes new output paths from missing inputs', () => {
  const missing = path.join(os.tmpdir(), 'apple-native-missing', 'new.swift');
  assert.equal(resolveOutput(missing), missing);
  assert.throws(() => resolveTarget(missing), { code: 'PATH_NOT_FOUND' });
  for (const invalid of ['', ' ', '\0']) {
    assert.throws(() => resolveOutput(invalid), { code: 'INVALID_OUTPUT_PATH' });
  }
});

it('advertises overwrite capabilities and creates a new icon destination over MCP', async () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'apple-native-output-'));
  const server = createServer();
  const [ct, st] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: 'output-test', version: '1.0.0' });
  try {
    await Promise.all([server.connect(st), client.connect(ct)]);
    const { tools } = await client.listTools();
    for (const name of ['forge_design_tokens', 'generate_release_report', 'prepare_icon_assets', 'compose_marketing_screenshots']) {
      const tool = tools.find(t => t.name === name);
      assert.equal(tool.annotations.readOnlyHint, false, name);
      assert.equal(tool.annotations.destructiveHint, true, name);
    }
    for (const name of ['search_apple_documentation', 'read_apple_documentation',
                        'inspect_apple_api_availability', 'find_apple_guidelines', 'app_store_connect']) {
      const tool = tools.find(t => t.name === name);
      assert.equal(tool.annotations.openWorldHint, true, name);
      assert.equal(tool.annotations.readOnlyHint, true, name);
    }
    const out = path.join(tmp, 'New.appiconset');
    const result = await client.callTool({ name: 'prepare_icon_assets', arguments: {
      source: path.join(REPO_ROOT, 'tests/fixtures/clean-app/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png'), out,
    }});
    assert.notEqual(result.isError, true, JSON.stringify(result));
    assert.ok(fs.existsSync(path.join(out, 'Contents.json')));
    const verified = await client.callTool({ name: 'verify_icon_set', arguments: { path: out } });
    assert.equal(verified.structuredContent.status, 'pass');
  } finally {
    await client.close();
    await server.close();
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});
