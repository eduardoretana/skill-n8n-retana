# n8n Public API Surface

## Baseline

- Public API base: `<instance-base>/api/v1`
- Authentication header: `X-N8N-API-KEY: <api-key>`
- Self-hosted interactive docs: `<instance-base>/api/v1/docs`
- Preferred capability discovery: `GET /discover`
- Compatibility fallback: `<instance-base>/api/v1/openapi.yml`
- Pagination: list endpoints accept `limit` and `cursor`; responses return `nextCursor`
- Current public spec default limit is `100` and max page size is `250`
- Some self-hosted builds expose the public API but not the newer `GET /discover` route.

## Discovery First

Use `GET /discover` before planning a mutation when the instance supports it. It returns the resources and operations available to the current API key.

Use `GET /discover?include=schemas` when you need inline request schemas without loading the full OpenAPI spec.

If `GET /discover` returns `404`, fall back to the instance's `openapi.yml`. The bundled helper already does this automatically.

This is the safest first request because it adapts to:
- Limited enterprise scopes
- Instance-level feature differences
- Future API growth

## High-Value Endpoint Groups

### Workflows

- `GET /workflows`
  Use to list workflows.
  Helpful query keys: `active`, `tags`, `name`, `projectId`, `excludePinnedData`
- `POST /workflows`
  Use to create a workflow.
- `GET /workflows/{id}`
  Use to fetch a workflow.
  Helpful query key: `excludePinnedData`
- `PUT /workflows/{id}`
  Use to update a workflow.
- `DELETE /workflows/{id}`
  Use to delete a workflow.
- `GET /workflows/{id}/{versionId}`
  Use to read a historical workflow version.
- `POST /workflows/{id}/activate`
  Use to publish or activate a workflow.
  Optional body keys: `versionId`, `name`, `description`
- `POST /workflows/{id}/deactivate`
  Use to deactivate a workflow.
- `PUT /workflows/{id}/transfer`
  Use to transfer ownership when supported.
- `GET` and `PUT /workflows/{id}/tags`
  Use to inspect or change workflow tags.

### Executions

- `GET /executions`
  Use to list executions.
  Helpful query keys: `includeData`, `status`, `workflowId`, `projectId`
- `GET /executions/{id}`
  Use to inspect one execution.
- `DELETE /executions/{id}`
  Use to remove one execution record.
- `POST /executions/{id}/retry`
  Use to retry one execution.
  Optional body key: `loadWorkflow`
- `POST /executions/{id}/stop`
  Use to stop one execution.
- `POST /executions/stop`
  Use to stop multiple executions by filters.
- `GET` and `PUT /executions/{id}/tags`
  Use to inspect or update execution annotation tags.

### Audit

- `POST /audit`
  Generate a security audit for the instance.
  Optional body shape:
  - `additionalOptions.daysAbandonedWorkflow`
  - `additionalOptions.categories`

Supported audit categories in the public spec:
- `credentials`
- `database`
- `nodes`
- `filesystem`
- `instance`

### Credentials

- `GET /credentials`
  List credentials without secrets.
- `POST /credentials`
  Create a credential.
- `PATCH /credentials/{id}`
  Update a credential.
- `DELETE /credentials/{id}`
  Delete a credential.
- `GET /credentials/schema/{credentialTypeName}`
  Fetch the schema for a credential type before building or updating a payload.
- `PUT /credentials/{id}/transfer`
  Transfer a credential when supported.

### Users

- `GET /users`
  List users.
  Useful query keys: `includeRole`, `projectId`
- `POST /users`
  Invite or create one or more users.
- `GET /users/{id}`
  Fetch a user by ID or email.
- `DELETE /users/{id}`
  Remove a user.
- `PATCH /users/{id}/role`
  Change a user's global role.

### Projects

- `GET /projects`
  List projects.
- `POST /projects`
  Create a project.
- `PUT /projects/{projectId}`
  Update a project.
- `DELETE /projects/{projectId}`
  Delete a project.
- `GET /projects/{projectId}/users`
  List project members.
- `POST /projects/{projectId}/users`
  Add members to a project.
- `DELETE /projects/{projectId}/users/{userId}`
  Remove a user from a project.

### Variables

- `GET /variables`
  List variables.
  Helpful query keys: `projectId`, `state`
- `POST /variables`
  Create a variable.
- `DELETE /variables/{id}`
  Delete a variable.

### Source Control

- `POST /source-control/pull`
  Pull changes from the configured remote repository.
  Use only when the feature is licensed and already connected.

## Guardrails

- Prefer `discover` over guessing whether a key can mutate users, credentials, or projects.
- If `discover` is unavailable, prefer the helper's OpenAPI fallback over hard-coding assumptions about endpoints.
- Prefer `excludePinnedData=true` when you only need workflow structure.
- Prefer first-party instance docs at `/api/v1/docs` for sensitive environments.
- Use test keys with limited scopes when interacting with the public docs site's playground because those requests traverse Scalar's proxy.
- Expect some endpoints to return `403` when the instance license does not include that feature. Treat that as product capability evidence, not automatically as an auth failure.
