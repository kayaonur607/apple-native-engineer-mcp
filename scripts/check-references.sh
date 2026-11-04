#!/usr/bin/env bash
# Link-integrity only. Kept for compatibility with existing docs and CI.
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/validate_repo.py" --links
