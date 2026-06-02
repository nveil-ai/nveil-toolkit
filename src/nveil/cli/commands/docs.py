# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``nveil docs`` — open the online API reference."""

from __future__ import annotations

import webbrowser


NAME = "docs"
_DOCS_URL = "https://docs.nveil.com/api-reference/"


def register(subparsers) -> None:
    p = subparsers.add_parser(
        NAME,
        help=f"Open the NVEIL API reference ({_DOCS_URL}).",
        description=(
            "Open the online API reference in your default browser, or print "
            "the URL with --print for agents that cannot open browsers."
        ),
    )
    p.add_argument(
        "--print", dest="print_only", action="store_true",
        help="Print the URL to stdout instead of opening a browser.",
    )
    p.set_defaults(_run=run)


def run(args) -> int:
    if args.print_only:
        print(_DOCS_URL)
        return 0
    webbrowser.open(_DOCS_URL)
    print(_DOCS_URL)
    return 0
