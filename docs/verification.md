# Implementation verification

Recorded 2026-10-27, Asia/Calcutta. These results distinguish local checks from
the remaining Jenkins and Azure work. No phase requiring cloud/Jenkins evidence
is marked complete.

## Azure storage implementation update

- Azure CLI confirmed the selected subscription is Enabled; no cloud resources
  have been created by this work.
- Runtime supports Azure Table Storage, managed identity/CLI authentication,
  conditional ETag updates, bounded concurrency retries, and storage readiness.
- 51 unit tests pass, including Azure SDK Int64 decoding, concurrent-update
  conflicts, insufficient stock, storage failure handling and endpoint validation.
- Official Azurite 3.37.0 integration passes: records survive a new Flask/SDK
  instance; concurrent issues do not overdraw stock. Emulator containers removed.
- Docker build passes. Packaged dashboard, assets, UID 10001 and 36 Newman
  assertions pass. This tests the container locally, not Azure runtime identity.
- Cosign 3.1.4 authenticated with Python Sigstore 4.5.1, then Trivy 0.76.1 archive
  verified using its exact GitHub Actions release-workflow identity.
- Trivy filesystem and image gates pass for fixable CRITICAL vulnerabilities.
- Bandit and Gitleaks pass. Terraform formatting/validation pass.
- Terraform security scan FAILS AZU-0012: unrestricted storage-network endpoint.
  No suppression or weakening of the blocking gate has been introduced.
- Owner selected keeping ACI and reviewing networking alternatives before any
  hosting change. No deployable plan/apply or image publication for this change
  has been claimed. The storage-enabled changes remain local pending that choice.
- Follow-up: owner requested keeping the project simple. Gateway/NAT/VNet drafts
  were removed. The simple public ACI + managed-identity Table Storage configuration
  validates. A narrowly scoped AZU-0012 policy exception remains unapproved; all
  existing blocking scan behavior is unchanged.

The table below records the earlier baseline; this update supersedes its local
Docker, Trivy and unit-test entries. Jenkins/Azure deployment evidence is pending.

### Approved simple-deployment release

Owner approved the scoped AZU-0012 network-policy exception on 2026-10-27; it
expires 2026-11-26. The actual Terraform scan now passes with that exception;
51 unit tests, Bandit and Gitleaks pass. Filesystem and built-image Trivy scans
passed for fixable CRITICAL vulnerabilities. No scan exit code was disabled.
The extra temporary scope-probe command was declined and not run. See
security-exceptions.md for the fixed scan-root/path convention and accepted risk.

| Check | Observed result |
|---|---|
| Python | 3.14.3 on this Windows machine |
| Dependencies | Pinned runtime, pytest 9.1.1 and Bandit 1.9.4 installed in .venv |
| pytest | PASS: 37 tests including dashboard and asset serving, reports/junit.xml |
| Bandit | PASS: no MEDIUM/HIGH findings; reports/bandit.json |
| Gitleaks | 8.30.1 ZIP downloaded, published SHA256 verified |
| Local secret scan | PASS: no leaks in project sources; reports/gitleaks.json |
| Terraform | 1.17.0; fmt passes; init downloaded signed AzureRM 5.10.0 |
| Provider lockfile | Generated terraform/.terraform.lock.hcl; retain in Git |
| Terraform validate | PASS: Success! The configuration is valid. |
| PowerShell scripts | All parsed; helper correctly throws on native exit code 7 |
| Newman | 6.2.3; PASS locally against temporary Flask process: 12 requests, 36 assertions |
| npm audit | CRITICAL removed with Handlebars 4.7.10 override; 18 findings remain (7 moderate, 11 high) |
| Docker | Client 28.5.1; Desktop launch attempted; Linux engine pipe remains unavailable |
| Container build/UID/API tests | NOT TESTED: no running Docker engine |
| Base image digest | Retrieved from official Docker registry and pinned in Dockerfile |
| Trivy signature/scans | NOT TESTED: independently verified cosign not installed |
| Java | PATH points to 17; separately verified Temurin Java 21.0.3 installed |
| Jenkins | NOT TESTED: no Jenkins service found; job/plugins/credentials not configured |
| Git | Dedicated project repository initialized for publication to deva-nandhana15/Warehouse-Stock-Tracker; see GitHub for publication status |
| Azure plan/apply/deployed health | NOT RUN: owner account, reviewed plan and cost required |
| Failure demonstrations | Procedure written; real red Jenkins builds/screenshots NOT CAPTURED |
| Teardown | NOT RUN: this implementation created no cloud resources |

The SKU validation regression test rejects a trailing newline, increasing the
guide's original 34 cases to 35; two dashboard/metadata cases bring the total to 37.
Browser checks verified adding an item, issuing stock, insufficient-stock error
handling, receiving stock, search and low-stock filtering against the live Flask
server. Container packaging was updated for templates/assets but still requires
a running Docker engine for verification. Initial Gitleaks directory findings came only from
the downloaded scanner's own README examples. Generated tool/dependency folders
are now explicitly excluded by .gitleaks.toml; application sources remain scanned.
The pipeline scans Git history, which has not yet been tested for a dedicated
project repository.

Remaining owner sequence: get Docker healthy, bootstrap verified cosign and run
Trivy installation/scans, create a dedicated repository and push, configure
Jenkins using Java 21 and the windows agent label, collect green/red builds,
publish the SHA image, review Azure pricing and plan, apply manually, capture
deployed evidence, then tear down manually. See runbook.md for exact commands.
