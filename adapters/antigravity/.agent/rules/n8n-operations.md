# n8n Operations

- Canonical n8n skill repo: `{{SKILL_REPO_PATH}}`
- Source of truth skill: `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/SKILL.md`
- Canonical helper: `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py`
- Start with `discover` before mutations.
- Prefer `config-set-base-url` plus `keychain-set` for local setup.
- Keep workflow backups and support dumps outside the target repo unless explicitly requested.
- Treat `403` on feature areas like `projects` or `variables` as likely license gating.
