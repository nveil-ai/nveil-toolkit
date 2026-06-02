# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``nveil describe`` — print a data file's schema for agent grounding.

Minimal JSON payload an AI agent can read before constructing a prompt:
shape, dtypes, and a 5-row head preview.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


NAME = "describe"


def register(subparsers) -> None:
    p = subparsers.add_parser(
        NAME,
        help="Print a data file's shape / dtypes / head as JSON.",
        description=(
            "Ground an AI agent (or a human) on a dataset before generating a "
            "chart. Loads the file locally — no API call, no network."
        ),
    )
    p.add_argument("data", help="Path to a CSV / Parquet / JSON / Excel file.")
    p.add_argument(
        "--rows", type=int, default=5,
        help="Number of head rows to include in the preview (default: 5).",
    )
    p.set_defaults(_run=run)


def run(args) -> int:
    path = Path(args.data)
    if not path.exists():
        print(f"nveil: error: data file not found: {path}", file=sys.stderr)
        return 1

    # Reuse the same transient reader the engine uses so CLI dtype reporting
    # matches what the pipeline will see at load time.
    from dive._engine import _read_path_transient, _EXT_TO_FMT

    ext = path.suffix.lstrip(".").lower()
    fmt = _EXT_TO_FMT.get(ext)
    if fmt is None:
        print(
            f"nveil: error: unsupported file type {path.suffix!r}. "
            f"Supported: {sorted(set(_EXT_TO_FMT))}",
            file=sys.stderr,
        )
        return 1

    df = _read_path_transient(path, fmt)
    payload = {
        "path": str(path.resolve()),
        "format": fmt,
        "shape": {"rows": int(df.shape[0]), "cols": int(df.shape[1])},
        "columns": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "head": df.head(args.rows).to_dict(orient="records"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0
