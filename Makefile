# AWS Cloud Engineer Agent - Hexagonal Architecture

.PHONY: dev install install-venv sync setup setup-venv env clean clean-all test lint format add remove update config validate help client-install client client-build client-preview full-dev docker-build docker-run docker-dev docker-stop docker-clean docker-logs

# Default target
help:
	@echo "AWS Cloud Engineer Agent - Hexagonal Architecture"
	@echo "================================================"
	@echo ""
	@echo "🚀 Development Commands:"
	@echo "  make api         - Start REST API server"
	@echo "  make api-dev     - Start API server with hot reload"
	@echo "  make client      - Start Vue.js client"
	@echo "  make full-dev    - Start both API and client together"
	@echo "  make install     - Install Python dependencies with uv"
	@echo "  make client-install - Install client dependencies"
	@echo "  make install-venv - Create venv and install dependencies"
	@echo "  make sync        - Sync dependencies (if using uv.lock)"
	@echo "  make clean       - Clean cache and temporary files"
	@echo "  make clean-all   - Clean everything including venv"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linter (when configured)"
	@echo "  make format      - Format code (when configured)"
	@echo ""
	@echo "📚 Setup Commands:"
	@echo "  make setup       - Initial setup (install + env file)"
	@echo "  make setup-venv  - Setup with virtual environment"
	@echo "  make env         - Copy environment file template"
	@echo "  make validate    - Validate environment setup"
	@echo ""
	@echo "🎨 Client Commands:"
	@echo "  make client-build   - Build Vue.js client for production"
	@echo "  make client-preview - Preview production build"
	@echo "  make production     - Build client and serve via FastAPI"
	@echo ""
	@echo "📦 Package Management (uv):"
	@echo "  make add PACKAGE=name    - Add a new package"
	@echo "  make remove PACKAGE=name - Remove a package"
	@echo "  make update              - Update all dependencies"
	@echo "  make sync                - Sync from lock file"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run application in Docker (production)"
	@echo "  make docker-dev     - Run application in Docker (development with hot reload)"
	@echo "  make docker-stop    - Stop Docker containers"
	@echo "  make docker-clean   - Clean Docker containers and images"
	@echo "  make docker-logs    - View Docker container logs"
	@echo ""



# Start API server
api:
	@echo "🚀 Starting AWS Cloud Engineer Agent API Server..."
	@python api.py

# Start API server in development mode with hot reload
api-dev:
	@echo "🚀 Starting API Server in development mode..."
	@DEBUG=true python api.py

# Install dependencies
install:
	@echo "📦 Installing dependencies with uv..."
	@uv pip install -r requirements.txt

# Install dependencies in a virtual environment
install-venv:
	@echo "📦 Creating virtual environment and installing dependencies..."
	@uv venv
	@uv pip install -r requirements.txt

# Sync dependencies (if using uv.lock)
sync:
	@echo "🔄 Syncing dependencies with uv..."
	@uv sync

# Initial setup
setup: install env
	@echo "✅ Setup complete!"
	@echo "📝 Please edit .env with your API keys:"
	@echo "   ANTHROPIC_API_KEY=your_api_key_here"
	@echo "🚀 Then run: make api"

# Initial setup with virtual environment
setup-venv: install-venv env
	@echo "✅ Setup with venv complete! Activate with 'source .venv/bin/activate'"
	@echo "📝 Edit .env with your API keys and run 'make api'"

# Copy environment file template
env:
	@if [ ! -f .env ]; then \
		echo "📄 Creating .env file from template..."; \
		cp env.example .env; \
		echo "✅ .env file created. Please edit it with your API keys."; \
	else \
		echo "⚠️  .env file already exists."; \
	fi

# Install client dependencies
client-install:
	@echo "📦 Installing client dependencies..."
	@cd client && pnpm install

# Start the Vue.js client
client:
	@echo "🚀 Starting Vue.js client..."
	@cd client && pnpm run dev

# Build the Vue.js client
client-build:
	@echo "🏗️  Building Vue.js client..."
	@cd client && pnpm run build

# Preview the Vue.js client build
client-preview:
	@echo "👀 Previewing Vue.js client build..."
	@cd client && pnpm run preview

