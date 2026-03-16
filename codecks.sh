#!/usr/bin/env bash
# codecks.sh — Wrapper script for codecks-cli
# Eliminates the need for PYTHONPATH= prefix in every invocation.
# Permission-friendly: whitelist "Bash(*codecks.sh:*)" once.
export PYTHONPATH="C:/Users/USER/GitHubDirectory/codecks-cli"
exec "C:/Users/USER/GitHubDirectory/codecks-cli/.venv/Scripts/python" -m codecks_cli.cli "$@"
