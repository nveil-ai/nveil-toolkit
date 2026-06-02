# SPDX-FileCopyrightText: 2026 NVEIL SAS
# SPDX-FileContributor: Pierre Jacquet
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Smoke tests for the ``nveil`` CLI.

Covers argument parsing, offline subcommands (``describe``, ``docs``,
``explain``, ``install-skill``), and the MCP stdio cleanliness invariant
(stdout must carry only valid JSON-RPC frames, never stray prints).

Network-dependent subcommands (``generate``, ``render`` against a real
server) are covered by the end-to-end verification script, not unit tests.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
IBMHR_CSV = REPO_ROOT / "examples" / "Miscellaneous" / "IBMHR" / "IBMHR.csv"


def _nveil(*args, env_extra=None):
    """Invoke the CLI as a subprocess and return (returncode, stdout, stderr)."""
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, "-m", "nveil.cli", *args],
        capture_output=True, text=True, env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_version():
    rc, out, _ = _nveil("--version")
    assert rc == 0
    assert out.startswith("nveil ")


def test_help_lists_all_subcommands():
    rc, out, _ = _nveil("--help")
    assert rc == 0
    for name in ("generate", "render", "describe", "explain",
                 "install-skill", "docs", "mcp"):
        assert name in out


def test_describe_outputs_valid_json():
    if not IBMHR_CSV.exists():
        pytest.skip(f"fixture missing: {IBMHR_CSV}")
    rc, out, _ = _nveil("describe", str(IBMHR_CSV), "--rows", "2")
    assert rc == 0
    payload = json.loads(out)
    assert payload["format"] == "CSV"
    assert payload["shape"]["rows"] > 0
    assert payload["shape"]["cols"] > 0
    assert len(payload["head"]) <= 2


def test_describe_unknown_extension_errors_cleanly(tmp_path):
    bogus = tmp_path / "not_a_data_file.xyz"
    bogus.write_text("noise")
    rc, _out, err = _nveil("describe", str(bogus))
    assert rc == 1
    assert "unsupported" in err.lower()


def test_docs_print_emits_url():
    rc, out, _ = _nveil("docs", "--print")
    assert rc == 0
    assert out.strip() == "https://docs.nveil.com/api-reference/"


def test_install_skill_claude_code(tmp_path):
    rc, _out, _err = _nveil(
        "install-skill", "--client", "claude-code", "--path", str(tmp_path),
    )
    assert rc == 0
    dst = tmp_path / "skills" / "nveil" / "SKILL.md"
    assert dst.exists()
    content = dst.read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "name: nveil" in content


def test_install_skill_refuses_overwrite(tmp_path):
    dst_dir = tmp_path / "skills" / "nveil"
    dst_dir.mkdir(parents=True)
    (dst_dir / "SKILL.md").write_text("existing")
    rc, _out, err = _nveil(
        "install-skill", "--client", "claude-code", "--path", str(tmp_path),
    )
    assert rc == 1
    assert "--force" in err


def test_install_skill_force(tmp_path):
    dst_dir = tmp_path / "skills" / "nveil"
    dst_dir.mkdir(parents=True)
    (dst_dir / "SKILL.md").write_text("existing")
    rc, _out, _err = _nveil(
        "install-skill", "--client", "claude-code",
        "--path", str(tmp_path), "--force",
    )
    assert rc == 0
    content = (dst_dir / "SKILL.md").read_text(encoding="utf-8")
    assert content.startswith("---")


@pytest.mark.parametrize("client,expected_rel_path", [
    ("codex", "AGENTS.md"),
    ("cursor", ".cursor/rules/nveil.mdc"),
    ("copilot", ".github/copilot-instructions.md"),
    ("aider", "CONVENTIONS.md"),
    ("openclaw", "skills/nveil/SKILL.md"),
])
def test_install_skill_per_target(tmp_path, client, expected_rel_path):
    """Each non-plugin target writes to its canonical relative path."""
    rc, _out, _err = _nveil(
        "install-skill", "--client", client, "--scope", "project",
        "--path", str(tmp_path),
    )
    assert rc == 0
    dst = tmp_path / expected_rel_path
    assert dst.exists(), f"missing {expected_rel_path} for client {client}"
    body = dst.read_text(encoding="utf-8")
    # The body should always carry our canonical H1 heading.
    assert "NVEIL — you are not writing data-science code" in body


def test_install_skill_cursor_has_mdc_frontmatter(tmp_path):
    rc, _out, _err = _nveil(
        "install-skill", "--client", "cursor",
        "--scope", "project", "--path", str(tmp_path),
    )
    assert rc == 0
    content = (tmp_path / ".cursor" / "rules" / "nveil.mdc").read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert "description:" in content
    assert "alwaysApply: false" in content


def test_install_skill_codex_strips_claude_frontmatter(tmp_path):
    rc, _out, _err = _nveil(
        "install-skill", "--client", "codex",
        "--scope", "project", "--path", str(tmp_path),
    )
    assert rc == 0
    content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    # No YAML frontmatter at the top — Codex expects plain markdown.
    assert not content.startswith("---")
    # But the body should start with our canonical H1.
    assert content.lstrip().startswith("# NVEIL")


def test_implicit_generate_dispatch_preserves_argv():
    """A bare prompt should route to `generate` but still error cleanly
    without NVEIL_API_KEY — proving the argv rewrite fired."""
    env = {k: v for k, v in os.environ.items() if k != "NVEIL_API_KEY"}
    proc = subprocess.run(
        [sys.executable, "-m", "nveil.cli", "bar chart of revenue",
         "--data", str(IBMHR_CSV) if IBMHR_CSV.exists() else "nonexistent.csv"],
        capture_output=True, text=True, env=env,
    )
    # We expect a ConfigError about NVEIL_API_KEY, not a usage error.
    assert proc.returncode == 1
    assert "NVEIL_API_KEY" in proc.stderr


def test_mcp_stdio_cleanliness():
    """Critical: `nveil mcp`'s stdout must carry only JSON-RPC frames.

    Any stray print/log on stdout corrupts MCP. We spawn the server, send
    an ``initialize`` + ``tools/list`` pair, close stdin to signal EOF so
    the server exits, collect everything on stdout, and assert every
    non-empty line parses as valid JSON-RPC.
    """
    requests = "\n".join([
        json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "0"},
            },
        }),
        json.dumps({
            "jsonrpc": "2.0", "method": "notifications/initialized", "params": {},
        }),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
        "",  # trailing newline so last line terminates
    ])

    # communicate() with input closes stdin after write → server sees EOF
    # and exits cleanly. Single blocking call with an overall timeout means
    # no dangling subprocess on failure.
    proc = subprocess.Popen(
        [sys.executable, "-m", "nveil.cli", "mcp"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = proc.communicate(input=requests, timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        pytest.fail(f"nveil mcp did not exit after stdin EOF.\nstderr:\n{stderr[-500:]}")

    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    assert lines, f"no stdout frames received; stderr tail:\n{stderr[-500:]}"
    for line in lines:
        parsed = json.loads(line)
        assert "jsonrpc" in parsed, f"non-JSON-RPC frame on stdout: {line!r}"
