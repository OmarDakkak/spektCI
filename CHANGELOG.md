# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project scaffold
- Core models: `PipelineModel`, `Finding`, `AnalysisResult`, `Severity`
- Configuration layer with Pydantic v2 schema and YAML loader
- Click-based CLI with `analyze`, `config init`, `config view`, `config validate`
- 8 compliance controls (C001–C008)
- GitHub Actions platform adapter (collector + parser)
- Stub adapters for Jenkins, Bitbucket, Azure DevOps, CircleCI
- Terminal (Rich), JSON, and SARIF v2.1.0 reporters
- Platform auto-detection from git remote URL
- `.spektci.yaml` default config generator
- Unit test suite with fixtures
- GitHub Actions CI workflows (ci, release, dogfood)
- Dockerfile (Alpine-based, multi-stage)
