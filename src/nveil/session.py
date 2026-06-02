# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-FileContributor: Guillaume Franque
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Scoped session — owns a temporary workspace for the duration of a ``with:`` block.

Usage::

    with nveil.session() as s:
        spec = s.generate_spec("bar chart of revenue", df)
        fig = spec.render(df)    # reuses the same workspace — no re-run
        nveil.show(fig)
        print(s.timer.summary())
    # workspace cleaned up here
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Optional

from .exceptions import NveilError, SpecGenerationError
from .spec import NveilSpec
from .timing import Timer


class Session:
    """Scoped workspace session.

    The session owns a temporary workspace and a pipeline instance.
    ``generate_spec`` builds and runs the pipeline once; subsequent
    ``render()`` calls reuse the already-computed outputs.

    When ``timing=True``, all operations are tracked in ``self.timer``.
    """

    def __init__(self, client=None, timing: bool = False):
        self._client = client
        self._pipeline = None  # Pipeline instance — alive for the session
        self._workspace: Optional[Path] = None
        self._session_id: Optional[str] = None
        self.timer = Timer(enabled=timing)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if self._workspace and self._workspace.exists():
            shutil.rmtree(self._workspace, ignore_errors=True)
        self._pipeline = None
        self._workspace = None
        self._session_id = None

    def _get_client(self):
        if self._client:
            return self._client
        from . import _get_client
        return _get_client()

    def generate_spec(self, prompt: str, data: Any) -> NveilSpec:
        """Generate a visualization specification.

        All internal processing is done by the engine.
        The session keeps the pipeline instance alive for render() reuse.

        If the server-generated data pipeline fails locally, retries
        with a new server call (the plan is non-deterministic).

        Args:
            prompt: Natural language visualization request.
            data: pandas DataFrame, dict of DataFrames, path (``str`` /
                ``pathlib.Path``) to a CSV/Parquet/JSON/Excel file, or a
                dict mixing those types.

        Returns:
            NveilSpec bound to this session's workspace.
        """
        import logging
        import shutil
        from dive._engine import prepare, apply_plan, finalize
        from . import _normalize_inputs, _MAX_RETRIES

        log = logging.getLogger("nveil")
        client = self._get_client()
        inputs = _normalize_inputs(data)
        last_error = None

        for attempt in range(_MAX_RETRIES + 1):
            with self.timer.measure("build workspace"):
                workspace = prepare(inputs)

            try:
                with self.timer.measure("API: processing plan"):
                    plan_response = client.processing_plan(
                        prompt=prompt,
                        request_blob=workspace["request_blob"],
                        catalogue_stats=workspace["catalogue_stats"],
                    )
                    self._session_id = plan_response.get("session_id", "")

                with self.timer.measure("pipeline run"):
                    pipeline = apply_plan(
                        server_plan_response=plan_response,
                        workspace_state=workspace,
                    )
                    self._pipeline = pipeline.get("_choregraph")
                    self._workspace = pipeline.get("_workspace")

                with self.timer.measure("API: visualization"):
                    viz_response = client.visualization_generate(
                        session_id=self._session_id,
                        request_blob=pipeline["request_blob"],
                    )

                for warning in viz_response.get("warnings", []):
                    log.warning(warning)

                spec_blob = finalize(
                    server_viz_response=viz_response,
                    pipeline_state_blob=pipeline["request_blob"],
                )

                spec = NveilSpec(spec_blob=spec_blob)
                spec._session = self
                return spec

            except RuntimeError as e:
                last_error = e
                if attempt < _MAX_RETRIES:
                    log.warning(
                        "Pipeline execution failed (attempt %d/%d): %s — retrying",
                        attempt + 1, _MAX_RETRIES + 1, e,
                    )
                    # Clean up failed workspace before retry
                    ws = workspace.get("_workspace")
                    if ws and ws.exists():
                        shutil.rmtree(ws, ignore_errors=True)
                continue

        raise SpecGenerationError(
            f"Pipeline execution failed after {_MAX_RETRIES + 1} attempts: {last_error}"
        )
