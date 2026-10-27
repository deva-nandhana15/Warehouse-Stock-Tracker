#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# install-bandit.sh — install Bandit (Python SAST scanner)
#
# Version pinned: 1.9.4 (latest stable as of 2026-10-24)
# Source: https://github.com/PyCQA/bandit/releases
# ──────────────────────────────────────────────────────────────
set -euo pipefail

BANDIT_VERSION="1.9.4"

echo "==> Installing Bandit ${BANDIT_VERSION}..."
pip install --no-cache-dir "bandit==${BANDIT_VERSION}"

echo "==> Bandit $(bandit --version 2>&1 | head -1) installed successfully"
