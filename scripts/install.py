#!/usr/bin/env python3
"""Install Codex skill files and agent adapters into other projects."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PLACEHOLDER = "{{SKILL_REPO_PATH}}"


def fail(message: str) -> None:
    raise SystemExit(f"[ERROR] {message}")


def render_text(path: Path, repo_path: Path) -> str:
    return path.read_text().replace(PLACEHOLDER, str(repo_path))


def write_file(src: Path, dest: Path, repo_path: Path, *, force: bool) -> None:
    if dest.exists() and not force:
        fail(f"Destination already exists: {dest}. Re-run with --force to overwrite.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_text(src, repo_path))


def copy_tree(src: Path, dest: Path, *, force: bool) -> None:
    if dest.exists():
        if not force:
            fail(f"Destination already exists: {dest}. Re-run with --force to overwrite.")
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def install_codex(repo_root: Path, dest_root: Path, *, force: bool) -> list[Path]:
    skill_src = repo_root / "codex" / "skills" / "n8n-self-hosted-admin"
    skill_dest = dest_root / "n8n-self-hosted-admin"
    copy_tree(skill_src, skill_dest, force=force)
    return [skill_dest]


def install_shared(repo_root: Path, target_root: Path, *, force: bool) -> list[Path]:
    src = repo_root / "adapters" / "shared" / "AGENTS.md"
    dest = target_root / "AGENTS.md"
    write_file(src, dest, repo_root, force=force)
    return [dest]


def install_claude(repo_root: Path, target_root: Path, *, force: bool) -> list[Path]:
    src = repo_root / "adapters" / "claude" / "CLAUDE.md"
    dest = target_root / "CLAUDE.md"
    write_file(src, dest, repo_root, force=force)
    return [dest]


def install_gemini(repo_root: Path, target_root: Path, *, force: bool) -> list[Path]:
    src = repo_root / "adapters" / "gemini" / "GEMINI.md"
    dest = target_root / "GEMINI.md"
    write_file(src, dest, repo_root, force=force)
    return [dest]


def install_antigravity(repo_root: Path, target_root: Path, *, force: bool) -> list[Path]:
    files = []
    src_root = repo_root / "adapters" / "antigravity" / ".agent" / "rules"
    dest_root = target_root / ".agent" / "rules"
    for src in sorted(src_root.glob("*.md")):
        dest = dest_root / src.name
        write_file(src, dest, repo_root, force=force)
        files.append(dest)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Install n8n skill adapters into another project.")
    parser.add_argument(
        "--tool",
        required=True,
        choices=("codex", "claude", "gemini", "antigravity", "shared", "all"),
        help="Tool adapter to install.",
    )
    parser.add_argument(
        "--target",
        help="Target project root. Required for every tool except codex.",
    )
    parser.add_argument(
        "--codex-dest",
        default=str(Path.home() / ".codex" / "skills"),
        help="Destination directory for Codex skill installs. Defaults to ~/.codex/skills.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    installed: list[Path] = []

    if args.tool == "codex":
        installed.extend(install_codex(repo_root, Path(args.codex_dest).expanduser(), force=args.force))
    else:
        if not args.target:
            fail("--target is required for this tool.")
        target_root = Path(args.target).expanduser().resolve()
        if args.tool in {"shared", "all"}:
            installed.extend(install_shared(repo_root, target_root, force=args.force))
        if args.tool in {"claude", "all"}:
            installed.extend(install_claude(repo_root, target_root, force=args.force))
        if args.tool in {"gemini", "all"}:
            installed.extend(install_gemini(repo_root, target_root, force=args.force))
        if args.tool in {"antigravity", "all"}:
            installed.extend(install_antigravity(repo_root, target_root, force=args.force))

    print("# Installed Files\n")
    for path in installed:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
