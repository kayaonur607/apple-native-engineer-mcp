/**
 * Store production and distribution tools over a real MCP client:
 * specs, HIG index, screenshot capture plan, screenshot audit, localized
 * composition and the distribution planner.
 */

import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { after, before, describe, it } from 'node:test';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { createServer } from '../src/server.js';
import { REPO_ROOT } from '../src/runner.js';

const codes = result => (result.structuredContent?.findings ?? []).map(f => f.code);

describe('store production and distribution tools', () => {
  let client, server, tmp;

  before(async () => {
    tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'apple-native-production-'));
    server = createServer();
    const [ct, st] = InMemoryTransport.createLinkedPair();
    client = new Client({ name: 'production-test', version: '1.0.0' });
    await Promise.all([server.connect(st), client.connect(ct)]);
  });

  after(async () => {
    await client?.close();
    await server?.close();
    fs.rmSync(tmp, { recursive: true, force: true });
  });

  it('declares write capabilities for capture, composition and planning', async () => {
    const { tools } = await client.listTools();
    for (const name of ['capture_screenshots', 'compose_marketing_screenshots', 'plan_distribution']) {
      const tool = tools.find(t => t.name === name);
      assert.ok(tool, name);
      assert.equal(tool.annotations.readOnlyHint, false, name);
    }
    for (const name of ['get_app_store_specs', 'audit_screenshots', 'search_apple_guidelines']) {
      assert.equal(tools.find(t => t.name === name).annotations.readOnlyHint, true, name);
    }
  });

  it("returns Apple's dated screenshot specification per platform", async () => {
    const result = await client.callTool({ name: 'get_app_store_specs', arguments: { platforms: ['watchOS'] } });
    const data = result.structuredContent.data;
    assert.match(data.sources.screenshots, /^https:\/\/developer\.apple\.com\//);
    assert.ok(data.screenshots.slots.length >= 6);
    assert.ok(data.screenshots.slots.every(slot => slot.platform === 'watchOS'));
    assert.equal(data.screenshots.alpha_allowed, false);
  });

  it('finds HIG pages offline, including new platforms', async () => {
    const result = await client.callTool({ name: 'search_apple_guidelines', arguments: { query: 'iPhone Duo' } });
    const slugs = result.structuredContent.data.matches.map(match => match.slug);
    assert.equal(slugs[0], 'designing-for-iphone-duo');
  });

  it('audits screenshot sets and required coverage', async () => {
    const result = await client.callTool({ name: 'audit_screenshots', arguments: {
      path: path.join(REPO_ROOT, 'tests/fixtures/clean-app/screenshots'), platforms: ['iOS', 'iPadOS'],
    }});
    assert.ok(codes(result).includes('SHOT022'), JSON.stringify(codes(result)));
    assert.equal(result.structuredContent.data.sets.default['iphone-6.9'].count, 3);
  });

  it('plans a Simulator capture without executing it', async () => {
    const plan = path.join(tmp, 'plan.json');
    fs.writeFileSync(plan, JSON.stringify({
      bundle_id: 'dev.example.app', devices: ['iphone-6.9'], locales: ['en-US', 'ar-SA'],
      appearances: ['light', 'dark'], screens: [{ name: '01-home', arguments: ['-screen', 'home'] }],
    }));
    const result = await client.callTool({ name: 'capture_screenshots', arguments: { plan, out: path.join(tmp, 'shots'), dry_run: true } });
    const data = result.structuredContent.data;
    assert.equal(data.dry_run, true);
    assert.equal(data.capture_count, 4);
    assert.ok(data.commands.some(command => command.includes('-AppleLocale ar_SA')));
    assert.ok(data.commands.some(command => command.includes('status_bar') && command.includes('9:41')));
    assert.equal(fs.existsSync(path.join(tmp, 'shots')), false);
  });

  it('composes localized frames into mirrored locale folders', async () => {
    const shots = path.join(tmp, 'captures');
    for (const locale of ['en-US', 'tr-TR']) {
      fs.mkdirSync(path.join(shots, locale), { recursive: true });
      fs.copyFileSync(path.join(REPO_ROOT, 'tests/fixtures/clean-app/screenshots/home.png'),
                      path.join(shots, locale, '01-home.png'));
    }
    const captions = path.join(tmp, 'captions.json');
    fs.writeFileSync(captions, JSON.stringify({ 'en-US': { '01-home': { headline: 'Plan your week' } } }));
    const out = path.join(tmp, 'frames');
    const result = await client.callTool({ name: 'compose_marketing_screenshots', arguments: { screenshots: shots, out, captions } });
    assert.notEqual(result.isError, true, JSON.stringify(result));
    assert.ok(fs.existsSync(path.join(out, 'en-US', '01-home.svg')));
    assert.ok(fs.readFileSync(path.join(out, 'en-US', '01-home.svg'), 'utf8').includes('Plan your week'));
    assert.ok(codes(result).includes('SHOT115'), 'tr-TR fell back and must be reported');
  });

  it('plans distribution with preflight findings and ExportOptions', async () => {
    const exportOptions = path.join(tmp, 'ExportOptions.plist');
    const result = await client.callTool({ name: 'plan_distribution', arguments: {
      path: path.join(REPO_ROOT, 'tests/fixtures/distribution-app'), method: 'testflight-internal',
      write_export_options: exportOptions,
    }});
    const data = result.structuredContent.data;
    assert.equal(data.export_options.method, 'app-store-connect');
    assert.equal(data.export_options.testFlightInternalTestingOnly, true);
    assert.ok(codes(result).includes('DST030'));
    assert.ok(fs.readFileSync(exportOptions, 'utf8').includes('<string>app-store-connect</string>'));
    assert.ok(data.steps.some(step => step.step === 'archive' && step.command.startsWith('xcodebuild archive')));
  });
});

describe('cross-platform apps', () => {
  let client, server;

  before(async () => {
    server = createServer();
    const [ct, st] = InMemoryTransport.createLinkedPair();
    client = new Client({ name: 'cross-platform-test', version: '1.0.0' });
    await Promise.all([server.connect(st), client.connect(ct)]);
  });

  after(async () => {
    await client?.close();
    await server?.close();
  });

  it('audits a Flutter app through its iOS host', async () => {
    const result = await client.callTool({ name: 'audit_cross_platform', arguments: {
      path: path.join(REPO_ROOT, 'tests/fixtures/flutter-app') } });
    assert.equal(result.structuredContent.data.framework, 'flutter');
    for (const code of ['FLT001', 'FLT002', 'FLT009', 'XPL010']) assert.ok(codes(result).includes(code), code);
  });

  it('plans an Expo release through EAS when there is no iOS host', async () => {
    const result = await client.callTool({ name: 'plan_distribution', arguments: {
      path: path.join(REPO_ROOT, 'tests/fixtures/react-native-app') } });
    const steps = result.structuredContent.data.steps;
    assert.ok(steps.some(step => step.command.includes('eas-cli@latest submit')));
    assert.ok(steps.find(step => step.step === 'upload').requires_approval);
    assert.ok(codes(result).includes('DST003'));
  });

  it('plans a Flutter release with flutter build ipa', async () => {
    const result = await client.callTool({ name: 'plan_distribution', arguments: {
      path: path.join(REPO_ROOT, 'tests/fixtures/flutter-app') } });
    const archive = result.structuredContent.data.steps.find(step => step.step === 'archive');
    assert.match(archive.command, /^flutter build ipa --release --export-options-plist=/);
  });
});
