#!/usr/bin/env python3
"""Regenerate the verification transcript inside docs/PROOF.md.

Proof that is typed by hand stops being proof the first time it disagrees with the
run. This script executes `./scripts/verify.sh`, strips ANSI escapes, and replaces
the block between `<!-- proof:begin -->` and `<!-- proof:end -->`.

Usage::

    python3 scripts/update_proof.py            # rewrite the block
    python3 scripts/update_proof.py --check    # fail if it is stale (CI)
"""

from __future__ import annotations

import datetime
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROOF = REPO / "docs" / "PROOF.md"
BEGIN = "<!-- proof:begin -->"
END = "<!-- proof:end -->"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run_verification() -> str:
    proc = subprocess.run(["./scripts/verify.sh"], cwd=REPO, capture_output=True, text=True)
    output = ANSI.sub("", proc.stdout + proc.stderr)
    # Keep the transcript to what a reader needs; drop per-test dots noise.
    lines = [line for line in output.splitlines() if line.strip() != "OK"]
    return "\n".join(lines).strip() + "\n"


def render_block(transcript: str) -> str:
    stamp = datetime.date.today().isoformat()
    return f"""{BEGIN}
Recorded by `./scripts/update_proof.py` on {stamp}. Re-run it after any change that could affect these numbers.

```
{transcript}```
{END}"""


def main(argv: list[str]) -> int:
    text = PROOF.read_text()
    if BEGIN not in text or END not in text:
        print("docs/PROOF.md has no proof markers", file=sys.stderr)
        return 2

    transcript = run_verification()
    block = render_block(transcript)
    updated = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), block, text, flags=re.DOTALL)

    if "--check" in argv:
        if updated != text:
            print("docs/PROOF.md is stale — run python3 scripts/update_proof.py", file=sys.stderr)
            return 1
        print("docs/PROOF.md transcript is current")
        return 0

    PROOF.write_text(updated)
    print(f"updated {PROOF.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
