# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest configuration for NVEIL SDK tests."""

import os
import sys
from pathlib import Path

# Transport key is now embedded in the SDK — no env var needed.

SDK_ROOT = Path(__file__).parent.parent
SDK_SRC = SDK_ROOT / "src"
sys.path.insert(0, str(SDK_SRC))

BACKEND_ROOT = SDK_ROOT.parent / "backend"
sys.path.insert(0, str(BACKEND_ROOT))
