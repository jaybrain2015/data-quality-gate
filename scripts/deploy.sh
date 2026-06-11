#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root regardless of where the script is called from
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build"

echo "==> Building Lambda package"
rm -rf "$BUILD"
mkdir -p "$BUILD/package"

# Install the one runtime dependency (pyyaml) into the package
pip install --quiet --target "$BUILD/package" pyyaml

# Copy our source and config alongside it
cp "$ROOT"/src/*.py "$BUILD/package/"
cp "$ROOT/config.yaml" "$BUILD/package/"

# Zip the package contents (not the folder itself)
( cd "$BUILD/package" && zip -qr "$BUILD/function.zip" . )
echo "    built $BUILD/function.zip"

echo "==> Deploying with Terraform"
cd "$ROOT/terraform"
terraform init -input=false
terraform apply -auto-approve
echo "==> Done. Outputs:"
terraform output