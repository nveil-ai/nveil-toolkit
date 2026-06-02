# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``nveil install-skill`` — write the NVEIL skill into an AI agent's
instruction format.

Single canonical source (the shipped ``SKILL.md``), many per-agent output
formats. Each target writes the same body with the right wrapping to the
place that agent expects.

Supported targets
    claude-code    — ``~/.claude/skills/nveil/SKILL.md`` (or ``.claude/`` in project)
    claude-plugin  — full plugin tree: ``.claude-plugin/plugin.json`` +
                     ``skills/nveil/SKILL.md`` + ``.mcp.json``; covers Claude
                     Desktop AND namespaced Claude Code
    codex          — ``~/.codex/AGENTS.md`` (or ``./AGENTS.md``)
    cursor         — ``~/.cursor/rules/nveil.mdc`` (or ``.cursor/rules/…``)
    copilot        — ``.github/copilot-instructions.md`` (project-only)
    aider          — ``./CONVENTIONS.md`` (project-only)
    openclaw       — ``<workspace>/skills/nveil/SKILL.md``
    all            — every target applicable to the chosen scope
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

from ..skill_source import SkillSource, load as _load_skill


NAME = "install-skill"

_TARGETS = (
    "claude-code", "claude-plugin", "codex", "cursor",
    "copilot", "aider", "openclaw", "all",
)
_PROJECT_ONLY = {"copilot", "aider"}  # no reasonable home-dir install


def register(subparsers) -> None:
    p = subparsers.add_parser(
        NAME,
        help="Install the NVEIL skill into an AI agent's instruction format.",
        description=(
            "Generates the NVEIL skill in the format the chosen agent expects "
            "(Claude Code skill, Claude plugin, Codex AGENTS.md, Cursor rule, "
            "Copilot instructions, Aider conventions, OpenClaw skill) and "
            "writes it to that agent's default path. One canonical source — "
            "re-run any time the SKILL.md ships a new version."
        ),
    )
    p.add_argument(
        "--client", choices=_TARGETS, default="claude-plugin",
        help="Which agent format to install. Default is 'claude-plugin' — "
             "registers the bundled Claude plugin (covers Claude Code and, via "
             "GitHub marketplace, Claude Desktop). Pass 'claude-code' for a "
             "loose ~/.claude/skills/ drop-in when you don't have the claude CLI.",
    )
    p.add_argument(
        "--scope", choices=("user", "project"), default="user",
        help="'user' writes to the user's home dir; 'project' writes to the current dir. "
             "Copilot / Aider are always project-scoped.",
    )
    p.add_argument(
        "--path",
        help="Override the output directory. Wins over --scope.",
    )
    p.add_argument(
        "--force", action="store_true",
        help="Overwrite existing files without asking.",
    )
    p.set_defaults(_run=run)


# ── Shared helpers ───────────────────────────────────────────────────

def _write(path: Path, content: str, force: bool, label: str) -> int:
    if path.exists() and not force:
        print(
            f"nveil: {path} already exists. Re-run with --force to overwrite.",
            file=sys.stderr,
        )
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"installed ({label}): {path}")
    return 0


def _write_json(path: Path, data: dict, force: bool, label: str) -> int:
    if path.exists() and not force:
        print(
            f"nveil: {path} already exists. Re-run with --force to overwrite.",
            file=sys.stderr,
        )
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"installed ({label}): {path}")
    return 0


# ── Target-specific generators ───────────────────────────────────────

def _target_claude_code(src: SkillSource, scope: str, custom: Path | None, force: bool) -> int:
    """Drop SKILL.md as a standalone Claude Code skill."""
    base = custom or (Path.home() / ".claude" if scope == "user" else Path.cwd() / ".claude")
    dst = base / "skills" / src.name / "SKILL.md"
    return _write(dst, src.frontmatter + src.body, force, "Claude Code skill")


_MARKETPLACE_NAME = "nveil"


