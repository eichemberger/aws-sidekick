# AWS Sidekick

**AWS Sidekick** is an intelligent cloud engineering assistant that helps you analyze, optimize, and secure your AWS infrastructure. Built with a modern hexagonal architecture, it combines the power of AI agents with specialized AWS tools to provide comprehensive cloud management support.

## Quick Start

```bash
touch .env # Copy format from quickstart.env

docker compose --build --no-cache
docker compose up
```

Wait a few seconds and open http://localhost:8000. Configure the AWS credentials in the UI and start chatting.

## 💬 Writing Effective Prompts

To get the best results from AWS Sidekick, follow these guidelines for crafting your prompts:

### ✅ Good Prompts

**Read-only Questions** - Be as ambiguous as you want:
- "What's the status of my infrastructure?"
- "Show me my EC2 costs this month"
- "Are there any security issues I should know about?"
- "Help me understand my VPC configuration"

**Write Operations** - Give concise and clear instructions:
- "Create a new S3 bucket named 'my-app-logs' with versioning enabled in us-west-2"
- "Add a security group rule to allow HTTPS traffic from 0.0.0.0/0 to my web servers"
- "Scale my Auto Scaling group 'web-tier' to 3 instances"
- "Update the RDS instance 'prod-db' to enable automated backups with 7-day retention"

### ❌ Bad Prompts

**Ambiguous Write Operations** - Avoid vague requests that require guesswork:
- ❌ "My EC2 instance cannot connect to RDS, fix it"
- ❌ "Make my app faster"
- ❌ "Something is wrong with my load balancer"
- ❌ "Optimize my costs"

**Better alternatives:**
- ✅ "Check connectivity between EC2 instance i-1234567890abcdef0 and RDS instance prod-db"
- ✅ "Analyze the performance of my application load balancer and suggest specific optimizations"
- ✅ "Review my EC2 instance types and recommend right-sizing opportunities to reduce costs"

### 💡 Pro Tips

- **Be specific** about resource names, regions, and desired outcomes for write operations
- **Ask follow-up questions** to clarify requirements before making changes
- **Use read-only analysis first** to understand the current state before requesting modifications
- **Request confirmation** for destructive operations by asking "show me what will change first"


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

### Configuration Files

AWS Sidekick uses YAML configuration files in the `config/` directory to control agent behavior and tool integrations:

| File | Purpose | When to Modify |
|------|---------|----------------|
| `system-prompt.yaml` | Defines the AI agent's personality, expertise, and behavior | Customize agent behavior or add new capabilities |
| `mcp-config.yaml` | Configures MCP servers that provide tools and integrations | Enable/disable specific AWS services or add new tools |

#### system-prompt.yaml

Controls the AI agent's role as a Senior AWS Cloud Engineer, including:
- **Role Definition**: Establishes expertise areas and capabilities
- **Communication Style**: Adaptive responses based on question complexity
- **Safety Guidelines**: Rules for infrastructure changes and destructive operations
- **Execution Standards**: Default behaviors and best practices

**Example customization:**
```yaml
system_prompt: |
  **Custom Principles:**
  - Always use least privilege IAM policies
  - Implement multi-region deployments for production
  - Include cost estimates for infrastructure changes
```

#### mcp-config.yaml

Configures MCP (Model Context Protocol) servers that extend the agent's capabilities:

**Structure:**
```yaml
mcp_servers:
  server_name:
    enabled: true/false          # Whether to load this server
    command: uvx/npx/python     # Command to run the server
    args: [...]                 # Arguments passed to the command
    env:                        # Environment variables (optional)
      VAR_NAME: "${VAR_VALUE}"
    description: "..."          # Human-readable description
```

**Example MCP Servers:**

*Pre-configured (in config/mcp-config.yaml):*
- `aws_docs` - AWS documentation and service information
- `aws_diagram` - Generate AWS architecture diagrams
- `github` - GitHub repository management (requires `GITHUB_PERSONAL_ACCESS_TOKEN`)
- `cdk` - AWS CDK infrastructure as code
- `terraform` - Terraform infrastructure management
- `cost_explorer` - AWS cost analysis and optimization
- `cloudwatch` - CloudWatch logs querying and analysis

**Add any MCP server:**
```yaml
# Community MCP servers
filesystem:
  enabled: true
  command: npx
  args:
    - "@modelcontextprotocol/server-filesystem"
    - "/path/to/allowed/directory"
  description: "File system operations"

postgres:
  enabled: true
  command: uvx
  args:
    - "mcp-server-postgres"
  env:
    POSTGRES_CONNECTION_STRING: "${DATABASE_URL}"
  description: "PostgreSQL database operations"

# Custom Python MCP server
custom_tools:
  enabled: true
  command: python
  args:
    - "/path/to/your/custom_mcp_server.py"
  env:
    API_KEY: "${YOUR_API_KEY}"
    CUSTOM_CONFIG: "value"
  description: "Your custom tools and integrations"

# Docker-based MCP server
docker_mcp:
  enabled: true
  command: docker
  args:
    - "run"
    - "--rm"
    - "-i"
    - "your-org/custom-mcp-server:latest"
  description: "Containerized MCP server"
```

**Find MCP servers:**
- **AWS Labs**: https://github.com/awslabs/mcp - Official AWS MCP servers
- **Official Community**: https://github.com/modelcontextprotocol/servers - Maintained by MCP team
- **Community Registry**: https://github.com/modelcontextprotocol/registry - Community contributions
- **Build Your Own**: https://modelcontextprotocol.io/docs - MCP protocol specification

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MODEL_PROVIDER` | Yes | `anthropic` | AI provider: `anthropic` or `openai` |
| `ANTHROPIC_API_KEY` | If using Anthropic | - | Anthropic API key |
| `OPENAI_API_KEY` | If using OpenAI | - | OpenAI API key |
| `MODEL_ID` | No | Auto-detected | Specific model ID |
| `AWS_DEFAULT_REGION` | No | `us-east-1` | Default AWS region |
| `AWS_PROFILE` | No | `default` | AWS profile to use |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | No | - | GitHub API token (required for GitHub MCP server) |
| `API_HOST` | No | `0.0.0.0` | API server host |
| `API_PORT` | No | `8000` | API server port |
| `DEBUG` | No | `false` | Enable debug mode |

### Configuration Best Practices

**Security:**
- Store sensitive values (API keys, tokens) in environment variables
- Use `"${VAR_NAME}"` syntax in YAML files to reference environment variables
- Never commit secrets directly to configuration files

**Performance:**
- Only enable MCP servers you actively use
- Monitor resource usage if running many servers
- Use `@latest` versions for AWS Labs servers to get updates

**Maintenance:**
- Test configuration changes in development first
- Restart the application after modifying configuration files
- Check logs for MCP server connection issues

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