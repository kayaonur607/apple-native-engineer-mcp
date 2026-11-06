/**
 * Runs the Python analysis tools and normalises their output.
 *
 * Contract with the CLI layer (see tools/lib/apple_native/report.py):
 *   - `--json` prints exactly one JSON envelope to stdout
 *   - exit code 0 = pass, 1 = warnings under --strict, 2 = failures
 *
 * A tool that crashes still produces a syntactically valid envelope so the
 * agent can reason about the failure instead of seeing a stack trace.
 */

import { execFile } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));

const VENDOR_ROOT = path.resolve(HERE, "..", "vendor");
const REPO_LAYOUT = path.resolve(HERE, "..", "..", "..");

/**
 * Development always runs the live repository so an edited auditor takes effect
 * immediately. The published tarball has no repository above it, so it falls
 * back to the staged copy.
 */
function defaultRoot() {
  if (fs.existsSync(path.join(REPO_LAYOUT, "tools"))) return REPO_LAYOUT;
  if (fs.existsSync(path.join(VENDOR_ROOT, "tools"))) return VENDOR_ROOT;
  return REPO_LAYOUT;
}

export const REPO_ROOT = process.env.APPLE_NATIVE_ROOT || defaultRoot();

const PYTHON = process.env.APPLE_NATIVE_PYTHON || "python3";
const DEFAULT_TIMEOUT_MS = Number(process.env.APPLE_NATIVE_TIMEOUT_MS || 180_000);

export class ToolError extends Error {
  constructor(message, { code = "TOOL_ERROR", details } = {}) {
    super(message);
    this.name = "ToolError";
    this.code = code;
    this.details = details;
  }
}

/**
 * Resolve an existing input path against `cwd`. This does not impose a sandbox.
 * Agents pass relative paths most of the time; absolute paths
 * are allowed because a monorepo often lives elsewhere.
 */
export function resolveTarget(input, cwd = process.cwd()) {
  const raw = input && input.trim() ? input : ".";
  const resolved = path.isAbsolute(raw) ? path.normalize(raw) : path.resolve(cwd, raw);
  if (!fs.existsSync(resolved)) {
    throw new ToolError(`Path does not exist: ${resolved}`, { code: "PATH_NOT_FOUND" });
  }
  return resolved;
}

/** Resolve a write destination; the tool creates directories as needed.
 * Like input paths, this is not a filesystem sandbox. MCP clients must approve writes.
 */
export function resolveOutput(input, cwd = process.cwd()) {
  if (typeof input !== "string" || !input.trim() || input.includes("\0")) {
    throw new ToolError("Output path must be a non-empty path", { code: "INVALID_OUTPUT_PATH" });
  }
  return path.resolve(cwd, input);
}

function summarise(envelope) {
  const counts = envelope.summary ?? {};
  const lines = [
    `${envelope.tool} · ${envelope.status?.toUpperCase() ?? "UNKNOWN"}`,
    `target: ${envelope.target}`,
  ];
  if (counts.total !== undefined) {
    lines.push(
      `findings: ${counts.total} (${counts.critical ?? 0} critical, ${counts.error ?? 0} error, ` +
        `${counts.warning ?? 0} warning, ${counts.info ?? 0} info)`,
    );
  }
  const findings = envelope.findings ?? [];
  for (const finding of findings.slice(0, 10)) {
    const location = finding.file ? ` (${finding.file}${finding.line ? ":" + finding.line : ""})` : "";
    lines.push(`  ${finding.severity.toUpperCase()} ${finding.code} — ${finding.message}${location}`);
  }
  if (findings.length > 10) {
    lines.push(`  … ${findings.length - 10} more finding(s)`);
  }
  return lines.join("\n");
}

/**
 * Execute a tool script and return `{ envelope, summary, exitCode }`.
 *
 * `signal` is the MCP request cancellation signal: when the client cancels, the
 * child process is killed instead of being left to finish in the background.
 */
