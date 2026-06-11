#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/terraform"

# S3 won't let Terraform delete a non-empty bucket, so empty it first
BUCKET="$(terraform output -raw landing_bucket 2>/dev/null || true)"
if [ -n "${BUCKET:-}" ]; then
  echo "==> Emptying s3://$BUCKET"
  aws s3 rm "s3://$BUCKET" --recursive || true
fi

echo "==> Destroying infrastructure"
terraform destroy -auto-approve
echo "==> All resources removed."