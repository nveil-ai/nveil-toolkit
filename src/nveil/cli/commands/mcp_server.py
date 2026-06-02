# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``nveil mcp`` — MCP stdio server exposing the CLI subcommands as tools.

Critical invariants (see ``feedback_mcp_stdio_stdout.md``):
    * MCP stdio transport reserves stdout (fd 1) for JSON-RPC frames.
    * Any stray ``print(...)`` or log handler targeting stdout silently
      corrupts the protocol. We redirect ``sys.stdout`` to ``sys.stderr``
      at import time so Python-level writes go to stderr. The MCP SDK's
      stdio transport uses the raw file descriptor directly, so it keeps
      working.
    * ``mcp`` is imported lazily so other subcommands don't pay the cost.
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from typing import Any


NAME = "mcp"


def register(subparsers) -> None:
    p = subparsers.add_parser(
        NAME,
        help="Run the NVEIL MCP stdio server (for Claude Desktop, Cursor, etc.).",
        description=(
            "Start an MCP stdio server that exposes generate / render / "
            "describe / explain as MCP tools. Launched as a subprocess by an "
            "MCP client; not meant to be run by hand beyond smoke tests."
        ),
    )
    p.set_defaults(_run=run)


# ── Tool schemas ─────────────────────────────────────────────────────

_GENERATE_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "Natural-language chart description.",
        },
        "data_path": {
            "type": "string",
            "description": "Absolute path to a CSV / Parquet / JSON / Excel file.",
        },
        "output_dir": {
            "type": "string",
            "description": "Directory for generated artifacts. Default: ./nveil_out",
        },
        "format": {
            "type": "string",
            "enum": ["html", "png", "nveil", "all"],
            "description": "Output format. 'all' writes html+png+.nveil.",
            "default": "all",
        },
    },
    "required": ["prompt", "data_path"],
}

_RENDER_SCHEMA = {
    "type": "object",
    "properties": {
        "spec_path": {"type": "string", "description": "Path to a .nveil file."},
        "data_path": {"type": "string", "description": "Path to a compatible data file."},
        "output_dir": {"type": "string", "description": "Directory for outputs."},
        "format": {
            "type": "string",
            "enum": ["html", "png", "all"],
            "default": "html",
        },
    },
    "required": ["spec_path", "data_path"],
}

_DESCRIBE_SCHEMA = {
    "type": "object",
    "properties": {
        "data_path": {"type": "string"},
        "rows": {"type": "integer", "default": 5},
    },
    "required": ["data_path"],
}

_EXPLAIN_SCHEMA = {
    "type": "object",
    "properties": {"spec_path": {"type": "string"}},
    "required": ["spec_path"],
}


# ── Tool handlers ────────────────────────────────────────────────────

def _capture_stdout(callable_):
    """Run a CLI ``run(args)`` and capture its stdout (paths + JSON payloads).

    Our module-level ``sys.stdout = sys.stderr`` redirect would otherwise
    swallow the subcommand's output. Re-direct back to a StringIO for the
    duration of the call so we can return its contents to the MCP client.
    """
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = callable_()
    return rc, buf.getvalue()


def _tool_generate(arguments: dict[str, Any]) -> str:
    from . import generate as _generate
    args = SimpleNamespace(
        prompt=arguments["prompt"],
        data=arguments["data_path"],
        output=arguments.get("output_dir"),
        format=arguments.get("format", "all"),
        explain=True,
        api_key=None,
    )
    rc, out = _capture_stdout(lambda: _generate.run(args))
    if rc != 0:
        raise RuntimeError(f"generate failed (exit {rc}):\n{out}")
    return out.strip()


def _tool_render(arguments: dict[str, Any]) -> str:
    from . import render as _render
    args = SimpleNamespace(
        spec=arguments["spec_path"],
        data=arguments["data_path"],
        output=arguments.get("output_dir"),
        format=arguments.get("format", "html"),
        api_key=None,
    )
    rc, out = _capture_stdout(lambda: _render.run(args))
    if rc != 0:
        raise RuntimeError(f"render failed (exit {rc}):\n{out}")
    return out.strip()


