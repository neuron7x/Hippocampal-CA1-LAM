#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

for version in 3.11 3.12 3.13; do
    uv pip compile --generate-hashes --only-binary :all: --python-version "$version" \
        --python-platform x86_64-manylinux_2_28 ci/requirements.in \
        --output-file "ci/requirements-${version}.txt" "$@"
done
