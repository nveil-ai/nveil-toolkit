# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-FileContributor: Clément Baraille
# SPDX-License-Identifier: AGPL-3.0-or-later

"""NVEIL API client — handles HTTP communication with the NVEIL server."""

import logging

import httpx

from .exceptions import (
    AuthenticationError,
    QuotaExceededError,
    ScopeError,
    SpecGenerationError,
)

DEFAULT_BASE_URL = "https://app.nveil.com"
DEFAULT_TIMEOUT = 120.0


class NveilClient:
    """HTTP client for the NVEIL public API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        verify: bool = True,
    ):
        """Build a client.

        The LLM provider, credentials and endpoint are NOT configurable
        from the SDK: they are fixed server-side at setup time (the
        operator's ``.env``). Every request runs on the server's
        configured provider — there is no per-call override.

        Args:
            api_key: NVEIL platform key (sent as ``X-API-Key``).
            base_url: NVEIL API base URL.
            timeout: Per-request timeout (seconds).
            verify: TLS certificate verification.
        """
        from . import __version__

        if not verify:
            logging.getLogger("nveil").warning(
                "SSL verification disabled (verify=False). "
                "Only use this for local development with self-signed certificates."
            )

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

        headers = {
            "X-API-Key": api_key,
            "X-Nveil-Schema-Version": __version__,
        }

        self._client = httpx.Client(
            base_url=self._base_url,
            headers=headers,
            timeout=timeout,
            verify=verify,
        )

    def _handle_response(self, resp: httpx.Response) -> dict:
        if resp.status_code == 401:
            raise AuthenticationError(
                "Invalid, expired, or revoked API key"
            )
        if resp.status_code == 403:
            raise ScopeError(resp.json().get("detail", "Missing required scope"))
        if resp.status_code == 429:
            raise QuotaExceededError("Rate limit exceeded")
        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                pass
            raise SpecGenerationError(f"API error ({resp.status_code}): {detail}")
        return resp.json()

    def sdk_process(
        self,
        request_blob: str,
        *,
        prompt: str | None = None,
        session_id: str | None = None,
        catalogue_stats: str | None = None,
    ) -> dict:
        """Invoke the unified SDK endpoint — polymorphic on ``session_id``.

        Fresh turn (no ``session_id``): provide ``prompt`` + initial
        ``catalogue_stats``. The server runs the plan graph and pauses
        for local choregraph execution. Response::

            {"status": "awaiting_choregraph", "session_id", "choregraph_xml",
             "visualization_plan"}

        Resume (``session_id`` + post-transform artifacts in
        ``request_blob``): the server resumes the graph and runs viz +
        ASP. Response::

            {"status": "complete", "visuspec_xml", "explanation", "warnings"}

        Args:
            request_blob: Base64-encoded request payload.
                Contains ``choregraph_xml`` on the fresh call; contains
                ``choregraph_xml`` + ``specifications_xml`` +
                ``catalogue_stats`` on resume.
            prompt: User's natural language prompt (fresh call only).
            session_id: Session ID returned by the previous call (resume
                only).
            catalogue_stats: JSON string of dataset metadata (fresh call
                only; subsequent catalogue stats travel in
                ``request_blob``).
        """
        payload: dict = {"request_blob": request_blob}
        if session_id:
            payload["session_id"] = session_id
        if prompt is not None:
            payload["prompt"] = prompt
        if catalogue_stats is not None:
            payload["catalogue_stats"] = catalogue_stats
        resp = self._client.post("/api/v1/sdk/process", json=payload)
        return self._handle_response(resp)

    # --- Backwards-compatible wrappers (thin) ---

    def processing_plan(
        self,
        prompt: str,
        request_blob: str,
        catalogue_stats: str,
    ) -> dict:
        """Start a two-step SDK flow — thin wrapper around ``sdk_process``.

        Kept for call-site compatibility; prefer ``sdk_process`` directly.
        """
        return self.sdk_process(
            request_blob=request_blob,
            prompt=prompt,
            catalogue_stats=catalogue_stats,
        )

    def visualization_generate(
        self,
        session_id: str,
        request_blob: str,
    ) -> dict:
        """Resume an SDK flow — thin wrapper around ``sdk_process``."""
        return self.sdk_process(
            request_blob=request_blob,
            session_id=session_id,
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
