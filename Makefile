.PHONY: setup dev-backend dev-frontend test test-backend lint clean

# ── Setup ────────────────────────────────────────────────────────────
setup:
	pip install -r requirements.txt
	cd frontend && npm install

# ── Development ──────────────────────────────────────────────────────
dev-backend:
	python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# ── Testing ──────────────────────────────────────────────────────────
test: test-backend

test-backend:
	python -m pytest backend/tests/ -v

# ── ML Pipeline (Phase 1+) ──────────────────────────────────────────
generate-data:
	python -m ml.scripts.generate_data

train:
	python -m ml.scripts.train

evaluate:
	python -m ml.scripts.evaluate

# ── Cleanup ──────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f sentinel.db
