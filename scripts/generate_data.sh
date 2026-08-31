#!/usr/bin/env bash
# Generate synthetic dataset
set -euo pipefail
python -m ml.scripts.generate_data "$@"
