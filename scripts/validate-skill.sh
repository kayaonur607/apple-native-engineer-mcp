#!/usr/bin/env bash
# Thin wrapper kept for compatibility with existing docs and CI.
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/validate_repo.py" "$@"