def _shipped_package_root() -> Path:
    """Resolve the installed ``nveil`` package directory."""
    from ... import __file__ as _nveil_init
    return Path(_nveil_init).parent


def _find_marketplace_root(pkg_root: Path) -> Path | None:
    """Walk up from the installed package to find the SDK repo's
    ``.claude-plugin/marketplace.json`` (only present in editable installs).

    Returns the directory containing ``.claude-plugin/`` (i.e. the repo root
    that users would pass to ``claude plugin marketplace add``).
    """
    for p in (pkg_root, *pkg_root.parents):
        if (p / ".claude-plugin" / "marketplace.json").is_file():
            return p
    return None


def _target_claude_plugin(src: SkillSource, scope: str, custom: Path | None, force: bool) -> int:
    """Register the NVEIL plugin with Claude Code via its marketplace mechanism.

    The Claude CLI installs plugins only from marketplaces — there is no
    ``claude plugin add <path>`` equivalent. The NVEIL repo ships
    ``.claude-plugin/marketplace.json`` at its root pointing at the in-repo
    plugin (``source: "./src/nveil"``). For local / editable installs we
    add that repo as a local marketplace; otherwise we suggest the public
    GitHub marketplace.

    Plugin files are NOT regenerated: they live inside the installed
    package (``src/nveil/.claude-plugin/*``, ``src/nveil/.mcp.json``,
    ``src/nveil/skills/nveil/SKILL.md``).
    """
    pkg_root = _shipped_package_root()
    plugin_manifest = pkg_root / ".claude-plugin" / "plugin.json"
    if not plugin_manifest.exists():
        print(
            f"nveil: error: shipped plugin manifest not found at {plugin_manifest}. "
            "Reinstall the nveil package.",
            file=sys.stderr,
        )
        return 1

    claude_bin = shutil.which("claude")
    if not claude_bin:
        print(
            "nveil: Claude CLI ('claude') not found on PATH.\n"
            f"  Install manually — inside a Claude Code / Desktop session, run:\n"
            f"    /plugin marketplace add nveil-ai/nveil-toolkit\n"
            f"    /plugin install nveil@nveil",
            file=sys.stderr,
        )
        return 1

    marketplace_root = custom or _find_marketplace_root(pkg_root)
    if marketplace_root is None:
        # pip-installed case — point users at the public GitHub marketplace.
        print(
            "nveil: no local marketplace.json found (non-editable install).\n"
            "  Add the public marketplace and install the plugin with:\n"
            "    claude plugin marketplace add nveil-ai/nveil-toolkit\n"
            "    claude plugin install nveil@nveil",
            file=sys.stderr,
        )
        return 1

    # Local / editable install — register the repo as a local marketplace.
    if force:
        subprocess.run(
            [claude_bin, "plugin", "marketplace", "remove", _MARKETPLACE_NAME],
            capture_output=True,
        )
    add_mp = subprocess.run(
        [claude_bin, "plugin", "marketplace", "add", str(marketplace_root)],
        capture_output=True, text=True,
    )
    if add_mp.returncode != 0 and "already" not in (add_mp.stderr + add_mp.stdout).lower():
        print(
            f"nveil: `claude plugin marketplace add` failed: "
            f"{add_mp.stderr.strip() or add_mp.stdout.strip()}",
            file=sys.stderr,
        )
        return add_mp.returncode

    install_cmd = [
        claude_bin, "plugin", "install", f"{src.name}@{_MARKETPLACE_NAME}",
    ]
    install = subprocess.run(install_cmd, capture_output=True, text=True)
    if install.returncode != 0:
        if force:
            subprocess.run(
                [claude_bin, "plugin", "uninstall", src.name],
                capture_output=True,
            )
            install = subprocess.run(install_cmd, capture_output=True, text=True)
        if install.returncode != 0:
            print(
                f"nveil: `claude plugin install` failed: "
                f"{install.stderr.strip() or install.stdout.strip()}",
                file=sys.stderr,
            )
            return install.returncode

    print(f"registered (Claude plugin): {src.name}@{_MARKETPLACE_NAME} ← {marketplace_root}")
    return 0


