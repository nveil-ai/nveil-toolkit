# Changelog

All notable changes to the NVEIL Toolkit will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.4.1] — 2026-06-05

### Fixed

- **Server-side-only LLM configuration is now actually shipped.** The 1.4.0
  release still carried the old client that accepted `llm_provider`,
  `llm_api_key` and `llm_base_url`; those are now removed from `NveilClient` /
  `nveil.configure()`. Point `base_url` at your NVEIL server and every request
  runs on the provider that server was set up with.
- The `VERSION` file is now included in the sdist (`MANIFEST.in`), so source
  builds report the correct version.

### Changed

- PyPI summary aligned with the README.

## [1.4.0] — 2026-06-02

*The NVEIL Toolkit is now open source under the GNU Affero General Public
License, version 3 or later, with a commercial dual-licensing option for
organizations that cannot use the AGPL.*

### Changed

- **LLM configuration is server-side only.** The provider, credentials
  and endpoint are fixed when the operator runs the setup (their
  `.env`); the SDK never sends them. `NveilClient` / `nveil.configure()`
  no longer accept `llm_provider`, `llm_api_key`, or `llm_base_url` —
  point `base_url` at your NVEIL server and every request runs on the
  provider that server was set up with.

- **Relicensed to AGPL-3.0-or-later.** Previously proprietary, the Toolkit is
  now open source; a separate commercial license remains available for
  embedding or closed-source hosting. Outside contributions are welcome
  under the project's Contributor License Agreement.
- **`.nveil` files are no longer encrypted.** They are now plain, portable
  spec blobs — rendering stays fully local either way, and raw data was
  never stored in them. **Compatibility:** `.nveil` files saved with
  earlier (encrypted) versions may not load in 1.4.0; regenerate them with
  `generate_spec()` if needed.

## [1.3.0] — 2026-04-23

### Added

- **EDF/EDF+ biosignal support.** NVEIL now accepts EDF and EDF+
  files (EEG, ECG, polysomnography, and other multi-channel
  recordings) as data sources. Channel metadata — names, units,
  sampling rates, physical ranges — is extracted automatically.
  Raw signal data stays local, as with every other format.
- **Smarter heatmaps for category-vs-category data.** When both
  axes are categorical, heatmaps now group similar rows and
  columns together so patterns stand out at a glance. A toggle
  lets you switch the reordering off to see the original order.
  The smoothing controls are hidden in this mode since they don't
  apply to categorical cells.
- **Chord diagrams for circular flow data.** Flow charts now
  render as a chord diagram when a polar layout is requested —
  every category sits on a ring and arcs between them show who
  flows to whom. Links inherit the color of the source category
  so the direction of each flow is visible without a legend.
  Ideal for migrations, trade between regions, or any dataset
  where the same categories appear on both ends of the flow.
- **New `NveilClient.sdk_process()` method** — a single call that
  handles both the initial request and the resume step of a
  generation. Pass `prompt` + `catalogue_stats` for the first
  call, then pass back the returned `session_id` with the
  post-pipeline blob for the second. `generate_spec()` and
  `Session.generate_spec()` work exactly as before — this only
  matters if you drive the client yourself.

### Changed

- **CLI output format selection via bracket syntax** *(breaking)*. The `-f` /
  `--format` flag has been removed from `nveil generate` and `nveil render`.
  Formats are now specified directly in the `--output` path using bracket
  notation: `output.[png]`, `output.[html,pdf]`, `output.[all]`. `.[all]` expands to
  every supported format (`html`, `png`, `nveil`, `jpg`, `svg`, `pdf`, `json`
  for `generate`; same minus `nveil` for `render`). Plain extensions still
  work (`--output output.png`). Invalid extensions and bracket formats now
  produce a clean error message instead of a traceback.

- **Hierarchical rollup output columns renamed** *(breaking,
  `choregraph`)*. `hierarchical_rollup` now returns `target` and
  `source` columns in place of `id` and `parent`. The triple
  `(source, target, value)` can now be fed straight into a
  sankey or chord flow chart. Pipelines that bind these columns
  to chart channels need to update the column names.
- **`processing_plan()` and `visualization_generate()` are now
  thin shortcuts around `sdk_process()`.** Existing call sites
  keep working unchanged; both return-shapes now also include a
  `status` field (`"awaiting_choregraph"` on the first call,
  `"complete"` on the second) if you inspect responses directly.
- **Direct HTTP callers: single endpoint.** The SDK now talks to
  `/api/v1/sdk/process` instead of the two previous paths
  (`/api/v1/processing/plan`, `/api/v1/visualization/generate`).
  Only relevant if you bypass the Python client and hit the HTTP
  API yourself; in that case pass a `session_id` to distinguish
  the resume call from the initial one.

## [1.2.0] — 2026-04-16

*Realigns all three packages (`nveil`, `nveil-dive`, `choregraph`) on a shared
version — the "future substantive release" flagged in 1.1.1 / 1.1.2.*

### Added

- **Category ordering on bar charts.** Bars are now sorted by value by
  default (largest first), with a dashboard toggle to switch between
  decreasing, increasing, or the data's natural order. Works on any
  categorical axis.
