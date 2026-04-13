#!/usr/bin/env python3
"""Repository validation for skill-n8n-retana."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "codex" / "skills" / "n8n-self-hosted-admin"
INSTALLER = REPO_ROOT / "scripts" / "install.py"
PYTHON_FILES = [
    REPO_ROOT / "codex" / "skills" / "n8n-self-hosted-admin" / "scripts" / "n8n_admin.py",
    REPO_ROOT / "scripts" / "install.py",
    REPO_ROOT / "scripts" / "validate.py",
]
EXPECTED_TOP_LEVEL = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "LICENSE",
    REPO_ROOT / "CHANGELOG.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / "GEMINI.md",
]


def fail(message: str) -> None:
    raise SystemExit(f"[ERROR] {message}")


def validate_exists() -> None:
    for path in EXPECTED_TOP_LEVEL:
        if not path.exists():
            fail(f"Missing required file: {path}")
    if not SKILL_DIR.exists():
        fail(f"Missing Codex skill directory: {SKILL_DIR}")


def validate_skill_frontmatter() -> None:
    skill_md = SKILL_DIR / "SKILL.md"
    content = skill_md.read_text()
    if not content.startswith("---"):
        fail("SKILL.md missing YAML frontmatter.")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        fail("SKILL.md frontmatter is malformed.")
    frontmatter_text = match.group(1)
    try:
        import yaml  # type: ignore
    except ImportError:
        fail("PyYAML is required for validation in this repo.")
    frontmatter = yaml.safe_load(frontmatter_text)
    if not isinstance(frontmatter, dict):
        fail("SKILL.md frontmatter must parse to a mapping.")
    required = {"name", "description"}
    if set(frontmatter.keys()) != required:
        fail(f"SKILL.md frontmatter must contain exactly {sorted(required)}.")
    if frontmatter["name"] != "n8n-self-hosted-admin":
        fail("Unexpected skill name in SKILL.md frontmatter.")


def validate_python_compiles() -> None:
    cmd = [sys.executable, "-m", "py_compile", *[str(path) for path in PYTHON_FILES]]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"Python compilation failed:\n{result.stderr}")


def validate_installer() -> None:
    with tempfile.TemporaryDirectory(prefix="n8n-skill-validate-") as tmp:
        tmp_path = Path(tmp)

        shared_target = tmp_path / "shared-project"
        shared_cmd = [sys.executable, str(INSTALLER), "--tool", "all", "--target", str(shared_target)]
        result = subprocess.run(shared_cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            fail(f"Installer failed for shared adapters:\n{result.stderr}\n{result.stdout}")

        expected_shared = [
            shared_target / "AGENTS.md",
            shared_target / "CLAUDE.md",
            shared_target / "GEMINI.md",
            shared_target / ".agent" / "rules" / "documentation.md",
            shared_target / ".agent" / "rules" / "n8n-operations.md",
        ]
        for path in expected_shared:
            if not path.exists():
                fail(f"Installer did not create expected file: {path}")
            if "{{SKILL_REPO_PATH}}" in path.read_text():
                fail(f"Installer left placeholder in {path}")

        codex_target = tmp_path / "codex-skills"
        codex_cmd = [sys.executable, str(INSTALLER), "--tool", "codex", "--codex-dest", str(codex_target)]
        result = subprocess.run(codex_cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            fail(f"Installer failed for Codex skill:\n{result.stderr}\n{result.stdout}")

        expected_skill = codex_target / "n8n-self-hosted-admin" / "SKILL.md"
        if not expected_skill.exists():
            fail("Codex installer did not copy the skill.")


def validate_no_secrets() -> None:
    suspicious_regexes = [
        re.compile(r"eyJ[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}"),
    ]
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        content = path.read_text(errors="ignore")
        for regex in suspicious_regexes:
            if regex.search(content):
                fail(f"Suspicious secret-like token found in {path}: {regex.pattern}")


def main() -> int:
    validate_exists()
    validate_skill_frontmatter()
    validate_python_compiles()
    validate_installer()
    validate_no_secrets()
    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
