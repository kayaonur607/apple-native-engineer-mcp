/**
 * `review_diff` — audits only the files a change touched.
 *
 * The value of this tool is scope, so the tests build a throwaway git repository
 * with a committed baseline and a modified file, then assert three things: clean
 * code passes, the introduced defect is caught, and untouched files are never
 * re-audited.
 */

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { after, before, describe, it } from "node:test";

import { TOOL_SPECS } from "../src/tools.js";

const reviewDiff = TOOL_SPECS.find((spec) => spec.name === "review_diff");

const CLEAN = `import SwiftUI

struct ContentView: View {
    var body: some View {
        NavigationStack {
            Text("Hello")
                .foregroundStyle(.primary)
        }
    }
}
`;

const DIRTY = `import SwiftUI

struct ContentView: View {
    var body: some View {
        NavigationView {
            Text("Hello")
                .foregroundColor(Color(hex: "#FF0000"))
        }
    }
}
`;

function git(cwd, ...args) {
  return execFileSync("git", args, {
    cwd,
    encoding: "utf8",
    env: {
      ...process.env,
      GIT_AUTHOR_NAME: "Test",
      GIT_AUTHOR_EMAIL: "test@example.com",
      GIT_COMMITTER_NAME: "Test",
      GIT_COMMITTER_EMAIL: "test@example.com",
    },
  });
}

describe("review_diff", () => {
  let repo;

  before(() => {
    repo = fs.mkdtempSync(path.join(os.tmpdir(), "anm-diff-"));
    fs.mkdirSync(path.join(repo, "App"), { recursive: true });
    fs.writeFileSync(path.join(repo, "App", "ContentView.swift"), CLEAN);
    fs.writeFileSync(path.join(repo, "App", "Untouched.swift"), DIRTY);
    git(repo, "init", "-q");
    git(repo, "add", ".");
    git(repo, "commit", "-qm", "baseline");
  });

  after(() => {
    fs.rmSync(repo, { recursive: true, force: true });
  });

  it("reports nothing when the working tree is clean", async () => {
    const run = await reviewDiff.run({ path: repo });
    assert.equal(run.envelope.tool, "diff-review");
    assert.equal(run.envelope.status, "pass");
    assert.equal(run.envelope.findings.length, 0);
    assert.equal(run.envelope.data.note, "No changes to review.");
  });

  it("catches only the defect introduced by the change", async () => {
    fs.writeFileSync(path.join(repo, "App", "ContentView.swift"), DIRTY);
    const run = await reviewDiff.run({ path: repo });
    const envelope = run.envelope;

    assert.equal(envelope.status, "fail");
    const codes = envelope.findings.map((finding) => finding.code);
    assert.ok(codes.includes("SWU003"), `expected SWU003 (NavigationView), got ${codes.join(",")}`);

    // Scope is the point: the untouched file already contained the same defect
    // in the baseline, and must not appear.
    const files = Object.keys(envelope.data.files);
    assert.deepEqual(files, ["App/ContentView.swift"]);
    for (const finding of envelope.findings) {
      assert.equal(finding.file, "App/ContentView.swift");
      assert.ok(["swiftui-linter", "accessibility-auditor", "liquid-glass-auditor"].includes(finding.tool));
    }
    assert.ok(!JSON.stringify(envelope).includes("Untouched.swift"));

    // Restore the baseline for the next test.
    fs.writeFileSync(path.join(repo, "App", "ContentView.swift"), CLEAN);
  });

  it("passes when the change is clean even though the project is not", async () => {
    fs.appendFileSync(path.join(repo, "App", "ContentView.swift"), "\n// touch\n");
    const run = await reviewDiff.run({ path: repo });
    assert.equal(run.envelope.status, "pass");
    assert.deepEqual(Object.keys(run.envelope.data.files), ["App/ContentView.swift"]);
  });

  it("reviews the index when staged is set", async () => {
    fs.writeFileSync(path.join(repo, "App", "ContentView.swift"), DIRTY);
    git(repo, "add", "App/ContentView.swift");
    const run = await reviewDiff.run({ path: repo, staged: true });
    assert.ok(run.envelope.findings.some((finding) => finding.code === "SWU003"));
    fs.writeFileSync(path.join(repo, "App", "ContentView.swift"), CLEAN);
    git(repo, "add", "App/ContentView.swift");
  });

  it("says so instead of failing when the diff contains no Swift", async () => {
    fs.writeFileSync(path.join(repo, "notes.md"), "hello\n");
    git(repo, "add", "notes.md");
    const run = await reviewDiff.run({ path: repo });
    assert.equal(run.envelope.status, "pass");
    assert.match(run.envelope.data.note, /none of them Swift/);
    fs.rmSync(path.join(repo, "notes.md"));
    git(repo, "rm", "-q", "--cached", "notes.md");
  });

  it("explains that a non-repository directory cannot be diffed", async () => {
    const plain = fs.mkdtempSync(path.join(os.tmpdir(), "anm-nogit-"));
    await assert.rejects(() => reviewDiff.run({ path: plain }), (error) => error.code === "NOT_A_GIT_REPO");
    fs.rmSync(plain, { recursive: true, force: true });
  });
});

describe("check_environment", () => {
  it("reports the runtime it actually found", async () => {
    const spec = TOOL_SPECS.find((entry) => entry.name === "check_environment");
    const run = await spec.run({});
    assert.equal(run.envelope.tool, "environment-check");
    const ids = run.envelope.data.checks.map((check) => check.id);
    for (const expected of ["node", "python", "auditors", "references", "git", "telemetry"]) {
      assert.ok(ids.includes(expected), `missing check: ${expected}`);
    }
    const node = run.envelope.data.checks.find((check) => check.id === "node");
    assert.match(node.message, /^Node \d+\./);
    assert.ok(!JSON.stringify(run.envelope).includes("ASC_PRIVATE_KEY="), "credentials must never be echoed");
  });
});
