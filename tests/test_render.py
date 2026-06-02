# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-FileContributor: Guillaume Franque
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for NveilSpec.render(), show(), save_image(), save_html().

Mocks engine and export functions to test SDK orchestration.
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from nveil.spec import NveilSpec, show, save_image, save_html
from nveil.timing import Timer
from dive._engine import _serialize


def _make_spec_blob(**overrides):
    payload = {
        "type": "nveil_spec",
        "schema_version": "1.0.0",
        "visuspec_xml": "<spec/>",
        "choregraph_xml": "<cg/>",
        "explanation": "test",
    }
    payload.update(overrides)
    return _serialize(payload)


# ── NveilSpec.render() ──

class TestRender:
    @patch("dive._engine.render")
    def test_delegates_to_engine(self, mock_render):
        mock_render.return_value = MagicMock(name="figure")
        blob = _make_spec_blob()
        spec = NveilSpec(spec_blob=blob)

        import pandas as pd
        df = pd.DataFrame({"x": [1, 2]})
        fig = spec.render(df)

        mock_render.assert_called_once()
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs["spec_blob"] is blob
        assert call_kwargs["data"] is df
        assert call_kwargs["choregraph_instance"] is None

    @patch("dive._engine.render")
    def test_passes_session_pipeline(self, mock_render):
        mock_render.return_value = MagicMock(name="figure")
        blob = _make_spec_blob()
        spec = NveilSpec(spec_blob=blob)

        mock_session = MagicMock()
        mock_session._pipeline = MagicMock(name="pipeline_instance")
        mock_session.timer = Timer(enabled=False)
        spec._session = mock_session

        fig = spec.render(None)

        call_kwargs = mock_render.call_args[1]
        assert call_kwargs["choregraph_instance"] is mock_session._pipeline

    @patch("dive._engine.render")
    def test_render_without_data(self, mock_render):
        mock_render.return_value = MagicMock()
        blob = _make_spec_blob()
        spec = NveilSpec(spec_blob=blob)
        fig = spec.render()
        assert fig is not None
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs["data"] is None


# ── explanation ──

class TestExplanation:
    def test_extracts_from_blob(self):
        blob = _make_spec_blob(explanation="Revenue by region")
        spec = NveilSpec(spec_blob=blob)
        assert spec.explanation == "Revenue by region"

    def test_empty_explanation(self):
        blob = _make_spec_blob(explanation="")
        spec = NveilSpec(spec_blob=blob)
        assert spec.explanation == ""


# ── show() ──

class TestShow:
    def test_raises_on_none_figure(self):
        with pytest.raises(RuntimeError, match="No figure"):
            show(None)

    @patch("webbrowser.open")
    @patch("dive.builder.export.export_image", return_value="<html>test</html>")
    def test_opens_browser(self, mock_export, mock_open):
        show(MagicMock(), theme="dark")
        mock_export.assert_called_once()
        mock_open.assert_called_once()

    @patch("webbrowser.open")
    @patch("dive.builder.export.export_image", return_value="<html>x</html>")
    def test_passes_theme(self, mock_export, mock_open):
        show(MagicMock(), theme="light")
        args = mock_export.call_args
        assert args[1]["theme"] == "light"


# ── save_image() ──

class TestSaveImage:
    def test_raises_on_none_figure(self):
        with pytest.raises(RuntimeError, match="No figure"):
            save_image(None, "test.png")

    @patch("dive.builder.export.export_to_file")
    def test_delegates_to_export(self, mock_export):
        fig = MagicMock()
        save_image(fig, "chart.png", theme="light", width=800, height=600, scale=2)
        mock_export.assert_called_once_with(
            fig, "chart.png", theme="light", width=800, height=600, scale=2,
        )

    @patch("dive.builder.export.export_to_file")
    def test_default_params(self, mock_export):
        fig = MagicMock()
        save_image(fig, "chart.svg")
        mock_export.assert_called_once_with(
            fig, "chart.svg", theme="dark", width=1200, height=800, scale=1,
        )


# ── save_html() ──

class TestSaveHtml:
    @patch("dive.builder.export.export_to_file")
    def test_delegates_to_export(self, mock_export):
        fig = MagicMock()
        save_html(fig, "chart.html", theme="light")
        mock_export.assert_called_once_with(fig, "chart.html", theme="light")

    @patch("dive.builder.export.export_to_file")
    def test_default_theme(self, mock_export):
        fig = MagicMock()
        save_html(fig, "out.html")
        mock_export.assert_called_once_with(fig, "out.html", theme="dark")
