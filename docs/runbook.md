# Windows implementation and operations

## 0. Owner setup

Confirm course acceptance of ACI, Jenkins, Terraform and Docker Hub. Create the
accounts and an Azure budget alert. Use synthetic inventory data. Install a Java
version supported by your chosen Jenkins LTS (Java 17 here is insufficient for
the current Windows installation requirements). Java 21.0.3 was also found at
`C:/Program Files/Eclipse Adoptium/jdk-21.0.3.9-hotspot`; select this installation
explicitly in Jenkins setup rather than the Java 17 executable on PATH.
Start Docker Desktop using Linux
containers. Verify `git --version`, `python --version`, `docker version`,
`java -version`, `az --version`, `terraform version`, `node --version`, `npm --version`.

Chosen implementation: Windows-native Jenkins with PowerShell, Poll SCM, manual
cloud deployment. No Azure service principal or Azure Jenkins credentials are
needed for this mode. Fully automatic deployment is not implemented.

## 1. Application and container

Run from the project root in PowerShell:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt -r requirements-security.txt
./.venv/Scripts/python.exe -m pytest -q --junitxml=reports/junit.xml
npm.cmd ci --ignore-scripts
docker build -f docker/Dockerfile -t warehouse-stock-tracker:dev .
./scripts/test-container.ps1 -Image warehouse-stock-tracker:dev
```

The container helper binds a random loopback port, waits for health, checks UID
10001, executes Newman, and stops only the container it created in a finally block.
For development use `./.venv/Scripts/python.exe app/app.py` and, in another terminal,
`npm.cmd run test:api`. Gunicorn runs inside Linux containers, not Windows.

## 2. Terraform validation

```powershell
terraform -chdir=terraform fmt -check
terraform -chdir=terraform init -backend=false -input=false
terraform -chdir=terraform validate
```

Commit `.terraform.lock.hcl`. Do not commit state, real tfvars or saved plans.
Terraform is pinned to 1.17.0 and AzureRM to 5.10.0. Validation needs no Azure login.

## 3. Security tools

Independently install and verify cosign following
https://docs.sigstore.dev/cosign/system_config/installation/ . Then run:

```powershell
./scripts/install-trivy.ps1 -CosignPath 'C:/path/to/verified/cosign.exe'
./scripts/install-gitleaks.ps1
./scripts/install-bandit.ps1
$env:PATH = "$PWD/.tools/trivy;$PWD/.tools/gitleaks;$env:PATH"
./.venv/Scripts/python.exe -m bandit -r app -ll
gitleaks git . --redact
trivy fs --scanners vuln --skip-dirs .venv,node_modules,.tools,.terraform --severity CRITICAL --ignore-unfixed --exit-code 1 .
trivy config --severity HIGH,CRITICAL --exit-code 1 terraform
```

Provision scanners on the Jenkins agent's PATH too. Restart the agent after PATH
changes. Native PowerShell does not automatically propagate executable failures;
the pipeline's `Invoke-Checked` helper throws for every nonzero native exit code.

## 4. Git and Jenkins

This project uses a dedicated Git repository on `main`:
https://github.com/deva-nandhana15/Warehouse-Stock-Tracker . Configure Jenkins with
this repository and script path `Jenkinsfile`. Do not publish credentials or local reports.
Install Jenkins LTS locally and use its setup wizard yourself. Configure a Windows
agent with label `windows` and Docker access. Required plugins: Git (`git`), Pipeline
(`workflow-aggregator`), Credentials Binding (`credentials-binding`), JUnit (`junit`).
Use the installed Jenkins update center to select compatible releases; actual
plugin compatibility is not tested until Jenkins is installed.

Create a Pipeline from SCM for `*/main`, script path `Jenkinsfile`. Poll SCM is
declared as `H/5 * * * *`. For a multibranch job, use the same Jenkinsfile. Begin
with `PUBLISH_IMAGE=false`. After every gate passes, create a username/password
credential ID `dockerhub` using a scoped Docker Hub token, choose your public
`IMAGE_REPOSITORY`, and enable publishing. Enter token values in Jenkins yourself.
The build never applies Terraform. A successful published build archives the image
reference in `deployment.txt`. A failed gate prevents later stages, including push
and deployment handoff.

## 5. Owner deployment and rollback

After a scanned image is published, run these commands yourself. Review current
ACI pricing, subscription and quota before saving and applying a plan.

```powershell
az login
az account show
Copy-Item terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit the local file: subscription ID, unique DNS label, your public image,
# and the exact 40-character SHA from a successful published build.
terraform -chdir=terraform init
terraform -chdir=terraform plan -out=tfplan
# Read the plan and approve its resources and cost before continuing.
terraform -chdir=terraform apply tfplan
terraform -chdir=terraform output -raw app_url
./scripts/wait-health.ps1 -BaseUrl 'http://YOUR-FQDN:5000'
Invoke-RestMethod 'http://YOUR-FQDN:5000/'
```

Check the version endpoint matches the released SHA. For rollback, select a
previously scanned and published SHA, change only the image tag in local inputs,
review a fresh plan and apply it yourself. Rollback resets in-memory inventory.
Avoid concurrent local deployments; state is local. Production use needs encrypted
remote state, locking, authenticated HTTPS access and persistent storage.

## 6. Gate demonstrations

Follow `gate-demonstrations.md`; capture real Jenkins results, not simulated logs.

## 7. Teardown (owner only)

Save evidence, inspect the selected subscription and Terraform state, then run
`terraform -chdir=terraform plan -destroy` and review what will be deleted. Run
`terraform -chdir=terraform destroy` yourself after approval. Confirm in Azure that
the resource group and public address are gone. Revoke the registry token and
remove temporary Jenkins credentials. Budget alerts do not stop charges.
