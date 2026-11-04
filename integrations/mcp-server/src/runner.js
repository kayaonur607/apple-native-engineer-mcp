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

/** Repository root: integrations/mcp-server/src -> repository root */
export const REPO_ROOT = path.resolve(process.env.APPLE_NATIVE_ROOT || path.join(HERE, "..", "..", ".."));

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
 * Resolve a user supplied path against `cwd`, rejecting paths that escape a
 * sensible root. Agents pass relative paths most of the time; absolute paths
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
 */
export async function runTool(scriptRelativePath, args = [], { timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  const script = path.join(REPO_ROOT, scriptRelativePath);
  if (!fs.existsSync(script)) {
    throw new ToolError(`Tool script is missing: ${script}`, { code: "TOOL_MISSING" });
  }

  return new Promise((resolve, reject) => {
    execFile(
      PYTHON,
      [script, ...args, "--json"],
      { timeout: timeoutMs, maxBuffer: 32 * 1024 * 1024, cwd: REPO_ROOT },
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
