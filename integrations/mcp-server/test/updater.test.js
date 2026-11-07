import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { after, before, describe, it } from 'node:test';
import { compareTags, selectRelease, versionOf, prepareRelease, readActive, resolveInstallation } from '../scripts/github-launcher.mjs';
const exec = promisify(execFile);
const release = tag => ({ tag_name: tag, published_at: '2026-11-07T00:00:00Z', draft: false, prerelease: false });

describe('GitHub release updates', () => {
  let temporary, remote;
  before(async () => {
    temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'apple-updater-test-'));
    remote = path.join(temporary, 'origin');
    const pkg = path.join(remote, 'integrations/mcp-server');
    await fs.mkdir(path.join(pkg, 'src'), { recursive: true });
    await fs.writeFile(path.join(pkg, 'package.json'), JSON.stringify({ name: 'test-release', version: '2.2.0', private: true }));
    await fs.writeFile(path.join(pkg, 'package-lock.json'), JSON.stringify({ name: 'test-release', version: '2.2.0', lockfileVersion: 3, packages: { '': { name: 'test-release', version: '2.2.0' } } }));
    await fs.writeFile(path.join(pkg, 'src/index.js'), `console.log(JSON.stringify({version:'2.2.0',tools:['audit_project'],resources:1,prompts:['apple-native-start']}));`);
    await exec('git', ['init', remote]);
    await exec('git', ['-C', remote, 'add', '.']);
    await exec('git', ['-C', remote, '-c', 'user.name=Test', '-c', 'user.email=test@example.com', '-c', 'commit.gpgsign=false', 'commit', '-m', 'fixture']);
    await exec('git', ['-C', remote, 'tag', 'mcp-v2.2.0']);
    await exec('git', ['-C', remote, 'tag', 'mcp-v2.3.0']); // deliberately mismatched package
  });
  after(async () => fs.rm(temporary, { recursive: true, force: true }));
  const cacheFor = async name => { const cache = path.join(temporary, name); await fs.mkdir(cache); return cache; };

  it('chooses numeric stable versions, excludes drafts/prereleases and avoids downgrades', () => {
    assert.equal(selectRelease([release('mcp-v2.9.0'), release('mcp-v2.10.0'), { ...release('mcp-v9.0.0'), draft: true }, { ...release('mcp-v8.0.0'), prerelease: true }, release('mcp-v3.0.0-beta')]).tag_name, 'mcp-v2.10.0');
    assert.equal(selectRelease([release('mcp-v2.1.0')], 'mcp-v2.2.0'), undefined);
    assert.equal(compareTags('mcp-v2.2.0', 'mcp-v2.2.0'), 0);
    assert.throws(() => versionOf('../../main'));
  });

  it('clones a tagged repository, smoke-tests and atomically activates it', async () => {
    const cache = await cacheFor('success');
    const installed = await prepareRelease(cache, release('mcp-v2.2.0'), { remote });
    // npm ci can omit node_modules with zero dependencies; production always has SDK dependencies.
    await fs.mkdir(path.join(installed.directory, 'integrations/mcp-server/node_modules'), { recursive: true });
    assert.equal((await readActive(cache)).tag, 'mcp-v2.2.0');
    const reused = await prepareRelease(cache, release('mcp-v2.2.0'), { remote });
    assert.equal(reused.directory, installed.directory, 'validated rollback cache remains usable');
    assert.equal((await exec('git', ['-C', installed.directory, 'rev-parse', 'HEAD'])).stdout.trim(), installed.commit);
    assert.ok(!(await fs.readdir(cache)).some(name => name.startsWith('stage-')));
  });

  it('never activates an existing damaged release directory', async () => {
    const cache = await cacheFor('damaged');
    const commit = (await exec('git', ['-C', remote, 'rev-parse', 'HEAD'])).stdout.trim();
    await fs.mkdir(path.join(cache, 'releases', `mcp-v2.2.0-${commit}`), { recursive: true });
    await assert.rejects(prepareRelease(cache, release('mcp-v2.2.0'), { remote }), /cache directory already exists/);
    assert.equal(await readActive(cache), null);
    await assert.rejects(fs.access(path.join(cache, 'active.json')));
  });

  it('keeps the active version if a release tag disagrees with its package', async () => {
    const cache = path.join(temporary, 'success');
    const previous = await fs.readFile(path.join(cache, 'active.json'), 'utf8');
    await assert.rejects(prepareRelease(cache, release('mcp-v2.3.0'), { remote }), /version mismatch/);
    assert.equal(await fs.readFile(path.join(cache, 'active.json'), 'utf8'), previous);
  });

  it('keeps the active version when dependency installation fails', async () => {
    const cache = path.join(temporary, 'success');
    const previous = await fs.readFile(path.join(cache, 'active.json'), 'utf8');
    await assert.rejects(prepareRelease(cache, release('mcp-v2.2.0'), { remote, execute: async (command, args, cwd) => {
      if (args[0] === 'ci') throw new Error('dependency install failed');
      return exec(command, args, { cwd });
    } }), /dependency install failed/);
    assert.equal(await fs.readFile(path.join(cache, 'active.json'), 'utf8'), previous);
  });

  it('continues offline with the last successful installation', async () => {
    const cache = path.join(temporary, 'success');
    const installed = await resolveInstallation({ cache, env: {}, fetchReleases: async () => { throw new Error('offline'); }, logger: () => {} });
    assert.equal(installed.tag, 'mcp-v2.2.0');
  });

  it('honours disabled updates without contacting GitHub', async () => {
    const cache = path.join(temporary, 'success');
    const installed = await resolveInstallation({ cache, env: { APPLE_NATIVE_AUTO_UPDATE: 'off' }, fetchReleases: async () => { assert.fail('network used'); } });
    assert.equal(installed.tag, 'mcp-v2.2.0');
  });

  it('fails rather than silently replacing an unavailable pinned version', async () => {
    const cache = path.join(temporary, 'success');
    await assert.rejects(resolveInstallation({ cache, env: { APPLE_NATIVE_VERSION: 'mcp-v1.0.0' }, fetchReleases: async () => [] }), /Pinned published release/);
  });

  it('avoids competing installs when another client holds the update lock', async () => {
    const cache = path.join(temporary, 'success');
    await fs.mkdir(path.join(cache, 'update.lock'));
    try {
      const installed = await resolveInstallation({ cache, env: {}, fetchReleases: async () => { assert.fail('competing network request'); }, logger: () => {} });
      assert.equal(installed.tag, 'mcp-v2.2.0');
      await fs.access(path.join(cache, 'update.lock'));
    } finally { await fs.rm(path.join(cache, 'update.lock'), { recursive: true }); }
  });

  it('rejects a corrupted active pointer and retains the bootstrap checkout', async () => {
    const cache = await cacheFor('corrupt');
    await fs.writeFile(path.join(cache, 'active.json'), JSON.stringify({ tag: '../../bad', commit: '../../bad' }));
    assert.equal(await readActive(cache), null);
    const installed = await resolveInstallation({ cache, baseline: '/bootstrap', env: { APPLE_NATIVE_AUTO_UPDATE: 'off' } });
    assert.equal(installed.directory, '/bootstrap');
  });
});
