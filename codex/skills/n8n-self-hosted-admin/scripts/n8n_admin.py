#!/usr/bin/env python3
"""Portable self-hosted n8n public API helper."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT = 30
DEFAULT_PAGE_LIMIT = 100
MAX_PAGE_LIMIT = 250
DEFAULT_KEYCHAIN_ACCOUNT = os.environ.get("USER", "codex")
AUDIT_CATEGORIES = ("credentials", "database", "nodes", "filesystem", "instance")
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "n8n-self-hosted-admin"
CONFIG_PATH = CONFIG_DIR / "config.json"

LIST_RESOURCES = {
    "workflows": "/workflows",
    "executions": "/executions",
    "credentials": "/credentials",
    "users": "/users",
    "variables": "/variables",
    "projects": "/projects",
    "tags": "/tags",
}

DISCOVER_RESOURCE_MAP = {
    "audit": "audit",
    "credentials": "credential",
    "data-tables": "data-table",
    "executions": "execution",
    "projects": "project",
    "source-control": "source-control",
    "tags": "tag",
    "users": "user",
    "variables": "variable",
    "workflows": "workflow",
}

GET_RESOURCES = {
    "workflow": "/workflows/{id}",
    "execution": "/executions/{id}",
    "user": "/users/{id}",
}

WORKFLOW_SERVER_FIELDS = {
    "active",
    "activeVersion",
    "createdAt",
    "id",
    "isArchived",
    "meta",
    "shared",
    "tags",
    "triggerCount",
    "updatedAt",
    "versionId",
}


class ApiError(RuntimeError):
    """Raised when the API responds with an actionable error."""


def fail(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_key_value_pairs(items: list[str] | None) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            fail(f"Invalid key=value pair: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            fail(f"Invalid key=value pair: {item}")
        pairs[key] = value
    return pairs


def load_json_file(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        fail(f"JSON file not found: {path}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {path}: {exc}")


def write_output(payload: Any, output: str | None = None, *, as_json: bool = True) -> None:
    if as_json:
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    else:
        text = str(payload)
        if not text.endswith("\n"):
            text += "\n"

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text)
    else:
        sys.stdout.write(text)


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        content = json.loads(CONFIG_PATH.read_text())
    except json.JSONDecodeError as exc:
        fail(f"Invalid config file {CONFIG_PATH}: {exc}")
    if not isinstance(content, dict):
        fail(f"Invalid config file {CONFIG_PATH}: expected a JSON object.")
    return content


def save_config(config: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")


def normalize_base_url(base_url: str, api_version: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base:
        fail("A base URL is required. Use --base-url, N8N_BASE_URL, N8N_API_URL, or config-set-base-url.")

    expected_suffix = f"/api/{api_version}"
    if base.endswith(expected_suffix):
        return base
    if "/api/" in base:
        return base
    return f"{base}{expected_suffix}"


def sanitize_workflow_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        fail("Workflow payload must be a JSON object.")

    sanitized = {key: value for key, value in payload.items() if key not in WORKFLOW_SERVER_FIELDS}
    for required_key in ("name", "nodes", "connections"):
        if required_key not in sanitized:
            fail(f"Workflow payload is missing required key: {required_key}")

    sanitized.setdefault("settings", {})
    return sanitized


def get_keychain_service(base_url: str) -> str:
    parsed = urlparse(base_url)
    host = parsed.netloc or parsed.path or "default"
    host = host.rstrip("/")
    return f"codex:n8n-self-hosted-admin:{host}"


def keychain_available() -> bool:
    return shutil.which("security") is not None


def read_api_key_from_keychain(service: str, account: str) -> str | None:
    if not keychain_available():
        return None
    result = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def save_api_key_to_keychain(service: str, account: str, api_key: str) -> None:
    if not keychain_available():
        fail("macOS Keychain is not available on this system.")
    result = subprocess.run(
        ["security", "add-generic-password", "-U", "-s", service, "-a", account, "-w", api_key],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "Unknown Keychain error"
        raise ApiError(f"Could not save API key to Keychain: {stderr}")


def delete_api_key_from_keychain(service: str, account: str) -> bool:
    if not keychain_available():
        return False
    result = subprocess.run(
        ["security", "delete-generic-password", "-s", service, "-a", account],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def resolve_base_url(args: argparse.Namespace) -> str:
    config = load_config()
    base_url = args.base_url or os.environ.get("N8N_BASE_URL") or os.environ.get("N8N_API_URL") or config.get("default_base_url")
    if not base_url:
        fail("n8n base URL not found. Use --base-url, N8N_BASE_URL, N8N_API_URL, or run `config-set-base-url`.")
    return base_url


def resolve_keychain_account(args: argparse.Namespace) -> str:
    config = load_config()
    return args.keychain_account or os.environ.get("N8N_KEYCHAIN_ACCOUNT") or config.get("default_keychain_account") or DEFAULT_KEYCHAIN_ACCOUNT


class N8nClient:
    """Minimal JSON client for the n8n public API."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        api_version: str,
        insecure: bool = False,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            fail("n8n API key not found. Use --api-key, N8N_API_KEY, or run `keychain-set` once on macOS.")
        self.api_base = normalize_base_url(base_url, api_version)
        self.api_key = api_key
        self.timeout = timeout
        self.ssl_context = ssl._create_unverified_context() if insecure else None

    def _url(self, path: str, query: dict[str, Any] | None = None) -> str:
        api_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.api_base}{api_path}"
        if query:
            clean_query = {key: value for key, value in query.items() if value is not None and value != ""}
            if clean_query:
                url = f"{url}?{urlencode(clean_query, doseq=True)}"
        return url

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        data: Any = None,
    ) -> Any:
        body = None
        headers = {
            "Accept": "application/json",
            "X-N8N-API-KEY": self.api_key,
        }
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(self._url(path, query), data=body, headers=headers, method=method.upper())

        try:
            with urlopen(request, timeout=self.timeout, context=self.ssl_context) as response:
                raw = response.read().decode("utf-8").strip()
                if not raw:
                    return None
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return raw
        except HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            try:
                parsed_body = json.loads(response_body)
                response_body = json.dumps(parsed_body, indent=2, sort_keys=True)
            except json.JSONDecodeError:
                response_body = response_body.strip()
            raise ApiError(f"HTTP {exc.code} for {method.upper()} {path}\n{response_body}") from exc
        except URLError as exc:
            raise ApiError(f"Failed to reach n8n API: {exc.reason}") from exc

    def list_endpoint(
        self,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        limit: int = DEFAULT_PAGE_LIMIT,
        all_pages: bool = False,
    ) -> Any:
        params = dict(query or {})
        params["limit"] = max(1, min(limit, MAX_PAGE_LIMIT))

        if not all_pages:
            return self.request("GET", path, query=params)

        aggregated: list[Any] = []
        cursor = None

        while True:
            page_params = dict(params)
            if cursor:
                page_params["cursor"] = cursor
            page = self.request("GET", path, query=page_params)
            if not isinstance(page, dict) or "data" not in page:
                return page
            aggregated.extend(page.get("data", []))
            cursor = page.get("nextCursor")
            if not cursor:
                return {"data": aggregated, "nextCursor": None}


