<p align="center">
  <img src="assets/spektci-logo.svg" alt="spektci" width="280" />
</p>

<h3 align="center">CI/CD compliance scanner for GitHub Actions, Jenkins, Bitbucket, Azure DevOps & CircleCI</h3>

<p align="center">
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

## 📄 License

[MIT](LICENSE)
