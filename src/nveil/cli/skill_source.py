# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Canonical skill source — single place that reads the shipped SKILL.md
and exposes its parts to the per-target install generators.

We treat the file at ``<pkg>/skills/nveil/SKILL.md`` as the source of truth.
Every other AI-agent format (Codex ``AGENTS.md``, Cursor rules, GitHub
Copilot instructions, Aider conventions, OpenClaw skills) is derived from
it at install time — the content body is identical, only the wrapping
frontmatter and the destination path differ.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillSource:
    """Parsed view of the canonical SKILL.md."""

    name: str
    description: str
    frontmatter: str   # the verbatim ``---…---`` block, including fences
    body: str          # everything after the frontmatter, stripped of leading blanks


def _shipped_skill_path() -> Path:
    """Resolve the SKILL.md that ships with the installed package."""
    from .. import __file__ as _nveil_init
    return Path(_nveil_init).parent / "skills" / "nveil" / "SKILL.md"


def _parse(text: str) -> tuple[str, dict[str, str], str]:
    """Split a ``---`` YAML-frontmatter markdown file into (fm_text, fm_fields, body)."""
    if not text.startswith("---"):
        raise ValueError(
            "shipped SKILL.md is missing the leading '---' frontmatter fence"
        )
    _, fm_text, body = text.split("---", 2)
    fields: dict[str, str] = {}
    for line in fm_text.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fm_text, fields, body.lstrip("\n")


def load() -> SkillSource:
    """Load and parse the shipped SKILL.md."""
    path = _shipped_skill_path()
    if not path.exists():
        raise FileNotFoundError(
            f"shipped SKILL.md not found at {path}. Reinstall the nveil package."
        )
    text = path.read_text(encoding="utf-8")
    fm_text, fields, body = _parse(text)
    return SkillSource(
        name=fields.get("name", "nveil"),
        description=fields.get("description", ""),
        frontmatter=f"---\n{fm_text.strip()}\n---\n",
        body=body,
    )
