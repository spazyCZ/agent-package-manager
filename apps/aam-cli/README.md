# AAM CLI

Command-line interface for the Agent Package Manager.

## Installation

```bash
# From the monorepo root
npm run cli:install

# Or directly
cd apps/aam-cli
pip install -e '.[dev]'
```

## Usage

```bash
# Show help
aam --help

# Show version
aam --version

# Search for packages
aam search chatbot

# Install a package
aam install my-agent
aam install my-agent@1.0.0

# Show package info
aam show my-agent

# List installed packages
aam list

# Publish a package
aam publish

# Manage configuration
aam config get
aam config set registry https://my-registry.example.com

# Manage registries
aam registry list
aam registry add mycompany https://registry.mycompany.com
aam registry login
```

## Development

```bash
# Install development dependencies
pip install -e '.[dev]'

# Run tests
pytest

# Run linting
ruff check src/ tests/
mypy src/

# Format code
ruff format src/ tests/
```

## Commands

| Command | Description |
|---------|-------------|
| `aam install <package>` | Install packages |
| `aam search <query>` | Search for packages |
| `aam show <package>` | Show package details |
| `aam list` | List installed packages |
| `aam publish` | Publish a package |
| `aam config` | Manage configuration |
| `aam registry` | Manage registry connections |
| `aam info` | Display AAM information |
