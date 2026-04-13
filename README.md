# skill-n8n-retana

[![Validate](https://github.com/eduardoretana/skill-n8n-retana/actions/workflows/validate.yml/badge.svg)](https://github.com/eduardoretana/skill-n8n-retana/actions/workflows/validate.yml)

Portable self-hosted n8n admin skill and adapter pack.

This repository packages a reusable n8n operations skill so it can be used from:

- Codex
- Claude Code
- Gemini
- Antigravity
- Any agent that can read `AGENTS.md`-style guidance

The repo keeps one canonical implementation for the skill logic and then adds lightweight adapters for other agents.

## Positioning

`skill-n8n-retana` is a practical operations pack for teams running self-hosted n8n and wanting agent help without re-explaining their operational playbook on every project.

It is designed for:

- operators who need safe workflow updates
- developers supporting automation incidents
- AI-assisted teams that switch between Codex, Claude Code, Gemini, and Antigravity
- consulting or agency setups where the same n8n admin workflow repeats across multiple clients and instances

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

Generate a quick incident snapshot:

```bash
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py support-report
```

Inspect active workflows:

```bash
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py list workflows --query active=true --query excludePinnedData=true
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

## Tool-by-Tool Usage

### Codex

Install the skill into `~/.codex/skills`:

```bash
python3 scripts/install.py --tool codex
```

Then invoke it from Codex with the canonical skill:

```text
Use $n8n-self-hosted-admin to inspect this self-hosted n8n instance, summarize risk, and make a safe workflow update.
```

### Claude Code

Install the adapter into a project:

```bash
python3 scripts/install.py --tool claude --target /path/to/project
```

The generated `CLAUDE.md` points Claude back to the canonical skill files and helper script in this repo.

### Gemini

Install the adapter into a project:

```bash
python3 scripts/install.py --tool gemini --target /path/to/project
```

The generated `GEMINI.md` gives Gemini the same operating rules and script entrypoint.

### Antigravity

Install the adapter into a project:

```bash
python3 scripts/install.py --tool antigravity --target /path/to/project
```

This writes modular `.agent/rules/` files for always-on context.

### Shared `AGENTS.md`

If a tool understands `AGENTS.md`-style repo instructions, install the shared adapter:

```bash
python3 scripts/install.py --tool shared --target /path/to/project
```

Or install all non-Codex adapters at once:

```bash
python3 scripts/install.py --tool all --target /path/to/project
```

## Typical Workflows

### 1. Set up one instance for repeated use

```bash
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py config-set-base-url "https://n8n.example.com"
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py keychain-set
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py discover
```

### 2. Triage an n8n incident

```bash
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py support-report
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py list executions --query status=error --limit 50
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py get workflow WORKFLOW_ID --query excludePinnedData=true
```

### 3. Update a workflow safely

```bash
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py get workflow WORKFLOW_ID --query excludePinnedData=true > /tmp/workflow.before.json
cp /tmp/workflow.before.json /tmp/workflow.edit.json
# edit /tmp/workflow.edit.json
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py workflow-update WORKFLOW_ID --file /tmp/workflow.edit.json
```

### 4. Audit the instance

```bash
python3 codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py audit --category credentials --category filesystem --category instance
```

## Notes on Compatibility

- Codex uses the self-contained skill under `codex/skills/n8n-self-hosted-admin/`.
- Claude Code and Gemini adapters point back to the canonical skill in this repo.
- Antigravity gets modular `.agent/rules/` files for always-on context.
- Some n8n endpoints may return `403` depending on plan or license. Treat that as product capability evidence, not automatically as a bad token.
- Some self-hosted builds expose the public API but not `GET /discover`; the helper falls back to `openapi.yml`.

## Validation and CI

Run local validation:

```bash
python3 scripts/validate.py
```

GitHub Actions runs the same validation on pushes and pull requests.

## Security

- Never commit real API keys.
- Prefer Keychain over plaintext `.env` files on macOS.
- If you use `.env` for convenience, keep it local and untracked.

## License

MIT
