<!-- mcp-name: io.github.nveil-ai/nveil -->

<p align="center">
  <img src="https://raw.githubusercontent.com/nveil-ai/nveil-toolkit/main/assets/logo.png" alt="NVEIL" width="180">
</p>

<h1 align="center">NVEIL Toolkit</h1>

<p align="center">
  <strong>Describe your data. Get production charts. Your data stays local.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/nveil/"><img src="https://img.shields.io/pypi/v/nveil?color=orange&label=PyPI" alt="PyPI"></a>
  <a href="https://pypi.org/project/nveil/"><img src="https://img.shields.io/pypi/pyversions/nveil?color=blue" alt="Python"></a>
  <a href="https://docs.nveil.com"><img src="https://img.shields.io/badge/docs-docs.nveil.com-blue" alt="Docs"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0--or--later-blue" alt="License"></a>
</p>

<p align="center">
  <a href="https://docs.nveil.com/getting-started/quickstart/">Quickstart</a> &bull;
  <a href="https://docs.nveil.com/api-reference/">API Reference</a> &bull;
  <a href="https://docs.nveil.com/examples/">Examples</a> &bull;
  <a href="https://docs.nveil.com/changelog/">Changelog</a>
</p>

---

NVEIL is an AI-powered data visualization toolkit. Write one line of natural language, and NVEIL processes your data and generates publication-ready visualizations — no chart code, no hallucinations, no data leaving your machine.

```python
import nveil

nveil.configure(api_key="nveil_...")

# Pass a file path directly — no DataFrame loading required.
spec = nveil.generate_spec("Revenue by region, colored by quarter", "sales.csv")

fig = spec.render("sales.csv")   # 100% local — no API call
nveil.show(fig)                   # opens in browser
```

### From your shell

After `pip install nveil` the `nveil` command is on your `$PATH`:

```bash
export NVEIL_API_KEY=nveil_...

# Ground yourself on the dataset (shape / dtypes / head preview)
nveil describe sales.csv

# Generate HTML + PNG + a reusable .nveil spec, print the explanation
nveil generate "Revenue by region, colored by quarter" \
  --data sales.csv --format all --explain

# Re-render an existing spec on fresh data — no API call
nveil render chart.nveil --data new_sales.csv
```

### For AI agents (Claude Code / Claude Desktop / Cursor / Codex / …)

NVEIL ships first-class integrations:

```bash
# Claude Code / Claude Desktop — install the bundled skill
nveil install-skill

# Claude Desktop, Cursor, any MCP client — add an MCP server:
# {"mcpServers": {"nveil": {"command": "nveil", "args": ["mcp"]}}}
nveil mcp                    # stdio server; launched by the MCP client
```

<p align="center">
  <img src="https://raw.githubusercontent.com/nveil-ai/nveil-toolkit/main/assets/dashboard.png" alt="NVEIL multi-panel dashboard with charts, heatmaps, and flow diagrams" width="800">
</p>

## Why NVEIL?

| Capability | **NVEIL** | Chatbot data analysis¹ | LLM-to-viz libraries² | Traditional plotting³ |
|---|:-:|:-:|:-:|:-:|
| Natural-language input | ✓ | ✓ | ✓ | ✗ |
| Raw data stays on your machine | ✓ | ✗ | ✗ | ✓ |
| Only schema + stats sent to server | ✓ | ✗ | ✗ | N/A |
| Deterministic, reproducible output | ✓ | ✗ | ✗ | ✓ |
| Offline re-rendering, zero API calls | ✓ | ✗ | ✗ | ✓ |
| Portable saved specs (`.nveil` files) | ✓ | ✗ | ✗ | ✗ |
| 2D + 3D + geospatial + scientific | ✓ | 2D | 2D | varies |
| Multi-backend (Plotly, VTK, DeckGL) | ✓ | ✗ | ✗ | ✗ |
| Data processing engine | ✓ | ✓ | partial | ✗ |

