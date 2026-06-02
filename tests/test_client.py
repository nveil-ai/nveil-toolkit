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
        # No LLM headers when provider/key are not provided — server uses default.
        assert "x-nveil-llm-provider" not in headers
        assert "x-nveil-llm-api-key" not in headers
        client.close()

    def test_context_manager(self):
        with NveilClient(api_key="nveil_test") as client:
            assert client._client is not None
        # After exit, client should be closed


class TestClientLLMConfig:
    def test_llm_headers_attached_when_provided(self):
        client = NveilClient(
            api_key="nveil_test123",
            base_url="https://example.com",
            llm_provider="anthropic",
            llm_api_key="sk-ant-xyz",
        )
        headers = client._client.headers
        assert headers["X-Nveil-LLM-Provider"] == "anthropic"
        assert headers["X-Nveil-LLM-API-Key"] == "sk-ant-xyz"
        # Base URL header is absent when not requested.
        assert "x-nveil-llm-base-url" not in headers
        client.close()

    def test_partial_llm_config_raises(self):
        # provider without key
        with pytest.raises(ValueError, match="must be set together"):
            NveilClient(api_key="nveil_test", llm_provider="openai")
        # key without provider
        with pytest.raises(ValueError, match="must be set together"):
            NveilClient(api_key="nveil_test", llm_api_key="sk-x")

    def test_openrouter_via_base_url(self):
        # Typical OpenRouter usage: provider="openai", a sk-or-... key,
        # and the OpenRouter v1 endpoint as base URL.
        client = NveilClient(
            api_key="nveil_test123",
            base_url="https://example.com",
            llm_provider="openai",
            llm_api_key="sk-or-xyz",
            llm_base_url="https://openrouter.ai/api/v1",
        )
        headers = client._client.headers
        assert headers["X-Nveil-LLM-Provider"] == "openai"
        assert headers["X-Nveil-LLM-API-Key"] == "sk-or-xyz"
        assert headers["X-Nveil-LLM-Base-URL"] == "https://openrouter.ai/api/v1"
        client.close()

    def test_base_url_alone_raises(self):
        with pytest.raises(ValueError, match="requires llm_provider and llm_api_key"):
            NveilClient(
                api_key="nveil_test",
                llm_base_url="https://openrouter.ai/api/v1",
            )


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
