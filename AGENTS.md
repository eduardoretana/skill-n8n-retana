# n8n Self-Hosted Admin

Canonical implementation lives in:

- `codex/skills/n8n-self-hosted-admin/SKILL.md`
- `codex/skills/n8n-self-hosted-admin/references/api-surface.md`
- `codex/skills/n8n-self-hosted-admin/references/ops-playbook.md`
- `codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py`

## Rules

- Treat the Codex skill folder as the source of truth for behavior.
- Keep adapters aligned with the Codex skill when changing commands or setup flow.
- Never commit real API keys or raw sensitive n8n exports.
- Prefer local config plus Keychain over hard-coded instance defaults.
- Start with `discover` before mutating workflows.
