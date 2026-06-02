# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-FileContributor: Guillaume Franque
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``nveil render`` — re-render a saved .nveil spec against fresh data."""

from __future__ import annotations

import sys
from pathlib import Path

from ..config import configure_from_args
from .generate import _parse_output, _RENDER_ALL_FORMATS, _resolve_output_paths, _slug


NAME = "render"


def register(subparsers) -> None:
    p = subparsers.add_parser(
        NAME,
        help="Re-render a saved .nveil spec against a data file (no API call).",
        description=(
            "Load an opaque .nveil spec and render it locally. This is free — "
            "no server round trip."
        ),
    )
    p.add_argument("spec", help="Path to a .nveil file.")
    p.add_argument("--data", required=True, help="Path to a compatible data file.")
    p.add_argument(
        "-o", "--output",
        help=(
            "Output path with optional format brackets. Examples: output.[all], output.[png], "
            "output.[html,pdf]. Supported formats: html, png, jpg, svg, pdf, json. "
            ".[all] writes all formats. Default: ./nveil_out/<spec-stem>.html"
        ),
    )
    p.add_argument("--api-key", help="Unused for offline render; accepted for symmetry.")
    p.set_defaults(_run=run)


def run(args) -> int:
    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"nveil: error: spec file not found: {spec_path}", file=sys.stderr)
        return 1
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"nveil: error: data file not found: {data_path}", file=sys.stderr)
        return 1

    # render doesn't call the API, but nveil.load_spec + nveil.save_image need
    # the package loaded. Configure lazily so missing API key is not fatal here.
    try:
        configure_from_args(args)
    except Exception:
        pass

    import nveil

    bracket_base, formats = _parse_output(args.output, _RENDER_ALL_FORMATS)
    if formats is None:
        return 1

    out_paths = _resolve_output_paths(args.output, spec_path.stem, formats, bracket_base)

    spec = nveil.load_spec(str(spec_path))
    fig = spec.render(data_path)

    if "html" in out_paths:
        nveil.save_html(fig, str(out_paths["html"]))
        print(str(out_paths["html"]))
    for fmt in out_paths:
        if fmt == "html":
            continue
        nveil.save_image(fig, str(out_paths[fmt]))
        print(str(out_paths[fmt]))

    return 0
