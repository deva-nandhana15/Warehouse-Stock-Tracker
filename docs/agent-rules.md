# Rules for the AI agent in Antigravity (paste into the workspace/global rules)

1. Never run `terraform apply` or `terraform destroy`, and never run `az` commands that create,
   modify or delete resources. You may run `terraform fmt`, `init`, `validate`, and `plan` only
   when the user asks. The human runs apply/destroy in their own terminal.
2. Never create, print, read or commit secrets: no tokens, passwords, private keys, `.env`,
   `*.tfvars` (only `*.tfvars.example`), or `terraform.tfstate`.
3. Never use `latest` tags for tools or base images. Pin versions. Before adding a dependency or
   tool version, check the official release page and say what you verified.
4. Security gates must fail the pipeline (non-zero exit). Never add `|| true`, `set +e`,
   `catchError`, or `--exit-code 0` to a scan to make a build pass.
5. Do not claim a command passed unless you ran it and the output shows it. Mark anything
   not run as "NOT TESTED".
6. Do not add deliberately vulnerable code to `main`. Failure demos go on a disposable branch.
7. Keep changes small: one phase at a time, and stop to wait for the user's confirmation.
