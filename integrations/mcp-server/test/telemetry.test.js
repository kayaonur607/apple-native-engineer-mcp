/**
 * Telemetry purity tests.
 *
 * The privacy claim in the README is only worth something if it is enforced by
 * code that fails when someone adds a field. These tests do exactly that: they
 * feed the sanitiser hostile input stuffed with paths, names and prompts, and
 * assert that the closed event shape survives unchanged.
 */

import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, describe, it } from "node:test";

import {
  buildEvent,
  durationBucket,
  previewPayload,
  recordToolRun,
  sanitiseEvent,
  telemetryEndpoint,
  telemetryMode,
  usageFilePath,
} from "../src/telemetry.js";

const EVENT_KEYS = ["schema", "tool", "outcome", "duration_bucket", "day"];

const saved = { ...process.env };
afterEach(() => {
  for (const key of ["APPLE_NATIVE_TELEMETRY", "APPLE_NATIVE_TELEMETRY_URL", "APPLE_NATIVE_USAGE_FILE"]) {
    if (saved[key] === undefined) delete process.env[key];
    else process.env[key] = saved[key];
  }
});

describe("telemetry is off unless explicitly enabled", () => {
  it("defaults to off", () => {
    delete process.env.APPLE_NATIVE_TELEMETRY;
    assert.equal(telemetryMode(), "off");
    assert.equal(recordToolRun({ tool: "lint_swiftui", outcome: "pass", durationMs: 10 }), null);
  });

  it("treats an unrecognised value as off rather than collecting", () => {
    process.env.APPLE_NATIVE_TELEMETRY = "yes";
    assert.equal(telemetryMode(), "off");
  });

  it("requires https for the anonymous endpoint", () => {
    process.env.APPLE_NATIVE_TELEMETRY = "anonymous";
    process.env.APPLE_NATIVE_TELEMETRY_URL = "http://plaintext.example/collect";
    assert.equal(telemetryEndpoint(), null);
    process.env.APPLE_NATIVE_TELEMETRY_URL = "https://collect.example/v1";
    assert.equal(telemetryEndpoint(), "https://collect.example/v1");
  });
});

describe("the event shape is closed", () => {
  it("drops every unexpected field, including hostile ones", () => {
    const event = sanitiseEvent({
      tool: "lint_swiftui",
      outcome: "fail",
      duration_bucket: "150-400ms",
      day: "2026-11-05",
      path: "/Users/someone/SecretClient/App.swift",
      file: "App.swift",
      message: "Hard-coded API key in Settings.swift",
      prompt: "review my unreleased roadmap",
      user: "someone",
      hostname: "macbook-of-someone",
      env: { ASC_PRIVATE_KEY_PATH: "/tmp/key.p8" },
      id: "user-1234",
    });
    assert.deepEqual(Object.keys(event).sort(), [...EVENT_KEYS].sort());
    const serialised = JSON.stringify(event);
    for (const leak of ["Users", "SecretClient", "App.swift", "roadmap", "someone", "key.p8", "user-1234"]) {
      assert.ok(!serialised.includes(leak), `event leaked ${leak}: ${serialised}`);
    }
  });

  it("coerces unknown outcomes to error instead of passing them through", () => {
    assert.equal(sanitiseEvent({ outcome: "catastrophic" }).outcome, "error");
    assert.equal(sanitiseEvent({ outcome: "warn" }).outcome, "warn");
  });

  it("rejects a malformed day", () => {
    assert.match(sanitiseEvent({ day: "yesterday" }).day, /^\d{4}-\d{2}-\d{2}$/);
  });

  it("buckets duration instead of recording milliseconds", () => {
    assert.equal(durationBucket(0), "0-50ms");
    assert.equal(durationBucket(120), "50-150ms");
    assert.equal(durationBucket(250), "150-400ms");
    assert.equal(durationBucket(60_000), "10s+");
    assert.equal(durationBucket(Number.NaN), "unknown");
    assert.equal(buildEvent({ tool: "lint_swiftui", outcome: "pass", durationMs: 120 }).duration_bucket, "50-150ms");
  });
});

describe("local recording", () => {
  it("writes one aggregate line and nothing else", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "anm-telemetry-"));
    const file = path.join(dir, "usage.jsonl");
    process.env.APPLE_NATIVE_TELEMETRY = "local";
    process.env.APPLE_NATIVE_USAGE_FILE = file;

    assert.equal(usageFilePath(), file);
    recordToolRun({
      tool: "lint_swiftui",
      outcome: "warn",
      durationMs: 300,
      knownTools: ["lint_swiftui"],
    });

    const lines = fs.readFileSync(file, "utf8").trim().split("\n");
    assert.equal(lines.length, 1);
    const parsed = JSON.parse(lines[0]);
    assert.deepEqual(Object.keys(parsed).sort(), [...EVENT_KEYS].sort());
    assert.equal(parsed.tool, "lint_swiftui");
    assert.equal(parsed.outcome, "warn");
    fs.rmSync(dir, { recursive: true, force: true });
  });

  it("refuses to record a tool that does not exist", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "anm-telemetry-"));
    const file = path.join(dir, "usage.jsonl");
    process.env.APPLE_NATIVE_TELEMETRY = "local";
    process.env.APPLE_NATIVE_USAGE_FILE = file;

    assert.equal(
      recordToolRun({ tool: "not_a_real_tool", outcome: "pass", durationMs: 1, knownTools: ["lint_swiftui"] }),
      null,
    );
    assert.equal(fs.existsSync(file), false);
    fs.rmSync(dir, { recursive: true, force: true });
  });
});

describe("the preview is the same data that would be written", () => {
  it("contains only the closed event shape plus explanatory metadata", () => {
    process.env.APPLE_NATIVE_TELEMETRY = "local";
    const preview = previewPayload({ tool: "validate_app_icon", outcome: "fail", durationMs: 42 });
    assert.equal(preview.mode, "local");
    assert.deepEqual(Object.keys(preview.sample_event).sort(), [...EVENT_KEYS].sort());
    assert.deepEqual(preview.event_keys, EVENT_KEYS);
    assert.match(preview.note, /ever recorded/i);
  });

  it("reports no file and no endpoint when telemetry is off", () => {
    delete process.env.APPLE_NATIVE_TELEMETRY;
    const preview = previewPayload();
    assert.equal(preview.mode, "off");
    assert.equal(preview.local_file, null);
    assert.equal(preview.endpoint, null);
  });
});