def classify_operation(method: str, path: str) -> str:
    normalized_path = path.strip("/")
    segments = normalized_path.split("/") if normalized_path else []
    method = method.lower()

    if method == "get":
        if len(segments) <= 1 or (len(segments) == 2 and segments[1].startswith("{")):
            return "list" if len(segments) == 1 else "read"
        return "read"
    if method == "post":
        if path == "/audit":
            return "generate"
        if any(part in {"activate", "deactivate", "retry", "stop", "pull", "transfer"} for part in segments):
            return "action"
        return "create"
    if method in {"put", "patch"}:
        if any(part in {"activate", "deactivate", "retry", "stop", "pull", "transfer"} for part in segments):
            return "action"
        return "update"
    if method == "delete":
        return "delete"
    return method


def resource_from_path(path: str) -> str:
    segments = path.strip("/").split("/")
    head = segments[0] if segments and segments[0] else "root"
    return DISCOVER_RESOURCE_MAP.get(head, head.rstrip("s") or head)


def fallback_discover_from_openapi(client: N8nClient, args: argparse.Namespace) -> dict[str, Any]:
    raw_spec = client.request("GET", "/openapi.yml")
    if not isinstance(raw_spec, str):
        raise ApiError("OpenAPI fallback did not return text.")

    resources: dict[str, dict[str, Any]] = {}
    current_path: str | None = None

    for line in raw_spec.splitlines():
        path_match = re.match(r"^  (/[^:]+):\s*$", line)
        if path_match:
            current_path = path_match.group(1)
            continue

        method_match = re.match(r"^    (get|post|put|patch|delete):\s*$", line)
        if not current_path or not method_match:
            continue

        method = method_match.group(1)
        resource_name = resource_from_path(current_path)
        operation = classify_operation(method, current_path)

        bucket = resources.setdefault(resource_name, {"operations": [], "endpoints": []})
        if operation not in bucket["operations"]:
            bucket["operations"].append(operation)
        bucket["endpoints"].append({"method": method.upper(), "path": current_path, "operation": operation})

    if args.resource:
        resources = {name: value for name, value in resources.items() if name == args.resource}

    if args.operation:
        filtered_resources: dict[str, dict[str, Any]] = {}
        for name, value in resources.items():
            endpoints = [item for item in value["endpoints"] if item["operation"] == args.operation]
            if not endpoints:
                continue
            filtered_resources[name] = {
                "operations": sorted({item["operation"] for item in endpoints}),
                "endpoints": endpoints,
            }
        resources = filtered_resources

    for value in resources.values():
        value["operations"] = sorted(value["operations"])

    return {
        "data": {
            "scopes": [],
            "resources": resources,
            "filters": {},
        },
        "meta": {
            "source": "openapi-fallback",
            "discoverEndpointAvailable": False,
        },
    }


