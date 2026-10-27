# Threat model

Assets: repository integrity, registry token, Azure identity, Terraform state,
inventory integrity and build evidence. Boundaries: developer to GitHub, GitHub to
Jenkins, Jenkins to Docker Hub, deployment owner to Azure, public client to API.

Azure persistence uses table-scoped managed identity, conditional ETag writes,
TLS 1.2+ and disabled account-key authorization. The owner accepted the public
storage-network endpoint for this classroom demo; see security-exceptions.md for
the exact expiring AZU-0012 exception. This is separate from the other security
gates, which continue to block. Ambiguous stock-update failures require checking
the current quantity before retry because the API has no idempotency keys yet.

| Threat | Control | Residual risk |
|---|---|---|
| Secret committed to Git | Gitleaks history scan, redacted reports, ignored local files | Rotate any exposed credential; deleting commits is insufficient |
| Insecure Python | Bandit blocks MEDIUM and HIGH | Static analysis is incomplete |
| Vulnerable dependency or image | Trivy blocks fixable CRITICAL vulnerabilities | HIGH and unfixed issues remain; databases need network access |
| Unsafe infrastructure | fmt, validate and Trivy HIGH/CRITICAL gate | Static checks do not establish region availability or account permissions |
| Scanner substitution | Exact versions, Trivy cosign identity verification, Gitleaks checksum | Cosign bootstrap must be independently trusted; checksums share release trust |
| Registry compromise | SHA tags, temporary token config, main-only publishing | Tags can be overwritten by an authorized publisher |
| Inventory corruption | Input validation, thread lock, non-root process | Public API has no authorization; use synthetic data only |
| Cloud overspend | Manual plan review, budget alert, owner teardown | Alerts do not cap spending |

The March 2026 Trivy incident is documented by the upstream advisory:
https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23
Pinning alone does not establish authenticity. Both installers require cosign and
verify the archive before extracting. There is no skip-verification option and
the pipeline invokes the scanner binary rather than a moving action tag.

Do not run untrusted pull requests with registry or cloud credentials. Keep Jenkins
local, restrict who may change the Jenkinsfile, patch its plugins, and run its
agent under a dedicated account with Docker access. Docker access is privileged.
