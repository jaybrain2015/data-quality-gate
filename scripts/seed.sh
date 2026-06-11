#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/terraform"

BUCKET="$(terraform output -raw landing_bucket)"
echo "==> Uploading samples to s3://$BUCKET/incoming/"

aws s3 cp "$ROOT/tests/sample_data/good.csv" "s3://$BUCKET/incoming/good.csv"
aws s3 cp "$ROOT/tests/sample_data/bad.csv"  "s3://$BUCKET/incoming/bad.csv"

echo "==> Done. Check the verdicts:"
TABLE="$(terraform output -raw results_table)"
echo "    aws dynamodb scan --table-name $TABLE"