# n8n Self-Hosted Admin

Claude Code should use the shared self-hosted n8n admin skill stored at:

`{{SKILL_REPO_PATH}}`

## Canonical Files

- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/SKILL.md`
- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/references/api-surface.md`
- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/references/ops-playbook.md`
- `{{SKILL_REPO_PATH}}/codex/skills/n8n-self-hosted-admin/scripts/n8n_admin.py`

## Operating Rules

- Prefer the canonical helper script over ad hoc curl commands.
- Start with `discover` before making workflow changes.
- Use `config-set-base-url` for convenience and `keychain-set` for secrets on macOS.
- Keep workflow backups outside the target repo unless the user explicitly wants them committed.
- Never store real API keys or raw sensitive exports in the target repo.
- Treat `403` on some resources as a likely n8n plan or license limitation.
