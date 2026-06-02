# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-FileContributor: Guillaume Franque
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for nveil.__init__ — configure, _get_client, session, generate_spec, load_spec.

Mocks engine and client to test SDK orchestration without a real server.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np

import nveil
from nveil.exceptions import NveilError, SpecGenerationError
from nveil.spec import NveilSpec
from nveil.session import Session
from dive._engine import _serialize


def _make_blob(**overrides):
    payload = {
        "type": "nveil_spec",
        "schema_version": "1.0.0",
        "visuspec_xml": "<spec/>",
        "choregraph_xml": "<cg/>",
        "explanation": "mocked chart",
    }
    payload.update(overrides)
    return _serialize(payload)


class TestConfigure:
    def setup_method(self):
        nveil._client = None
        nveil._timing_enabled = False

    def teardown_method(self):
        if nveil._client:
            nveil._client.close()
        nveil._client = None
        nveil._timing_enabled = False

    def test_sets_global_client(self):
        nveil.configure(api_key="nveil_test", base_url="https://example.com")
        assert nveil._client is not None
        assert nveil._client._api_key == "nveil_test"

    def test_timing_flag(self):
        nveil.configure(api_key="nveil_test", timing=True)
        assert nveil._timing_enabled is True

    def test_verbose_flag(self):
        nveil.configure(api_key="nveil_test", verbose=True)
        import logging
        # Kedro loggers should be at INFO
        assert logging.getLogger("kedro").level == logging.INFO


class TestGetClient:
    def test_raises_when_not_configured(self):
        nveil._client = None
        with pytest.raises(NveilError, match="not configured"):
            nveil._get_client()

    def test_returns_client_when_configured(self):
        nveil.configure(api_key="nveil_test")
        client = nveil._get_client()
        assert client is nveil._client
        nveil._client.close()
        nveil._client = None


class TestSession:
    def test_session_returns_session_object(self):
        nveil._client = MagicMock()
        s = nveil.session()
        assert isinstance(s, Session)
        nveil._client = None

    def test_session_passes_timing(self):
        nveil._client = MagicMock()
        nveil._timing_enabled = True
        s = nveil.session()
        # Timer is enabled via the session constructor
        assert s.timer is not None
        nveil._client = None
        nveil._timing_enabled = False


class TestNormalizeInputs:
    def test_dataframe(self):
        df = pd.DataFrame({"a": [1]})
        result = nveil._normalize_inputs(df)
        assert "dataset" in result

    def test_dict_of_dataframes(self):
        result = nveil._normalize_inputs({
            "a": pd.DataFrame({"x": [1]}),
            "b": pd.DataFrame({"y": [2]}),
        })
        assert "a" in result and "b" in result

    def test_dict_with_plain_values(self):
        result = nveil._normalize_inputs({"data": {"col": [1, 2]}})
        assert isinstance(result["data"], pd.DataFrame)

    def test_numpy_array(self):
        result = nveil._normalize_inputs(np.array([[1, 2], [3, 4]]))
        assert "dataset" in result

    def test_list_of_lists(self):
        result = nveil._normalize_inputs([["x", "y"], [1, 2], [3, 4]])
        assert "dataset" in result
        assert list(result["dataset"].columns) == ["x", "y"]

    def test_plain_list(self):
        result = nveil._normalize_inputs([1, 2, 3])
        assert "dataset" in result

    def test_unsupported_raises_type_error(self):
        with pytest.raises(TypeError, match="Cannot convert"):
            nveil._normalize_inputs(42)

    def test_string_is_treated_as_path(self):
        """Strings are now valid input — they denote a file path.

        Normalization is pure bookkeeping; path existence is only checked
        later by ``dive._engine.prepare``.
        """
        from pathlib import Path as _Path
        result = nveil._normalize_inputs("sales.csv")
        assert isinstance(result["dataset"], _Path)
        assert str(result["dataset"]) == "sales.csv"