export async function runTool(scriptRelativePath, args = [], { timeoutMs = DEFAULT_TIMEOUT_MS, signal } = {}) {
  const script = path.join(REPO_ROOT, scriptRelativePath);
  if (!fs.existsSync(script)) {
    throw new ToolError(`Tool script is missing: ${script}`, { code: "TOOL_MISSING" });
  }

  return new Promise((resolve, reject) => {
    execFile(
      PYTHON,
      [script, ...args, "--json"],
      { timeout: timeoutMs, maxBuffer: 32 * 1024 * 1024, cwd: REPO_ROOT, signal },
      (error, stdout, stderr) => {
        const trimmed = (stdout || "").trim();
        if (!trimmed) {
          reject(
            new ToolError(`Tool produced no output: ${path.basename(script)}`, {
              code: "TOOL_NO_OUTPUT",
              details: (stderr || "").slice(0, 2000),
            }),
          );
          return;
        }
        let envelope;
        try {
          envelope = JSON.parse(trimmed);
        } catch {
          reject(
            new ToolError(`Tool produced invalid JSON: ${path.basename(script)}`, {
              code: "TOOL_BAD_JSON",
              details: trimmed.slice(0, 2000),
            }),
          );
          return;
        }
        if (error && error.killed) {
          reject(new ToolError(`Tool timed out after ${timeoutMs} ms`, { code: "TOOL_TIMEOUT" }));
          return;
        }
        if (error?.name === "AbortError") {
          reject(new ToolError("Tool run was cancelled by the client", { code: "TOOL_CANCELLED" }));
          return;
        }
        resolve({
          envelope,
          summary: summarise(envelope),
          exitCode: typeof error?.code === "number" ? error.code : 0,
          stderr: (stderr || "").slice(0, 2000),
        });
      },
    );
  });
}

/**
 * Run several independent tools concurrently and collapse their envelopes into
 * one, so an agent can ask "what is wrong with this project?" in a single call
 * instead of eight round trips.
 *
 * Each child result is kept separate under `data.tools`; the merged `findings`
 * list is tagged with the tool that produced it, and the merged `status` is the
 * worst status any child reported.
 */
export async function runToolsParallel(specs, { timeoutMs = DEFAULT_TIMEOUT_MS, signal, onProgress } = {}) {
  let completed = 0;
  const notify = (label, status) => {
    completed += 1;
    try {
      onProgress?.({ completed, total: specs.length, label, status });
    } catch {
      // Progress is a courtesy; it must never break a tool call.
    }
  };
  const settled = await Promise.all(
    specs.map(async (spec) => {
      try {
        const run = await runTool(spec.script, spec.args, { timeoutMs, signal });
        notify(spec.name, run.envelope.status);
        return { name: spec.name, ok: true, ...run };
      } catch (error) {
        notify(spec.name, "error");
        return { name: spec.name, ok: false, error };
      }
    }),
  );

  const severityRank = { pass: 0, warn: 1, fail: 2 };
  let status = "pass";
  const findings = [];
  const tools = {};
  const summary = { critical: 0, error: 0, warning: 0, info: 0, total: 0 };
  const failures = [];

  for (const entry of settled) {
    if (!entry.ok) {
      const code = entry.error?.code ?? "TOOL_ERROR";
      failures.push({ tool: entry.name, code, message: entry.error?.message ?? String(entry.error) });
      status = "fail";
      tools[entry.name] = { status: "fail", error: { code, message: entry.error?.message ?? String(entry.error) } };
      continue;
    }
    const envelope = entry.envelope;
    tools[entry.name] = {
      status: envelope.status,
      summary: envelope.summary,
      exit_code: entry.exitCode,
      data: envelope.data ?? {},
    };
    if ((severityRank[envelope.status] ?? 0) > (severityRank[status] ?? 0)) status = envelope.status;
    for (const key of ["critical", "error", "warning", "info", "total"]) {
      summary[key] += Number(envelope.summary?.[key] ?? 0);
    }
    for (const finding of envelope.findings ?? []) {
      findings.push({ ...finding, tool: entry.name });
    }
  }

  return {
    envelope: {
      schema_version: "2.0",
      tool: "suite",
      tool_version: "2.0.0",
      target: specs[0]?.targetLabel ?? "",
      status,
      summary,
      findings,
      data: { tools, failures },
    },
    summary: `${specs.length} audits · ${status.toUpperCase()} · ${summary.total} finding(s)`,
    exitCode: status === "fail" ? 2 : status === "warn" ? 1 : 0,
  };
}

/**
 * Ask git which files changed, so a review can be scoped to a diff instead of a
 * whole checkout.
 *
 * Returns paths relative to `target`, already filtered to files that still
 * exist (a deletion has nothing to audit).
 */
export async function gitChangedFiles(
  target,
  { base = "HEAD", staged = false, maxFiles = 200, timeoutMs = 30_000 } = {},
) {
  const runGit = (args) =>
    new Promise((resolve, reject) => {
      execFile("git", ["-C", target, ...args], { timeout: timeoutMs, maxBuffer: 8 * 1024 * 1024 }, (error, out, err) => {
        resolve({ error, out: out ?? "", err: (err ?? "").trim() });
      });
    });

  // Detect "not a repository" from git's exit code rather than its message:
  // git is localised, and parsing translated stderr breaks in every non-English
  // locale.
  const inside = await runGit(["rev-parse", "--is-inside-work-tree"]);
  if (inside.error?.code === "ENOENT") {
    throw new ToolError("git is not installed or not on PATH", { code: "GIT_MISSING" });
  }
  if (inside.error || inside.out.trim() !== "true") {
    throw new ToolError(`${target} is not inside a git repository`, { code: "NOT_A_GIT_REPO" });
  }

  const args = ["diff", "--name-only", "--diff-filter=ACMR", "--relative"];
  if (staged) args.push("--cached");
  args.push(base, "--");
  const diff = await runGit(args);
  if (diff.error) {
    throw new ToolError(`git diff failed: ${diff.err.slice(0, 500) || diff.error.message}`, {
      code: "GIT_DIFF_FAILED",
    });
  }

  const files = diff.out
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((file) => fs.existsSync(path.join(target, file)));

  return { files, truncated: files.length > maxFiles, selected: files.slice(0, maxFiles) };
}

