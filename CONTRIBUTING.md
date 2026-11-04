# Contributing

The goal is simple: every rule in this repository should be checkable, and every check should be tested. If you
add an opinion that cannot be verified, it belongs in a reference guide — not in a tool.

---

## The rule for adding a rule

A new finding needs **three** things, or it does not ship:

1. **A finding code** — stable and namespaced (`SWU021`, `A11Y031`, `PRIV022`). Codes are never reused or
   renumbered; retire them instead.
2. **A fixture that reproduces the defect** — add the bad pattern to `tests/fixtures/legacy-app` so the rule has
   something to catch.
3. **A test that asserts it fires** — and, just as important, a test that asserts the clean fixture does **not**
   trip it.

```python
def test_my_new_rule(self):
    envelope = run_tool("swiftui-linter/lint_swiftui.py", str(LEGACY), expect=2)
    self.assertIn("SWU021", codes(envelope))

def test_my_new_rule_has_no_false_positives(self):
    envelope = run_tool("swiftui-linter/lint_swiftui.py", str(CLEAN), expect=0)
    self.assertEqual(envelope["data"]["violations"], 0)
```

A rule without the second test is a rule that will eventually annoy someone into disabling the tool.

---

## Before you open a PR

```bash
./scripts/verify.sh
```

This runs, in order:

| Stage | What it proves |
| :--- | :--- |
| `scripts/validate_repo.py` | Frontmatter, required paths, internal links, and README counts matching the filesystem |
| `python3 -m unittest` | Shared library and every tool, against both fixtures |
| `npm test` | The MCP protocol surface, via a real client/server pair |
| `scripts/verify-swift.sh` | The Swift fixtures type-check and all documentation snippets parse |

Green locally means green in CI, because CI runs the same script.

---

## Style

**Python.** Standard library only. Every tool is a thin CLI over `tools/lib/apple_native/`; if you are writing
analysis logic in a tool instead of the library, move it. Type hints, `from __future__ import annotations`, no
`print()` for anything the caller parses (`--json` owns stdout).

**Findings.** Message = what is wrong and why it matters, in one sentence. `hint` = the exact fix. `docs` = a
working Apple URL. Severity must be honest:

| Severity | Means |
| :--- | :--- |
| `critical` | Guaranteed rejection, crash or data loss |
| `error` | Wrong behaviour or a rule Apple enforces |
| `warning` | Will look or behave wrong for real users |
| `info` | Preference or optimisation |

**JavaScript.** ESM, no new runtime dependencies beyond the MCP SDK and zod. Tools are invoked through
`src/runner.js` — never `exec` a shell string.

**Markdown.** One H1, sentence-case headings, code fences with a language, no personal absolute paths. Links are
validated by CI.

---

## Correcting a factual claim

Apple moves every June. If a reference guide is out of date:

1. Quote the source (Apple documentation URL, WWDC session, or the SDK interface).
2. Update the guide **and** any tool constant that encodes it (for example the iOS 26 glass API table in
   `tools/liquid-glass-auditor/audit_liquid_glass.py`).
3. If the change invalidates a finding code, update the fixture and the test in the same commit.

Claims that cannot be sourced from Apple's documentation, a WWDC session, or the SDK itself do not go in.

---

## Commit messages

Conventional Commits, imperative mood, scoped:

```
feat(swiftui-linter): add SWU022 for timer-in-body
fix(release-readiness): stop scoring uninspected gates as passing
docs(liquid-glass): correct availability to iOS 26
test(accessibility): cover icon-only button labelling
```

---

## Reporting a false positive

Open an issue with:

- the tool and the exact command,
- the finding code,
- the smallest Swift snippet that reproduces it,

A false positive is a bug of the same severity as a missed detection: it teaches users to ignore the tool.