class TestGenerateSpec:
    def _setup_mocks(self):
        """Create mocks for engine and client."""
        ws = Path(tempfile.mkdtemp(prefix="test_gen_"))
        pipeline_instance = MagicMock()
        spec_blob = _make_blob()

        mock_prepare = MagicMock(return_value={
            "request_blob": "prep_blob",
            "catalogue_stats": "{}",
            "_workspace": ws,
            "_choregraph": pipeline_instance,
        })
        mock_apply = MagicMock(return_value={
            "request_blob": "apply_blob",
            "session_id": "s1",
            "_workspace": ws,
            "_choregraph": pipeline_instance,
        })
        mock_finalize = MagicMock(return_value=spec_blob)

        mock_client = MagicMock()
        mock_client.processing_plan.return_value = {"session_id": "s1", "spec": "b1"}
        mock_client.visualization_generate.return_value = {
            "spec": "b2", "explanation": "ok", "warnings": [],
        }

        return mock_prepare, mock_apply, mock_finalize, mock_client, ws

    @patch("dive._engine.finalize")
    @patch("dive._engine.apply_plan")
    @patch("dive._engine.prepare")
    def test_full_flow(self, mock_prepare, mock_apply, mock_finalize):
        prep, apply, final, client, ws = self._setup_mocks()
        mock_prepare.return_value = prep.return_value
        mock_apply.return_value = apply.return_value
        mock_finalize.return_value = final.return_value
        nveil._client = client

        df = pd.DataFrame({"x": [1, 2]})
        spec = nveil.generate_spec("bar chart", df)

        assert isinstance(spec, NveilSpec)
        mock_prepare.assert_called()
        mock_apply.assert_called()
        mock_finalize.assert_called()
        nveil._client = None

    @patch("dive._engine.finalize")
    @patch("dive._engine.apply_plan")
    @patch("dive._engine.prepare")
    def test_surfaces_server_warnings(self, mock_prepare, mock_apply, mock_finalize, caplog):
        prep, apply, final, client, ws = self._setup_mocks()
        mock_prepare.return_value = prep.return_value
        mock_apply.return_value = apply.return_value
        mock_finalize.return_value = final.return_value
        client.visualization_generate.return_value = {
            "spec": "b2", "explanation": "ok",
            "warnings": ["ASP optimization failed"],
        }
        nveil._client = client

        import logging
        with caplog.at_level(logging.WARNING, logger="nveil"):
            nveil.generate_spec("bar chart", pd.DataFrame({"x": [1]}))

        assert "ASP optimization failed" in caplog.text
        nveil._client = None

    @patch("dive._engine.apply_plan")
    @patch("dive._engine.prepare")
    def test_retry_on_pipeline_failure(self, mock_prepare, mock_apply, caplog):
        ws = Path(tempfile.mkdtemp(prefix="test_retry_"))
        mock_prepare.return_value = {
            "request_blob": "blob", "catalogue_stats": "{}",
            "_workspace": ws, "_choregraph": MagicMock(),
        }
        mock_apply.side_effect = RuntimeError("Pipeline input not found")

        client = MagicMock()
        client.processing_plan.return_value = {"session_id": "s1", "spec": "b1"}
        nveil._client = client

        import logging
        with caplog.at_level(logging.WARNING, logger="nveil"):
            with pytest.raises(SpecGenerationError, match="after 3 attempts"):
                nveil.generate_spec("bar chart", pd.DataFrame({"x": [1]}))

        assert "retrying" in caplog.text
        assert mock_apply.call_count == 3
        nveil._client = None


class TestLoadSpec:
    def test_load_roundtrip(self, tmp_path):
        blob = _make_blob(explanation="loaded chart")
        spec = NveilSpec(spec_blob=blob)
        path = str(tmp_path / "test.nveil")
        spec.save(path)

        loaded = nveil.load_spec(path)
        assert isinstance(loaded, NveilSpec)
        assert loaded.explanation == "loaded chart"
