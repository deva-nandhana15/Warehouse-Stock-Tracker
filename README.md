# Warehouse Stock Tracker

Repository: [deva-nandhana15/Warehouse-Stock-Tracker](https://github.com/deva-nandhana15/Warehouse-Stock-Tracker)

Live Azure application: http://warehouse-devanandhana15.centralindia.azurecontainer.io:5000

Azure deployment and persistence across a container restart were verified on
2026-10-29. Jenkins installation and a real pipeline run remain pending.

A Flask inventory API with a Windows-native Jenkins DevSecOps delivery pipeline,
Docker packaging, Newman API tests and Terraform for Azure Container Instances.

Start with [the step-by-step runbook](docs/runbook.md). Actual results and pending
setup are in [verification](docs/verification.md). Cloud deployment is manual:
Jenkins tests, scans and optionally publishes, then produces a deployment handoff.
It never runs Terraform apply or destroy.

## Quick start (PowerShell)

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt -r requirements-security.txt
./.venv/Scripts/python.exe -m pytest -q --junitxml=reports/junit.xml
npm.cmd ci --ignore-scripts
./.venv/Scripts/python.exe scripts/test-local-api.py
```

Once Docker Desktop is running with Linux containers:

```powershell
docker build -f docker/Dockerfile -t warehouse-stock-tracker:dev .
./scripts/test-container.ps1 -Image warehouse-stock-tracker:dev
```

## Dashboard

Run `./.venv/Scripts/python.exe app/app.py`, then open http://127.0.0.1:5000 in a
browser. The monochrome dashboard includes inventory totals, search, a low-stock
view, an add-item form, and receive/issue dialogs. All changes use the Flask API.
If an older server is already running, stop it and restart to load the dashboard.
The UI has no external fonts, frameworks or CDN dependencies and is included in
the same Docker container. It adapts to smaller screens with a scrollable table.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health status |
| GET | `/` | Dashboard for browsers; JSON metadata for JSON clients |
| GET | `/api` | Application name and APP_VERSION, always JSON |
| GET | `/items` | Sorted inventory |
| POST | `/items` | Add {sku, name, quantity?, reorder_level?} |
| POST | `/items/<sku>/receive` | Stock in {quantity>0} |
| POST | `/items/<sku>/issue` | Stock out; 409 if insufficient |
| GET | `/alerts/low-stock` | Items at or below reorder level |

Local inventory defaults to memory and resets on restart. Azure mode persists data
in Table Storage. The public app has no authentication or HTTPS front end; use
synthetic classroom data only.

Azure persistent storage support is now implemented. `STORAGE_BACKEND=azure-table`
uses Azure Table Storage with managed identity in ACI; local runs still default
to memory. See [Azure deployment](docs/azure-deployment.md). The current draft
Terraform storage-network finding AZU-0012 has an owner-approved, file-scoped
exception expiring 2026-11-26. See [the accepted risk](docs/security-exceptions.md).
All other security gates remain blocking. The current Azure deployment is live;
future infrastructure changes require reviewing a fresh Terraform plan.

## Pipeline

Checkout -> pytest -> Gitleaks -> Bandit/Trivy filesystem -> Terraform checks and
Trivy config -> Docker build -> Trivy image -> container smoke/Newman -> optional
main-only push -> manual deployment handoff. Native executable failures stop the
stage. Reports are archived on failure too. Docker Hub credentials use Jenkins ID
`dockerhub`, bound only during optional publication. Configure agent label `windows`.

Bandit blocks MEDIUM/HIGH; Trivy vulnerability scans block fixable CRITICAL;
Trivy config blocks HIGH/CRITICAL; Gitleaks blocks detected secrets. Unfixed and
HIGH vulnerabilities remain residual risks. Trivy must pass cosign verification
before installation. See [the threat model](docs/threat-model.md).

Pinned tools: Terraform 1.17.0, AzureRM 5.10.0, AzAPI 2.13.0, Bandit 1.9.4, Trivy 0.76.1,
Gitleaks 8.30.1, Newman 6.2.3. Python dependencies are pinned in requirements files.
The Python base image uses a registry digest; npm/Terraform lockfiles are included.
See [official verification sources](docs/sources.md).

Newman's dependency tree retains HIGH/MODERATE advisories. Handlebars is overridden
to patched 4.7.10 to remove the detected CRITICAL advisory. Do not blindly run
`npm audit fix --force`: it suggests a major Newman downgrade. Test-tool dependencies
are excluded from the application Docker context.

## Documentation

- [Architecture](docs/architecture.md)
- [Deployment, rollback and teardown](docs/runbook.md)
- [Failure demonstrations](docs/gate-demonstrations.md)
- [Evidence checklist](docs/evidence-checklist.md)

Do not commit credentials, real tfvars, Terraform state or saved plans. Finish the
owner setup and collect real Jenkins/Azure evidence before claiming full completion.
