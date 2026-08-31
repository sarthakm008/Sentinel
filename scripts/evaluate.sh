#!/usr/bin/env bash
# Evaluate models
set -euo pipefail
python -m ml.scripts.evaluate "$@"