def _target_codex(src: SkillSource, scope: str, custom: Path | None, force: bool) -> int:
    """Codex reads AGENTS.md (project-local preferred; ~/.codex/AGENTS.md also supported)."""
    if custom is not None:
        dst = custom / "AGENTS.md"
    elif scope == "user":
        dst = Path.home() / ".codex" / "AGENTS.md"
    else:
        dst = Path.cwd() / "AGENTS.md"
    # AGENTS.md is plain markdown — no YAML frontmatter.
    content = src.body
    return _write(dst, content, force, "Codex AGENTS.md")


def _target_cursor(src: SkillSource, scope: str, custom: Path | None, force: bool) -> int:
    """Cursor rule — ``.mdc`` with its own minimal frontmatter schema."""
    base = custom or (Path.home() if scope == "user" else Path.cwd())
    dst = base / ".cursor" / "rules" / f"{src.name}.mdc"
    header = (
        "---\n"
        f"description: {src.description}\n"
        "alwaysApply: false\n"
        "---\n"
    )
    return _write(dst, header + src.body, force, "Cursor rule")


def _target_copilot(src: SkillSource, scope: str, custom: Path | None, force: bool) -> int:
    """GitHub Copilot (VS Code) — project-local ``.github/copilot-instructions.md``."""
    if scope == "user":
        print(
            "nveil: copilot target is project-scoped; ignoring --scope user.",
            file=sys.stderr,
        )
    base = custom or Path.cwd()
    dst = base / ".github" / "copilot-instructions.md"
    content = src.body
    return _write(dst, content, force, "Copilot instructions")


def _target_aider(src: SkillSource, scope: str, custom: Path | None, force: bool) -> int:
    """Aider — project-local ``CONVENTIONS.md``."""
    if scope == "user":
        print(
            "nveil: aider target is project-scoped; ignoring --scope user.",
            file=sys.stderr,
        )
    base = custom or Path.cwd()
    dst = base / "CONVENTIONS.md"
    content = src.body
    return _write(dst, content, force, "Aider conventions")


def _target_openclaw(src: SkillSource, scope: str, custom: Path | None, force: bool) -> int:
    """OpenClaw — ``<workspace>/skills/<name>/SKILL.md``.

    OpenClaw's SKILL.md format is compatible with ours (same YAML frontmatter,
    same markdown body). It supports extra fields (``tools``, ``triggers``)
    that we don't populate — the agent still invokes based on ``description``.
    """
    if custom is not None:
        base = custom
    elif scope == "user":
        base = Path.home() / ".openclaw"
    else:
        base = Path.cwd()
    dst = base / "skills" / src.name / "SKILL.md"
    return _write(dst, src.frontmatter + src.body, force, "OpenClaw skill")


_INSTALLERS: dict[str, Callable[[SkillSource, str, Path | None, bool], int]] = {
    "claude-code": _target_claude_code,
    "claude-plugin": _target_claude_plugin,
    "codex": _target_codex,
    "cursor": _target_cursor,
    "copilot": _target_copilot,
    "aider": _target_aider,
    "openclaw": _target_openclaw,
}


# ── Entry point ──────────────────────────────────────────────────────

def run(args) -> int:
    try:
        src = _load_skill()
    except FileNotFoundError as e:
        print(f"nveil: error: {e}", file=sys.stderr)
        return 1

    custom = Path(args.path).expanduser() if args.path else None
    scope = args.scope

    clients = list(_INSTALLERS) if args.client == "all" else [args.client]
    rc = 0
    for client in clients:
        # "all" + user scope skips the project-only targets, which would
        # silently write to cwd and surprise the user.
        if args.client == "all" and scope == "user" and client in _PROJECT_ONLY:
            continue
        rc |= _INSTALLERS[client](src, scope, custom, args.force)
    return rc
