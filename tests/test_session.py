# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-FileContributor: Guillaume Franque
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for nveil.session — lifecycle, workspace cleanup, pipeline reuse.

Mocks the engine functions and client to test SDK orchestration.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile

from nveil.session import Session
from nveil.spec import NveilSpec
from nveil.timing import Timer
from dive._engine import _serialize


class TestSessionLifecycle:
    def test_enter_returns_self(self):
        s = Session()
        result = s.__enter__()
        assert result is s
        s.__exit__(None, None, None)

    def test_exit_clears_state(self):
        s = Session()
        s.__enter__()
        s._pipeline = MagicMock()
        ws = Path(tempfile.mkdtemp(prefix="test_session_"))
        s._workspace = ws
        s._session_id = "test-123"

        s.__exit__(None, None, None)
        assert s._pipeline is None
        assert s._workspace is None
        assert s._session_id is None
        assert not ws.exists()

    def test_exit_handles_missing_workspace(self):
        s = Session()
        s.__enter__()
        s._workspace = None
        s.__exit__(None, None, None)

    def test_timer_disabled_by_default(self):
        s = Session()
        assert isinstance(s.timer, Timer)

    def test_timer_enabled(self):
        s = Session(timing=True)
        assert isinstance(s.timer, Timer)


class TestSessionGetClient:
    def test_uses_provided_client(self):
        mock_client = MagicMock()
        s = Session(client=mock_client)
        assert s._get_client() is mock_client

    def test_falls_back_to_global(self):
        s = Session(client=None)
        with patch("nveil._get_client") as mock:
            mock.return_value = MagicMock()
            result = s._get_client()
            mock.assert_called_once()


class TestSessionGenerateSpec:
    @patch("dive._engine.apply_plan")
    @patch("dive._engine.prepare")
    @patch("dive._engine.finalize")
    def test_returns_nveil_spec(self, mock_finalize, mock_prepare, mock_apply):
        import pandas as pd

        ws = Path(tempfile.mkdtemp(prefix="test_engine_"))
        pipeline_instance = MagicMock()

        spec_blob = _serialize({
            "type": "nveil_spec",
            "schema_version": "1.0.0",
            "visuspec_xml": "<spec/>",
            "choregraph_xml": "<pipeline/>",
            "explanation": "test chart",
        })

        mock_prepare.return_value = {
            "request_blob": "encrypted_prepare",
            "catalogue_stats": "{}",
            "_workspace": ws,
            "_choregraph": pipeline_instance,
        }
        mock_apply.return_value = {
            "request_blob": "encrypted_apply",
            "session_id": "test-session",
            "_workspace": ws,
            "_choregraph": pipeline_instance,
        }
        mock_finalize.return_value = spec_blob

        mock_client = MagicMock()
        mock_client.processing_plan.return_value = {"session_id": "s1", "spec": "blob"}
        mock_client.visualization_generate.return_value = {"spec": "blob2", "explanation": "test"}

        s = Session(client=mock_client)
        s.__enter__()
        try:
            df = pd.DataFrame({"x": [1, 2]})
            spec = s.generate_spec("bar chart", df)

            assert isinstance(spec, NveilSpec)
            assert spec._session is s
            assert s._pipeline is not None
            assert s._workspace is not None
            mock_prepare.assert_called_once()
            mock_apply.assert_called_once()
            mock_finalize.assert_called_once()
        finally:
            s.__exit__(None, None, None)
