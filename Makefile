# One-word commands.
#   make setup   install everything (first time)
#   make check   test your database + LLM key
#   make run     start backend + frontend (Ctrl+C stops both)
#   make test    run the tests (add TEST_DATABASE_URL for the database tests)
#   make lint    check code style and types
#
# Ports busy? make run BACKEND_PORT=8001 FRONTEND_PORT=5174

# First Python 3.10+ found (macOS's built-in python3 is 3.9, too old)
PYTHON ?= $(shell for p in python3.13 python3.12 python3.11 python3.10 python3; do \
	$$p -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null && echo $$p && break; done)
VENV          = backend/.venv/bin
BACKEND_PORT  ?= 8000
FRONTEND_PORT ?= 5173

.PHONY: help setup check run backend frontend test lint

help:
	@echo "make setup     install backend + frontend (first time only)"
	@echo "make check     test DATABASE_URL and your LLM key in backend/.env"
	@echo "make run       start backend (:$(BACKEND_PORT)) + frontend (:$(FRONTEND_PORT))"
	@echo "make test      run tests (set TEST_DATABASE_URL to include database tests)"
	@echo "make lint      ruff (Python) + TypeScript check"

setup:
	@if [ -z "$(PYTHON)" ]; then echo "❌ Python 3.10 or newer not found. Install it: https://www.python.org/downloads/"; exit 1; fi
	@node -e 'const [a, b] = process.versions.node.split(".").map(Number); process.exit(a > 22 || (a === 22 && b >= 12) || (a === 20 && b >= 19) ? 0 : 1)' 2>/dev/null || \
		{ echo "❌ Node.js 22 needed (or 20.19+). Install it: https://nodejs.org/"; exit 1; }
	@echo "Using $$($(PYTHON) --version) and Node $$(node --version)"
	cd backend && $(PYTHON) -m venv .venv
	$(VENV)/pip install -q --upgrade pip
	$(VENV)/pip install -q -r backend/requirements-dev.txt
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; echo "Created backend/.env"; fi
	cd frontend && npm install --no-audit --no-fund
	@echo ""
	@echo "Done. Next: put DATABASE_URL and GEMINI_API_KEY in backend/.env, then run: make check"

check:
	cd backend && .venv/bin/python check_setup.py

backend:
	cd backend && .venv/bin/python -m uvicorn app.main:app --reload --port $(BACKEND_PORT)

frontend:
	cd frontend && BACKEND_URL=http://localhost:$(BACKEND_PORT) npm run dev -- --port $(FRONTEND_PORT)

run:
	@echo "Backend  -> http://localhost:$(BACKEND_PORT)/docs"
	@echo "Frontend -> http://localhost:$(FRONTEND_PORT)   (Ctrl+C stops both)"
	@trap 'kill 0' INT TERM EXIT; \
	$(MAKE) --no-print-directory backend & \
	$(MAKE) --no-print-directory frontend & \
	wait

test:
	cd backend && .venv/bin/python -m pytest -q

lint:
	cd backend && .venv/bin/ruff check .
	cd frontend && npm run typecheck
