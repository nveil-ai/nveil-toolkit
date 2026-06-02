# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Setup for the nveil SDK (pure Python).

The SDK is a thin client that depends on nveil-dive and choregraph
for local data processing and visualization rendering.

Version is read from the root VERSION file.
"""

from pathlib import Path
from setuptools import setup, find_packages

_version_file = Path(__file__).resolve().parent / "VERSION"
_version = _version_file.read_text().strip() if _version_file.exists() else "0.0.0"

setup(
    version=_version,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "nveil": [
            "skills/nveil/SKILL.md",
            ".claude-plugin/plugin.json",
            ".mcp.json",
        ],
    },
    install_requires=[
        "httpx>=0.25",
        "pydantic>=2.0",
        "pandas>=2.0",
        "numpy>=1.24",
        "nveil-dive",
        "choregraph",
        "mcp>=1.0",
    ],
    extras_require={
        "extra": ["nveil-dive[extra]", "choregraph[extra]"],
    },
)
