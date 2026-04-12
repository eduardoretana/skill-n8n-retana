---
name: "n8n-self-hosted-admin"
description: "Create, maintain, audit, and support self-hosted n8n instances through the public API. Use when Codex needs to inspect API capabilities, create or update workflows, publish or deactivate flows, review executions, generate security audits, manage projects/users/variables/credentials, or triage support issues on a self-hosted n8n instance without depending on the UI."
---

# n8n Self-Hosted Admin

## Overview

Use this skill to operate a self-hosted n8n instance through the public API with safe, reversible steps. Prefer API-backed inspection, snapshots, and narrow mutations over ad hoc UI work.

## Required Setup

- Keep secrets out of repos, notes, and skill files.
- Set the target instance once with either `N8N_BASE_URL`, `N8N_API_URL`, or the helper's local config:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" config-set-base-url "https://n8n.example.com"
```

- Recommended zero-friction setup on macOS: save the API key once in Keychain, then use the skill without exporting `N8N_API_KEY` again:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" keychain-set --base-url "https://n8n.example.com"
```

- Verify that Keychain storage is available with:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" keychain-status --base-url "https://n8n.example.com"
```

- If you do not want to use Keychain, export the base URL and API key in the shell:

```bash
export N8N_BASE_URL="https://n8n.example.com"
export N8N_API_KEY="..."
```

- Accept `N8N_API_URL` as an alias for `N8N_BASE_URL` when the environment already uses that name.
- Include any self-hosted path prefix in `N8N_BASE_URL`, for example `https://automation.example.com/n8n`.
- Treat any API token pasted by the user as sensitive material. Do not write it into the skill, the repo, shell history files, or long-lived notes.
- The helper resolves the base URL in this order: `--base-url`, `N8N_BASE_URL`, `N8N_API_URL`, local config file.
- The helper resolves the API key in this order: `--api-key`, `N8N_API_KEY`, macOS Keychain.

## First Move

Run discovery before making assumptions about scopes or available endpoints:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" discover
```

Use this first call to confirm:
- The API key is valid.
- The instance really exposes the public API.
- The key can see the resources needed for the task.
- If the instance does not implement `GET /discover`, the helper automatically falls back to the instance's `openapi.yml` and returns a capability map built from that spec.

## Default Workflow

1. Inspect capabilities.
   - Run `discover`.
   - If the task needs request shapes, run `discover --include-schemas` or read [api-surface.md](references/api-surface.md).
2. Choose a safe operating mode.
   - Use read-only commands for diagnosis first.
   - Only mutate workflows or executions after clarifying user intent when impact is non-obvious.
3. Snapshot before mutation.
   - Export the current workflow JSON before updating it.
   - Keep the backup outside the repo unless the user explicitly wants it versioned.
4. Apply the narrowest change possible.
   - Prefer a single workflow update over broad bulk operations.
   - Prefer `excludePinnedData=true` when topology is enough.
5. Re-read and verify.
   - Fetch the updated workflow again.
   - Confirm the expected shape, activation state, and any execution behavior change.
6. Close with an operator-grade summary.
   - State what changed, what was verified, what was not verified, and how to roll back.

## High-Value Commands

Use the bundled helper for the common tasks:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" discover --include-schemas
python3 "<path-to-skill>/scripts/n8n_admin.py" list workflows --query active=true --query excludePinnedData=true
python3 "<path-to-skill>/scripts/n8n_admin.py" get workflow "WORKFLOW_ID" --query excludePinnedData=true
python3 "<path-to-skill>/scripts/n8n_admin.py" workflow-update "WORKFLOW_ID" --file /tmp/workflow.json
python3 "<path-to-skill>/scripts/n8n_admin.py" workflow-activate "WORKFLOW_ID"
python3 "<path-to-skill>/scripts/n8n_admin.py" list executions --query status=error --limit 50
python3 "<path-to-skill>/scripts/n8n_admin.py" execution-retry "EXECUTION_ID" --load-workflow
python3 "<path-to-skill>/scripts/n8n_admin.py" audit --category credentials --category filesystem
python3 "<path-to-skill>/scripts/n8n_admin.py" support-report --limit 25
```

Use the generic request mode when the API surface grows beyond the opinionated helpers:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" request GET /projects
python3 "<path-to-skill>/scripts/n8n_admin.py" request POST /source-control/pull --data-file pull.json
```

## Operating Rules

- Start with `discover` for every new instance, key, or incident.
- Prefer the instance's built-in docs UI on self-hosted deployments. Avoid public playgrounds for sensitive data because the official docs site routes playground traffic through Scalar's proxy.
- Avoid writing workflow exports, support bundles, audits, or API responses into the current repo unless the user explicitly asks for tracked artifacts.
- Avoid printing credential secrets or variable values in summaries unless the user explicitly requests them and the scope is justified.
- Treat `execution-retry`, `execution-stop`, `workflow-activate`, `workflow-deactivate`, and write operations as operational changes, not diagnostics.
- Sanitize workflow payloads before create or update calls. The helper script strips common server-managed fields from fetched workflow JSON before replaying it.
- Prefer `GET /credentials/schema/{credentialTypeName}` before creating or editing credentials. Do not invent credential fields when the API can describe them.
- Treat `403` responses on resources such as `projects` or `variables` as likely license or feature-gating limits unless other evidence points to auth or transport problems.
- Prefer the local config command over hard-coding a default production instance into shared or public copies of this skill.

## Task Playbooks

### Create a workflow

1. Read [api-surface.md](references/api-surface.md) for the workflow schema surface.
2. Build the workflow JSON locally.
3. Run:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" workflow-create --file /tmp/new-workflow.json
```

4. Re-fetch the created workflow and confirm topology and settings.
5. Activate it only if the user asked for a live workflow.

### Update a workflow safely

1. Fetch a clean backup:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" get workflow "WORKFLOW_ID" --query excludePinnedData=true > /tmp/workflow.before.json
cp /tmp/workflow.before.json /tmp/workflow.edit.json
```

2. Edit `/tmp/workflow.edit.json`.
3. Apply the change:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" workflow-update "WORKFLOW_ID" --file /tmp/workflow.edit.json
```

4. Re-fetch after the update and compare with the backup.
5. Publish or deactivate only if needed.

### Audit an instance

1. Run the built-in audit:

```bash
python3 "<path-to-skill>/scripts/n8n_admin.py" audit --category credentials --category database --category filesystem --category instance --category nodes
```

2. If the API key allows it, inspect users, projects, credentials, variables, and executions.
3. Summarize risk by category, not by raw dump.
4. Redact or omit sensitive values from user-facing output.

### Support an incident

1. Run `support-report`.
2. List recent executions, focusing on `status=error`, `status=running`, or `status=waiting`.
3. Fetch the relevant workflow and confirm whether the issue is:
   - A single bad execution.
   - A broken workflow definition.
   - A credential or environment problem.
   - A permissions or project-scoping problem.
   - A plan or license limitation on the instance.
4. Use `execution-stop` or `execution-retry` only when the user wants an operational intervention.
5. Summarize current state, likely cause, immediate mitigation, and next verification step.

## Bundled Resources

- [scripts/n8n_admin.py](scripts/n8n_admin.py): Safe CLI wrapper for the public API, including discovery, workflow operations, execution actions, audits, and support reporting.
- [references/api-surface.md](references/api-surface.md): Concise map of the most useful API endpoints, auth expectations, pagination, and discovery.
- [references/ops-playbook.md](references/ops-playbook.md): Mutation, audit, and support sequences with recommended commands and guardrails.