/**
 * Run file-scoped auditors across a set of files and merge the results.
 *
 * This is the same merge contract as `runToolsParallel`, with one difference:
 * findings carry the auditor that produced them while `data.files` groups them
 * by path, because a diff review is read per file, not per tool.
 */
export async function runFileMatrix({ target, files, auditors, signal, timeoutMs = DEFAULT_TIMEOUT_MS, onProgress }) {
  const jobs = files.flatMap((file) => auditors.map((auditor) => ({ file, auditor })));
  let completed = 0;
  const notify = (label, status) => {
    completed += 1;
    try {
      onProgress?.({ completed, total: jobs.length, label, status });
    } catch {
      // Progress is a courtesy; it must never break a tool call.
    }
  };
  const settled = await Promise.all(
    jobs.map(async (job) => {
      try {
        const run = await runTool(job.auditor.script, [path.join(target, job.file)], { timeoutMs, signal });
        notify(`${job.file} · ${job.auditor.name}`, run.envelope.status);
        return { ...job, ok: true, ...run };
      } catch (error) {
        notify(`${job.file} · ${job.auditor.name}`, "error");
        return { ...job, ok: false, error };
      }
    }),
  );

  const severityRank = { pass: 0, warn: 1, fail: 2 };
  let status = "pass";
  const findings = [];
  const perFile = {};
  const summary = { critical: 0, error: 0, warning: 0, info: 0, total: 0 };
  const failures = [];

  for (const entry of settled) {
    const bucket = (perFile[entry.file] ??= { status: "pass", findings: 0, auditors: [] });
    if (!entry.ok) {
      const code = entry.error?.code ?? "TOOL_ERROR";
      failures.push({ file: entry.file, tool: entry.auditor.name, code, message: entry.error?.message ?? String(entry.error) });
      bucket.status = "fail";
      status = "fail";
      continue;
    }
    const envelope = entry.envelope;
    bucket.auditors.push(entry.auditor.name);
    if ((severityRank[envelope.status] ?? 0) > (severityRank[bucket.status] ?? 0)) {
      bucket.status = envelope.status;
    }
    bucket.findings += envelope.findings?.length ?? 0;
    if ((severityRank[envelope.status] ?? 0) > (severityRank[status] ?? 0)) status = envelope.status;
    for (const key of ["critical", "error", "warning", "info", "total"]) {
      summary[key] += Number(envelope.summary?.[key] ?? 0);
    }
    for (const finding of envelope.findings ?? []) {
      // Each run is scoped to one file, so the finding's location is that file.
      // Rewriting the basename to the repo-relative path keeps two files with
      // the same name distinguishable in a review.
      findings.push({ ...finding, tool: entry.auditor.name, file: entry.file });
    }
  }

  return {
    envelope: {
      schema_version: "2.0",
      tool: "diff-review",
      tool_version: "2.0.0",
      target,
      status,
      summary,
      findings,
      data: {
        files: perFile,
        file_count: files.length,
        auditors: auditors.map((auditor) => auditor.name),
        failures,
      },
    },
    summary:
      `${files.length} changed file(s) · ${status.toUpperCase()} · ${summary.total} finding(s)` +
      (failures.length ? ` · ${failures.length} auditor failure(s)` : ""),
    exitCode: status === "fail" ? 2 : status === "warn" ? 1 : 0,
  };
}

/** Build the MCP tool result payload from a tool run. */
export function toResult({ envelope, summary, exitCode }) {
  const failed = envelope.status === "fail" || exitCode >= 2;
  const text = `${summary}\n\n${JSON.stringify(envelope, null, 2)}`;
  const result = {
    content: [{ type: "text", text }],
    structuredContent: envelope,
  };
  if (failed) {
    result.isError = true;
  }
  return result;
}

export function errorResult(error) {
  const payload = {
    schema_version: "2.0",
    tool: error.code ?? "TOOL_ERROR",
    status: "fail",
    message: error.message,
    details: error.details ?? null,
  };
  return {
    content: [{ type: "text", text: `Tool execution failed: ${error.message}\n${JSON.stringify(payload, null, 2)}` }],
    isError: true,
  };
}