def build_client(args: argparse.Namespace) -> N8nClient:
    base_url = resolve_base_url(args)
    keychain_service = args.keychain_service or os.environ.get("N8N_KEYCHAIN_SERVICE") or get_keychain_service(base_url)
    keychain_account = resolve_keychain_account(args)
    api_key = args.api_key or os.environ.get("N8N_API_KEY") or read_api_key_from_keychain(keychain_service, keychain_account)
    return N8nClient(
        base_url=base_url,
        api_key=api_key or "",
        api_version=args.api_version,
        insecure=args.insecure,
        timeout=args.timeout,
    )


def command_config_show(args: argparse.Namespace) -> str:
    config = load_config()
    return (
        "# n8n Local Config\n\n"
        f"- Config path: `{CONFIG_PATH}`\n"
        f"- Default base URL: `{config.get('default_base_url', 'unset')}`\n"
        f"- Default keychain account: `{config.get('default_keychain_account', DEFAULT_KEYCHAIN_ACCOUNT)}`\n"
    )


def command_config_set_base_url(args: argparse.Namespace) -> str:
    config = load_config()
    config["default_base_url"] = args.base_url_value.rstrip("/")
    save_config(config)
    return (
        "# n8n Local Config\n\n"
        f"- Config path: `{CONFIG_PATH}`\n"
        f"- Default base URL: `{config['default_base_url']}`\n"
        "- Result: `stored`\n"
    )


def command_config_clear_base_url(args: argparse.Namespace) -> str:
    config = load_config()
    previous = config.pop("default_base_url", None)
    save_config(config)
    result = "deleted" if previous else "not-found"
    return (
        "# n8n Local Config\n\n"
        f"- Config path: `{CONFIG_PATH}`\n"
        f"- Result: `{result}`\n"
    )


def command_discover(client: N8nClient, args: argparse.Namespace) -> Any:
    query: dict[str, Any] = {}
    if args.include_schemas:
        query["include"] = "schemas"
    if args.resource:
        query["resource"] = args.resource
    if args.operation:
        query["operation"] = args.operation
    try:
        return client.request("GET", "/discover", query=query)
    except ApiError as exc:
        if "HTTP 404" not in str(exc):
            raise
        return fallback_discover_from_openapi(client, args)


