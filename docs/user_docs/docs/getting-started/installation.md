# Installation

This page covers everything you need to install AAM, verify the installation, configure your environment, and set up shell completions.

---

## System Requirements

Before installing AAM, ensure your system meets these requirements:

| Requirement | Minimum Version | Recommended |
|-------------|-----------------|-------------|
| **Python** | 3.11 | 3.12+ |
| **pip** | 22.0 | Latest |
| **Operating System** | Linux, macOS, Windows | Any |

Check your Python version:

```bash
python --version
```

!!! warning "Python 3.11+ Required"
    AAM uses modern Python features and requires Python 3.11 or later. If you have an older version, consider using [pyenv](https://github.com/pyenv/pyenv) to install a newer Python alongside your system version.

---

## Install AAM

### Option 1: Install Globally

Install AAM globally with pip:

```bash
pip install aam
```

This makes the `aam` command available system-wide.

### Option 2: Install in a Virtual Environment (Recommended)

Using a virtual environment keeps your system Python clean and avoids dependency conflicts:

```bash
# Create a virtual environment
python -m venv ~/.aam-venv

# Activate it
source ~/.aam-venv/bin/activate  # On macOS/Linux
# Or on Windows:
# .\.aam-venv\Scripts\activate

# Install AAM
pip install aam
```

!!! tip "Permanent activation"
    To make the `aam` command always available, add the activation command to your shell's RC file (`.bashrc`, `.zshrc`, etc.), or create an alias:

    ```bash
    # Add to ~/.bashrc or ~/.zshrc
    alias aam='~/.aam-venv/bin/aam'
    ```

### Option 3: Install from Source

For development or to get the latest unreleased features:

```bash
git clone https://github.com/spazyCZ/agent-package-manager.git
cd agent-package-manager
pip install -e .
```

---

## Verify Installation

Confirm that AAM is installed and accessible:

```bash
aam --version
```

**Expected output:**

```
aam 0.1.0
```

If the `aam` command is not found:

1. Ensure your Python scripts directory is on your `PATH`
2. If using a virtual environment, make sure it's activated
3. Try `python -m aam --version` as a fallback

Get help on available commands:

```bash
aam --help
```

---

## First-Time Configuration

### Set Your Default Platform

AAM deploys artifacts to AI platforms like Cursor, Claude, GitHub Copilot, or Codex. Set your default platform so you don't need to specify it on every command:

```bash
aam config set default_platform cursor
```

**Supported platforms:**

| Platform | Value | Deployment Location |
|----------|-------|---------------------|
| **Cursor** | `cursor` | `.cursor/skills/`, `.cursor/rules/`, `.cursor/prompts/` |
| **Claude** | `claude` | `.claude/skills/`, `CLAUDE.md` |
| **GitHub Copilot** | `copilot` | `.github/copilot-skills/`, `.github/copilot-instructions.md` |
| **OpenAI Codex** | `codex` | `.codex/skills/` |

You can always override this per-command with `--platform`:

```bash
aam install @author/some-skill --platform copilot
```

### Set Your Author Name

When creating packages, AAM uses your author name in the package metadata:

```bash
aam config set author.name "Your Name"
aam config set author.email "you@example.com"
```

This information appears in published packages and helps users identify package authors.

### View Your Configuration

Check all current settings:

```bash
aam config list
```

**Example output:**

```yaml
default_platform: cursor
author:
  name: Your Name
  email: you@example.com
```

---

## Set Up a Registry

A **registry** is where AAM stores and discovers packages. The fastest way to get started is with a **local file-based registry** — no server required.

### Create a Local Registry

Initialize a new registry directory:

```bash
# Create a registry directory
aam registry init ~/my-packages
```

**Expected output:**

```
Created local registry at /home/user/my-packages
```

Register it with AAM and set it as the default:

```bash
aam registry add local file:///home/user/my-packages --default
```

**Expected output:**

```
Added registry 'local' (file:///home/user/my-packages)
Set 'local' as default registry
```

### Verify Registry Configuration

List all configured registries:

```bash
aam registry list
```

**Example output:**

```
Name     Type    URL                                Default
----     ----    ---                                -------
local    file    file:///home/user/my-packages      yes
```

!!! tip "Why local registries?"
    Local registries are:

    - **Simple** — Just a directory with a specific structure
    - **Fast** — No network latency
    - **Offline** — Work without internet
    - **Version-controllable** — Share via Git, NFS, or cloud sync
    - **No server required** — No Docker, no Postgres, no configuration

### Connect to a Remote Registry (Optional)

If your team has an HTTP registry server:

```bash
aam registry add company https://aam.company.com --default
```

Then log in with your credentials:

```bash
aam login company
```

---

## Shell Completion

AAM supports tab completion for commands, options, and package names. Enable it for your shell:

=== "Bash"

    ```bash
    # Add completion to your bashrc
    aam completion bash >> ~/.bashrc

    # Reload your shell
    source ~/.bashrc
    ```

=== "Zsh"

    ```bash
    # Add completion to your zshrc
    aam completion zsh >> ~/.zshrc

    # Reload your shell
    source ~/.zshrc
    ```

=== "Fish"

    ```bash
    # Install completion for Fish
    aam completion fish > ~/.config/fish/completions/aam.fish

    # Fish will automatically load it
    ```

After setup, try typing `aam ` and pressing ++tab++ to see available commands.

**Example:**

```bash
aam in<TAB>
```

Expands to:

```bash
aam install
```

---

## Configuration File Locations

AAM stores configuration in the following locations:

### Global Configuration

| OS | Path |
|----|------|
| **Linux / macOS** | `~/.config/aam/config.yaml` |
| **Windows** | `%APPDATA%\aam\config.yaml` |

### Project Configuration

Each project can have its own configuration in:

```
.aam/config.yaml
```

Project settings override global settings.

### Credentials

API tokens and login credentials are stored separately:

| OS | Path |
|----|------|
| **Linux / macOS** | `~/.config/aam/credentials.yaml` |
| **Windows** | `%APPDATA%\aam\credentials.yaml` |

!!! warning "Keep credentials secure"
    Never commit `credentials.yaml` to version control. It contains sensitive API tokens.

---

## Upgrading AAM

To upgrade to the latest version:

```bash
pip install --upgrade aam
```

Check the changelog for breaking changes:

```bash
aam changelog
```

Or visit the [GitHub releases page](https://github.com/spazyCZ/agent-package-manager/releases).

---

## Uninstalling AAM

To remove AAM:

```bash
pip uninstall aam
```

To also remove configuration and cache:

```bash
# Remove global configuration
rm -rf ~/.config/aam/

# Remove cache
rm -rf ~/.cache/aam/
```

---

## Troubleshooting

### Command Not Found

If `aam` is not found after installation:

1. **Check Python scripts directory is on PATH:**

    ```bash
    python -m site --user-base
    ```

    Add `<output>/bin` to your PATH.

2. **Use the module syntax:**

    ```bash
    python -m aam --version
    ```

3. **Reinstall with `--user` flag:**

    ```bash
    pip install --user aam
    ```

### Permission Errors

If you get permission errors during installation:

```bash
# Use --user flag to install in your home directory
pip install --user aam
```

### Import Errors

If you see `ModuleNotFoundError` after installation:

```bash
# Ensure pip is using the same Python as your shell
python -m pip install aam
```

---

## Next Steps

AAM is now installed and configured. Continue with:

- **[Quick Start](quickstart.md)** — Create, publish, and install your first package in 5 minutes
- **[Your First Package](first-package.md)** — Build a complete package with all artifact types
- **[CLI Reference](../cli/index.md)** — Explore all available commands

!!! success "You're ready!"
    You've successfully installed AAM, configured your platform, and set up a registry. You're ready to start managing AI agent artifacts!
