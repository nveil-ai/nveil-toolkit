# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""End-to-end test of the NVEIL public API using engine blobs.

Tests the raw two-step flow without the SDK wrapper.
Requires a running server on localhost.

Run with: pytest tests/test_api.py -v
"""

import os
import pytest
import httpx
import pandas as pd
import numpy as np
from pathlib import Path

from dive._engine import prepare, apply_plan, finalize, save_spec, load_spec, get_explanation

API_KEY = os.environ.get("NVEIL_TEST_API_KEY", "")

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not API_KEY, reason="NVEIL_TEST_API_KEY not set"),
]

OUT_DIR = Path(__file__).parent / "out"


@pytest.fixture(scope="module")
def http_client():
    OUT_DIR.mkdir(exist_ok=True)
    client = httpx.Client(
        base_url="https://localhost:8000",
        verify=False,
        headers={
            "X-API-Key": API_KEY,
            "X-Nveil-Schema-Version": "1.0.0",
        },
        timeout=120,
    )
    yield client
    client.close()


@pytest.fixture
def dataframes():
    df = pd.DataFrame({
        "region": np.random.choice(["North", "South", "East", "West"], 50),
        "revenue": np.random.uniform(1000, 50000, 50).round(2),
    })
    return {"sales": df}


class TestProcessingPlan:
    def test_returns_200(self, http_client, dataframes):
        workspace = prepare(dataframes)
        resp = http_client.post("/api/v1/sdk/process", json={
            "prompt": "bar chart of revenue by region",
            "request_blob": workspace["request_blob"],
            "catalogue_stats": workspace["catalogue_stats"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "awaiting_choregraph"
        assert "session_id" in data
        assert "choregraph_xml" in data

    def test_response_contains_plan_data(self, http_client, dataframes):
        workspace = prepare(dataframes)
        resp = http_client.post("/api/v1/sdk/process", json={
            "prompt": "bar chart",
            "request_blob": workspace["request_blob"],
            "catalogue_stats": workspace["catalogue_stats"],
        })
        data = resp.json()
        assert data["status"] == "awaiting_choregraph"
        assert "choregraph_xml" in data
        assert "visualization_plan" in data


class TestFullFlow:
    def test_two_step_flow(self, http_client, dataframes):
        # Step 1: Prepare
        workspace = prepare(dataframes)

        # Step 2: Fresh call — graph pauses at trigger_choregraph_run_node
        resp1 = http_client.post("/api/v1/sdk/process", json={
            "prompt": "bar chart of revenue by region",
            "request_blob": workspace["request_blob"],
            "catalogue_stats": workspace["catalogue_stats"],
        })
        assert resp1.status_code == 200
        body1 = resp1.json()
        assert body1["status"] == "awaiting_choregraph"
        session_id = body1["session_id"]

        # Step 3: Apply plan locally
        pipeline = apply_plan(
            server_plan_response=body1,
            workspace_state=workspace,
        )

        # Step 4: Resume — graph runs viz + ASP then ends (is_api skips viz_build)
        resp2 = http_client.post("/api/v1/sdk/process", json={
            "session_id": session_id,
            "request_blob": pipeline["request_blob"],
        })
        assert resp2.status_code == 200
        body2 = resp2.json()
        assert body2["status"] == "complete"
        assert "visuspec_xml" in body2

        # Step 5: Finalize
        spec_blob = finalize(
            server_viz_response=body2,
            pipeline_state_blob=pipeline["request_blob"],
        )
        assert isinstance(spec_blob, bytes)
        assert len(spec_blob) > 0

    def test_save_load_roundtrip(self, http_client, dataframes):
        workspace = prepare(dataframes)
        resp1 = http_client.post("/api/v1/sdk/process", json={
            "prompt": "bar chart",
            "request_blob": workspace["request_blob"],
            "catalogue_stats": workspace["catalogue_stats"],
        })
        body1 = resp1.json()
        pipeline = apply_plan(
            server_plan_response=body1,
            workspace_state=workspace,
        )
        resp2 = http_client.post("/api/v1/sdk/process", json={
            "session_id": body1["session_id"],
            "request_blob": pipeline["request_blob"],
        })
        body2 = resp2.json()
        spec_blob = finalize(
            server_viz_response=body2,
            pipeline_state_blob=pipeline["request_blob"],
        )

        # Save and load
        path = str(OUT_DIR / "api_test.nveil")
        save_spec(spec_blob, path)
        loaded = load_spec(path)
        assert get_explanation(loaded) == get_explanation(spec_blob)
