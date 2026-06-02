"""NVEIL Toolkit — no-code AI data visualization.

Usage::

    import nveil
    import pandas as pd

    nveil.configure(api_key="nveil_...")

    df = pd.read_csv("sales.csv")
    spec = nveil.generate_spec("Show revenue by region", df)

    fig = spec.render(df)
    fig.show()

    spec.save("revenue.nveil")
    spec = nveil.load_spec("revenue.nveil")
    fig = spec.render(new_df)
"""

import logging as _logging
import os as _os
import warnings as _warnings
from typing import Any

from importlib.metadata import version as _pkg_version
try:
    __version__ = _pkg_version("nveil")
except Exception:
    __version__ = "0.0.0"

# Silence verbose internal logging by default.
if not _os.environ.get("NVEIL_VERBOSE"):
    for _name in (
        "kedro", "kedro.io", "kedro.runner", "kedro.pipeline",
        "kedro.framework", "dive", "dive.builder", "choregraph",
    ):
        _logging.getLogger(_name).setLevel(_logging.WARNING)
    _logging.getLogger().setLevel(_logging.WARNING)

    # Suppress pandas 3.x ChainedAssignmentError warnings raised from internal
    # dive/choregraph operations. These are cosmetic — the operations work
    # correctly. Users can re-enable by setting NVEIL_VERBOSE=1.
    try:
        from pandas.errors import ChainedAssignmentError as _CAE
        _warnings.filterwarnings("ignore", category=_CAE)
    except ImportError:
        pass

from .client import NveilClient
from .exceptions import (
    AuthenticationError,
    IncompatibleDataError,
    NveilError,
    QuotaExceededError,
    ScopeError,
    SpecGenerationError,
)
from .spec import NveilSpec, show, save_image, save_html
from .session import Session

__all__ = [
    "configure",
    "session",
    "generate_spec",
    "load_spec",
    "show",
    "save_image",
    "save_html",
    "NveilClient",
    "NveilSpec",
    "Session",
    "NveilError",
    "AuthenticationError",
    "ScopeError",
    "QuotaExceededError",
    "SpecGenerationError",
    "IncompatibleDataError",
]

_client: NveilClient | None = None
_timing_enabled: bool = False


def _warn_missing_extras() -> None:
    """Print a one-time hint when optional heavy extras are not installed.

    Fires inside ``configure()`` so it appears exactly once per script,
    at the moment the user has already expressed intent to use the Toolkit.
    pip has no reliable post-install hook for wheel-based installs, so
    this is the best available substitute.
    """
    try:
        import vtk  # noqa: F401
    except ImportError:
        import sys
        print(
            "\n[nveil] Tip: 3D visualizations (voxel, 3D scatter/lines, 3D vector field)\n"
            "        require VTK, which is not installed. To enable them run:\n"
            "            pip install 'nveil[extra]'\n",
            file=sys.stderr,
        )


def configure(
    api_key: str,
    base_url: str = "https://app.nveil.com",
    verify: bool = True,
    verbose: bool = False,
    timing: bool = False,
    **kwargs,
):
    """Configure the global NVEIL client.

    Args:
        api_key: Your NVEIL API key (starts with ``nveil_``).
        base_url: NVEIL server URL (default: ``https://app.nveil.com``).
        verify: Verify SSL certificates (set ``False`` for local dev with self-signed certs).
        verbose: Enable internal library logging (default: silent).
        timing: Enable timing instrumentation (default: ``False``).
    """
    global _client, _timing_enabled
    _timing_enabled = timing
    if verbose:
        for name in ("kedro", "kedro.io", "kedro.runner", "kedro.pipeline", "kedro.framework"):
            _logging.getLogger(name).setLevel(_logging.INFO)
    _client = NveilClient(api_key=api_key, base_url=base_url, verify=verify, **kwargs)
    _warn_missing_extras()


def _get_client() -> NveilClient:
    if _client is None:
        raise NveilError(
            "NVEIL not configured. Call nveil.configure(api_key='nveil_...') first."
        )
    return _client


def session() -> Session:
    """Create a scoped session with a shared workspace.

    Use as a context manager to keep the workspace alive across
    ``generate_spec`` and ``render`` calls — the data pipeline
    runs once, not on every render.

    Example::

        with nveil.session() as s:
            spec = s.generate_spec("bar chart of revenue", df)
            fig = spec.render(df)  # reuses pipeline — no re-run
            nveil.show(fig)
        # workspace cleaned up here
    """
    return Session(client=_client, timing=_timing_enabled)


