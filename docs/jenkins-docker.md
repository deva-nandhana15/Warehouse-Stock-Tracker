# Jenkins pipeline in Docker

The default Jenkinsfile now targets the `docker-linux` node label. The earlier
Windows pipeline is retained as `Jenkinsfile.windows` for an explicitly configured
Windows agent. This change does not redeploy the running Azure application.

## Verified run

On 2026-10-29, Docker Jenkins build **#4** completed with **SUCCESS** for commit
`7efedecf4f32a090066c301a189196821519bf8c` in 2 minutes 29 seconds. It passed
51 pytest tests, Gitleaks, Bandit, the configured Trivy dependency/IaC/image gates,
Terraform validation, the dashboard/non-root container checks, 36 Newman
assertions, and Azurite persistence/concurrency integration. Publishing was
disabled, so push and deployment handoff were skipped. Local evidence is in
`reports/jenkins-build-4/`; Jenkins also archives the reports with the build.

On 2026-10-29, build **#7** completed with **SUCCESS**, with `PUBLISH_IMAGE=true`,
for commit `e59fdc2294a1f05ffba942de20c3723179046dc8` in 1 minute 18 seconds.
All tests and configured security gates passed again. Jenkins authenticated using
the owner-entered `dockerhub` credential and pushed
`dva15/warehouse-stock-tracker:e59fdc2294a1f05ffba942de20c3723179046dc8`.
An independent anonymous registry inspection confirmed digest
`sha256:30490ede37e0c61fdb21126ec27169d256373c51adb14170b8bb60a1efcba783`.
Evidence and the manual deployment handoff are in `reports/jenkins-build-7/`.
Azure was not redeployed by this publishing run.

## Local services

`compose.jenkins.yaml` starts Jenkins 2.580.2 and a separate Docker 28.5.1 engine.
Both base images are pinned by digest. Jenkins is exposed only at
http://localhost:8080 . Its jobs/settings and the build engine's image cache use
named volumes. Native Windows Jenkins must remain stopped if still installed.

The build engine is a privileged Docker-in-Docker container, reachable only on the
Compose network using TLS certificates. It is not published to host ports and
does not mount the host Docker socket. The pipeline's temporary app/emulator ports
are on this private engine network. No Azure credentials or host Docker Hub
credentials are mounted into Jenkins.

## Build and start

```powershell
./scripts/prepare-jenkins-tools.ps1
docker compose -f compose.jenkins.yaml build jenkins
docker compose -f compose.jenkins.yaml up -d
```

The preparation helper verifies Trivy's signature with the authenticated Cosign
installation, checks Gitleaks and Terraform archives against upstream checksums,
and pins compatible required plugins from the official update center. Downloaded
archives stay in ignored `jenkins/assets/`, outside the application image context.

## Job and setup

Bootstrap creates a Pipeline-from-SCM job named `Warehouse-Stock-Tracker`, using
the project's public GitHub repository, branch `main`, script path `Jenkinsfile`.
It schedules the first build. Jenkins keeps its standard setup wizard, security
realm and CSRF protection; the bootstrap never reads or prints administrator
passwords. Complete the unlock/admin wizard yourself to view the job in the UI.
Keep the bundled pinned plugins when completing setup. After signing in, open
`Warehouse-Stock-Tracker` and select **Build with Parameters**, leave
`PUBLISH_IMAGE` unchecked, and select **Build** to repeat the verified run.
The job also polls GitHub every five minutes while these containers are running.

To display the initial unlock password in YOUR terminal only, run:

```powershell
docker compose -f compose.jenkins.yaml exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Do not paste that password into chat or Git. The CLI verification file exported
by the build listener contains only job name, build number, result, duration and
URL. This permits checking a build without reading administrator credentials or
making anonymous job access available.

## Stages

Checkout/install -> pytest -> Gitleaks -> Bandit/Trivy dependencies -> Terraform
fmt/init/validate and Trivy IaC -> Docker build -> Trivy image -> UID/dashboard/API
checks and Newman -> Azurite persistence/concurrency integration -> optional push
-> manual deployment handoff. All native failures block later stages. The approved
AZU-0012 exception remains file-scoped and expires 2026-11-26.

The default is `PUBLISH_IMAGE=false`. Push and deployment handoff are skipped
unless enabled. The owner configured credential ID `dockerhub` and publishing
was verified in build #7. On another Jenkins installation, create that credential
using your Docker Hub username/token, then enable publishing for a trusted main
build. Terraform apply and Azure deployment remain separate reviewed operations.

## Stop or restart

```powershell
docker compose -f compose.jenkins.yaml stop
docker compose -f compose.jenkins.yaml start
```

`stop` preserves settings, build evidence and caches. Do not remove named volumes
unless intentionally deleting that local Jenkins data. This is a trusted local
course-project setup with one executor on the controller; production use should
isolate builds on a separate agent and restrict who can change pipeline code.

Official references:
https://www.jenkins.io/doc/book/installing/docker/
https://www.jenkins.io/doc/book/security/controller-isolation/
