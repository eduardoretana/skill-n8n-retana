# skill-n8n-retana

Portable self-hosted n8n admin skill and adapter pack.

This repository packages a reusable n8n operations skill so it can be used from:

- Codex
- Claude Code
- Gemini
- Antigravity
- Any agent that can read `AGENTS.md`-style guidance

The repo keeps one canonical implementation for the skill logic and then adds lightweight adapters for other agents.

## What It Does

- Inspect self-hosted n8n public API capabilities
- Create and update workflows safely
- Activate and deactivate workflows
- Review executions and produce support reports
- Generate security audits
- Inspect credentials, users, projects, variables, and tags when the instance license allows it
- Fall back from `GET /discover` to the instance's `openapi.yml` when needed
- Store API keys in macOS Keychain for low-friction local use
- Persist a default base URL in local config so commands stay short

## Repo Layout

```text
codex/skills/n8n-self-hosted-admin/
  SKILL.md
  agents/openai.yaml
  references/
  scripts/n8n_admin.py
adapters/
  claude/CLAUDE.md
  gemini/GEMINI.md
  shared/AGENTS.md
  antigravity/.agent/rules/
scripts/install.py
examples/.env.n8n.example
```

## Quick Start

1. Clone the repo.
2. Set the default instance URL once:

```bash
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py config-set-base-url "https://n8n.example.com"
```

3. Store the API key once on macOS:

```bash
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py keychain-set
```

4. Verify setup:

```bash
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py keychain-status
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py discover
```

## Install Into Other Tools

Use the installer to copy the right adapter files into another project.

Install the Codex skill globally:

```bash
python3 scripts/install.py --tool codex
```

Install Claude Code guidance into a target project:

```bash
python3 scripts/install.py --tool claude --target /path/to/project
```

Install Gemini guidance into a target project:

```bash
python3 scripts/install.py --tool gemini --target /path/to/project
```

Install Antigravity guidance into a target project:

```bash
python3 scripts/install.py --tool antigravity --target /path/to/project
```

Install all non-Codex adapters plus a shared `AGENTS.md`:

```bash
python3 scripts/install.py --tool all --target /path/to/project
```

Use `--force` to overwrite existing files.

## Notes on Compatibility

- Codex uses the self-contained skill under `codex/skills/n8n-self-hosted-admin/`.
- Claude Code and Gemini adapters point back to the canonical skill in this repo.
- Antigravity gets modular `.agent/rules/` files for always-on context.
- Some n8n endpoints may return `403` depending on plan or license. Treat that as product capability evidence, not automatically as a bad token.

## Security

- Never commit real API keys.
- Prefer Keychain over plaintext `.env` files on macOS.
- If you use `.env` for convenience, keep it local and untracked.

## License

No license file is included yet. Add one before publishing if you want third-party reuse beyond your own projects and accounts.
