# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``nveil install-mcp`` — register the NVEIL MCP stdio server in an MCP client.

Knows two clients today:
    - claude-desktop — edits the platform-specific JSON config in-place.
    - cursor         — edits ``~/.cursor/mcp.json``.

Claude Code is deliberately NOT a target here: the bundled plugin
(``nveil install-skill --client claude-plugin``) already ships the MCP
server via its ``.mcp.json``, and Claude Code picks it up automatically as
``plugin:nveil:nveil``. Registering separately creates a duplicate.

Pass ``--client all`` to try every client we know about (skipping any that
isn't present on disk). The MCP server itself is always the same: the
``nveil`` binary with the ``mcp`` argument, picking ``NVEIL_API_KEY`` from
the host process environment.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable


NAME = "install-mcp"
_SERVER_NAME = "nveil"

_KNOWN_CLIENTS = ("claude-desktop", "cursor", "all")


def register(subparsers) -> None:
    p = subparsers.add_parser(
        NAME,
        help="Register the nveil MCP server in an MCP client (Claude Desktop, Cursor).",
        description=(
            "Edit the target client's MCP config so it launches `nveil mcp` "
            "as a stdio subprocess. Idempotent — re-run safely. Honors an "
            "existing NVEIL_API_KEY in your environment and propagates it.\n\n"
            "Note: Claude Code is not a target here because the bundled plugin "
            "(`nveil install-skill --client claude-plugin`) already ships the "
            "MCP server via its .mcp.json — Claude Code picks it up automatically "
            "and registering separately would create a duplicate."
        ),
    )
    p.add_argument(
        "--client", choices=_KNOWN_CLIENTS, default="claude-desktop",
        help="Which MCP client to configure. 'all' tries every known client.",
    )
    p.add_argument(
        "--force", action="store_true",
        help="Overwrite an existing `nveil` entry without prompting.",
    )
    p.set_defaults(_run=run)


# ── Client config paths ──────────────────────────────────────────────

def _claude_desktop_config() -> Path:
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) \
            / "Claude" / "claude_desktop_config.json"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" \
            / "claude_desktop_config.json"
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def _cursor_config() -> Path:
    return Path.home() / ".cursor" / "mcp.json"


# ── Entry shape ──────────────────────────────────────────────────────

_PROPAGATED_ENV_VARS = ("NVEIL_API_KEY", "NVEIL_BASE_URL", "NVEIL_VERIFY")


def _server_entry() -> dict:
    """JSON shape registered with the client.

    ``command`` is the ``nveil`` binary (or the current Python as a fallback
    when ``nveil`` isn't yet on PATH — happens during editable installs on
    some Windows setups). Propagates ``NVEIL_API_KEY``, ``NVEIL_BASE_URL``,
    and ``NVEIL_VERIFY`` from the current environment so the spawned MCP
    server talks to the same endpoint the installer was pointed at.

    Note: the client captures env at subprocess spawn time — if the user
    rotates their API key, re-run ``nveil install-mcp --force`` and
    restart the host so the fresh key lands in the registered env.
    """
    nveil_bin = shutil.which("nveil")
    if nveil_bin:
        entry: dict = {"command": nveil_bin, "args": ["mcp"]}
    else:
        # Fallback: `python -m nveil.cli mcp`
        entry = {"command": sys.executable, "args": ["-m", "nveil.cli", "mcp"]}
    env = {k: os.environ[k] for k in _PROPAGATED_ENV_VARS if k in os.environ}
    if env:
        entry["env"] = env
    return entry


# ── Per-client installers ────────────────────────────────────────────

def _install_json_config(
    config_path: Path, root_key: str, force: bool, client_label: str,
) -> int:
    """Generic JSON edit for clients that expose ``{root_key: {server: {...}}}``."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(
                f"nveil: error: {client_label} config at {config_path} is not valid JSON: {e}",
                file=sys.stderr,
            )
            return 1
    else:
        data = {}

    servers = data.setdefault(root_key, {})
    if _SERVER_NAME in servers and not force:
        print(
            f"nveil: {client_label} already has an '{_SERVER_NAME}' entry at {config_path}. "
            "Re-run with --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    servers[_SERVER_NAME] = _server_entry()
    config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"registered: {client_label} → {config_path}")
    return 0


def _install_claude_desktop(force: bool) -> int:
    return _install_json_config(
        _claude_desktop_config(), "mcpServers", force, "Claude Desktop",
    )


def _install_cursor(force: bool) -> int:
    return _install_json_config(
        _cursor_config(), "mcpServers", force, "Cursor",
    )


_INSTALLERS: dict[str, Callable[[bool], int]] = {
    "claude-desktop": _install_claude_desktop,
    "cursor": _install_cursor,
}


def run(args) -> int:
    if args.client == "all":
        # Best-effort across all known clients. Any single failure is
        # reported but does not abort the others.
        rc = 0
        for client in ("claude-desktop", "cursor"):
            r = _INSTALLERS[client](args.force)
            rc = rc or r
        return rc
    return _INSTALLERS[args.client](args.force)
