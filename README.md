# AWS Sidekick

**AWS Sidekick** is an intelligent cloud engineering assistant that helps you analyze, optimize, and secure your AWS infrastructure. Built with a modern hexagonal architecture, it combines the power of AI agents with specialized AWS tools to provide comprehensive cloud management support.

## 🚀 Features

- **AI-Powered Analysis**: Uses Anthropic Claude or OpenAI GPT models for intelligent AWS infrastructure analysis
- **Multi-Tool Integration**: Leverages MCP (Model Context Protocol) servers for AWS documentation, diagrams, CDK, Terraform, and more
- **Modern Web Interface**: Vue.js 3 + TypeScript frontend with real-time chat and task management
- **RESTful API**: FastAPI-based backend with comprehensive API documentation
- **Flexible Deployment**: Supports local development, Docker containers, and production deployments
- **Data Persistence**: SQLite database for chat history and task management
- **GitHub Integration**: Optional GitHub tools for repository management

## 🏗️ Architecture

AWS Sidekick follows **Hexagonal Architecture** (Clean Architecture) principles:

```
┌─────────────────────────────────────────────────────────────┐
│                        Presentation Layer                   │
│  ┌─────────────────┐              ┌─────────────────────┐   │
│  │   Vue.js Client │              │   FastAPI Adapter  │   │
│  │   (TypeScript)  │              │   (REST API)       │   │
│  └─────────────────┘              └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Chat Service    │  │ Task Service    │  │ AWS Service │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                         Domain Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Chat Entities   │  │ Task Entities   │  │ AWS Entities│ │
│  │ Use Cases       │  │ Use Cases       │  │ Use Cases   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ SQLite Repos    │  │ AWS Client      │  │ MCP Servers │ │
│  │ Agent Repo      │  │ Adapter         │  │ Integration │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

- **Presentation Layer**: Vue.js frontend and FastAPI REST API
- **Application Layer**: Business logic services orchestrating use cases
- **Domain Layer**: Core business entities and use cases
- **Infrastructure Layer**: External integrations (database, AWS, AI models)

## 🛠️ Technology Stack

### Backend
- **Python 3.12+** with modern async/await support
- **FastAPI** for REST API with automatic OpenAPI documentation
- **Pydantic** for data validation and serialization
- **SQLite** with aiosqlite for persistent data storage
- **Structlog** for structured logging
- **UV** for fast Python package management

### Frontend
- **Vue.js 3** with Composition API
- **TypeScript** for type safety
- **Tailwind CSS** for utility-first styling
- **Pinia** for state management
- **Axios** for HTTP client
- **Vite** for fast development and building

### AI & Integration
- **Anthropic Claude** or **OpenAI GPT** models
- **MCP Servers** for specialized AWS tools
- **Boto3** for AWS SDK integration
- **GitHub API** for repository management (optional)

## 📋 Prerequisites

- **Python 3.10+** (recommended 3.12+)
- **Node.js 18+** with `pnpm` package manager
- **UV** Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Docker** (optional, for containerized deployment)

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd aws-sidekick
```

### 2. Initial Setup

```bash
# Install dependencies and setup environment
make setup

# Or with virtual environment
make setup-venv
```

### 3. Configure Environment

```bash
# Edit the generated .env file with your API keys
cp example.env .env
vim .env  # or your preferred editor
```

**Required Configuration:**
```bash
# Choose your AI provider
MODEL_PROVIDER=anthropic  # or "openai"

# Add your API key (based on provider)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# OR
OPENAI_API_KEY=your_openai_api_key_here

# AWS Configuration (uses your AWS profile by default)
AWS_DEFAULT_REGION=us-east-1
AWS_PROFILE=default

# Optional: GitHub integration
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
```

### 4. Install Client Dependencies

```bash
make client-install
```

### 5. Start Development Servers

```bash
# Start both API and client together
make full-dev

# Or start them separately:
make api-dev    # API server at http://localhost:8000
make client     # Client at http://localhost:3000
```

## 🐳 Docker Deployment

### Quick Docker Start

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or using Makefile commands
make docker-build
make docker-run
```

### Production Docker Deployment

```bash
# Build production image
docker build -t aws-sidekick .

