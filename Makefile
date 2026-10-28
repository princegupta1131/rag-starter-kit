# One-word commands.
#   make setup   install everything (first time)
#   make check   test your database + LLM key
#   make run     start backend + frontend (Ctrl+C stops both)
#   make test    run the tests (add TEST_DATABASE_URL for the database tests)
#   make lint    check code style and types

PYTHON ?= python3
VENV    = backend/.venv/bin

.PHONY: help setup check run backend frontend test lint

help:
	@echo "make setup     install backend + frontend (first time only)"
	@echo "make check     test DATABASE_URL and your LLM key in backend/.env"
	@echo "make run       start backend (:8000) + frontend (:5173)"
	@echo "make test      run tests (set TEST_DATABASE_URL to include database tests)"
	@echo "make lint      ruff (Python) + TypeScript check"

setup:
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
	cd backend && .venv/bin/python -m uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

run:
	@echo "Backend  -> http://localhost:8000/docs"
	@echo "Frontend -> http://localhost:5173   (Ctrl+C stops both)"
	@trap 'kill 0' INT TERM EXIT; \
	$(MAKE) --no-print-directory backend & \
	$(MAKE) --no-print-directory frontend & \
	wait

test:
	cd backend && .venv/bin/python -m pytest -q

lint:
	cd backend && .venv/bin/ruff check .
	cd frontend && npm run typecheck
