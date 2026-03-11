"""Default configuration generation for `spektci config init`."""

from __future__ import annotations

DEFAULT_CONFIG_YAML = """\
# spektci configuration
# Docs: https://github.com/spektci/spektci
version: "1"

# Global settings
global:
  threshold: 80              # Minimum compliance % to pass (0-100)
  fail_on: "error"           # Minimum severity to fail: error | warning | info
  output_format: "terminal"  # terminal | json | sarif
  output_file: null           # Path for file output (null = stdout only)

# Platform-specific overrides (usually auto-detected)
platform:
  type: auto                 # auto | github | jenkins | bitbucket | azure | circleci
  api_url: null              # Override API base URL (for self-hosted instances)
  project: null              # Override project/repo path
  branch: null               # Override branch to analyze

# Compliance controls
controls:
  image_tags:
    enabled: true
    forbidden_tags: [latest, dev, main, master, staging]

  image_sources:
    enabled: true
    trust_docker_official: true
    trusted_registries: []

  branch_protection:
    enabled: true
    branches: [main, master, release/*, production]
    require_pr_review: true
    min_approvals: 1
    require_status_checks: true
    block_force_push: true

  hardcoded_secrets:
    enabled: true
    patterns: []              # Additional regex patterns
    exclude_paths: []

  pinned_actions:
    enabled: true
    require_sha_pinning: false
    forbidden_refs: [main, master, HEAD, latest]

  required_stages:
    enabled: true
    require_all: [sast, secret_scanning]
    require_any: []

  permissions:
    enabled: true
    max_github_permissions: "read"
    flag_privileged_containers: true
    flag_unrestricted_network: true

  outdated_deps:
    enabled: true
    max_major_behind: 1
    max_minor_behind: 3
"""


def generate_default_config() -> str:
    """Return the default .spektci.yaml content as a string."""
    return DEFAULT_CONFIG_YAML
