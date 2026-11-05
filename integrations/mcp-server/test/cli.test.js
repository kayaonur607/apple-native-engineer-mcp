/**
 * CLI surface tests.
 *
 * The flags are the first thing a human or a CI job touches, and they are the
 * only part of the server that is not exercised by the protocol tests. These
 * spawn the real entry point so a broken import graph or a missing `await`
 * fails here instead of in someone's terminal.
 */

import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const ENTRY = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "src", "index.js");

function run(...args) {
  return new Promise((resolve) => {
    execFile(process.execPath, [ENTRY, ...args], { timeout: 60_000 }, (error, stdout, stderr) => {
      resolve({ code: error?.code ?? 0, stdout, stderr });
    });
  });
}

describe("command line", () => {
  it("prints its version", async () => {
    const { code, stdout } = await run("--version");
    assert.equal(code, 0);
    assert.match(stdout.trim(), /^\d+\.\d+\.\d+$/);
  });

  it("documents every flag it accepts", async () => {
    const { code, stdout } = await run("--help");
    assert.equal(code, 0);
    for (const flag of ["--http", "--selftest", "--doctor", "--telemetry-preview", "--allow-remote", "--version"]) {
      assert.ok(stdout.includes(flag), `--help does not mention ${flag}`);
    }
    assert.match(stdout, /telemetry is off unless you turn it on/i);
  });

  it("reports a complete inventory without a client", async () => {
    const { code, stdout } = await run("--selftest");
    assert.equal(code, 0);
    const payload = JSON.parse(stdout);
    assert.ok(payload.tools.length >= 16);
    assert.ok(payload.tools.includes("review_diff"));
    assert.ok(payload.tools.includes("check_environment"));
    assert.equal(payload.transport, "stdio");
    assert.ok(payload.resources > 0);
    assert.ok(payload.prompts.includes("apple-native"));
  });

  it("exits 0 from --doctor when the machine can run everything", async () => {
    const { code, stdout } = await run("--doctor");
    // 0 = healthy, 1 = degraded (no git or no references), 2 = blocked.
    assert.ok([0, 1].includes(code), `--doctor reported a blocking problem:\n${stdout}`);
    assert.match(stdout, /^environment · /);
    for (const check of ["node", "python", "auditors"]) {
      assert.match(stdout, new RegExp(`PASS ${check}:`), `--doctor did not pass ${check}`);
    }
  });

  it("rejects an invalid port with a sentence, not a stack trace", async () => {
    const { code, stderr } = await run("--http", "99999");
    assert.equal(code, 2);
    assert.match(stderr, /^error: Invalid port: 99999/);
    assert.ok(!stderr.includes("    at "), "configuration errors must not print a stack trace");
  });
});
