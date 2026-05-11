.PHONY: help install dev build start stop logs clean update test setup-google check free-ports check-docker test-services

# ══════════════════════════════════════════════════════════════════
# Axeng — Makefile
# ══════════════════════════════════════════════════════════════════

help: ## Show this help message
	@echo "Axeng — Engineering Manager Accelerator"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies (Python + system)
	@echo "📦 Installing Python dependencies..."
	@echo ""
	@echo "Note: Python dependencies are installed in Docker."
	@echo "For local development outside Docker, install manually:"
	@echo "  python3 -m venv venv"
	@echo "  source venv/bin/activate"
	@echo "  pip install -r requirements.txt"
	@echo ""
	@echo "System dependencies (install via Homebrew):"
	@echo "  brew bundle    # Installs all dependencies from Brewfile"
	@echo ""
	@echo "Or individually:"
	@echo "  brew install python@3.12 gh git make"
	@echo "  brew install --cask docker"
	@echo ""
	@make setup-env

setup-env: ## Set up .env and config files
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env from template..."; \
		cp .env.example .env; \
		echo "✅ .env created — edit it with your API keys"; \
	else \
		echo "✅ .env already exists"; \
	fi
	@if [ ! -f config/config.yaml ]; then \
		echo "📝 Creating config.yaml from template..."; \
		cp config/config.yaml.example config/config.yaml; \
		echo "✅ config.yaml created — edit it with your team info"; \
	else \
		echo "✅ config.yaml already exists"; \
	fi
	@mkdir -p ~/.hermes/secrets
	@mkdir -p ~/.hermes/skills/productivity/google-workspace/scripts

setup-google: ## Set up Google Workspace authentication
	@echo "🔐 Setting up Google Workspace authentication..."
	@echo ""
	@echo "Prerequisites:"
	@echo "  1. Download OAuth client secret from Google Cloud Console"
	@echo "  2. Save it as ~/.hermes/secrets/google_client_secret.json"
	@echo ""
	@echo "Steps:"
	@echo "  1. Go to: https://console.cloud.google.com/"
	@echo "  2. Create a project (or select existing)"
	@echo "  3. Enable APIs: Calendar API + Gmail API"
	@echo "  4. Create OAuth 2.0 credentials (Desktop app)"
	@echo "  5. Download JSON and save to: ~/.hermes/secrets/google_client_secret.json"
	@echo ""
	@if [ -f ~/.hermes/secrets/google_client_secret.json ]; then \
		echo "✅ Client secret found!"; \
		echo ""; \
		echo "Now run: make test-google"; \
	else \
		echo "⚠️  Client secret not found at ~/.hermes/secrets/google_client_secret.json"; \
	fi

test-google: ## Test Google Workspace authentication (generates token)
	@echo "🧪 Testing Google authentication..."
	@python3 ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py auth test
	@echo ""
	@echo "✅ Google authentication successful!"
	@echo "   Token saved to: ~/.hermes/secrets/google_token.json"

dev: ## Start development environment (Docker)
	@echo "🚀 Starting Axeng in dev mode..."
	@make check-docker
	@make setup-env
	@make free-ports
	docker compose -f docker/docker-compose.yml up

start: ## Start Axeng (background)
	@echo "🚀 Starting Axeng..."
	@make check-docker
	@make setup-env
	@make free-ports
	docker compose -f docker/docker-compose.yml up -d
	@echo ""
	@echo "✅ Axeng is running at http://localhost:8501"
	@echo "   Logs: make logs"
	@echo "   Stop: make stop"

stop: ## Stop Axeng
	@echo "🛑 Stopping Axeng..."
	docker compose -f docker/docker-compose.yml down
	@echo "✅ Axeng stopped"

logs: ## View logs (follow)
	docker compose -f docker/docker-compose.yml logs -f

build: ## Rebuild Docker image
	@echo "🔨 Building Docker image..."
	@make check-docker
	docker compose -f docker/docker-compose.yml build

rebuild: ## Rebuild and restart
	@make build
	@make start

update: ## Pull latest and restart
	@echo "📦 Updating Axeng..."
	git pull
	@make rebuild
	@echo "✅ Axeng updated and running at http://localhost:8501"

clean: ## Remove containers and volumes
	@echo "🧹 Cleaning up..."
	docker compose -f docker/docker-compose.yml down -v
	@echo "✅ Cleaned up"

test: ## Run tests
	@echo "🧪 Running tests..."
	python -m pytest tests/
	@echo "✅ Tests passed"

test-services: ## Test connectivity to all configured services
	@echo "🔌 Testing service connectivity..."
	@python3 test_services.py

# ── Quick start ────────────────────────────────────────────────────
quick-start: install setup-env build start ## Complete setup and start (one command)
	@echo ""
	@echo "🎉 Axeng is ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env with your API keys"
	@echo "  2. Edit config/config.yaml with your team info"
	@echo "  3. (Optional) Set up Google Workspace: make setup-google"
	@echo "  4. Restart: make restart"
	@echo ""
	@echo "Access: http://localhost:8501"

restart: stop start ## Restart Axeng

check: ## Verify setup and dependencies
	@./bin/check-setup

check-docker: ## Check if Docker is running
	@if ! docker ps >/dev/null 2>&1; then \
		echo "❌ Docker is not running"; \
		echo ""; \
		echo "Please start Docker Desktop:"; \
		echo "  • macOS: Open Docker.app or run: open -a Docker"; \
		echo "  • Linux: sudo systemctl start docker"; \
		echo ""; \
		echo "Then try again."; \
		exit 1; \
	fi

free-ports: ## Free required ports (8501) before starting
	@echo "🔍 Checking for processes on port 8501..."
	@PIDS=$$(lsof -ti:8501 2>/dev/null); \
	if [ -n "$$PIDS" ]; then \
		echo "⚠️  Port 8501 is in use by process(es): $$PIDS"; \
		for PID in $$PIDS; do \
			PNAME=$$(ps -p $$PID -o comm= 2>/dev/null || echo "unknown"); \
			echo "   PID $$PID: $$PNAME"; \
		done; \
		echo "🔨 Killing process(es) on port 8501..."; \
		echo "$$PIDS" | xargs kill -9 2>/dev/null || true; \
		sleep 1; \
		if lsof -ti:8501 >/dev/null 2>&1; then \
			echo "❌ Failed to free port 8501"; \
			exit 1; \
		else \
			echo "✅ Port 8501 freed"; \
		fi; \
	else \
		echo "✅ Port 8501 is available"; \
	fi
