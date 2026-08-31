#!/usr/bin/env bash
# Sentinel — Setup Script
set -euo pipefail

echo "=== Sentinel Setup ==="

echo "[1/3] Installing Python dependencies..."
pip install -r requirements.txt

echo "[2/3] Installing frontend dependencies..."
cd frontend && npm install && cd ..

echo "[3/3] Running health check test..."
python -m pytest backend/tests/test_health.py -v

echo "=== Setup Complete ==="
echo "Start backend:  python -m uvicorn backend.app.main:app --reload"
echo "Start frontend: cd frontend && npm run dev"
