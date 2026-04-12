# n8n Self-Hosted Admin

Gemini should use the shared self-hosted n8n admin skill stored at:

`{{SKILL_REPO_PATH}}`

## Canonical Files

- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/SKILL.md`
- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/references/api-surface.md`
- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/references/ops-playbook.md`
- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py`

## Core Rules

- Use the helper script as the default execution path for n8n tasks.
- Start with `discover` and prefer read-only inspection first.
- Use local config and Keychain instead of hard-coded instance defaults.
- Never write secrets into the repo.
- Treat license-gated `403` responses as product capability evidence, not automatically as invalid credentials.
