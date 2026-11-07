#!/usr/bin/env node
/** GitHub-only release launcher. stdout belongs exclusively to the child MCP. */
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile, spawn } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
export const REPOSITORY = 'kayaonur607/apple-native-engineer-mcp';
const REMOTE = `https://github.com/${REPOSITORY}.git`;
const BASELINE = fileURLToPath(new URL('../../../', import.meta.url));
const TAG = /^mcp-v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const log = message => process.stderr.write(`[apple-native-update] ${message}\n`);
const exists = async p => fs.access(p).then(() => true, () => false);

export function versionOf(tag) {
  const match = TAG.exec(tag ?? '');
  if (!match) throw new Error('Expected a stable release tag: mcp-vMAJOR.MINOR.PATCH');
  return match.slice(1).map(Number);
}
export function compareTags(a, b) {
  const left = versionOf(a), right = versionOf(b);
  for (let i = 0; i < 3; i++) if (left[i] !== right[i]) return left[i] > right[i] ? 1 : -1;
  return 0;
}
export function selectRelease(releases, current) {
  return releases.filter(r => !r.draft && !r.prerelease && r.published_at && TAG.test(r.tag_name))
    .filter(r => !current || compareTags(r.tag_name, current) > 0)
    .sort((a, b) => compareTags(b.tag_name, a.tag_name))[0];
}
async function run(command, args, cwd, timeout = 120_000) {
  const env = { ...process.env, GIT_TERMINAL_PROMPT: '0', GIT_CONFIG_NOSYSTEM: '1' };
  delete env.APPLE_NATIVE_ROOT;
  return exec(command, args, { cwd, timeout, maxBuffer: 4 * 1024 * 1024, env });
}
export async function readActive(cache) {
  try {
    const record = JSON.parse(await fs.readFile(path.join(cache, 'active.json'), 'utf8'));
    versionOf(record.tag);
    if (!/^[a-f0-9]{40,64}$/.test(record.commit)) return null;
    const directory = path.join(cache, 'releases', `${record.tag}-${record.commit}`);
    if (!(await exists(path.join(directory, 'integrations/mcp-server/node_modules')))) return null;
    if (!(await exists(path.join(directory, 'integrations/mcp-server/src/index.js')))) return null;
    return { ...record, directory };
  } catch { return null; }
}

/** Stage, install and smoke-test before atomically publishing the active pointer. */
export async function prepareRelease(cache, release, { execute = run, remote = REMOTE } = {}) {
  versionOf(release.tag_name);
  const releases = path.join(cache, 'releases');
  await fs.mkdir(releases, { recursive: true });
  const stage = await fs.mkdtemp(path.join(cache, 'stage-'));
  try {
    await execute('git', ['clone', '--depth', '1', '--branch', release.tag_name, '--', remote, stage], cache);
    const { stdout } = await execute('git', ['rev-parse', 'HEAD'], stage);
    const commit = stdout.trim();
    if (!/^[a-f0-9]{40,64}$/.test(commit)) throw new Error('Invalid release commit');
    const packageDir = path.join(stage, 'integrations/mcp-server');
    const manifest = JSON.parse(await fs.readFile(path.join(packageDir, 'package.json'), 'utf8'));
    if (`mcp-v${manifest.version}` !== release.tag_name) throw new Error('Tag/package version mismatch');
    await execute(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['ci', '--ignore-scripts', '--no-audit', '--no-fund'], packageDir, 240_000);
    const { stdout: inventory } = await execute(process.execPath, ['src/index.js', '--selftest'], packageDir);
    const info = JSON.parse(inventory);
    if (info.version !== manifest.version || !info.tools?.includes('audit_project') || !info.resources || !info.prompts?.includes('apple-native-start')) {
      throw new Error('Release smoke test failed');
    }
    const directory = path.join(releases, `${release.tag_name}-${commit}`);
    // A release directory is immutable once activated. Never reinstall into a running version.
    if (!(await exists(directory))) await fs.rename(stage, directory);
    const record = { tag: release.tag_name, commit, activated_at: new Date().toISOString(),
      release_url: `https://github.com/${REPOSITORY}/releases/tag/${release.tag_name}` };
    const temporary = path.join(cache, `active-${process.pid}.json`);
    await fs.writeFile(temporary, JSON.stringify(record, null, 2) + '\n', { mode: 0o600 });
    await fs.rename(temporary, path.join(cache, 'active.json'));
    return { ...record, directory };
  } finally {
    await fs.rm(stage, { recursive: true, force: true });
  }
}

