<p align="center">
  <img src="assets/spektci-logo.svg" alt="spektci" width="280" />
</p>

<h3 align="center">CI/CD compliance scanner for GitHub Actions, Jenkins, Bitbucket, Azure DevOps & CircleCI</h3>

<p align="center">
  <a href="https://github.com/OmarDakkak/spektCI/actions/workflows/ci.yml"><img src="https://github.com/OmarDakkak/spektCI/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
  <a href="docs/adapters.md"><img src="https://img.shields.io/badge/platforms-5-brightgreen" alt="Platforms"></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/status-alpha-orange" alt="Status"></a>
</p>

<p align="center">
  <a href="#-quickstart">Quickstart</a> •
  <a href="docs/controls.md">Controls</a> •
  <a href="#%EF%B8%8F-configuration">Configuration</a> •
  <a href="#-cli-reference">CLI Reference</a> •
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## 🤔 What is spektci?

**spektCI** (from *inspect* + *CI*) is a multi-platform compliance scanner for CI/CD pipelines. It reads your pipeline configuration files and repository settings, then checks for security and compliance issues across **5 major CI/CD platforms**.

**What it detects:**

- Container images using mutable tags (`latest`, `dev`)
- Secrets or credentials hardcoded in pipeline definitions
- Unprotected branches and missing branch policies
- Missing required security stages (SAST, SCA, secret scanning)
- Outdated or pinned-to-mutable-ref actions/orbs/plugins
- Overly permissive workflow permissions

## 🚀 Quickstart

```bash
# Install
pip install spektci

# Generate config
spektci config init

# Set token
export GITHUB_TOKEN=ghp_xxxx

# Run analysis
spektci analyze
```

See the full [CLI Reference](#-cli-reference) for all options.

## 🔍 Compliance Controls

| ID | Control | What it catches |
|----|---------|-----------------|
| C001 | Image Tags | `node:latest` instead of `node:20.11.1` |
| C002 | Image Sources | Untrusted container registries |
| C003 | Branch Protection | Missing PR reviews, force push allowed |
| C004 | Hardcoded Secrets | Passwords / tokens in workflow files |
| C005 | Pinned Actions | `actions/checkout@main` instead of a tag or SHA |
| C006 | Required Stages | Missing SAST or secret scanning steps |
| C007 | Permissions | `permissions: write-all` on workflows |
| C008 | Outdated Deps | Actions multiple major versions behind |

See [docs/controls.md](docs/controls.md) for detailed descriptions and configuration options.

## 🌐 Supported Platforms

| Platform | Status |
|----------|--------|
| GitHub Actions | ✅ Full support |
| Jenkins | 🚧 Stub (planned) |
| Bitbucket Pipelines | 🚧 Stub (planned) |
| Azure DevOps | 🚧 Stub (planned) |
| CircleCI | 🚧 Stub (planned) |

See [docs/adapters.md](docs/adapters.md) for adapter details.

## 💻 CLI Reference

```bash
# Auto-detect platform from git remote
spektci analyze

# Specify platform and repo explicitly
spektci analyze --platform github --repo owner/repo --branch main

# Set a custom compliance threshold (default: 80%)
spektci analyze --threshold 90

# Output as JSON or SARIF (for GitHub Security tab / SonarQube)
spektci analyze --format json --output report.json
spektci analyze --format sarif --output report.sarif

# Config management
spektci config init                        # Generate default .spektci.yaml
spektci config init --platform github      # Pre-configured for GitHub
spektci config view                        # Display effective config
spektci config validate                    # Validate config file
```

## ⚙️ Configuration

spektCI is configured via `.spektci.yaml` in your project root. Generate one with:

```bash
spektci config init
```

Key settings:

```yaml
global:
  threshold: 80              # Minimum compliance % to pass
  fail_on: "error"           # Minimum severity to fail: error | warning | info
  output_format: "terminal"  # terminal | json | sarif

platform:
  type: auto                 # auto | github | jenkins | bitbucket | azure | circleci

controls:
  image_tags:
    enabled: true
    forbidden_tags: [latest, dev, main, master, staging]
  pinned_actions:
    enabled: true
    require_sha_pinning: false
  # ... see .spektci.yaml for all options
```

## 🧪 Development

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests (92 tests, 85% coverage)
pytest tests/ -v

# Lint + type check
ruff check src/ tests/
mypy src/spektci/

# Or use the Makefile
make all    # lint + typecheck + test
```

## 📄 License

[MIT](LICENSE)