<sub>¹ ChatGPT Advanced Data Analysis, Claude Analysis tool, Gemini Data Agent &nbsp;·&nbsp; ² PandasAI, LIDA, Julius, Vanna &nbsp;·&nbsp; ³ Plotly, Matplotlib, Seaborn</sub>

## How It Works

```
Your Data ──> Toolkit ──metadata only──> NVEIL AI ──> Processing Plan ──> Local Execution ──> Result
               ^                                                           ^
          raw data stays here                                     raw data stays here
```

1. **You describe** what you want in plain language
2. **NVEIL AI plans** the data processing and visualization (only metadata is sent — column names, types, statistics)
3. **The Toolkit executes locally** — joins, aggregations, pivots, rendering — all on your machine
4. **You get a figure** — Plotly, VTK, or DeckGL, auto-selected for your data

## Key Features

<table>
<tr>
<td width="50%">

### 🧠 Two Engines in One
Data processing (joins, pivots, aggregations, geocoding, time series) **AND** visualization generation from a single prompt.

### 🔒 Data Privacy by Design
Raw data never leaves your machine. Only column names, types, and aggregate statistics are sent.

### 📈 Multi-Backend Rendering
Auto-detects the best engine: **Plotly** (2D charts), **VTK** (3D/medical), **DeckGL** (geospatial).

</td>
<td width="50%">

### 🧪 Auditable Results
Powered by constraint solving, not random generation. Same input = same output, every time.

### ⚡ Offline Rendering
`spec.render()` runs 100% locally with zero API calls.

### 💾 Reusable Specs
Save to `.nveil` files, reload later, render on new data — no server needed.

</td>
</tr>
</table>

## Beyond Simple Charts

<p align="center">
  <img src="https://raw.githubusercontent.com/nveil-ai/nveil-toolkit/main/assets/ai-chat.png" alt="NVEIL AI chat — conversational data exploration with geospatial heatmaps" width="800">
</p>

NVEIL handles geospatial heatmaps, 3D volumes, scientific visualizations, medical imaging (DICOM), biosignal data (EDF/EDF+), network graphs, and 50+ other visualization types — all from natural language.

## Save Once, Render Forever

```python
# Generate once (API call)
spec = nveil.generate_spec("Monthly trend by category", df)
spec.save("trend.nveil")

# Reload anywhere — no API call, no server, no cost
spec = nveil.load_spec("trend.nveil")
fig = spec.render(fresh_data)
nveil.save_image(fig, "report.png")
```

## Installation

```bash
pip install nveil
```

**Requirements:** Python 3.10+

## Getting Started

1. Create an account at [app.nveil.com](https://app.nveil.com)
2. Generate an API key in **Settings**
3. Start visualizing

```python
import os
import nveil

nveil.configure(api_key=os.environ["NVEIL_API_KEY"])

spec = nveil.generate_spec("scatter plot of price vs area", df)
fig = spec.render(df)
nveil.show(fig)
```

See the [examples/](examples/) directory for more usage patterns.

## Documentation

Full documentation is available at **[docs.nveil.com](https://docs.nveil.com)**:

- [Quickstart Guide](https://docs.nveil.com/getting-started/quickstart/)
- [Core Concepts](https://docs.nveil.com/concepts/) — sessions, specs, and the two-stage flow
- [API Reference](https://docs.nveil.com/api-reference/) — full reference for all public functions
- [Privacy Model](https://docs.nveil.com/concepts/privacy-model/) — what data is sent, what stays local
- [Examples](https://docs.nveil.com/examples/) — bar charts, multi-dataset, offline rendering

## Contributing

Contributions are welcome under the project's [Contributor License Agreement](licensing/CLA.md). Bug reports and feature requests are welcome via [GitHub Issues](https://github.com/nveil-ai/nveil-toolkit/issues).

## License

GNU AGPL v3 or later. See [LICENSE](LICENSE). Commercial dual-licensing is available — contact `pierre.jacquet@nveil.com`.

---

<p align="center">
  <a href="https://nveil.com">Website</a> &bull;
  <a href="https://docs.nveil.com">Documentation</a> &bull;
  <a href="https://app.nveil.com">Platform</a>
</p>
