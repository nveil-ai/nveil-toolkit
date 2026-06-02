# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-FileContributor: Guillaume Franque
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for nveil.spec — NveilSpec save/load, data normalization."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from nveil.spec import NveilSpec
from nveil import _normalize_inputs
from dive._engine import _serialize


# ---------------------------------------------------------------------------
# NveilSpec save/load (opaque blob architecture)
# ---------------------------------------------------------------------------


class TestNveilSpec:
    def _make_blob(self, **overrides):
        """Create a test spec blob."""
        payload = {
            "type": "nveil_spec",
            "schema_version": "1.0.0",
            "visuspec_xml": "<visuSpec/>",
            "choregraph_xml": "<choregraph/>",
            "explanation": "Test chart",
        }
        payload.update(overrides)
        return _serialize(payload)

    def test_save_load_roundtrip(self, tmp_path):
        blob = self._make_blob(explanation="bar chart of revenue")
        spec = NveilSpec(spec_blob=blob)
        path = str(tmp_path / "spec.nveil")
        spec.save(path)

        loaded = NveilSpec.load(path)
        assert loaded.explanation == "bar chart of revenue"

    def test_explanation_property(self):
        blob = self._make_blob(explanation="scatter plot")
        spec = NveilSpec(spec_blob=blob)
        assert spec.explanation == "scatter plot"

    def test_file_is_plaintext_json(self, tmp_path):
        blob = self._make_blob(visuspec_xml="<myspec/>")
        spec = NveilSpec(spec_blob=blob)
        path = str(tmp_path / "spec.nveil")
        spec.save(path)
        raw = Path(path).read_bytes()
        assert b"<myspec/>" in raw
        assert raw[:5] == b"NVEIL"

    def test_file_has_nveil_header(self, tmp_path):
        blob = self._make_blob()
        spec = NveilSpec(spec_blob=blob)
        path = str(tmp_path / "spec.nveil")
        spec.save(path)
        raw = Path(path).read_bytes()
        assert raw[:5] == b"NVEIL"
        assert raw[5] == 2  # version byte

    def test_corrupted_json_fails(self, tmp_path):
        path = str(tmp_path / "spec.nveil")
        Path(path).write_bytes(b"NVEIL\x02not-valid-json")
        with pytest.raises(Exception):
            NveilSpec.load(path)


# ---------------------------------------------------------------------------
# Data normalization
# ---------------------------------------------------------------------------


class TestNormalizeToDict:
    def test_dataframe_wrapped(self):
        df = pd.DataFrame({"a": [1]})
        result = _normalize_inputs(df)
        assert "dataset" in result
        assert result["dataset"] is df

    def test_dict_of_dataframes(self):
        d = {"sales": pd.DataFrame({"x": [1]}), "costs": pd.DataFrame({"y": [2]})}
        result = _normalize_inputs(d)
        assert "sales" in result
        assert "costs" in result

    def test_dict_with_non_df_values(self):
        result = _normalize_inputs({"data": {"a": [1, 2]}})
        assert isinstance(result["data"], pd.DataFrame)

    def test_list_input(self):
        result = _normalize_inputs([["a", "b"], [1, 2]])
        assert "dataset" in result
        assert isinstance(result["dataset"], pd.DataFrame)

    def test_numpy_array(self):
        arr = np.array([[1, 2], [3, 4]])
        result = _normalize_inputs(arr)
        assert "dataset" in result
        assert isinstance(result["dataset"], pd.DataFrame)

    def test_unsupported_type_raises(self):
        # Integers, classes, etc. still raise — no reasonable coercion.
        with pytest.raises(TypeError, match="Cannot convert"):
            _normalize_inputs(42)

    def test_string_is_treated_as_path(self):
        # Strings are paths now; existence is checked later at prepare time.
        result = _normalize_inputs("sales.csv")
        assert isinstance(result["dataset"], Path)
