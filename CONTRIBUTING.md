# Contributing to AAM

Thank you for your interest in contributing to the Agent Artifact Manager!

---

## Repository Structure

This project is organized as an **Nx monorepo**:

```
agent-package-manager/
├── apps/
│   ├── aam-cli/           # Python CLI application
│   ├── aam-backend/       # Python FastAPI registry server
│   └── aam-web/           # React web application
├── deploy/                # Docker deployment configuration
├── docs/                  # Documentation
├── nx.json                # Nx workspace configuration
├── package.json           # Root package.json
└── tsconfig.base.json     # Shared TypeScript configuration
```

### Applications

| App | Description | Tech Stack |
|-----|-------------|------------|
| **aam-cli** | Command-line interface for package management | Python 3.11+, Click, Rich, httpx |
| **aam-backend** | Registry server with REST API | Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL, Redis |
| **aam-web** | Web interface for browsing packages | React 18, TypeScript, Vite, Tailwind CSS |

---

## Development Setup

### Prerequisites

- **Node.js** >= 20
- **Python** >= 3.11
- **Docker & Docker Compose** (for local services)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/spazyCZ/agent-package-manager.git
cd agent-package-manager

# Install Node.js dependencies
npm install

# Set up Python CLI
cd apps/aam-cli
pip install -e ".[dev]"
cd ../..

# Set up Python backend
cd apps/aam-backend
pip install -e ".[dev]"
cd ../..
```

---

## Running Applications

### Using npm Scripts

```bash
# CLI
npm run cli -- --help
npm run cli -- search test

# Backend (development server with hot reload)
npm run backend

# Web frontend (development server)
npm run web
```

### Using Nx Commands

```bash
# Serve applications
nx serve aam-backend
nx serve aam-web

# Build applications
nx build aam-cli
nx build aam-backend
nx build aam-web

# Run tests
nx test aam-cli
nx test aam-backend
nx test aam-web

# Lint
nx lint aam-cli
nx lint aam-backend
nx lint aam-web
```

### Run All

```bash
# Build everything
npm run build

# Test everything
npm run test

# Lint everything
npm run lint

# View dependency graph
npm run graph
```

---

## Docker Development

Start local services (PostgreSQL, Redis, MinIO) for development. From the repo root:

```bash
# Copy environment template
cp deploy/local/.env.example deploy/local/.env

# Start infrastructure services only
docker compose -f deploy/local/docker-compose.yml up -d postgres redis minio

# Or start everything in development mode (with hot reload)
docker compose -f deploy/local/docker-compose.yml \
  -f deploy/local/docker-compose.dev.yml up -d
```

See [deploy/local/README.md](deploy/local/README.md) for details.

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Redis cache |
| minio | 9000/9001 | S3-compatible storage |
| backend | 8000 | FastAPI API |
| web | 3000 | React frontend |
| nginx | 80/443 | Reverse proxy |

---

## Project-Specific Development

### aam-cli (Python CLI)

```bash
cd apps/aam-cli

# Install with dev dependencies
pip install -e ".[dev]"

# Run CLI
python -m aam_cli.main --help

# Run tests
pytest tests/ -v

# Lint and type check
ruff check src/ tests/
mypy src/

# Format code
ruff format src/ tests/
```

### aam-backend (FastAPI)

```bash
cd apps/aam-backend

# Install with dev dependencies
pip install -e ".[dev]"

# Run server
uvicorn aam_backend.main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Lint and type check
ruff check src/ tests/
mypy src/

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### aam-web (React)

```bash
cd apps/aam-web

# Install dependencies (from monorepo root)
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

---

## Code Style

### Python

- **Formatter**: Ruff
- **Linter**: Ruff + mypy
- **Line length**: 100 characters
- **Type hints**: Required for all functions

### TypeScript/JavaScript

- **Formatter**: Prettier
- **Linter**: ESLint
- **Style**: Single quotes, trailing commas

---

## Testing

### Running Tests

```bash
# All tests
npm run test

# Specific app
nx test aam-cli
nx test aam-backend
nx test aam-web

# With coverage
pytest --cov=src tests/
```

### Writing Tests

- Place tests in `tests/` directory within each app
- Name test files `test_*.py` (Python) or `*.test.ts` (TypeScript)
- Use pytest for Python, Vitest for TypeScript

---

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/my-feature`
3. **Make changes** and add tests
4. **Run tests and linting** locally
5. **Commit** with clear messages
6. **Push** and create a Pull Request

### Commit Messages

Follow conventional commits:

```
feat: add package search command
fix: resolve dependency resolution bug
docs: update installation guide
test: add tests for auth endpoints
refactor: simplify manifest parser
```

---

## Deployment

### Production Docker Deployment

```bash
# Configure environment (from repo root)
cp deploy/local/.env.example deploy/local/.env
# Edit deploy/local/.env with production values

# Build and start
docker compose -f deploy/local/docker-compose.yml up -d --build

# Run migrations
docker compose -f deploy/local/docker-compose.yml exec backend alembic upgrade head

# View logs
docker compose -f deploy/local/docker-compose.yml logs -f
```

See [deploy/local/README.md](deploy/local/README.md) for detailed deployment instructions.

---

## Roadmap

- [x] Core manifest parsing
- [x] Package validation and building
- [x] Cursor platform adapter
- [ ] Claude platform adapter
- [ ] GitHub Copilot adapter
- [x] HTTP registry service (aam-backend)
- [x] Web interface (aam-web)
- [ ] Sigstore integration
- [ ] Namespace/scope support (`@org/package`)

---

## Getting Help

- Open an [issue](https://github.com/spazyCZ/agent-package-manager/issues) for bugs
- Start a [discussion](https://github.com/spazyCZ/agent-package-manager/discussions) for questions
- Check existing issues before creating new ones

---

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
