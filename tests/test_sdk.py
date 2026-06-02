# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""End-to-end SDK tests — require a running NVEIL server on localhost.

Run with: pytest tests/test_sdk.py -v
Requires: Docker Compose backend running (make up)

Each test class generates one spec and validates multiple aspects of it,
to minimize redundant server calls.
"""

import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

import nveil
from nveil.spec import NveilSpec

API_KEY = os.environ.get("NVEIL_TEST_API_KEY", "")

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not API_KEY, reason="NVEIL_TEST_API_KEY not set"),
]

OUT_DIR = Path(__file__).parent / "out"


@pytest.fixture(scope="module", autouse=True)
def configure_sdk():
    OUT_DIR.mkdir(exist_ok=True)
    nveil.configure(
        api_key=API_KEY,
        base_url="https://localhost:8000",
        timeout=120,
        verify=False,
    )
    yield
    nveil._client.close()
    nveil._client = None


# ── Datasets ──

@pytest.fixture(scope="module")
def sales_df():
    return pd.DataFrame({
        "region": np.random.choice(["North", "South", "East", "West", "Central"], 100),
        "revenue": np.random.uniform(1000, 50000, 100).round(2),
        "quarter": np.random.choice(["Q1", "Q2", "Q3", "Q4"], 100),
        "units_sold": np.random.randint(1, 500, 100),
    })


@pytest.fixture(scope="module")
def timeseries_df():
    dates = pd.date_range("2024-01-01", periods=50, freq="W")
    return pd.DataFrame({
        "date": dates,
        "value": np.cumsum(np.random.randn(50)) + 100,
        "category": np.random.choice(["A", "B"], 50),
    })


# ── Bar Chart (the baseline) ──

class TestBarChart:
    @pytest.fixture(scope="class")
    def spec(self, sales_df):
        with nveil.session() as s:
            spec = s.generate_spec("bar chart of revenue by region", sales_df)
            # Detach from session so it can be used standalone
            spec._session = None
            return spec

    def test_returns_spec(self, spec):
        assert isinstance(spec, NveilSpec)
        assert len(spec._blob) > 0

    def test_blob_is_opaque(self, spec):
        assert not spec._blob.startswith(b"<")

    def test_has_explanation(self, spec):
        assert isinstance(spec.explanation, str)
        assert len(spec.explanation) > 0

    def test_render_returns_figure(self, spec, sales_df):
        fig = spec.render(sales_df)
        assert fig is not None

    def test_render_has_traces(self, spec, sales_df):
        fig = spec.render(sales_df)
        if hasattr(fig, "data"):
            assert len(fig.data) > 0, "Figure has no data traces"

    def test_save_load_roundtrip(self, spec):
        path = str(OUT_DIR / "bar_chart.nveil")
        spec.save(path)
        assert os.path.getsize(path) > 0
        with open(path, "rb") as f:
            assert f.read(5) == b"NVEIL"
        loaded = nveil.load_spec(path)
        assert loaded.explanation == spec.explanation

    def test_save_file_not_readable(self, spec):
        path = str(OUT_DIR / "bar_opaque.nveil")
        spec.save(path)
        raw = Path(path).read_bytes()
        assert b"<visuSpec" not in raw
        assert b"<choregraph" not in raw

    def test_save_html(self, spec, sales_df):
        fig = spec.render(sales_df)
        path = str(OUT_DIR / "bar_chart.html")
        nveil.save_html(fig, path)
        content = Path(path).read_text(encoding="utf-8")
        assert "<html" in content.lower() or "<div" in content.lower()
        assert len(content) > 100

    def test_save_image_png(self, spec, sales_df):
        fig = spec.render(sales_df)
        path = str(OUT_DIR / "bar_chart.png")
        try:
            nveil.save_image(fig, path)
            assert os.path.getsize(path) > 1000, "PNG file too small"
        except Exception as e:
            if "playwright" in str(e).lower() or "chromium" in str(e).lower() or "chrome" in str(e).lower():
                pytest.skip("Playwright/Chromium not installed for static image export")
            raise


# ── Scatter Plot ──

class TestScatterPlot:
    @pytest.fixture(scope="class")
    def spec(self, sales_df):
        return nveil.generate_spec("scatter plot of revenue vs units sold", sales_df)

    def test_returns_spec(self, spec):
        assert isinstance(spec, NveilSpec)

    def test_render(self, spec, sales_df):
        fig = spec.render(sales_df)
        assert fig is not None


# ── Line Chart (time series) ──

class TestLineChart:
    @pytest.fixture(scope="class")
    def spec(self, timeseries_df):
        return nveil.generate_spec(
            "line chart of value over time, colored by category",
            timeseries_df,
        )

    def test_returns_spec(self, spec):
        assert isinstance(spec, NveilSpec)

    def test_render(self, spec, timeseries_df):
        fig = spec.render(timeseries_df)
        assert fig is not None


# ── Multi-Dataset ──

class TestMultiDataset:
    @pytest.fixture(scope="class")
    def spec(self, sales_df):
        targets = pd.DataFrame({
            "region": ["North", "South", "East", "West", "Central"],
            "target": [30000, 25000, 20000, 35000, 28000],
        })
        return nveil.generate_spec(
            "Compare actual revenue vs target by region",
            {"sales": sales_df, "targets": targets},
        )

    @pytest.mark.xfail(
        reason="LLM-generated execute_code nodes sometimes produce Kedro catalog "
               "registration failures for multi-input pipelines — choregraph bug",
        strict=False,
    )
    def test_returns_spec(self, spec):
        assert isinstance(spec, NveilSpec)


# ── Offline Rendering (load .nveil and render without server) ──

class TestOfflineRender:
    """The key user scenario: save a spec, load it later, render on new data."""

    @pytest.fixture(scope="class")
    def nveil_path(self, sales_df):
        path = str(OUT_DIR / "offline_test.nveil")
        spec = nveil.generate_spec("bar chart of revenue by region", sales_df)
        spec.save(path)
        return path

    def test_load_and_render(self, nveil_path, sales_df):
        """Load from .nveil file and render — no API call, no session."""
        spec = nveil.load_spec(nveil_path)
        fig = spec.render(sales_df)
        assert fig is not None

    def test_render_on_new_data(self, nveil_path):
        """Render the saved spec on completely new data with same columns."""
        new_df = pd.DataFrame({
            "region": ["Paris", "Lyon", "Marseille"],
            "revenue": [50000, 30000, 40000],
            "quarter": ["Q1", "Q1", "Q1"],
            "units_sold": [100, 200, 150],
        })
        spec = nveil.load_spec(nveil_path)
        fig = spec.render(new_df)
        assert fig is not None

    def test_render_has_traces(self, nveil_path, sales_df):
        spec = nveil.load_spec(nveil_path)
        fig = spec.render(sales_df)
        if hasattr(fig, "data"):
            assert len(fig.data) > 0, "Offline-rendered figure has no traces"

    def test_export_html_from_loaded_spec(self, nveil_path, sales_df):
        spec = nveil.load_spec(nveil_path)
        fig = spec.render(sales_df)
        html_path = str(OUT_DIR / "offline_render.html")
        nveil.save_html(fig, html_path)
        assert os.path.getsize(html_path) > 100


# ── Session Reuse ──

class TestSessionReuse:
    def test_session_pipeline_reuse(self, sales_df):
        """Within a session, render() should reuse the pipeline."""
        with nveil.session() as s:
            spec = s.generate_spec("bar chart of revenue", sales_df)
            assert spec._session is s
            fig1 = spec.render(sales_df)
            fig2 = spec.render(sales_df)
            assert fig1 is not None
            assert fig2 is not None
