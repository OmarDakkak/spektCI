# Compliance Controls Reference

## C001 — Container images must not use forbidden tags

**ID:** `C001`
**Default:** Enabled

Detects container images using mutable tags that can change unexpectedly (e.g., `latest`, `dev`, `main`).

### Configuration

```yaml
controls:
  image_tags:
    enabled: true
    forbidden_tags:
      - latest
      - dev
      - main
      - master
      - staging
```

### Platform mapping

| Platform | Where images appear |
|----------|-------------------|
| GitHub Actions | `container:`, `services:`, `uses: docker://` |
| Jenkins | `agent { docker { image } }`, `docker.image()` |
| Bitbucket | `image:` at pipeline or step level |
| Azure DevOps | `container:`, `pool.vmImage` |
| CircleCI | `docker:` executor images |

---

## C002 — Container images must come from authorized sources

**ID:** `C002`
**Default:** Enabled

Ensures container images come from trusted registries only.

### Configuration

```yaml
controls:
  image_sources:
    enabled: true
    trust_docker_official: true
    trusted_registries:
      - ghcr.io/your-org/*
      - your-registry.azurecr.io/*
```

---

## C003 — Branches must be protected

**ID:** `C003`
**Default:** Enabled

Verifies that critical branches have proper protection settings via the platform API.

### Configuration

```yaml
controls:
  branch_protection:
    enabled: true
    branches: [main, master, release/*, production]
    require_pr_review: true
    min_approvals: 1
    require_status_checks: true
    block_force_push: true
```

---

## C004 — Pipeline must not contain hardcoded secrets

**ID:** `C004`
**Default:** Enabled

Scans pipeline definitions for patterns resembling secrets, tokens, or passwords.

### Built-in patterns

- Generic `password/secret/token/key = "value"` patterns
- GitHub PATs (`ghp_...`)
- GitLab PATs (`glpat-...`)
- AWS Access Key IDs (`AKIA...`)
- Bearer tokens
- Basic auth in URLs

### Configuration

```yaml
controls:
  hardcoded_secrets:
    enabled: true
    patterns: []              # Additional regex patterns
    exclude_paths:
      - "**/*.example.yml"
```

---

## C005 — Actions/orbs/plugins must use pinned versions

**ID:** `C005`
**Default:** Enabled

Prevents use of mutable version references (branches, `@main`, `@latest`).

### Configuration

```yaml
controls:
  pinned_actions:
    enabled: true
    require_sha_pinning: false
    forbidden_refs: [main, master, HEAD, latest]
```

---

## C006 — Pipeline must include required security stages

**ID:** `C006`
**Default:** Enabled

Ensures required security scanning stages are present. Detection is keyword-based.

### Recognized keywords

| Stage type | Keywords |
|-----------|----------|
| `sast` | semgrep, sonar, codeql, checkmarx, fortify, bandit |
| `sca` | dependabot, snyk, npm-audit, pip-audit, safety |
| `secret_scanning` | gitleaks, trufflehog, detect-secrets, talisman |
| `container_scanning` | trivy, grype, anchore, aqua, twistlock |
| `dast` | zap, burp |

### Configuration

```yaml
controls:
  required_stages:
    enabled: true
    require_all: [sast, secret_scanning]
    require_any: [sca, container_scanning]
```

---

## C007 — Permissions must follow least-privilege

**ID:** `C007`
**Default:** Enabled

Detects overly permissive workflow/pipeline permissions.

### Configuration

```yaml
controls:
  permissions:
    enabled: true
    max_github_permissions: "read"
    flag_privileged_containers: true
    flag_unrestricted_network: true
```

---

## C008 — Pipeline dependencies must be up to date

**ID:** `C008`
**Default:** Enabled

Checks if referenced actions, orbs, or plugins have newer versions available.

### Configuration

```yaml
controls:
  outdated_deps:
    enabled: true
    max_major_behind: 1
    max_minor_behind: 3
```
