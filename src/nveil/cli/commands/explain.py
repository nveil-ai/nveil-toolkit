# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``nveil explain`` — print a .nveil spec's human-readable explanation."""

from __future__ import annotations

import sys
from pathlib import Path


NAME = "explain"


def register(subparsers) -> None:
    p = subparsers.add_parser(
        NAME,
        help="Print a .nveil spec's explanation text.",
        description=(
            "Fully local — no API call. Reads the explanation that was baked "
            "into the spec at generation time."
        ),
    )
    p.add_argument("spec", help="Path to a .nveil file.")
    p.set_defaults(_run=run)


def run(args) -> int:
    path = Path(args.spec)
    if not path.exists():
        print(f"nveil: error: spec file not found: {path}", file=sys.stderr)
        return 1
    import nveil
    spec = nveil.load_spec(str(path))
    print(spec.explanation)
    return 0
