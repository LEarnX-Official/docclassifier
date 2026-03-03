.PHONY: help install env migrate run test ollama-pull ollama-serve setup

help:
	@echo ""
	@echo "  DocClassifier — available commands"
	@echo ""
	@echo "  make setup        → full first-time setup (install + env + migrate)"
	@echo "  make install      → pip install all dependencies"
	@echo "  make env          → copy .env.example to .env (skip if .env exists)"
	@echo "  make migrate      → create and apply database migrations"
	@echo "  make run          → start Django dev server on port 8000"
	@echo "  make test         → run all tests"
	@echo "  make ollama-pull  → download the llama3.2 model via Ollama"
	@echo "  make ollama-serve → start the Ollama server (run in separate terminal)"
	@echo ""

install:
	pip install -r requirements.txt

env:
	@if [ -f .env ]; then \
		echo ".env already exists, skipping."; \
	else \
		cp .env.example .env; \
		echo ".env created from .env.example"; \
		echo "Default provider is ollama (no API key needed)."; \
	fi

migrate:
	python manage.py makemigrations documents
	python manage.py migrate

run:
	python manage.py runserver

test:
	pytest

ollama-pull:
	ollama pull llama3.2

ollama-serve:
	ollama serve

setup: install env migrate
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Start Ollama in a separate terminal:  make ollama-serve"
	@echo "  2. Pull the model (first time only):     make ollama-pull"
	@echo "  3. Start the API:                        make run"
	@echo ""
	@echo "Test with:"
	@echo "  curl -X POST http://localhost:8000/api/documents/classify/ -F 'files=@your_doc.pdf'"
	@echo ""
