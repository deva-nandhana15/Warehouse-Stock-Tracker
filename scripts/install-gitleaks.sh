#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# install-gitleaks.sh — download and install Gitleaks
#
# Version pinned: v8.30.1 (latest stable as of 2026-10-24)
# Source: https://github.com/gitleaks/gitleaks/releases
#
# Gitleaks provides SHA256 checksums in the release assets.
# ──────────────────────────────────────────────────────────────
set -euo pipefail

GITLEAKS_VERSION="8.30.1"
GITLEAKS_TAG="v${GITLEAKS_VERSION}"

TARBALL="gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
CHECKSUMS="gitleaks_${GITLEAKS_VERSION}_checksums.txt"
BASE_URL="https://github.com/gitleaks/gitleaks/releases/download/${GITLEAKS_TAG}"

echo "==> Downloading Gitleaks ${GITLEAKS_TAG}..."
curl -fsSL -o "${TARBALL}"   "${BASE_URL}/${TARBALL}"
curl -fsSL -o "${CHECKSUMS}" "${BASE_URL}/${CHECKSUMS}"

echo "==> Verifying SHA256 checksum..."
# Extract the expected checksum for our tarball
EXPECTED=$(grep "${TARBALL}" "${CHECKSUMS}" | awk '{print $1}')
ACTUAL=$(sha256sum "${TARBALL}" | awk '{print $1}')

if [ "${EXPECTED}" != "${ACTUAL}" ]; then
  echo "FATAL: Checksum mismatch!"
  echo "  Expected: ${EXPECTED}"
  echo "  Actual:   ${ACTUAL}"
  exit 1
fi
echo "==> Checksum verified ✓"

echo "==> Extracting and installing Gitleaks..."
tar -xzf "${TARBALL}"
chmod +x gitleaks
mv gitleaks /usr/local/bin/gitleaks

# Clean up
rm -f "${TARBALL}" "${CHECKSUMS}"

echo "==> Gitleaks $(gitleaks version 2>&1) installed successfully"