- **Theme-matched color palettes.** Default qualitative palettes now
  follow the active chart theme — dark, paper, and light themes each
  pick a harmonised set of category colors so charts feel consistent
  without having to choose a palette manually.
- **Legend titles.** Discrete color legends now show the name of the
  field being encoded (e.g. *Region*, *Category*) above the swatches,
  matching how continuous color bars are already labelled.
- **Listed in the MCP Registry.** The bundled `nveil mcp` server is
  now discoverable from the official MCP Registry, so compatible
  clients can find and install it automatically.

### Changed

- **Bar chart polish.** Hovering a bar highlights the full column
  instead of a thin line, zoom is horizontal-only (no more accidental
  y-axis zoom), and single-color bars render with a subtle lightening
  gradient for a bit more depth.
- **Smarter default colors.** When no palette is specified, NVEIL now
  picks a qualitative palette for discrete fields and a sequential
  ramp for continuous ones, based on what the data actually represents
  rather than the chart type.
- **Sankey (flow) charts reworked.** Nodes are now coloured by a
  per-column gradient so depth structure reads at a glance. Hovering
  a node highlights the full upstream-to-downstream path instead of
  only its direct neighbours. Padding matches the rest of the theme
  for consistency.
- **`save_image(..., scale=...)` semantics changed (potential breaking
  change for callers).** `scale` is now a *font / zoom multiplier* —
  it controls how large text and chart elements appear *relative to
  the chart area*, not the output resolution. Output dimensions are
  always exactly `width × height` pixels, regardless of `scale`.
  Previously, `scale=2` produced an image at `2 × width` × `2 × height`
  pixels (retina-style). Callers who relied on the old upscaling
  behaviour should multiply `width` / `height` by their previous
  `scale` and leave `scale=1`. Works uniformly across 2D and 3D
  charts.
- **Tighter treemap / partition layout.** Padding and bottom margin
  now follow the active theme for more consistent breathing room,
  with breadcrumbs aligned to the shared baseline.

### Fixed

- **Volume rendering stability.** Toggling the multi-planar
  reconstruction (MPR) view on a freshly loaded volume no longer
  fails on the first render — the viewer now waits for the volume
  pipeline to settle before attaching the reslice.

## [1.1.2] — 2026-04-14

### Fixed

- **`nveil mcp` no longer hangs when rendering PNG / JPG / SVG / PDF.**
  The MCP stdio server now isolates its JSON-RPC pipes at the OS file
  descriptor level: fd 0 is redirected to the null device and fd 1 to
  stderr before any tool handler runs. Subprocesses spawned downstream
  (Playwright install, headless Chromium, native libs) inherit safe
  fds and can no longer read from or write into the JSON-RPC stream.
  Previously, Chromium inheriting the MCP pipes caused tool calls to
  hang indefinitely on the client side.
- Playwright's one-time Chromium install subprocess now explicitly
  redirects its own stdout/stderr to the parent's stderr.

*Note: only the `nveil` SDK wheel moves to 1.1.2; `nveil-dive` and `choregraph`
stay at 1.1.0 (their contents are unchanged and their pinned range accepts the
older versions).*

## [1.1.1] — 2026-04-14

### Fixed

- README images (logo, dashboard, AI chat) now display correctly on PyPI.
  Relative paths were replaced with absolute GitHub URLs so PyPI's renderer
  can resolve them.

### Changed

- Development Status classifier bumped from **Beta** to **Production/Stable**.

*Note: only the `nveil` SDK wheel moves to 1.1.1; `nveil-dive` and `choregraph`
stay at 1.1.0 (their contents are unchanged and their pinned range accepts the
older versions). A future substantive release will realign all three
packages on a shared version.*

## [1.1.0] — 2026-04-13

### Added

#### CLI and AI-agent integrations

- **`nveil` command on `$PATH` after install.** New CLI surface: `generate`,
  `render`, `describe`, `explain`, `docs`, `install-skill`, `install-mcp`,
  `mcp`. Bare prompts (`nveil "bar chart of revenue" --data x.csv`)
  dispatch implicitly to `generate`.
- **`nveil generate` writes HTML / PNG / `.nveil` artifacts directly** from
  a prompt + a data file. No Python scaffolding needed. Output paths are
  printed one-per-line on stdout so agents can capture them.
- **`nveil mcp` runs an MCP stdio server** exposing `nveil_generate`,
  `nveil_render`, `nveil_describe`, and `nveil_explain` as MCP tools for
  Claude Desktop, Claude Code, Cursor, and other MCP clients. Launched as
  a subprocess by the MCP client; no hosting. Strict stdio-stdout
  cleanliness (JSON-RPC frames only; all Python logging/prints redirected
  to stderr).
- **`nveil install-mcp`** auto-registers the MCP server with Claude
  Desktop (edits `claude_desktop_config.json`) or Cursor (edits
  `~/.cursor/mcp.json`). Propagates `NVEIL_API_KEY`, `NVEIL_BASE_URL`, and
  `NVEIL_VERIFY` from the current env into the registered server block.
  Claude Code is deliberately not a target — the bundled plugin covers it.
