# Failure demonstrations

Run each demonstration in a separate disposable branch from a clean passing
commit. Configure a separate Jenkins SCM job to build that branch with publishing
disabled. A main-only job will not see demo branches. Never merge demo changes.

| Gate | Change only this | Expected evidence |
|---|---|---|
| pytest | Change a health test assertion to expect 500 | Test stage red |
| Bandit | Add a temporary app file calling `pickle.loads` on a function input | Static stage red (B301) |
| Dependency | Add a dependency with a database-confirmed fixable CRITICAL CVE to a test requirements file | Trivy filesystem stage red; record CVE, fix and DB date |
| Terraform formatting | Misalign an assignment in a .tf file | IaC stage red at fmt |
| Terraform configuration | Add an insecure Azure storage resource with public access or TLS disabled | IaC stage red; record actual Trivy rule |
| Secret | Commit a synthetic token matching a configured Gitleaks rule | Secret scan red; never use an actual token |
| Newman | Change expected health status to 500 in the collection | Container API stage red and container stopped |

First confirm the fixture triggers the pinned scanner locally; detection depends
on scanner rules and database date. For a deterministic synthetic secret, generate
`'ghp_' + ('A' * 36)` in the disposable branch and, if the provider rule rejects
its entropy, use a disposable Gitleaks config rule with regex `DEMO_TOKEN_[A-Z]{32}`
and a matching clearly fake fixture. Record that a custom demo rule was used.

Capture the failing command, nonzero exit, red stage, and every downstream stage
skipped. With manual delivery, there is no automatic Deploy stage: show that Push
and Manual deployment handoff are skipped and record that no apply occurred.
Remove disposable jobs/branches after saving evidence. No red Jenkins builds have
been claimed or fabricated by the local implementation.
