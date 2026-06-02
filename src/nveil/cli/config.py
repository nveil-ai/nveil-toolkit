# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""CLI-side configuration helpers."""

from __future__ import annotations

import os
import sys

from .. import configure as _sdk_configure


class ConfigError(Exception):
    """Raised when required CLI configuration is missing or invalid."""


def resolve_api_key(explicit: str | None) -> str:
    """Return the API key to use, honoring --api-key > NVEIL_API_KEY.

    Raises ConfigError with a precise remediation message when neither is set.
    """
    if explicit:
        return explicit
    env = os.environ.get("NVEIL_API_KEY")
    if env:
        return env
    raise ConfigError(
        "No API key provided. Set NVEIL_API_KEY in your environment or pass --api-key.\n"
        "  export NVEIL_API_KEY=nveil_...        (Linux/macOS)\n"
        "  $env:NVEIL_API_KEY = 'nveil_...'      (Windows PowerShell)"
    )


def configure_from_args(args) -> None:
    """Configure the global nveil client from parsed CLI args + env vars.

    Honors the same env vars the dev-loop uses: ``NVEIL_BASE_URL`` for a
    custom server, ``NVEIL_VERIFY=0`` to disable TLS verification against
    self-signed local servers.
    """
    api_key = resolve_api_key(getattr(args, "api_key", None))
    _sdk_configure(
        api_key=api_key,
        base_url=os.environ.get("NVEIL_BASE_URL", "https://app.nveil.com"),
        verify=os.environ.get("NVEIL_VERIFY", "1") != "0",
    )


def die(msg: str, code: int = 1) -> int:
    """Print an error to stderr and return an exit code."""
    print(f"nveil: error: {msg}", file=sys.stderr)
    return code