def _normalize_inputs(data) -> dict:
    """Normalize user input to a dict mapping dataset name → DataFrame or file path.

    Accepts:
        - ``pd.DataFrame`` → ``{"dataset": df}``
        - ``str`` / ``pathlib.Path`` (path to CSV/Parquet/JSON/Excel) → ``{"dataset": path}``
        - ``dict`` where each value is a DataFrame, path, or path-like value
        - ``np.ndarray`` / ``list`` / ``list[list]`` → ``{"dataset": df}``

    Path values are passed through unchanged so the engine can register them
    as path-backed choregraph inputs (no DataFrame held in the caller's RAM).
    """
    import os
    from pathlib import Path as _Path
    import pandas as pd
    import numpy as np

    def _looks_like_path(v):
        return isinstance(v, (str, os.PathLike)) and not isinstance(v, bytes)

    if isinstance(data, pd.DataFrame):
        return {"dataset": data}
    if _looks_like_path(data):
        return {"dataset": _Path(data)}
    if isinstance(data, dict):
        result = {}
        for name, value in data.items():
            if isinstance(value, pd.DataFrame):
                result[name] = value
            elif _looks_like_path(value):
                result[name] = _Path(value)
            else:
                result[name] = pd.DataFrame(value)
        return result
    if isinstance(data, np.ndarray):
        return {"dataset": pd.DataFrame(data)}
    if isinstance(data, list):
        if data and isinstance(data[0], (list, tuple)):
            return {"dataset": pd.DataFrame(data[1:], columns=data[0])}
        return {"dataset": pd.DataFrame(data)}
    raise TypeError(f"Cannot convert {type(data).__name__} to a dataset")


_MAX_RETRIES = 2


def generate_spec(prompt: str, data: Any) -> NveilSpec:
    """Generate a visualization specification from data and a prompt.

    Only metadata leaves your machine — never raw data.
    All internal processing is handled by the engine.

    If the server-generated data pipeline fails locally, the Toolkit retries
    with a new server call (the plan is non-deterministic).

    Args:
        prompt: Natural language description of the desired visualization.
        data: pandas DataFrame, dict of DataFrames, numpy array, list of lists,
            or a path (``str`` / ``pathlib.Path``) to a CSV / Parquet / JSON /
            Excel file. A dict of paths is also accepted for multi-dataset
            inputs. Path inputs avoid holding the DataFrame in your process
            — the engine registers them as disk-backed choregraph inputs.

    Returns:
        NveilSpec that can render locally and be saved/reused.
    """
    import logging
    import shutil
    from dive._engine import prepare, apply_plan, finalize

    log = logging.getLogger("nveil")
    client = _get_client()
    inputs = _normalize_inputs(data)
    last_error = None

    for attempt in range(_MAX_RETRIES + 1):
        workspace = prepare(inputs)

        try:
            # Step 1: Send request to server for processing plan
            plan_response = client.processing_plan(
                prompt=prompt,
                request_blob=workspace["request_blob"],
                catalogue_stats=workspace["catalogue_stats"],
            )

            # Step 2: Apply plan + run pipeline locally
            pipeline = apply_plan(
                server_plan_response=plan_response,
                workspace_state=workspace,
            )

            # Step 3: Send request to server for visualization
            viz_response = client.visualization_generate(
                session_id=plan_response.get("session_id", ""),
                request_blob=pipeline["request_blob"],
            )

            # Surface server warnings
            for warning in viz_response.get("warnings", []):
                log.warning(warning)

            # Step 4: Package final spec as opaque blob
            spec_blob = finalize(
                server_viz_response=viz_response,
                pipeline_state_blob=pipeline["request_blob"],
            )

            return NveilSpec(spec_blob=spec_blob)

        except RuntimeError as e:
            # If the root cause is a missing optional dependency, retrying is
            # pointless — the package won't appear on its own. Surface it
            # immediately with a clean message instead of burning all retries.
            from choregraph._extras import find_import_error
            import_err = find_import_error(e)
            if import_err is not None:
                raise SpecGenerationError(str(import_err)) from None

            last_error = e
            if attempt < _MAX_RETRIES:
                log.warning(
                    "Pipeline execution failed (attempt %d/%d): %s — retrying",
                    attempt + 1, _MAX_RETRIES + 1, e,
                )
            continue
        finally:
            # Clean up workspace (standalone flow — no session to keep it alive)
            ws = workspace.get("_workspace")
            if ws and ws.exists():
                shutil.rmtree(ws, ignore_errors=True)

    raise SpecGenerationError(
        f"Pipeline execution failed after {_MAX_RETRIES + 1} attempts: {last_error}"
    )


def load_spec(path: str) -> NveilSpec:
    """Load a spec from an opaque .nveil file.

    No API call — loaded specs can be rendered locally for free.

    Args:
        path: Path to a ``.nveil`` file.

    Returns:
        NveilSpec ready to render.
    """
    return NveilSpec.load(path)
