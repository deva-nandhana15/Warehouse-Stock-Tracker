# Official verification sources

Source checks during implementation, 2026-10-26/27. Actual execution results are
listed separately in verification.md. A source check does not establish a test pass.

| Component | Verified | Official source |
|---|---|---|
| Terraform | Installed and pinned 1.17.0 | https://releases.hashicorp.com/terraform/1.17.0/ |
| AzureRM | Signed provider 5.10.0 downloaded | https://github.com/hashicorp/terraform-provider-azurerm/releases/tag/v5.10.0 |
| ACI | Versioned resource arguments; local validation | https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/v5.10.0/website/docs/r/container_group.html.markdown |
| Trivy | Official latest-release API returned 0.76.1; Windows ZIP/bundle exist | https://github.com/aquasecurity/trivy/releases/tag/v0.76.1 |
| Trivy signer | Release workflow identity pinned to exact tag | https://github.com/aquasecurity/trivy/blob/v0.76.1/.github/workflows/reusable-release.yaml |
| Cosign | Independent bootstrap required | https://docs.sigstore.dev/cosign/system_config/installation/ |
| Gitleaks | Official latest API returned 8.30.1; ZIP checksum verified | https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1 |
| Bandit | Official PyPI API returned 1.9.4 | https://pypi.org/project/bandit/1.9.4/ |
| Flask/Gunicorn/pytest | PyPI APIs confirmed 3.1.3/26.2.0/9.1.1 | https://pypi.org/ |
| Newman | Official npm registry returned 6.2.3 | https://registry.npmjs.org/newman/6.2.3 |
| Handlebars | Patched 4.7.10 verified and audit rechecked | https://registry.npmjs.org/handlebars/4.7.10 |
| Python base | Docker Registry manifest digest recorded in Dockerfile | https://hub.docker.com/_/python |
| Jenkins | Declarative syntax and SCM polling | https://www.jenkins.io/doc/book/pipeline/syntax/ |
| Java | Windows instructions require Java 21 or later | https://www.jenkins.io/doc/book/installing/windows/ |
| Git plugin | Compatibility must be checked in installed update center | https://plugins.jenkins.io/git/ |
| Pipeline plugin | Required suite | https://plugins.jenkins.io/workflow-aggregator/ |
| Credentials plugin | Scoped bindings | https://plugins.jenkins.io/credentials-binding/ |
| JUnit plugin | XML report publisher | https://plugins.jenkins.io/junit/ |

ACI pricing and subscription credit are NOT VERIFIED. The owner must check
https://azure.microsoft.com/pricing/details/container-instances/ before cloud
planning/applying. No plan, apply or destroy was run.
