# AWS Sidekick - Simple Makefile

.PHONY: help setup api api-dev client client-build full-dev clean test add remove update

# Default target
help:
	@echo "AWS Sidekick"
	@echo "============"
	@echo ""
	@echo "Setup:"
	@echo "  make setup      - Setup everything (venv + deps + client)"
	@echo ""
	@echo "Development:"
	@echo "  make api        - Start API server"
	@echo "  make api-dev    - Start API with hot reload"
	@echo "  make client     - Start Vue.js client"
	@echo "  make full-dev   - Start both API and client"
	@echo ""
	@echo "Build:"
	@echo "  make client-build - Build client for production"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean      - Clean cache files"
	@echo "  make test       - Run tests"
	@echo "  make add PACKAGE=name    - Add Python package"
	@echo "  make remove PACKAGE=name - Remove Python package"
	@echo "  make update     - Update all dependencies"

# Setup everything
setup:
	@echo "🚀 Setting up AWS Sidekick..."
	@echo "📦 Creating venv and syncing Python dependencies..."
	@uv sync
	@echo "📦 Installing client dependencies..."
	@cd client && pnpm i
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy example.env to .env and add your API keys"
	@echo "2. Run 'make full-dev' to start development"

# Start API server
api:
	@echo "🚀 Starting API server..."
	@uv run --project . python api.py

# Start API server with hot reload
api-dev:
	@echo "🚀 Starting API server (development mode)..."
	@DEBUG=true uv run --project . python api.py

# Start Vue.js client
client:
	@echo "🚀 Starting Vue.js client..."
	@cd client && pnpm run dev

# Build Vue.js client
client-build:
	@echo "🏗️ Building Vue.js client..."
	@cd client && pnpm run build

# Start both API and client
full-dev:
	@echo "🚀 Starting full development environment..."
	@echo "API: http://localhost:8000"
	@echo "Client: http://localhost:3000"
	@echo "Press Ctrl+C to stop both services"
	@(trap 'kill 0' SIGINT; make api-dev & make client & wait)

# Clean cache files
clean:
	@echo "🧹 Cleaning cache files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .uv_cache 2>/dev/null || true
	@cd client && rm -rf dist/ node_modules/.cache/ 2>/dev/null || true

# Run tests
test:
	@echo "🧪 Running tests..."
	@uv run --project . python -m pytest tests/ -v

# Add Python package
add:
	@if [ -z "$(PACKAGE)" ]; then echo "Usage: make add PACKAGE=name"; exit 1; fi
	@uv add $(PACKAGE)

# Remove Python package  
remove:
	@if [ -z "$(PACKAGE)" ]; then echo "Usage: make remove PACKAGE=name"; exit 1; fi
	@uv remove $(PACKAGE)

# Update dependencies
update:
	@echo "⬆️ Updating dependencies..."
	@uv lock --upgrade
	@uv sync
	@cd client && pnpm update 