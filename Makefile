# One-word commands for the RAG Starter Kit.
#   make setup   install everything (first time only)
#   make check   test your database + Gemini key
#   make run     start backend + frontend together (Ctrl+C stops both)

PYTHON ?= python3
VENV    = backend/.venv/bin

.PHONY: help setup check run backend frontend

help:
	@echo "make setup     install backend + frontend (first time only)"
	@echo "make check     test DATABASE_URL and GEMINI_API_KEY in backend/.env"
	@echo "make run       start backend (:8000) + frontend (:5173)"
	@echo "make backend   start only the backend"
	@echo "make frontend  start only the frontend"

setup:
	cd backend && $(PYTHON) -m venv .venv
	$(VENV)/pip install -q --upgrade pip
	$(VENV)/pip install -q -r backend/requirements.txt
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