export async function resolveInstallation({ cache, env = process.env, fetchReleases, execute, baseline = BASELINE, logger = log } = {}) {
  await fs.mkdir(cache, { recursive: true, mode: 0o700 });
  let active = await readActive(cache);
  const pinned = env.APPLE_NATIVE_VERSION;
  if (pinned) versionOf(pinned);
  if (env.APPLE_NATIVE_AUTO_UPDATE === 'off') {
    if (pinned && active?.tag !== pinned) throw new Error('Pinned version is not cached; enable updates once to install it');
    return active ?? { directory: baseline, tag: 'local-checkout' };
  }
  const lock = path.join(cache, 'update.lock');
  let acquired = false;
  try {
    // Locks older than the bounded installer can survive a crashed launcher.
    if (await exists(lock)) {
      const stat = await fs.stat(lock);
      if (Date.now() - stat.mtimeMs > 10 * 60_000) await fs.rm(lock, { recursive: true, force: true });
    }
    await fs.mkdir(lock);
    acquired = true;
    const releases = await (fetchReleases ?? (async () => {
      const response = await fetch(`https://api.github.com/repos/${REPOSITORY}/releases?per_page=100`, {
        headers: { Accept: 'application/vnd.github+json', 'User-Agent': 'apple-native-engineer-updater' },
        signal: AbortSignal.timeout(5000), redirect: 'error',
      });
      if (!response.ok) throw new Error(`GitHub returned HTTP ${response.status}`);
      const body = await response.json();
      if (!Array.isArray(body)) throw new Error('Invalid GitHub release response');
      return body;
    }))();
    const stable = releases.filter(r => !r.draft && !r.prerelease && r.published_at && TAG.test(r.tag_name));
    const release = pinned ? stable.find(r => r.tag_name === pinned) : selectRelease(stable, active?.tag);
    if (pinned && !release && active?.tag !== pinned) throw new Error('Pinned published release was not found');
    if (release && active?.tag !== release.tag_name) {
      active = await prepareRelease(cache, release, { execute });
      logger(`Activated ${active.tag}. What's new: ${active.release_url}`);
    }
  } catch (error) {
    if (pinned && active?.tag !== pinned) throw new Error(`Cannot install pinned release: ${error.message}`);
    logger(`Update skipped (${error.code === 'EEXIST' ? 'another client is updating' : error.message}); keeping ${active?.tag ?? 'local checkout'}.`);
  } finally {
    if (acquired) await fs.rm(lock, { recursive: true, force: true });
  }
  return active ?? { directory: baseline, tag: 'local-checkout' };
}

async function main() {
  const cache = path.resolve(process.env.APPLE_NATIVE_UPDATE_DIR ?? path.join(os.homedir(), '.cache/apple-native-engineer'));
  const install = await resolveInstallation({ cache });
  log(`Starting ${install.tag}. Updates apply on MCP restart, never during a tool call.`);
  const child = spawn(process.execPath, [path.join(install.directory, 'integrations/mcp-server/src/index.js'), ...process.argv.slice(2)], {
    stdio: 'inherit', env: { ...process.env, APPLE_NATIVE_ROOT: install.directory },
  });
  for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
  child.on('error', error => { log(error.message); process.exitCode = 1; });
  child.on('exit', (code, signal) => { process.exitCode = code ?? (signal ? 1 : 0); });
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => { log(error.message); process.exitCode = 1; });
}
