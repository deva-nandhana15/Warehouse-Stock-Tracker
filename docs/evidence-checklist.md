# Submission evidence

Only check a box after observing actual output. Local verification results are
recorded in `verification.md`; generated reports are excluded from Git.

- [ ] Instructor confirms stack and assignment title; student name and number filled in
- [ ] Accounts ready, budget alert configured, subscription and quota checked
- [ ] Required tool versions, supported Java and running Docker daemon
- [ ] Passing pytest report
- [ ] Container health and UID 10001
- [ ] Signed Trivy verification, scanner versions, first scan outputs
- [ ] Terraform fmt/init/validate and committed provider lockfile
- [ ] Newman output against built container
- [ ] Jenkins plugins compatible with installed LTS and green build with all gates
- [ ] Red build for each failure demonstration, later stages skipped
- [ ] SHA-tagged scanned image published to Docker Hub
- [ ] Reviewed Azure plan and current pricing before owner apply
- [ ] Deployed health and matching version response; Azure resource group screenshot
- [ ] Final screenshots saved before owner destroy
- [ ] Azure empty after teardown; temporary credentials revoked
