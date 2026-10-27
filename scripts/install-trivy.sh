#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# install-trivy.sh — download, verify, and install Trivy
#
# Version pinned: v0.76.1 (latest stable as of 2026-10-24)
# Source: https://github.com/aquasecurity/trivy/releases
#
# SECURITY: We verify the binary's cosign signature per the
# official Trivy docs to defend against supply-chain attacks.
# Trivy suffered a supply-chain compromise on 2026-03-19
# (v0.69.4 + trivy-action tags repointed by attacker "TeamPCP").
# We therefore:
#   1. Pin an exact version (never "latest")
#   2. Verify the Sigstore bundle with cosign
#   3. Never use trivy-action (per project policy)
# ──────────────────────────────────────────────────────────────
set -euo pipefail

TRIVY_VERSION="0.76.1"               # pin exact version
TRIVY_TAG="v${TRIVY_VERSION}"
ARCH="Linux-64bit"

TARBALL="trivy_${TRIVY_VERSION}_${ARCH}.tar.gz"
BUNDLE="${TARBALL}.sigstore.json"
BASE_URL="https://github.com/aquasecurity/trivy/releases/download/${TRIVY_TAG}"

echo "==> Downloading Trivy ${TRIVY_TAG}..."
curl -fsSL -o "${TARBALL}" "${BASE_URL}/${TARBALL}"
curl -fsSL -o "${BUNDLE}"  "${BASE_URL}/${BUNDLE}"

# ── Cosign verification (keyless, Sigstore bundle) ──────────
# Requires an independently verified cosign installation; never bootstrap blindly.
command -v cosign >/dev/null || { echo 'Install and verify cosign first'; exit 1; }

  echo "==> Verifying Trivy binary signature with cosign..."
  cosign verify-blob "${TARBALL}" \
    --bundle "${BUNDLE}" \
    --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
    --certificate-identity="https://github.com/aquasecurity/trivy/.github/workflows/reusable-release.yaml@refs/tags/${TRIVY_TAG}"

  echo "==> Signature verification PASSED ✓"

# ── Install ─────────────────────────────────────────────────
echo "==> Extracting and installing Trivy..."
tar -xzf "${TARBALL}"
chmod +x trivy
mv trivy /usr/local/bin/trivy

# Clean up
rm -f "${TARBALL}" "${BUNDLE}"

echo "==> Trivy $(trivy --version 2>&1 | head -1) installed successfully"
