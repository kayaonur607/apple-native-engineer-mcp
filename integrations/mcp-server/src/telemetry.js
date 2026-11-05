/**
 * Privacy-preserving usage accounting.
 *
 * Why this exists: the server gets better when we know which tools people
 * actually call and which of them fail. That is the only question we need to
 * answer, so that is the only question we are allowed to ask.
 *
 * Hard rules, enforced by `sanitiseEvent` and by `test/telemetry.test.js`:
 *
 *   - **Off by default.** `APPLE_NATIVE_TELEMETRY` must be explicitly set to
 *     `local` or `anonymous`. Unset means nothing is written and nothing is sent.
 *   - **No user data.** Never recorded: project paths, file names, source text,
 *     finding messages, prompts, environment variables, credentials, machine
 *     name, user name, or a stable identifier of any kind.
 *   - **Aggregate shape only.** An event is a fixed, closed set of fields:
 *     tool id, outcome, duration bucket, schema version, and a UTC day.
 *   - **Local by default when enabled.** `local` appends to a JSONL file the
 *     user owns and can delete. `anonymous` additionally posts the same
 *     aggregate events to an endpoint the user configures; there is no default
 *     endpoint and therefore no phone-home.
 *   - **Inspectable.** `--telemetry-preview` prints the exact payload. If it
 *     ever contains a field you did not expect, that is a bug.
 *   - **Never blocks.** All I/O is fire-and-forget; a failure is swallowed. A
 *     metrics outage must never fail a tool call.
 */

import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const MODES = new Set(["off", "local", "anonymous"]);
const MAX_BATCH = 50;

/** Closed allowlist of event keys. Anything else is dropped before write/send. */
const EVENT_KEYS = Object.freeze(["schema", "tool", "outcome", "duration_bucket", "day"]);

const DURATION_BUCKETS = [
  [50, "0-50ms"],
  [150, "50-150ms"],
  [400, "150-400ms"],
  [1000, "400ms-1s"],
  [3000, "1-3s"],
  [10000, "3-10s"],
  [Infinity, "10s+"],
];

export const TELEMETRY_SCHEMA = 1;

export function telemetryMode() {
  const raw = (process.env.APPLE_NATIVE_TELEMETRY || "off").trim().toLowerCase();
  if (MODES.has(raw)) return raw;
  // An unrecognised value must never silently enable collection.
  return "off";
}

export function telemetryEndpoint() {
  const raw = (process.env.APPLE_NATIVE_TELEMETRY_URL || "").trim();
  if (!raw) return null;
  try {
    const url = new URL(raw);
    return url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}

export function usageFilePath() {
  const explicit = process.env.APPLE_NATIVE_USAGE_FILE;
  if (explicit && explicit.trim()) return explicit.trim();
  const base = process.env.XDG_DATA_HOME || path.join(os.homedir(), ".local", "share");
  return path.join(base, "apple-native-engineer", "usage.jsonl");
}

export function durationBucket(ms) {
  if (!Number.isFinite(ms) || ms < 0) return "unknown";
  for (const [limit, label] of DURATION_BUCKETS) {
    if (ms < limit) return label;
  }
  return "10s+";
}

export function utcDay(date = new Date()) {
  return date.toISOString().slice(0, 10);
}

/**
 * Reduce an arbitrary object to the closed event shape. This is the security
 * boundary: callers may pass whatever they like, only these five fields survive.
 */
export function sanitiseEvent(input = {}) {
  const clean = {
    schema: TELEMETRY_SCHEMA,
    tool: typeof input.tool === "string" ? input.tool.slice(0, 64) : "unknown",
    outcome: ["pass", "warn", "fail", "error"].includes(input.outcome) ? input.outcome : "error",
    duration_bucket: DURATION_BUCKETS.some(([, label]) => label === input.duration_bucket)
      ? input.duration_bucket
      : "unknown",
    day: /^\d{4}-\d{2}-\d{2}$/.test(input.day || "") ? input.day : utcDay(),
  };
  const sanitised = {};
  for (const key of EVENT_KEYS) sanitised[key] = clean[key];
  return sanitised;
}

export function buildEvent({ tool, outcome, durationMs }) {
  return sanitiseEvent({ tool, outcome, duration_bucket: durationBucket(durationMs), day: utcDay() });
}

/** Only tools that exist are ever counted, so a typo cannot pollute the aggregate. */
export function recordToolRun({ tool, outcome, durationMs, knownTools }) {
  const mode = telemetryMode();
  if (mode === "off") return null;
  if (Array.isArray(knownTools) && !knownTools.includes(tool)) return null;

  const event = buildEvent({ tool, outcome, durationMs });
  if (mode === "local" || mode === "anonymous") appendLocal(event);
  if (mode === "anonymous") sendBatch([event]);
  return event;
}

function appendLocal(event) {
  try {
    const file = usageFilePath();
    fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
    fs.appendFileSync(file, `${JSON.stringify(event)}\n`, { mode: 0o600 });
  } catch {
    // Metrics must never break a tool call.
  }
}

function sendBatch(events) {
  const endpoint = telemetryEndpoint();
  if (!endpoint || events.length === 0) return;
  const body = JSON.stringify({ schema: TELEMETRY_SCHEMA, events: events.slice(-MAX_BATCH) });
  // Fire and forget: no await, no unhandled rejection.
  Promise.resolve()
    .then(() =>
      fetch(endpoint, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body,
        signal: AbortSignal.timeout(3000),
      }),
    )
    .catch(() => {});
}

/**
 * The exact bytes that `local` would write and `anonymous` would send.
 * Used by `--telemetry-preview` so the claim is inspectable rather than trusted.
 */
export function previewPayload({ tool = "lint_swiftui", outcome = "warn", durationMs = 320 } = {}) {
  return {
    mode: telemetryMode(),
    local_file: telemetryMode() === "off" ? null : usageFilePath(),
    endpoint: telemetryEndpoint(),
    sample_event: buildEvent({ tool, outcome, durationMs }),
    event_keys: [...EVENT_KEYS],
    note: "No path, file name, source text, finding, prompt, credential or identifier is ever recorded.",
  };
}