def command_request(client: N8nClient, args: argparse.Namespace) -> Any:
    query = parse_key_value_pairs(args.query)
    data = None
    if args.data_json and args.data_file:
        fail("Use either --data-json or --data-file, not both.")
    if args.data_json:
        try:
            data = json.loads(args.data_json)
        except json.JSONDecodeError as exc:
            fail(f"Invalid JSON passed to --data-json: {exc}")
    elif args.data_file:
        data = load_json_file(args.data_file)

    if args.paginate:
        return client.list_endpoint(args.path, query=query, limit=args.limit, all_pages=True)
    return client.request(args.method, args.path, query=query, data=data)


def command_list(client: N8nClient, args: argparse.Namespace) -> Any:
    query = parse_key_value_pairs(args.query)
    return client.list_endpoint(LIST_RESOURCES[args.resource], query=query, limit=args.limit, all_pages=args.all)


def command_get(client: N8nClient, args: argparse.Namespace) -> Any:
    query = parse_key_value_pairs(args.query)
    return client.request("GET", GET_RESOURCES[args.resource].format(id=args.identifier), query=query)


def command_credential_schema(client: N8nClient, args: argparse.Namespace) -> Any:
    return client.request("GET", f"/credentials/schema/{args.credential_type_name}")


def command_workflow_create(client: N8nClient, args: argparse.Namespace) -> Any:
    payload = load_json_file(args.file)
    if not args.no_sanitize:
        payload = sanitize_workflow_payload(payload)
    return client.request("POST", "/workflows", data=payload)


def command_workflow_update(client: N8nClient, args: argparse.Namespace) -> Any:
    payload = load_json_file(args.file)
    if not args.no_sanitize:
        payload = sanitize_workflow_payload(payload)
    return client.request("PUT", f"/workflows/{args.workflow_id}", data=payload)


def command_workflow_activate(client: N8nClient, args: argparse.Namespace) -> Any:
    payload = {key: value for key, value in {"versionId": args.version_id, "name": args.name, "description": args.description}.items() if value}
    return client.request("POST", f"/workflows/{args.workflow_id}/activate", data=payload or None)


def command_workflow_deactivate(client: N8nClient, args: argparse.Namespace) -> Any:
    return client.request("POST", f"/workflows/{args.workflow_id}/deactivate")


def command_execution_retry(client: N8nClient, args: argparse.Namespace) -> Any:
    body = {"loadWorkflow": True} if args.load_workflow else None
    return client.request("POST", f"/executions/{args.execution_id}/retry", data=body)


def command_execution_stop(client: N8nClient, args: argparse.Namespace) -> Any:
    return client.request("POST", f"/executions/{args.execution_id}/stop")


def command_audit(client: N8nClient, args: argparse.Namespace) -> Any:
    body: dict[str, Any] = {"additionalOptions": {}}
    if args.days_abandoned_workflow is not None:
        body["additionalOptions"]["daysAbandonedWorkflow"] = args.days_abandoned_workflow
    if args.category:
        body["additionalOptions"]["categories"] = args.category
    return client.request("POST", "/audit", data=body if body["additionalOptions"] else None)


def command_keychain_set(args: argparse.Namespace) -> str:
    base_url = resolve_base_url(args)
    keychain_service = args.keychain_service or os.environ.get("N8N_KEYCHAIN_SERVICE") or get_keychain_service(base_url)
    keychain_account = resolve_keychain_account(args)
    api_key = args.api_key or getpass.getpass("Enter n8n API key: ").strip()
    if not api_key:
        fail("API key cannot be empty.")
    save_api_key_to_keychain(keychain_service, keychain_account, api_key)
    return (
        "# n8n Keychain Setup\n\n"
        f"- Base URL: `{base_url}`\n"
        f"- Keychain service: `{keychain_service}`\n"
        f"- Keychain account: `{keychain_account}`\n"
        "- Result: `stored`\n"
    )


def command_keychain_status(args: argparse.Namespace) -> str:
    base_url = resolve_base_url(args)
    keychain_service = args.keychain_service or os.environ.get("N8N_KEYCHAIN_SERVICE") or get_keychain_service(base_url)
    keychain_account = resolve_keychain_account(args)
    api_key = read_api_key_from_keychain(keychain_service, keychain_account)
    status = "present" if api_key else "missing"
    return (
        "# n8n Keychain Status\n\n"
        f"- Base URL: `{base_url}`\n"
        f"- Keychain service: `{keychain_service}`\n"
        f"- Keychain account: `{keychain_account}`\n"
        f"- API key: `{status}`\n"
    )