def _tool_describe(arguments: dict[str, Any]) -> str:
    from . import describe as _describe
    args = SimpleNamespace(
        data=arguments["data_path"],
        rows=arguments.get("rows", 5),
    )
    rc, out = _capture_stdout(lambda: _describe.run(args))
    if rc != 0:
        raise RuntimeError(f"describe failed (exit {rc}):\n{out}")
    return out


def _tool_explain(arguments: dict[str, Any]) -> str:
    from . import explain as _explain
    args = SimpleNamespace(spec=arguments["spec_path"])
    rc, out = _capture_stdout(lambda: _explain.run(args))
    if rc != 0:
        raise RuntimeError(f"explain failed (exit {rc}):\n{out}")
    return out


_HANDLERS = {
    "nveil_generate": (_tool_generate, _GENERATE_SCHEMA,
                       "Generate a chart from a prompt and a data file. "
                       "Returns paths to the html/png/.nveil outputs plus "
                       "the human-readable explanation."),
    "nveil_render": (_tool_render, _RENDER_SCHEMA,
                     "Re-render a saved .nveil spec against fresh data "
                     "(no API call). Returns output file paths."),
    "nveil_describe": (_tool_describe, _DESCRIBE_SCHEMA,
                       "Inspect a data file: shape, dtypes, head preview. "
                       "Use this to ground a prompt on available columns."),
    "nveil_explain": (_tool_explain, _EXPLAIN_SCHEMA,
                      "Read a .nveil spec's explanation text."),
}


def run(args) -> int:
    """Start the MCP stdio server. Blocks until stdin closes."""
    # CRITICAL — see ``feedback_mcp_stdio_stdout.md``:
    # MCP stdio reserves stdout (fd 1) for JSON-RPC frames. We must
    # (a) keep a handle to the real stdout for the MCP transport,
    # (b) redirect Python-level ``sys.stdout`` to stderr so stray
    #     prints from transitive deps can't corrupt the protocol, AND
    # (c) redirect OS-level fd 1 to stderr so subprocesses we spawn
    #     (Playwright install, headless Chromium, any native dep) inherit
    #     a safe fd 1 and cannot write into the JSON-RPC pipe.
    import os
    from io import TextIOWrapper

    # Dup the real stdin/stdout to fresh fds, then redirect fd 0 → NUL
    # and fd 1 → fd 2 so spawned subprocesses (Chromium, Playwright
    # install, native libs) cannot read from or write to the MCP pipes.
    _real_stdin_fd = os.dup(0)
    _real_stdout_fd = os.dup(1)
    _devnull_fd = os.open(os.devnull, os.O_RDONLY)
    os.dup2(_devnull_fd, 0)
    os.close(_devnull_fd)
    os.dup2(2, 1)
    real_stdin_buffer = os.fdopen(_real_stdin_fd, "rb", buffering=0)
    real_stdout_buffer = os.fdopen(_real_stdout_fd, "wb", buffering=0)
    sys.stdout = sys.stderr

    import asyncio
    import logging

    # Force all Python logging to stderr — some deps call basicConfig.
    logging.basicConfig(stream=sys.stderr, force=True)

    try:
        import anyio
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp import types
    except ImportError:
        print(
            "nveil: error: the 'mcp' package is required for `nveil mcp` but "
            "is not installed. Reinstall: pip install --upgrade nveil",
            file=sys.stderr,
        )
        return 2

    server = Server("nveil")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(name=name, description=desc, inputSchema=schema)
            for name, (_fn, schema, desc) in _HANDLERS.items()
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None):
        arguments = arguments or {}
        if name not in _HANDLERS:
            raise ValueError(f"unknown tool: {name}")
        fn, _schema, _desc = _HANDLERS[name]
        # Run the blocking CLI handler in a thread so we don't stall the loop.
        text = await asyncio.to_thread(fn, arguments)
        return [types.TextContent(type="text", text=text)]

    # Wrap the pre-redirect stdin/stdout so MCP reads & writes JSON-RPC
    # on the real pipes (fd 0/1 in this process now point to NUL/stderr).
    real_stdin = anyio.wrap_file(
        TextIOWrapper(real_stdin_buffer, encoding="utf-8")
    )
    real_stdout = anyio.wrap_file(
        TextIOWrapper(real_stdout_buffer, encoding="utf-8")
    )

    async def _serve():
        async with stdio_server(stdin=real_stdin, stdout=real_stdout) as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(_serve())
    return 0
