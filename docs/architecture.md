# Architecture

GitHub -> Jenkins on Windows -> pytest -> Gitleaks -> Bandit and Trivy filesystem
-> Terraform formatting/validation and Trivy config -> Docker build -> Trivy image
-> temporary container smoke and Newman tests -> optional Docker Hub push on main
-> manual Terraform plan/apply -> Azure Container Instances -> deployed health check.

Jenkins polls SCM every five minutes; no public webhook or inbound Jenkins exposure
is required. Configure the build agent with label `windows`. Install verified Trivy
and Gitleaks binaries on its PATH; install Python, Node/npm, Terraform and Docker.
Jenkins creates a local virtual environment and installs Newman with `npm ci`.

The API runs as UID/GID 10001 in one Linux container, with one Gunicorn worker and
four threads. A lock serializes inventory changes. Each worker would have separate
in-memory data, so do not increase worker or replica counts. Restart, redeploy and
rollback reset inventory. There is no database, authentication or TLS termination.
This is a classroom demonstration using synthetic data.

Flask serves the monochrome dashboard at `/` for browser HTML requests, with local
CSS and JavaScript under `/static`. The UI calls the same inventory endpoints,
renders user values as text, and handles API validation failures in the dialog.
Metadata remains available as JSON at `/api` and at `/` for JSON clients. Templates
and assets are packaged in the existing Docker image without an extra build step.

Terraform owns one resource group and one public ACI group with an HTTP liveness
probe. Images must be public for anonymous ACI pulls and tagged with a full commit
SHA. Azure authentication and state remain on the deployment owner's machine.
The pipeline deliberately implements continuous delivery with a manual deployment
handoff; it does not claim automatic cloud deployment.
