# n8n Operations

- Canonical implementation: `codex/skills/n8n-self-hosted-admin/`
- Prefer the helper script over ad hoc API calls.
- Use `config-set-base-url` for local defaults and `keychain-set` for secrets on macOS.
- Treat `403` on some resources as likely license gating.
