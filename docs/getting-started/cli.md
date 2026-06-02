# Command Line & AI Agents

`pip install nveil` puts a `nveil` binary on your `$PATH`. The same binary powers three things:

- **A shell CLI** — `nveil describe / generate / render / explain` for terminals, scripts, and CI.
- **A Claude / Cursor / Codex skill** — installable with `nveil install-skill`.
- **An MCP server** — `nveil mcp`, registrable in any MCP client with `nveil install-mcp`.

All three share one implementation and one API key. Data stays local in every mode — `render` never hits the server, `generate` sends only metadata.

---

## Setup

```bash
pip install nveil
export NVEIL_API_KEY=nveil_...
```

Recognized environment variables:

| Variable | Purpose |
|---|---|
| `NVEIL_API_KEY` | API key for `generate` (not needed for `render` / `describe` / `explain`). |
| `NVEIL_BASE_URL` | Override the server endpoint (self-hosted deployments). |
| `NVEIL_VERIFY` | TLS verification toggle for custom CA bundles. |

Each command also accepts `--api-key` to override per-invocation.

---

## Shell commands

### `nveil describe`

Inspect a dataset before writing a prompt. Prints JSON with shape, dtypes, and a head preview. No network, no API key.

```bash
nveil describe sales.csv
nveil describe sales.parquet --rows 20
```

Supported inputs: CSV, Parquet, JSON, Excel.

### `nveil generate`

Generate a spec from a prompt + a data file, then render it.

```bash
nveil generate "Revenue by region, colored by quarter" \
  --data sales.csv \
  --output report.[all] \
  --explain
```

The output format is encoded in the `--output` path using bracket notation:

| Syntax | Result |
|---|---|
| `report.[png]` | `report.png` |
| `report.[html,pdf]` | `report.html` + `report.pdf` |
| `report.[all]` | all formats: `html`, `png`, `nveil`, `jpg`, `svg`, `pdf`, `json` |
| `report.png` | `report.png` (plain extension, single format) |
| omitted | `./nveil_out/<slug>.html` |

Supported formats: `html`, `png`, `nveil`, `jpg`, `svg`, `pdf`, `json`.

| Flag | Default | Description |
|---|---|---|
| `--data` | required | CSV / Parquet / JSON / Excel path. |
| `-o, --output` | `./nveil_out/<slug>.html` | File path with optional bracket format(s). |
| `--explain` | off | Print the spec's human-readable explanation. |
| `--api-key` | `$NVEIL_API_KEY` | Per-invocation override. |

Output paths are printed to stdout, one per line — safe to pipe into other tools.

**Shorthand.** If the first argument isn't a known subcommand, `generate` is implicit:

```bash
nveil "bar chart of revenue by region" --data sales.csv
```

### `nveil render`

Re-render a saved `.nveil` spec against fresh data. Fully local, no API call.

```bash
nveil render revenue.nveil --data sales_2026.csv --output revenue.[all]
```

Same `--output` bracket syntax as `generate`. `.[all]` expands to `html`, `png`, `jpg`, `svg`, `pdf`, `json` — `nveil` is excluded since the spec file is already the source.

### `nveil explain`

Print the human-readable explanation baked into a `.nveil` file. Local.

```bash
nveil explain revenue.nveil
```

### `nveil docs`

Open (or print, for agents) the online API reference.

```bash
nveil docs              # opens https://docs.nveil.com/api-reference/ in a browser
nveil docs --print      # prints the URL to stdout
```

---

## AI agent integrations

NVEIL ships first-class integrations for Claude Code, Claude Desktop, Cursor, Codex, GitHub Copilot, Aider, and OpenClaw. One canonical source (`SKILL.md`), written into each agent's native format.

### `nveil install-skill`

Writes the NVEIL skill into the chosen agent's instruction format.

```bash
# Claude Code / Desktop — registers the bundled plugin (covers both)
nveil install-skill                                # default: --client claude-plugin

# Loose ~/.claude/skills/nveil/SKILL.md drop-in (no claude CLI required)
nveil install-skill --client claude-code

# Other agents
nveil install-skill --client cursor
nveil install-skill --client codex
nveil install-skill --client copilot     # project-scoped
nveil install-skill --client aider       # project-scoped
nveil install-skill --client openclaw

# Install everywhere applicable to the chosen scope
nveil install-skill --client all
```

| Flag | Default | Description |
|---|---|---|
| `--client` | `claude-plugin` | `claude-plugin`, `claude-code`, `cursor`, `codex`, `copilot`, `aider`, `openclaw`, `all`. |
| `--scope` | `user` | `user` → home-dir install. `project` → current directory. |
| `--path` | — | Override the output directory (wins over `--scope`). |
| `--force` | off | Overwrite an existing file without prompting. |

`copilot` and `aider` are always project-scoped — `--scope user` is ignored with a warning.

Re-run any time the shipped `SKILL.md` updates; the install is idempotent.

### `nveil install-mcp`

Registers the NVEIL MCP stdio server in an MCP client by editing that client's config in place.

```bash
# Claude Desktop (macOS / Windows / Linux paths handled automatically)
nveil install-mcp                                  # default: --client claude-desktop

# Cursor
nveil install-mcp --client cursor

# Every known client
nveil install-mcp --client all
```

!!! note "Claude Code is not a target"
    The bundled Claude plugin (`nveil install-skill --client claude-plugin`) already ships the MCP server via its `.mcp.json`. Claude Code picks it up automatically as `plugin:nveil:nveil` — registering separately would create a duplicate.

The installer writes an `mcpServers.nveil` entry that launches `nveil mcp` as a subprocess and propagates `NVEIL_API_KEY`, `NVEIL_BASE_URL`, and `NVEIL_VERIFY` from your current environment.

!!! tip "Rotating your API key"
    MCP hosts capture env vars at subprocess spawn time. After rotating a key, run `nveil install-mcp --force` and restart the host.

### `nveil mcp`

Runs the MCP stdio server. Not meant to be invoked by hand beyond smoke tests — MCP clients launch it as a subprocess.

Exposed tools:

| Tool | Description |
|---|---|
| `nveil_describe` | Inspect a data file: shape, dtypes, head. Ground the agent before prompting. |
| `nveil_generate` | Create a chart from a prompt + data path. Returns output paths + explanation. |
| `nveil_render` | Re-render a `.nveil` spec against fresh data. No API call. |
| `nveil_explain` | Read a spec's explanation text. |

### Manual MCP config

If you'd rather edit the client config yourself, the server entry is just:

```json
{
  "mcpServers": {
    "nveil": {
      "command": "nveil",
      "args": ["mcp"],
      "env": { "NVEIL_API_KEY": "nveil_..." }
    }
  }
}
```

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Bad input (missing file, invalid config, existing output without `--force`) |
| `2` | Missing optional dependency (e.g. `mcp` package not installed) |
| `3` | Unhandled exception (traceback printed to stderr) |
| `130` | Interrupted (Ctrl-C) |

---

## Next steps

- [Quickstart](quickstart.md) — the Python API covering the same operations.
- [Authentication](authentication.md) — API-key management and scopes.
- [Specs & .nveil files](../concepts/specs.md) — what `generate` / `render` / `explain` operate on.
