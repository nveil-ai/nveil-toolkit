# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-FileContributor: Clément Baraille
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for nveil.client — HTTP error handling and request construction.

Uses httpx mock transport to simulate server responses without a real server.
"""

import json
import pytest
import httpx

from nveil.client import NveilClient
from nveil.exceptions import (
    AuthenticationError,
    ScopeError,
    QuotaExceededError,
    SpecGenerationError,
)


def _mock_transport(status_code, json_body=None, text_body=None):
    """Create a mock httpx transport that returns a fixed response."""
    def handler(request):
        if json_body is not None:
            content = json.dumps(json_body).encode()
            headers = {"content-type": "application/json"}
        else:
            content = (text_body or "").encode()
            headers = {"content-type": "text/plain"}
        return httpx.Response(status_code, content=content, headers=headers)
    return httpx.MockTransport(handler)


class TestClientInit:
    def test_sets_headers(self):
        client = NveilClient(api_key="nveil_test123", base_url="https://example.com")
        headers = client._client.headers
        assert headers["X-API-Key"] == "nveil_test123"
        assert "X-Nveil-Schema-Version" in headers
        # The LLM provider/key/endpoint are fixed server-side at setup time —
        # the client never sends them, regardless of how it's constructed.
        assert "x-nveil-llm-provider" not in headers
        assert "x-nveil-llm-api-key" not in headers
        assert "x-nveil-llm-base-url" not in headers
        client.close()

    def test_context_manager(self):
        with NveilClient(api_key="nveil_test") as client:
            assert client._client is not None
        # After exit, client should be closed


class TestClientLLMConfig:
    def test_llm_config_not_accepted(self):
        # Per-call LLM configuration was removed: the provider/key/endpoint
        # are determined solely by the server's setup (.env). Attempting to
        # pass them is a hard error, not a silent override.
        with pytest.raises(TypeError):
            NveilClient(api_key="nveil_test", llm_provider="anthropic", llm_api_key="sk-ant-xyz")
        with pytest.raises(TypeError):
            NveilClient(api_key="nveil_test", llm_base_url="https://openrouter.ai/api/v1")


class TestHandleResponse401:
    def test_raises_authentication_error(self):
        transport = _mock_transport(401, json_body={"detail": "bad key"})
        client = NveilClient.__new__(NveilClient)
        client._client = httpx.Client(transport=transport, base_url="https://x.com")
        with pytest.raises(AuthenticationError, match="Invalid, expired, or revoked"):
            client.processing_plan(prompt="test", request_blob="blob", catalogue_stats="{}")
        client.close()


class TestHandleResponse403:
    def test_raises_scope_error(self):
        transport = _mock_transport(403, json_body={"detail": "Missing scope: viz"})
        client = NveilClient.__new__(NveilClient)
        client._client = httpx.Client(transport=transport, base_url="https://x.com")
        with pytest.raises(ScopeError, match="Missing scope"):
            client.processing_plan(prompt="test", request_blob="blob", catalogue_stats="{}")
        client.close()


class TestHandleResponse429:
    def test_raises_quota_error(self):
        transport = _mock_transport(429, json_body={"detail": "rate limited"})
        client = NveilClient.__new__(NveilClient)
        client._client = httpx.Client(transport=transport, base_url="https://x.com")
        with pytest.raises(QuotaExceededError, match="Rate limit"):
            client.visualization_generate(session_id="s1", request_blob="blob")
        client.close()


class TestHandleResponse500:
    def test_raises_spec_generation_error_json(self):
        transport = _mock_transport(500, json_body={"detail": "Internal error"})
        client = NveilClient.__new__(NveilClient)
        client._client = httpx.Client(transport=transport, base_url="https://x.com")
        with pytest.raises(SpecGenerationError, match="Internal error"):
            client.processing_plan(prompt="test", request_blob="blob", catalogue_stats="{}")
        client.close()

    def test_raises_spec_generation_error_plaintext(self):
        transport = _mock_transport(502, text_body="Bad Gateway")
        client = NveilClient.__new__(NveilClient)
        client._client = httpx.Client(transport=transport, base_url="https://x.com")
        with pytest.raises(SpecGenerationError, match="Bad Gateway"):
            client.processing_plan(prompt="test", request_blob="blob", catalogue_stats="{}")
        client.close()


class TestSuccessfulResponse:
    def test_processing_plan_returns_json(self):
        body = {"session_id": "abc", "spec": "encrypted_blob", "explanation": "bar chart"}
        transport = _mock_transport(200, json_body=body)
        client = NveilClient.__new__(NveilClient)
        client._client = httpx.Client(transport=transport, base_url="https://x.com")
        result = client.processing_plan(prompt="test", request_blob="blob", catalogue_stats="{}")
        assert result == body
        client.close()

    def test_visualization_generate_returns_json(self):
        body = {"spec": "encrypted_blob", "explanation": "scatter plot"}
        transport = _mock_transport(200, json_body=body)
        client = NveilClient.__new__(NveilClient)
        client._client = httpx.Client(transport=transport, base_url="https://x.com")
        result = client.visualization_generate(session_id="s1", request_blob="blob")
        assert result == body
        client.close()
