# n8n Ops Playbook

## Preflight

1. Set the default instance once:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" config-set-base-url "https://n8n.example.com"
```

2. Prefer one-time Keychain setup on macOS:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" keychain-set --base-url "https://n8n.example.com"
```

3. Confirm the key is available:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" keychain-status --base-url "https://n8n.example.com"
```

4. If you are not using Keychain, export `N8N_BASE_URL` and `N8N_API_KEY`.
5. Run:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" discover
```

6. Confirm the key can see the resource you need.
7. If `discover` falls back to `openapi.yml`, keep working normally. That usually means the instance is on an older or different public API surface, not that auth failed.
8. Avoid production mutations until you have a backup or rollback path.

## Read-Only Triage

Use this sequence first:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" support-report --limit 25
python3 "<path-to-skill>/scripts/n8n_admin.py" list workflows --query excludePinnedData=true --limit 100
python3 "<path-to-skill>/scripts/n8n_admin.py" list executions --query status=error --limit 50
```

Use `request` for resources the helper does not wrap directly:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" request GET /projects
python3 "<path-to-skill>/scripts/n8n_admin.py" request GET /projects/PROJECT_ID/users
```

If `projects` or `variables` return `403`, treat that as a likely license limit before assuming the key is broken.

## Safe Workflow Update

1. Fetch a backup:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" get workflow "WORKFLOW_ID" --query excludePinnedData=true > /tmp/workflow.before.json
cp /tmp/workflow.before.json /tmp/workflow.edit.json
```

2. Edit `/tmp/workflow.edit.json`.
3. Apply:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" workflow-update "WORKFLOW_ID" --file /tmp/workflow.edit.json
```

4. Re-read:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" get workflow "WORKFLOW_ID" --query excludePinnedData=true > /tmp/workflow.after.json
```

5. Compare before and after.
6. Activate or deactivate only if the desired operational state changed.

## New Workflow

1. Build the workflow JSON locally.
2. Create it:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" workflow-create --file /tmp/new-workflow.json
```

3. Fetch the created object and verify nodes, connections, and settings.
4. Publish only after the user confirms the workflow should go live.

## Execution Intervention

Inspect before intervening:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" get execution "EXECUTION_ID" --query includeData=true
```

Use narrow interventions:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" execution-stop "EXECUTION_ID"
python3 "<path-to-skill>/scripts/n8n_admin.py" execution-retry "EXECUTION_ID" --load-workflow
```

Prefer retrying one failed execution over broad stop operations unless the user explicitly wants a wider incident response.

## Credentials and Variables

- Fetch a credential schema before constructing a credential payload:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" credential-schema "slackOAuth2Api"
```

- Do not print credential secrets in summaries.
- Do not dump variable values unless the user explicitly requests them.
- Prefer counts, names, scopes, or metadata over raw sensitive fields.

## Audit Sequence

Run the built-in audit first:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" audit \
  --category credentials \
  --category database \
  --category filesystem \
  --category instance \
  --category nodes
```

Then extend with targeted inspection if the key allows it:
- `list users`
- `list credentials`
- `list variables`
- `request GET /projects`

Summarize findings by severity, blast radius, and fix effort instead of pasting the full raw report unless the user asks for the raw JSON.
If `variables` or `projects` are blocked by license, report that explicitly as an instance capability limit.
