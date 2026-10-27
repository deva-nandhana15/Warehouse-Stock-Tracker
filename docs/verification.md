# Implementation verification

Recorded 2026-10-27, Asia/Calcutta. These results distinguish local checks from
the remaining Jenkins and Azure work. No phase requiring cloud/Jenkins evidence
is marked complete.

| Check | Observed result |
|---|---|
| Python | 3.14.3 on this Windows machine |
| Dependencies | Pinned runtime, pytest 9.1.1 and Bandit 1.9.4 installed in .venv |
| pytest | PASS: 35 tests, reports/junit.xml |
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
guide's original 34 cases to 35. Initial Gitleaks directory findings came only from
the downloaded scanner's own README examples. Generated tool/dependency folders
are now explicitly excluded by .gitleaks.toml; application sources remain scanned.
The pipeline scans Git history, which has not yet been tested for a dedicated
project repository.

Remaining owner sequence: get Docker healthy, bootstrap verified cosign and run
Trivy installation/scans, create a dedicated repository and push, configure
Jenkins using Java 21 and the windows agent label, collect green/red builds,
publish the SHA image, review Azure pricing and plan, apply manually, capture
deployed evidence, then tear down manually. See runbook.md for exact commands.
