# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""NVEIL Toolkit exceptions."""


class NveilError(Exception):
    """Base exception for all NVEIL Toolkit errors."""


class AuthenticationError(NveilError):
    """Raised when the API key is invalid, expired, or revoked."""


class ScopeError(NveilError):
    """Raised when the API key is missing a required scope."""


class QuotaExceededError(NveilError):
    """Raised when the rate limit or quota is exceeded."""


class SpecGenerationError(NveilError):
    """Raised when the server fails to generate a specification."""


class IncompatibleDataError(NveilError):
    """Raised when data columns don't match the spec's expected schema."""
