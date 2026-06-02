# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-FileContributor: Guillaume Franque
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``nveil generate`` — create a spec from a prompt + data file."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from ..config import configure_from_args


NAME = "generate"
_BRACKET_RE = re.compile(r"^(.*)\.\[([^\]]+)\]$")
_ALL_FORMATS = ("html", "png", "nveil", "jpg", "svg", "pdf", "json")
_RENDER_ALL_FORMATS = ("html", "png", "jpg", "svg", "pdf", "json")
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def register(subparsers) -> None:
    p = subparsers.add_parser(
        NAME,
        help="Generate a chart from a natural-language prompt and a data file.",
        description=(
            "Generate a visualization specification, render it, and write the "
            "resulting artifact(s) to disk. Paths of the created files are "
            "printed to stdout (one per line)."
        ),
    )
    p.add_argument("prompt", help="Natural-language description of the desired chart.")
    p.add_argument(
        "--data", required=True,
        help="Path to a CSV / Parquet / JSON / Excel file. No DataFrame load in this process.",
    )
    p.add_argument(
        "-o", "--output",
        help=(
            "Output path with optional format brackets. Examples: output.[all], output.[png], "
            "output.[html,pdf]. Supported formats: html, png, nveil, jpg, svg, pdf, json. "
            ".[all] writes all formats. Default: ./nveil_out/<slug>.html"
        ),
    )
    p.add_argument(
        "--explain", action="store_true",
        help="Print the spec's human-readable explanation to stdout.",
    )
    p.add_argument("--api-key", help="Override NVEIL_API_KEY for this invocation.")
    p.set_defaults(_run=run)


def _slug(text: str, max_len: int = 50) -> str:
    s = _SLUG_RE.sub("_", text.lower()).strip("_")
    return s[:max_len] or "chart"


def _parse_output(
    raw: str | None, all_formats: tuple[str, ...],
) -> tuple[str | None, tuple[str, ...] | None]:
    """Parse --output value, returning (bracket_base, formats) or (None, None) on error.

    bracket_base is None when no bracket syntax was used (plain path or no output).
    formats is None when a validation error was printed.
    """
    if raw is None:
        return None, ("html",)

    m = _BRACKET_RE.match(raw)
    if m:
        base = m.group(1) or None
        fmt_str = m.group(2).strip()
        if fmt_str.lower() == "all":
            return base, all_formats
        formats = tuple(f.strip().lower() for f in fmt_str.split(",") if f.strip())
        invalid = [f for f in formats if f not in _ALL_FORMATS]
        if invalid:
            print(
                f"nveil: error: unsupported format(s): {invalid}. "
                f"Choose from: {sorted(_ALL_FORMATS)}",
                file=sys.stderr,
            )
            return None, None
        return base, formats

    # Plain path — validate extension if present
    ext = Path(raw).suffix.lstrip(".").lower()
    if ext:
        if ext not in _ALL_FORMATS:
            print(
                f"nveil: error: unsupported extension '{ext}'. "
                f"Choose from: {sorted(_ALL_FORMATS)}",
                file=sys.stderr,
            )
            return None, None
        return None, (ext,)

    # No extension, no brackets — default html, treat as directory
    return None, ("html",)


def _resolve_output_paths(
    output: str | None,
    prompt: str,
    formats: tuple[str, ...],
    bracket_base: str | None = None,
) -> dict[str, Path]:
    """Return {fmt: Path} for each requested format."""
    if bracket_base is not None:
        # Bracket syntax: base is a stem or directory prefix
        base = Path(bracket_base) if bracket_base else None
        if base is None or str(bracket_base).endswith("/") or str(bracket_base).endswith("\\"):
            base_dir = base or Path("nveil_out")
            stem = _slug(prompt)
        else:
            base_dir = base.parent if base.parent != Path(".") or base.name else Path(".")
            stem = base.name if base.name else _slug(prompt)
        base_dir.mkdir(parents=True, exist_ok=True)
        return {fmt: base_dir / f"{stem}.{fmt}" for fmt in formats}

    if output:
        out = Path(output)
        if out.suffix and len(formats) == 1:
            # Explicit file path — use as-is for single format
            return {formats[0]: out}
        # Directory (or multi-format): fall through to stem-based naming
        base_dir = out if not out.suffix else out.parent
        stem = out.stem if out.suffix else _slug(prompt)
    else:
        base_dir = Path("nveil_out")
        stem = _slug(prompt)
    base_dir.mkdir(parents=True, exist_ok=True)
    return {fmt: base_dir / f"{stem}.{fmt}" for fmt in formats}


def run(args) -> int:
    configure_from_args(args)

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"nveil: error: data file not found: {data_path}", file=sys.stderr)
        return 1

    import nveil  # picks up freshly-configured client

    bracket_base, formats = _parse_output(args.output, _ALL_FORMATS)
    if formats is None:
        return 1

    out_paths = _resolve_output_paths(args.output, args.prompt, formats, bracket_base)

    spec = nveil.generate_spec(args.prompt, data_path)

    # .nveil output can be written from spec alone; other formats need a render.
    if "nveil" in out_paths:
        spec.save(str(out_paths["nveil"]))
        print(str(out_paths["nveil"]))

    render_fmts = [f for f in out_paths if f != "nveil"]
    if render_fmts:
        fig = spec.render(data_path)
        if "html" in out_paths:
            nveil.save_html(fig, str(out_paths["html"]))
            print(str(out_paths["html"]))
        for fmt in render_fmts:
            if fmt == "html":
                continue
            nveil.save_image(fig, str(out_paths[fmt]))
            print(str(out_paths[fmt]))

    if args.explain:
        print("---")
        print(spec.explanation)
    return 0