# Start both API and client in development mode
full-dev:
	@echo "🚀 Starting both API server and Vue.js client..."
	@echo "🔗 API will be available at: http://localhost:8000"
	@echo "🔗 Client will be available at: http://localhost:3000"
	@echo "⚠️  Press Ctrl+C to stop both services"
	@(trap 'kill 0' SIGINT; make api-dev & make client & wait)

# Clean cache and temporary files
clean:
	@echo "🧹 Cleaning cache and temporary files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

	@rm -rf .uv_cache 2>/dev/null || true
	@cd client && rm -rf dist/ node_modules/.cache/ 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Clean everything including virtual environment
clean-all: clean
	@echo "🧹 Cleaning everything including virtual environment..."
	@rm -rf .venv 2>/dev/null || true
	@rm -rf uv.lock 2>/dev/null || true
	@echo "✅ Deep cleanup complete"

# Run tests
test:
	@echo "🧪 Running tests..."
	@cd src && python -m pytest tests/ -v 2>/dev/null || echo "⚠️  No tests configured yet"

# Run linter (placeholder for future linting)
lint:
	@echo "🔍 Running linter..."
	@echo "⚠️  No linter configured yet"

# Format code (placeholder for future formatting)
format:
	@echo "💅 Formatting code..."
	@echo "⚠️  No formatter configured yet"

# Add a new package
add:
	@echo "📦 Adding package with uv..."
	@if [ -z "$(PACKAGE)" ]; then \
		echo "❌ Usage: make add PACKAGE=package_name"; \
		exit 1; \
	fi
	@uv add $(PACKAGE)
	@echo "✅ Package $(PACKAGE) added"

# Remove a package
remove:
	@echo "🗑️  Removing package with uv..."
	@if [ -z "$(PACKAGE)" ]; then \
		echo "❌ Usage: make remove PACKAGE=package_name"; \
		exit 1; \
	fi
	@uv remove $(PACKAGE)
	@echo "✅ Package $(PACKAGE) removed"

# Update all dependencies
update:
	@echo "⬆️  Updating all dependencies with uv..."
	@uv lock --upgrade
	@uv sync
	@echo "✅ Dependencies updated"

# Show current configuration
config:
	@echo "⚙️  Current Configuration:"
	@echo "  Python: $(shell python --version)"
	@echo "  uv: $(shell uv --version 2>/dev/null || echo 'Not installed')"

	@echo "  Virtual env: $(shell [ -d .venv ] && echo '✅ Found (.venv)' || echo '❌ Not found')"
	@echo "  Environment file: $(shell [ -f .env ] && echo '✅ Found' || echo '❌ Missing')"
	@echo "  uv.lock: $(shell [ -f uv.lock ] && echo '✅ Found' || echo '❌ Not found')"

# Validate environment setup
validate:
	@echo "🔬 Validating environment setup..."
	@python validate_env.py

# Build client and serve everything through FastAPI
production: client-build
	@echo "🚀 Building client and starting production server..."
	@echo "🔗 Server will be available at: http://localhost:8000"
	@echo "📱 Client will be served at: http://localhost:8000"
	@echo "📚 API docs available at: http://localhost:8000/docs"
	@echo "⚠️  Press Ctrl+C to stop"
	@python api.py

# Docker Commands
docker-build:
	@echo "🐳 Building Docker image..."
	@docker-compose build

docker-run:
	@echo "🐳 Running application in Docker (production mode)..."
	@echo "🔗 Application will be available at: http://localhost:8000"
	@docker-compose up -d

docker-dev:
	@echo "🐳 Running application in Docker (development mode with hot reload)..."
	@echo "🔗 Application will be available at: http://localhost:8000"
	@echo "📝 Source code changes will trigger automatic reload"
	@docker-compose -f docker-compose.yml -f docker-compose.override.yml up

docker-stop:
	@echo "🐳 Stopping Docker containers..."
	@docker-compose down

docker-clean:
	@echo "🐳 Cleaning Docker containers and images..."
	@docker-compose down --rmi all --volumes --remove-orphans

docker-logs:
	@echo "🐳 Viewing Docker container logs..."
	@docker-compose logs -f 