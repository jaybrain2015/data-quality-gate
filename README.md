# Data Quality Gate

An event-driven data quality gate on AWS. When a CSV file lands in an S3 bucket, a Lambda automatically validates it against configurable quality rules, records the verdict together with the file's metadata and lineage in DynamoDB, and posts a Slack alert if the file fails. The entire infrastructure is defined as code with Terraform and checked by a CI pipeline.

## Why

In regulated environments like banking, bad data flowing downstream into reports and data products is a compliance and reporting risk, not just an inconvenience. A file that arrives nearly empty, missing a required column, or full of blank values can corrupt everything built on top of it. This gate inspects files at the point of arrival and rejects low-quality data before it spreads, producing an auditable record of every decision and why it was made.

## Architecture

A CSV lands in the S3 landing bucket -> S3 triggers the Lambda -> the Lambda parses the file, runs the quality checks, and extracts metadata and lineage -> it writes the verdict to DynamoDB -> and posts a Slack alert if the file failed.

```
CSV -> S3 (landing bucket) -> Lambda (checks) -> DynamoDB (verdict)
                                    \-> Slack (alert on failure)
```

The flow is fully event-driven: nothing runs continuously. The Lambda only executes when a file arrives, so there is no server to maintain and effectively no cost at rest.

## Quality checks

The gate runs three checks, all driven by `config.yaml` so thresholds can be changed without touching code:

- **Row count** - the file must contain at least a minimum number of rows (catches broken or truncated upstream feeds).
- **Required columns** - columns the downstream systems depend on must be present.
- **Null fraction** - critical columns (for example, transaction amount) must not exceed a configured fraction of blank values.

Each check returns a structured result carrying its name, pass/fail, and a human-readable detail, so a failure alert can name exactly what went wrong (e.g. `null_fraction[amount]: 33% null (max 0%)`).

## Project structure

```
data-quality-gate/
├── src/
│   ├── checks.py      # the data quality checks (pure functions, no AWS)
│   ├── metadata.py    # metadata + lineage extraction (pure functions)
│   ├── notify.py      # Slack webhook integration
│   └── handler.py     # Lambda entry point: parse -> check -> store -> alert
├── terraform/
│   ├── main.tf        # S3 bucket, DynamoDB, Lambda, S3->Lambda trigger
│   ├── iam.tf         # least-privilege IAM role and policy for the Lambda
│   ├── variables.tf   # inputs (region, name prefix, Slack webhook)
│   └── outputs.tf     # bucket / table / function names
├── scripts/
│   ├── deploy.sh      # package the Lambda + terraform apply
│   ├── seed.sh        # upload sample CSVs to trigger the gate
│   └── teardown.sh    # empty the bucket + terraform destroy
├── tests/             # pytest suite + good/bad sample CSVs
├── config.yaml        # which checks run and their thresholds
└── .github/workflows/ci.yml   # CI: tests + terraform validate on every PR
```

## How to run

Prerequisites: AWS credentials configured (`aws configure`), Terraform installed, Python 3.12.

```bash
# Deploy all infrastructure to AWS
./scripts/deploy.sh

# Upload the sample CSVs (this triggers the gate)
./scripts/seed.sh

# Read the verdicts back from DynamoDB
aws dynamodb scan --table-name dq-gate-results \
  --query "Items[].{file: source_key.S, passed: passed.BOOL}"

# Remove everything when finished (so it costs nothing)
./scripts/teardown.sh
```

The Slack alert is optional. Set `slack_webhook_url` in `terraform/terraform.tfvars` (git-ignored) to enable failure alerts; without it, the gate runs normally and simply skips notification.

## Design and security decisions

- **Least-privilege IAM.** The Lambda's role grants exactly three things: read objects from the one landing bucket, write items to the one results table, and write its own logs. No wildcards, no access to any other resource. If the function were ever compromised, the blast radius is minimal.
- **No hardcoded secrets.** The Slack webhook URL is supplied through a variable backed by a git-ignored `terraform.tfvars`, marked `sensitive = true` so it never appears in Terraform output or logs.
- **Locked-down bucket.** The landing bucket has all four public-access settings blocked, so it can never accidentally become internet-readable.
- **Separation of concerns.** The check, metadata, and lineage logic are pure functions with no AWS dependencies, so they are unit-testable instantly and for free. All AWS I/O is isolated in a single function in the handler.
- **CI pipeline.** Every pull request automatically runs the test suite and `terraform validate`/`fmt`. Automated deployment on merge is documented in the workflow using OIDC, which issues short-lived credentials at deploy time so no static AWS keys are ever stored in GitHub.
- **Reliable, reproducible deploys.** Bucket names use a Terraform-generated random suffix to guarantee global uniqueness, and provider versions are pinned via a committed lock file so deploys are repeatable.

## Testing

The pure logic is covered by a `pytest` suite (13 tests) exercising the individual checks, the metadata and lineage functions, and the handler's full record-building logic against real good and bad sample CSVs. All tests run locally with no AWS account or network access.