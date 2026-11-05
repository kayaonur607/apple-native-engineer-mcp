/**
 * Environment diagnostics for `check_environment`.
 *
 * Every support question about an MCP server is one of three things: the
 * interpreter is wrong, the checkout is missing, or a platform tool is absent.
 * Answering that from inside the protocol means the agent can diagnose itself
 * instead of describing a stack trace to a human.
 *
 * This is the one tool that does not wrap a Python auditor, because its subject
 * is the server's own runtime — the thing the auditors cannot see.
 */

import { execFile } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { SERVER_NAME } from "./constants.js";
import { REPO_ROOT } from "./runner.js";
import { telemetryMode } from "./telemetry.js";

const PYTHON = process.env.APPLE_NATIVE_PYTHON || "python3";

/** The oldest interpreter the auditors support. */
const MIN_PYTHON = [3, 10];

function run(command, args, { timeoutMs = 20_000 } = {}) {
  return new Promise((resolve) => {
    execFile(command, args, { timeout: timeoutMs, maxBuffer: 4 * 1024 * 1024 }, (error, stdout, stderr) => {
      resolve({
        ok: !error,
        code: error?.code ?? 0,
        stdout: (stdout ?? "").trim(),
        stderr: (stderr ?? "").trim(),
      });
    });
  });
}

function parseVersion(output) {
  const match = output.match(/(\d+)\.(\d+)(?:\.(\d+))?/);
  if (!match) return null;
  return [Number(match[1]), Number(match[2]), Number(match[3] ?? 0)];
}

function atLeast(version, minimum) {
  for (let index = 0; index < minimum.length; index += 1) {
    if ((version[index] ?? 0) > minimum[index]) return true;
    if ((version[index] ?? 0) < minimum[index]) return false;
  }
  return true;
}

/**
 * @returns {Promise<{envelope: object, summary: string, exitCode: number}>}
 */
export async function checkEnvironment() {
  const checks = [];
  const add = (id, status, message, detail = {}) => checks.push({ id, status, message, ...detail });

  // 1. Node — the server itself.
  const nodeVersion = process.versions.node;
  add(
    "node",
    atLeast(parseVersion(nodeVersion) ?? [0, 0, 0], [20, 0]) ? "pass" : "fail",
    `Node ${nodeVersion}`,
    { required: ">=20" },
  );

  // 2. Python — every auditor depends on it.
  const python = await run(PYTHON, ["--version"]);
  if (!python.stdout && !python.stderr) {
    add("python", "fail", `${PYTHON} is not runnable`, { hint: "Set APPLE_NATIVE_PYTHON to a Python 3.10+ interpreter." });
  } else {
    const version = parseVersion(python.stdout || python.stderr);
    add(
      "python",
      version && atLeast(version, MIN_PYTHON) ? "pass" : "fail",
      `${PYTHON} → ${python.stdout || python.stderr}`,
      {
        required: ">=3.10",
        hint: version && !atLeast(version, MIN_PYTHON) ? "Upgrade Python or set APPLE_NATIVE_PYTHON." : undefined,
      },
    );
  }

  // 3. The auditors themselves.
  const toolsDir = path.join(REPO_ROOT, "tools");
  const toolCount = fs.existsSync(toolsDir)
    ? fs.readdirSync(toolsDir, { withFileTypes: true }).filter((entry) => entry.isDirectory() && entry.name !== "lib").length
    : 0;
  add(
    "auditors",
    toolCount >= 14 ? "pass" : "fail",
    toolCount === 0 ? `no auditors found under ${toolsDir}` : `${toolCount} auditors found`,
    { root: REPO_ROOT, hint: toolCount === 0 ? "Set APPLE_NATIVE_ROOT to the repository root." : undefined },
  );

  // 4. The knowledge base. Without it the resources list is empty, which is a
  //    degraded server rather than a broken one.
  const references = path.join(REPO_ROOT, "references");
  const referenceCount = fs.existsSync(references)
    ? fs.readdirSync(references).filter((name) => name.endsWith(".md")).length
    : 0;
  add(
    "references",
    referenceCount > 0 ? "pass" : "warn",
    referenceCount > 0 ? `${referenceCount} reference guides` : "reference guides are missing; resources will be empty",
  );

  // 5. git — only needed by `review_diff`.
  const git = await run("git", ["--version"]);
  add("git", git.ok ? "pass" : "warn", git.ok ? git.stdout : "git not found; review_diff is unavailable");

  // 6. Xcode — optional, and reported as a fact rather than a requirement,
  //    because the auditors are static analysis and do not need it.
  const xcode = await run("xcodebuild", ["-version"]);
  if (xcode.ok) {
    const version = xcode.stdout.split("\n")[0];
    const sdk = await run("xcrun", ["--sdk", "iphoneos", "--show-sdk-version"]);
    add("xcode", "pass", version, { ios_sdk: sdk.ok ? sdk.stdout : null });
  } else {
    add("xcode", "info", "Xcode not installed; static audits still work, Swift compilation does not");
  }

  // 7. App Store Connect credentials — presence only, never the value.
  const asc = Boolean(process.env.ASC_KEY_ID && process.env.ASC_ISSUER_ID && (process.env.ASC_PRIVATE_KEY_PATH || process.env.ASC_PRIVATE_KEY || process.env.ASC_PRIVATE_KEY_BASE64));
  add("app_store_connect", "info", asc ? "credentials detected" : "not configured; app_store_connect will report it needs credentials");

  // 8. Privacy posture, restated where a user will actually look.
  add("telemetry", "info", `telemetry is ${telemetryMode()}`, {
    hint: "Run with --telemetry-preview to see the exact event shape.",
  });

  const failed = checks.filter((check) => check.status === "fail");
  const warned = checks.filter((check) => check.status === "warn");
  const status = failed.length > 0 ? "fail" : warned.length > 0 ? "warn" : "pass";

  return {
    envelope: {
      schema_version: "2.0",
      tool: "environment-check",
      tool_version: "2.0.0",
      target: os.hostname(),
      status,
      summary: { critical: 0, error: failed.length, warning: warned.length, info: checks.length - failed.length - warned.length, total: checks.length },
      findings: [...failed, ...warned].map((check) => ({
        code: `ENV_${check.id.toUpperCase()}`,
        severity: check.status === "fail" ? "error" : "warning",
        message: check.message,
        hint: check.hint ?? "",
        file: null,
        line: null,
      })),
      data: {
        server: SERVER_NAME,
        repo_root: REPO_ROOT,
        platform: `${os.type()} ${os.release()} ${os.arch()}`,
        checks,
      },
    },
    summary:
      `environment · ${status.toUpperCase()} · ${failed.length} blocking, ${warned.length} warning(s)\n` +
      checks.map((check) => `  ${check.status.toUpperCase().padEnd(4)} ${check.id}: ${check.message}`).join("\n"),
    exitCode: status === "fail" ? 2 : status === "warn" ? 1 : 0,
  };
}