# Run with environment file
docker run -d \
  --name aws-sidekick \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  aws-sidekick
```

## 📁 Data Persistence Configuration

AWS Sidekick uses **SQLite** for data persistence with the following structure:

### Database Configuration

```python
# Configuration in src/infrastructure/config.py
DATABASE_TYPE=sqlite          # "sqlite" or "memory"
DATABASE_PATH=data/tasks.db   # SQLite file location
```

### Data Storage

- **Chat History**: Stored in SQLite with conversation threads and message history
- **Task Management**: Persistent task storage with status tracking and results
- **AWS Resources**: Cached AWS resource information for faster retrieval
- **Application Logs**: Structured logging to files in `logs/` directory

### Data Directory Structure

```
data/
├── tasks.db          # Main SQLite database
├── cache/           # Temporary cache files
└── exports/         # Exported reports and diagrams

logs/
├── app.log          # Application logs
└── error.log        # Error logs
```

### Database Schema

The application automatically creates the following tables:
- `chat_sessions` - Chat conversation sessions
- `messages` - Individual chat messages
- `tasks` - Task definitions and execution status
- `aws_resources` - Cached AWS resource metadata

## 🔧 Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MODEL_PROVIDER` | Yes | `anthropic` | AI provider: `anthropic` or `openai` |
| `ANTHROPIC_API_KEY` | If using Anthropic | - | Anthropic API key |
| `OPENAI_API_KEY` | If using OpenAI | - | OpenAI API key |
| `MODEL_ID` | No | Auto-detected | Specific model ID |
| `AWS_DEFAULT_REGION` | No | `us-east-1` | Default AWS region |
| `AWS_PROFILE` | No | `default` | AWS profile to use |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | No | - | GitHub API token |
| `API_HOST` | No | `0.0.0.0` | API server host |
| `API_PORT` | No | `8000` | API server port |
| `DEBUG` | No | `false` | Enable debug mode |

### MCP Server Configuration

AWS Sidekick integrates with multiple MCP servers:

- **AWS Documentation**: AWS service documentation and best practices
- **AWS Diagrams**: Infrastructure diagram generation
- **CDK Server**: AWS CDK code generation and management
- **Terraform Server**: Terraform configuration management
- **Cost Explorer**: AWS cost analysis and optimization
- **CloudWatch**: Log analysis and monitoring
- **GitHub**: Repository management (if token provided)

## 📚 Usage

### Web Interface

1. **Chat Interface**: Interactive AI assistant for AWS questions and tasks
2. **Task Management**: Create, track, and manage AWS-related tasks
3. **AWS Dashboard**: View and analyze AWS resources and costs
4. **Performance Monitor**: Real-time application performance metrics

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Available Commands

```bash
# Development
make full-dev          # Start both API and client
make api-dev          # Start API with hot reload
make client           # Start Vue.js client

# Production
make production       # Build client and serve via FastAPI
make client-build     # Build Vue.js for production

# Docker
make docker-build     # Build Docker image
make docker-run       # Run in Docker (production)
make docker-dev       # Run in Docker (development)

# Maintenance
make clean           # Clean cache and temporary files
make clean-all       # Clean everything including venv
make update          # Update all dependencies
make test            # Run tests
```

## 🔍 Development

### Project Structure

```
src/
├── adapters/        # External interfaces (API, Database, AWS)
├── application/     # Application services and orchestration
├── core/           # Domain entities, use cases, ports
└── infrastructure/ # Configuration, DI, logging

client/
├── src/
│   ├── components/ # Vue.js components
│   ├── stores/     # Pinia state management
│   ├── services/   # API client services
│   └── views/      # Page components
```

### Adding New Features

1. **Domain First**: Define entities and use cases in `core/`
2. **Application Layer**: Implement business logic in `application/services/`
3. **Adapters**: Add external integrations in `adapters/`
4. **Frontend**: Create Vue.js components and connect to API

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the hexagonal architecture principles
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check `/docs` endpoint when running
- **Issues**: Create GitHub issues for bugs and feature requests
- **Logs**: Check `logs/` directory for debugging information

---

**AWS Sidekick** - Your intelligent cloud engineering companion 🚀