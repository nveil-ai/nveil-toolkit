# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-FileContributor: Guillaume Franque
# SPDX-License-Identifier: AGPL-3.0-or-later

"""NveilSpec — opaque visualization specification with local rendering.

Once generated, a spec can be reused unlimited times on new data with
compatible columns — no API call, no cost.

All internal processing is handled by the engine. The Toolkit
only stores and passes opaque byte blobs.
"""

from __future__ import annotations

from typing import Any


class NveilSpec:
    """Opaque visualization specification with local rendering.

    Once generated, ``spec.render(new_data)`` is 100% local — no API call,
    no cost. Reusable on any data with compatible columns.
    """

    def __init__(self, spec_blob: bytes):
        self._blob = spec_blob
        self._session = None  # set by Session.generate_spec for workspace reuse

    def render(self, data: Any = None) -> Any:
        """Render using the auto-detected best backend (ECharts, VTK, DeckGL).

        100% local execution — no API call.

        If called within a session context (``with nveil.session()``),
        reuses the session's already-computed pipeline outputs —
        no pipeline re-run.

        Args:
            data: pandas DataFrame, dict of DataFrames, numpy array, or list.

        Returns:
            Backend-specific figure object (ECharts option dict, pydeck
            ``Deck`` / ``Layer``, VTK viz dict, or graph / html payload).
        """
        from dive._engine import render as engine_render
        from .timing import Timer

        session = self._session
        timer = session.timer if session else Timer()

        pipeline_instance = None
        if session and session._pipeline:
            pipeline_instance = session._pipeline

        with timer.measure("render"):
            return engine_render(
                spec_blob=self._blob,
                data=data,
                choregraph_instance=pipeline_instance,
            )

    @property
    def explanation(self) -> str:
        """Human-readable description of what was generated."""
        from dive._engine import get_explanation
        return get_explanation(self._blob)

    def save(self, path: str) -> None:
        """Save to .nveil file."""
        from dive._engine import save_spec
        save_spec(self._blob, path)

    @staticmethod
    def load(path: str) -> NveilSpec:
        """Load from opaque .nveil file."""
        from dive._engine import load_spec
        blob = load_spec(path)
        return NveilSpec(spec_blob=blob)


# ── Module-level display/export functions ──


def show(fig: Any, theme: str = "dark") -> None:
    """Display a figure in the default browser.

    Args:
        fig: Figure object returned by ``NveilSpec.render()``.
        theme: Display theme ("dark" or "light").
    """
    if fig is None:
        raise RuntimeError("No figure to display")

    if isinstance(fig, dict) and ("mapper" in fig or "volume" in fig):
        from dive.builder.export import show_vtk_window
        show_vtk_window(fig, theme=theme)
        return

    import tempfile
    import webbrowser
    from dive.builder.export import export_image

    html = export_image(fig, extension="html", theme=theme)

    tmp = tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8",
    )
    tmp.write(html)
    tmp.close()
    webbrowser.open(f"file://{tmp.name}")


def save_image(
    fig: Any,
    path: str,
    theme: str = "dark",
    width: int = 1200,
    height: int = 800,
    scale: int = 1,
) -> None:
    """Save a figure as a static image.

    Format is inferred from the file extension.
    Supported: .png, .jpg, .svg, .pdf, .html, .json

    Raster / vector formats (png, jpg, svg, pdf) render the figure via
    a headless Chromium instance provided by Playwright. The first run
    downloads Chromium one time (~170 MB); after that exports are local
    and offline.

    Args:
        fig: Figure object returned by ``NveilSpec.render()``.
        path: Output file path (e.g. ``"chart.png"``).
        theme: Export theme ("dark" or "light").
        width: Output image width in pixels. Always honored exactly —
            this is the final pixel dimension of the saved file.
        height: Output image height in pixels. Same contract as ``width``.
        scale: Font / zoom factor — how large text and chart elements
            appear relative to the chart area. Internally mapped to
            Chromium's ``deviceScaleFactor``: the CSS viewport shrinks
            to ``(width / scale, height / scale)`` while the rasteriser
            multiplies back to ``width × height`` device pixels. At
            ``scale=2`` text looks twice as prominent inside the same
            chart, not twice as many pixels. ``scale=1`` is the native
            layout; values above 2 rarely add visual quality.
    """
    if fig is None:
        raise RuntimeError("No figure to export")

    from dive.builder.export import export_to_file

    try:
        export_to_file(fig, path, theme=theme, width=width, height=height, scale=scale)
    except RuntimeError as e:
        msg = str(e).lower()
        if "playwright" in msg or "chromium" in msg:
            _print_chromium_install_banner()
            try:
                import subprocess
                import sys
                subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    check=True,
                    stdout=sys.stderr,
                    stderr=sys.stderr,
                )
                export_to_file(fig, path, theme=theme, width=width, height=height, scale=scale)
            except Exception as install_err:
                raise RuntimeError(
                    "Static image export requires Playwright + Chromium. "
                    "Auto-install failed.\n"
                    "Run manually: playwright install chromium\n"
                    "Or save as HTML instead: nveil.save_html(fig, 'chart.html')"
                ) from install_err
        else:
            raise


def _print_chromium_install_banner() -> None:
    """Visible one-time notice before the Playwright Chromium download.

    Printed via ``sys.stderr`` so it shows up regardless of logging
    configuration. Users otherwise see a silent ~30–60s pause and
    assume the script hung.
    """
    import sys
    banner = (
        "\n"
        "┌──────────────────────────────────────────────────────────────┐\n"
        "│  NVEIL — one-time setup                                      │\n"
        "├──────────────────────────────────────────────────────────────┤\n"
        "│  Downloading Chromium via Playwright (~170 MB)               │\n"
        "│  Needed by nveil.save_image() to render charts to PNG / JPG  │\n"
        "│  / SVG / PDF server-side. Cached locally after this run —    │\n"
        "│  future exports are instant and offline.                     │\n"
        "│                                                              │\n"
        "│  Skip this step next time by pre-installing:                 │\n"
        "│      playwright install chromium                             │\n"
        "└──────────────────────────────────────────────────────────────┘\n"
    )
    sys.stderr.write(banner)
    sys.stderr.flush()


def save_html(fig: Any, path: str, theme: str = "dark") -> None:
    """Save a figure as an interactive HTML file.

    Args:
        fig: Figure object returned by ``NveilSpec.render()``.
        path: Output file path (e.g. ``"chart.html"``).
        theme: Export theme ("dark" or "light").
    """
    from dive.builder.export import export_to_file
    export_to_file(fig, path, theme=theme)