def command_keychain_delete(args: argparse.Namespace) -> str:
    base_url = resolve_base_url(args)
    keychain_service = args.keychain_service or os.environ.get("N8N_KEYCHAIN_SERVICE") or get_keychain_service(base_url)
    keychain_account = resolve_keychain_account(args)
    deleted = delete_api_key_from_keychain(keychain_service, keychain_account)
    result = "deleted" if deleted else "not-found"
    return (
        "# n8n Keychain Delete\n\n"
        f"- Base URL: `{base_url}`\n"
        f"- Keychain service: `{keychain_service}`\n"
        f"- Keychain account: `{keychain_account}`\n"
        f"- Result: `{result}`\n"
    )


def _support_list(client: N8nClient, resource: str, *, limit: int, query: dict[str, Any] | None = None) -> Any:
    return client.list_endpoint(LIST_RESOURCES[resource], query=query, limit=limit, all_pages=False)


def _summarize_page(page: Any) -> tuple[int, bool]:
    if isinstance(page, dict) and isinstance(page.get("data"), list):
        return len(page["data"]), bool(page.get("nextCursor"))
    return 0, False


def command_support_report(client: N8nClient, args: argparse.Namespace) -> str:
    discover = command_discover(client, argparse.Namespace(include_schemas=False, resource=None, operation=None))
    scopes = []
    resources: dict[str, Any] = {}
    if isinstance(discover, dict):
        data = discover.get("data") or {}
        scopes = data.get("scopes") or []
        resources = data.get("resources") or {}

    lines = [
        "# n8n Support Report",
        "",
        f"- API base: `{client.api_base}`",
        f"- Active scopes: `{', '.join(scopes) if scopes else 'unknown or unrestricted'}`",
        f"- Discoverable resources: `{', '.join(sorted(resources.keys())) if resources else 'unknown'}`",
        "",
    ]

    try:
        workflows_page = _support_list(client, "workflows", limit=args.limit, query={"excludePinnedData": "true"})
        count, has_more = _summarize_page(workflows_page)
        lines.extend(["## Workflows", "", f"- Page items: `{count}`", f"- More pages: `{has_more}`"])
        if isinstance(workflows_page, dict):
            for item in workflows_page.get("data", [])[: args.limit]:
                lines.append(f"- `{item.get('id', '?')}` | {item.get('name', '(unnamed)')} | active={item.get('active')} | updated={item.get('updatedAt')}")
        lines.append("")
    except ApiError as exc:
        lines.extend(["## Workflows", "", f"- Could not read workflows: `{exc}`", ""])

    try:
        executions_page = _support_list(client, "executions", limit=args.limit)
        count, has_more = _summarize_page(executions_page)
        lines.extend(["## Executions", "", f"- Page items: `{count}`", f"- More pages: `{has_more}`"])
        if isinstance(executions_page, dict):
            for item in executions_page.get("data", [])[: args.limit]:
                lines.append(f"- `{item.get('id', '?')}` | status={item.get('status')} | workflowId={item.get('workflowId')} | started={item.get('startedAt')} | stopped={item.get('stoppedAt')}")
        lines.append("")
    except ApiError as exc:
        lines.extend(["## Executions", "", f"- Could not read executions: `{exc}`", ""])

    for resource in ("projects", "users", "credentials", "variables"):
        try:
            page = _support_list(client, resource, limit=min(args.limit, 50))
            count, has_more = _summarize_page(page)
            lines.extend([f"## {resource.title()}", "", f"- Page items: `{count}`", f"- More pages: `{has_more}`", ""])
        except ApiError as exc:
            lines.extend([f"## {resource.title()}", "", f"- Could not read {resource}: `{exc}`", ""])

    lines.extend([
        "## Next Steps",
        "",
        "- Inspect one failing execution if the issue is runtime-only.",
        "- Fetch the workflow JSON if the failure looks structural.",
        "- Run `audit` if the issue may involve credentials, filesystem, or instance configuration.",
    ])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate a self-hosted n8n instance through the public API.")
    parser.add_argument(
        "--base-url",
        help="n8n base URL or API URL. Defaults to N8N_BASE_URL, N8N_API_URL, or the local config file.",
    )
    parser.add_argument("--api-key", help="n8n API key. Defaults to N8N_API_KEY or macOS Keychain.")
    parser.add_argument("--keychain-service", help="macOS Keychain service override. Defaults to a service derived from the base URL.")
    parser.add_argument("--keychain-account", help=f"macOS Keychain account override. Defaults to {DEFAULT_KEYCHAIN_ACCOUNT}.")
    parser.add_argument("--api-version", default="v1", help="Public API version. Defaults to v1.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="HTTP timeout in seconds.")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    config_show = subparsers.add_parser("config-show", help="Show local n8n helper config.")
    config_show.add_argument("--output", help="Write Markdown output to a file.")

    config_set = subparsers.add_parser("config-set-base-url", help="Store the default base URL in local config.")
    config_set.add_argument("base_url_value", help="n8n instance base URL.")
    config_set.add_argument("--output", help="Write Markdown output to a file.")

    config_clear = subparsers.add_parser("config-clear-base-url", help="Remove the stored default base URL from local config.")
    config_clear.add_argument("--output", help="Write Markdown output to a file.")

    discover = subparsers.add_parser("discover", help="Inspect API capabilities for the current key.")
    discover.add_argument("--resource", help="Filter discover output to one resource.")
    discover.add_argument("--operation", help="Filter discover output to one operation.")
    discover.add_argument("--include-schemas", action="store_true", help='Include request schemas when available.')
    discover.add_argument("--output", help="Write JSON output to a file.")

    request = subparsers.add_parser("request", help="Send an arbitrary API request.")
    request.add_argument("method", help="HTTP method.")
    request.add_argument("path", help="API path such as /projects or /source-control/pull.")
    request.add_argument("--query", action="append", help="Query parameter in key=value form.")
    request.add_argument("--data-json", help="Inline JSON request body.")
    request.add_argument("--data-file", help="Path to a JSON file for the request body.")
    request.add_argument("--paginate", action="store_true", help="Follow nextCursor until all pages are collected.")
    request.add_argument("--limit", type=int, default=DEFAULT_PAGE_LIMIT, help="Page size when --paginate is used.")
    request.add_argument("--output", help="Write JSON output to a file.")

    list_parser = subparsers.add_parser("list", help="List a common resource.")
    list_parser.add_argument("resource", choices=sorted(LIST_RESOURCES), help="Plural resource name.")
    list_parser.add_argument("--query", action="append", help="Query parameter in key=value form.")
    list_parser.add_argument("--limit", type=int, default=DEFAULT_PAGE_LIMIT, help="Page size. Max 250.")
    list_parser.add_argument("--all", action="store_true", help="Follow nextCursor until all pages are collected.")
    list_parser.add_argument("--output", help="Write JSON output to a file.")

    get_parser = subparsers.add_parser("get", help="Fetch a common single resource.")
    get_parser.add_argument("resource", choices=sorted(GET_RESOURCES), help="Singular resource name.")
    get_parser.add_argument("identifier", help="Resource identifier.")
    get_parser.add_argument("--query", action="append", help="Query parameter in key=value form.")
    get_parser.add_argument("--output", help="Write JSON output to a file.")

    schema = subparsers.add_parser("credential-schema", help="Fetch the schema for a credential type.")
    schema.add_argument("credential_type_name", help="Credential type name, for example slackOAuth2Api.")
    schema.add_argument("--output", help="Write JSON output to a file.")

    workflow_create = subparsers.add_parser("workflow-create", help="Create a workflow from JSON.")
    workflow_create.add_argument("--file", required=True, help="Path to the workflow JSON file.")
    workflow_create.add_argument("--no-sanitize", action="store_true", help="Send the workflow JSON as-is.")
    workflow_create.add_argument("--output", help="Write JSON output to a file.")

    workflow_update = subparsers.add_parser("workflow-update", help="Update a workflow from JSON.")
    workflow_update.add_argument("workflow_id", help="Workflow ID.")
    workflow_update.add_argument("--file", required=True, help="Path to the workflow JSON file.")
    workflow_update.add_argument("--no-sanitize", action="store_true", help="Send the workflow JSON as-is.")
    workflow_update.add_argument("--output", help="Write JSON output to a file.")

    workflow_activate = subparsers.add_parser("workflow-activate", help="Activate or publish a workflow.")
    workflow_activate.add_argument("workflow_id", help="Workflow ID.")
    workflow_activate.add_argument("--version-id", help="Specific workflow version to publish.")
    workflow_activate.add_argument("--name", help="Optional version name.")
    workflow_activate.add_argument("--description", help="Optional version description.")
    workflow_activate.add_argument("--output", help="Write JSON output to a file.")

    workflow_deactivate = subparsers.add_parser("workflow-deactivate", help="Deactivate a workflow.")
    workflow_deactivate.add_argument("workflow_id", help="Workflow ID.")
    workflow_deactivate.add_argument("--output", help="Write JSON output to a file.")

    execution_retry = subparsers.add_parser("execution-retry", help="Retry one execution.")
    execution_retry.add_argument("execution_id", help="Execution ID.")
    execution_retry.add_argument("--load-workflow", action="store_true", help="Retry using the latest saved workflow definition.")
    execution_retry.add_argument("--output", help="Write JSON output to a file.")

    execution_stop = subparsers.add_parser("execution-stop", help="Stop one execution.")
    execution_stop.add_argument("execution_id", help="Execution ID.")
    execution_stop.add_argument("--output", help="Write JSON output to a file.")

    audit = subparsers.add_parser("audit", help="Generate an instance security audit.")
    audit.add_argument("--category", action="append", choices=AUDIT_CATEGORIES, help="Audit category to include.")
    audit.add_argument("--days-abandoned-workflow", type=int, help="Treat workflows older than this as abandoned.")
    audit.add_argument("--output", help="Write JSON output to a file.")

    support = subparsers.add_parser("support-report", help="Generate a compact Markdown support summary.")
    support.add_argument("--limit", type=int, default=25, help="Items to inspect per resource page.")
    support.add_argument("--output", help="Write Markdown output to a file.")

    keychain_set = subparsers.add_parser("keychain-set", help="Store the n8n API key in macOS Keychain.")
    keychain_set.add_argument("--api-key", dest="setup_api_key", help="API key to store. If omitted, the command prompts securely.")
    keychain_set.add_argument("--output", help="Write Markdown output to a file.")

    keychain_status = subparsers.add_parser("keychain-status", help="Check whether an API key exists in macOS Keychain.")
    keychain_status.add_argument("--output", help="Write Markdown output to a file.")

    keychain_delete = subparsers.add_parser("keychain-delete", help="Delete the stored n8n API key from macOS Keychain.")
    keychain_delete.add_argument("--output", help="Write Markdown output to a file.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if getattr(args, "setup_api_key", None) is not None:
        args.api_key = args.setup_api_key

    text_handlers = {
        "config-show": command_config_show,
        "config-set-base-url": command_config_set_base_url,
        "config-clear-base-url": command_config_clear_base_url,
        "keychain-set": command_keychain_set,
        "keychain-status": command_keychain_status,
        "keychain-delete": command_keychain_delete,
    }

    if args.command in text_handlers:
        try:
            output = text_handlers[args.command](args)
            write_output(output, getattr(args, "output", None), as_json=False)
            return 0
        except ApiError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    client = build_client(args)
    handlers = {
        "discover": command_discover,
        "request": command_request,
        "list": command_list,
        "get": command_get,
        "credential-schema": command_credential_schema,
        "workflow-create": command_workflow_create,
        "workflow-update": command_workflow_update,
        "workflow-activate": command_workflow_activate,
        "workflow-deactivate": command_workflow_deactivate,
        "execution-retry": command_execution_retry,
        "execution-stop": command_execution_stop,
        "audit": command_audit,
    }

    try:
        if args.command == "support-report":
            write_output(command_support_report(client, args), args.output, as_json=False)
        else:
            write_output(handlers[args.command](client, args), getattr(args, "output", None), as_json=True)
        return 0
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