- **Claude plugin shipped in-package.** NVEIL now ships as a Claude
  plugin: `src/nveil/.claude-plugin/plugin.json`, `src/nveil/.mcp.json`,
  and `src/nveil/skills/nveil/SKILL.md` are included in the wheel. A
  `.claude-plugin/marketplace.json` at the repo root lets users install
  with `/plugin marketplace add nveil-ai/nveil-toolkit` + `/plugin install
  nveil@nveil`. One install registers both the skill AND the bundled MCP
  server.
- **`nveil install-skill`** is now a multi-target generator from a single
  canonical `SKILL.md`. Supported targets: `claude-plugin` (default),
  `claude-code` (loose `~/.claude/skills/` drop-in fallback), `codex`
  (`AGENTS.md`), `cursor` (`.cursor/rules/nveil.mdc`), `copilot`
  (`.github/copilot-instructions.md`), `aider` (`CONVENTIONS.md`),
  `openclaw`, and `all`. Edit the canonical `SKILL.md` once, re-run
  `install-skill` per client.
- **`generate_spec` and `Session.generate_spec` now accept file paths**
  directly (`str` / `pathlib.Path` / dict of paths) in addition to
  DataFrames / ndarrays / lists. The engine registers path-backed inputs
  with choregraph (`Choregraph.add_input(location=..., format=...)`), so
  the caller's process never holds the DataFrame — the pipeline reads the
  file from disk on demand.
- **`NveilSpec.render` also accepts file paths**, symmetric with
  `generate_spec`. Offline `nveil render <spec.nveil> --data fresh.csv`
  now works without any DataFrame materialization in the caller.

#### Rendering

- `nveil[extra]` install option pulls in VTK for 3D scientific viz
  (voxels, 3D volumes, streamlines). The base `nveil` install stays
  lean — scipy / pydeck / natsort are core deps now but VTK is opt-in.
- Interactive data-zoom on most 2D marks — drag to pan, wheel to zoom,
  slider bar for time-series.

### Changed

- **Dashboard panels remember your tweaks.** Slider positions, toggles,
  palette choices, clipping planes, and contour / volume styling now
  survive a dashboard reload. Clicking "Export to dashboard" captures the
  live state of your visualization; opening the panel later restores it
  exactly as you left it.
- **Contour fill is now a three-way picker** — *Lines*, *Hybrid*, or
  *Filled* — instead of a slider. SDK code that set `Contour(fill=True)`
  should use `Contour(fill=ContourFillMode.FILLED)` (or one of the other
  two values); `fill=False` becomes `ContourFillMode.LINES`.
- **Migrated the 2D/3D chart backend from Plotly to Apache ECharts** (plus
  echarts-gl for 3D scatter / line / surface). Every chart you render now
  goes through a native ECharts option dict: sharper output, native
  WebGL 3D, built-in interactive zoom sliders, faster re-renders on
  slider drags.
- **Surface, 3D point, and 3D line marks now render via echarts-gl**
  instead of VTK. VTK is still the backend for voxels / 3D volumes /
  3D vector fields.
- **All tooltips render values consistently** — integers grouped by 3
  digits, floats capped at 2 decimals with trailing zeros stripped, dates
  as `YYYY-MM-DD HH:MM:SS`.
- **Datetime axes** (x/y) now display as proper date axes with interactive
  range sliders, not raw numbers. Works for ISO strings with timezone
  offsets (e.g. `2025-01-28T22:56:46.631+01:00`), French day-first formats
  (`02/01/2025`), and Unix timestamps in seconds / milliseconds.
- **Image export** now uses headless Chromium via Playwright (previously
  kaleido). More faithful rendering of interactive features.
- `mcp>=1.0` is now a core runtime dependency (used by `nveil mcp`).
- The shipped skill folder moved from `src/nveil/skill/` to
  `src/nveil/skills/nveil/` so the directory name matches the skill's
  frontmatter `name:` field (Claude skills convention).

### Fixed

- **Datetime parsing**: ISO strings with timezone offsets no longer
  silently fall back to STRING because of `"Mixed timezones detected"`
  pandas errors.
- **False-positive datetime detection**: a numeric column like `Id`
  (values ~6.5 billion) is no longer mis-detected as Unix seconds, and
  time-only strings like `"09h00"` no longer parse as year 1 AD.

### Removed

- Plotly backend and all associated dependencies (`plotly`, `kaleido`,
  `trame_plotly`).
- Figure export via kaleido — use Playwright (now the default).

## [0.1.0] — 2025-04-01

### Added
- Initial SDK release
- `configure()`, `generate_spec()`, `load_spec()`, `session()`
- `NveilSpec` with `render()`, `save()`, `load()`
- `show()`, `save_image()`, `save_html()` export functions
- AES-256-GCM encrypted `.nveil` file format
- Session-based workspace reuse
- Timing instrumentation
- Exception hierarchy: `AuthenticationError`, `ScopeError`, `QuotaExceededError`, `SpecGenerationError`, `IncompatibleDataError`
