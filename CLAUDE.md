# n8n Self-Hosted Admin

Claude Code should treat this repository as a portable n8n operations skill pack.

## Source of Truth

- `codex/skills/n8n-self-hosted-admin/SKILL.md`
- `codex/skills/n8n-self-hosted-admin/references/api-surface.md`
- `codex/skills/n8n-self-hosted-admin/references/ops-playbook.md`
- `codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py`

## Rules

- Keep the Codex skill as the canonical behavior spec.
- Keep the adapters under `adapters/` aligned with the canonical skill.
- Prefer the helper script over one-off curl commands.
- Never commit secrets or raw sensitive exports.
