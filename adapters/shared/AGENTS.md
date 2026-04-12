# n8n Self-Hosted Admin

This project uses a shared self-hosted n8n operations skill from:

`{{SKILL_REPO_PATH}}`

Canonical instructions live in:

- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/SKILL.md`
- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/references/api-surface.md`
- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/references/ops-playbook.md`

Canonical helper script:

- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py`

## Rules

- Treat the helper script and Codex skill folder as the source of truth.
- Never write real n8n API keys into this repository.
- Prefer `config-set-base-url` and macOS Keychain over hard-coded instance defaults.
- Start with `discover` before mutating workflows.
- Treat `403` responses on `projects` or `variables` as likely license limits unless other evidence points elsewhere.
