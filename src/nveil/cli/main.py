# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``nveil`` CLI entry point.

Dispatches to subcommands defined in :mod:`nveil.cli.commands`. Each
subcommand module exposes ``register(subparsers)`` and ``run(args) -> int``
so the MCP server can share the same implementations.

An **implicit-generate** pre-pass lets ``nveil "bar chart of revenue"
--data x.csv`` work as a shorthand for ``nveil generate ...``: if
``argv[1]`` doesn't match a known subcommand (or one of the global
flags), we insert ``generate`` in front of it before argparse runs.
"""

from __future__ import annotations

import argparse
import sys
import traceback

from .. import __version__
from .config import ConfigError, die
from .commands import (
    generate as _generate,
    render as _render,
    describe as _describe,
    explain as _explain,
    install_skill as _install_skill,
    install_mcp as _install_mcp,
    docs as _docs,
    mcp_server as _mcp,
)


_SUBCOMMANDS = [
    _generate,
    _render,
    _describe,
    _explain,
    _install_skill,
    _install_mcp,
    _docs,
    _mcp,
]

_GLOBAL_FLAGS = {"-h", "--help", "-V", "--version"}


def _known_subcommand_names() -> set[str]:
    return {mod.NAME for mod in _SUBCOMMANDS}


def _rewrite_argv_for_implicit_generate(argv: list[str]) -> list[str]:
    """Insert ``generate`` before a bare prompt.

    ``nveil "bar chart" --data x.csv`` → ``nveil generate "bar chart" --data x.csv``.
    Does nothing if the first positional is a known subcommand or a global flag.
    """
    if len(argv) <= 1:
        return argv
    first = argv[1]
    if first in _GLOBAL_FLAGS or first in _known_subcommand_names():
        return argv
    return [argv[0], "generate", *argv[1:]]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nveil",
        description=(
            "NVEIL — AI-powered data visualization. Describe what you want, "
            "get production charts. Data stays local."
        ),
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"nveil {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True
    for mod in _SUBCOMMANDS:
        mod.register(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    argv = _rewrite_argv_for_implicit_generate(argv)
    parser = _build_parser()
    args = parser.parse_args(argv[1:])

    try:
        return int(args._run(args) or 0)
    except ConfigError as e:
        return die(str(e), code=1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        traceback.print_exc()
        return die(str(e), code=3)
