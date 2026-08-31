#!/usr/bin/env bash
# Train models
set -euo pipefail
python -m ml.scripts.train "$@"
