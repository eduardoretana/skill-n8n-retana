# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and this project uses SemVer tags for releases.

## [0.1.0] - 2026-04-12

### Added

- Initial portable export of the self-hosted n8n admin skill.
- Canonical Codex skill under `codex/skills/n8n-self-hosted-admin/`.
- Cross-agent adapters for Claude Code, Gemini, Antigravity, and `AGENTS.md` consumers.
- Portable helper CLI with:
  - base URL local config
  - macOS Keychain support
  - `discover` fallback to `openapi.yml`
  - workflow, execution, audit, and support commands
- Installer script for dropping adapters into other projects.
- Example `.env` template for non-Keychain setups.
- Repository-level context files for Codex, Claude, Gemini, and Antigravity.
- CI validation workflow for Python compilation, installer smoke tests, and skill structure checks.

### Notes

- Some endpoints such as `projects` or `variables` may return `403` depending on n8n plan or license.
- The repository intentionally avoids shipping any real instance URL or secret.
