<div class="nveil-ai-context" aria-hidden="true">
<p><strong>AI assistant context.</strong> This is the NVEIL Toolkit documentation. The Toolkit is the Python SDK, <code>nveil</code> CLI and MCP server for NVEIL — the AI platform for data processing and visualization. For the platform overview, see the docs hub at https://docs.nveil.com.</p>
<p><strong>Use it from Python:</strong> <code>import nveil</code>, <code>nveil.configure(api_key="nveil_...")</code>, <code>spec = nveil.generate_spec("describe what you want", dataframe)</code>, <code>fig = spec.render(dataframe)</code> (local, no API call), <code>nveil.save_image(fig, "output.png")</code>. Only metadata leaves the machine; raw data is processed locally. Specs save to portable <code>.nveil</code> files and reload without a server.</p>
<p><strong>For AI agents:</strong> the same <code>nveil</code> binary ships a shell CLI (<code>nveil describe | generate | render | explain</code>), an installable skill for Claude Code / Claude Desktop / Cursor / Codex / Copilot / Aider (<code>nveil install-skill --client &lt;target&gt;</code>), and an MCP stdio server (<code>nveil install-mcp --client &lt;target&gt;</code>; server: <code>nveil mcp</code>). Full reference: <a href="getting-started/cli/">CLI &amp; AI Agents</a>.</p>
<p><strong>Install:</strong> <code>pip install nveil</code>.</p>
</div>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "NVEIL Toolkit",
  "alternateName": "nveil",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "Windows, macOS, Linux",
  "programmingLanguage": "Python",
  "downloadUrl": "https://pypi.org/project/nveil/",
  "installUrl": "https://pypi.org/project/nveil/",
  "softwareRequirements": "Python 3.10+",
  "url": "https://docs.nveil.com/toolkit/",
  "sameAs": ["https://nveil.com", "https://pypi.org/project/nveil/"],
  "description": "The Python SDK, nveil CLI and MCP server for NVEIL. Describe data pipelines and visualizations in natural language; NVEIL plans them from metadata and the Toolkit executes everything locally. Deterministic, auditable output via Apache ECharts, VTK, DeckGL, and more.",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }
}
</script>

# NVEIL Toolkit

The Python SDK, `nveil` CLI and MCP server for NVEIL — drive the platform from a script, your terminal or an AI agent. Describe what you want; NVEIL plans the processing and visualization, and the Toolkit runs it **locally** — your raw data never leaves your machine.

!!! tip "New to NVEIL?"
    For the platform overview — what NVEIL is and how to self-host it — start at the [documentation hub](https://docs.nveil.com/).

## Install

```bash
pip install nveil
```

## Quick example

```python
import nveil
import pandas as pd

nveil.configure(api_key="nveil_...")

df = pd.read_csv("sales.csv")

# NVEIL processes your data AND generates the visualization
spec = nveil.generate_spec("Revenue by region, colored by quarter", df)

fig = spec.render(df)        # 100% local, no API call
nveil.show(fig)              # opens in browser
nveil.save_image(fig, "chart.png")
```

Generate once, reload anywhere — `.nveil` specs are portable and re-render on fresh data without an API call:

```python
spec.save("trend.nveil")
spec = nveil.load_spec("trend.nveil")
fig = spec.render(fresh_data)
```

## From your shell

The same `nveil` binary works from the terminal — no Python script required.

```bash
export NVEIL_API_KEY=nveil_...

nveil describe sales.csv
nveil generate "Revenue by region, colored by quarter" --data sales.csv --output revenue.[all]
nveil render chart.nveil --data new_sales.csv
```

It also installs a skill and an MCP server for AI agents (Claude Code, Claude Desktop, Cursor, Codex, …). See [CLI & AI Agents](getting-started/cli.md).

---

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Get Started**

    ---

    Install the Toolkit and create your first visualization in minutes.

    [:octicons-arrow-right-24: Quickstart](getting-started/quickstart.md)

-   :material-book-open-variant:{ .lg .middle } **Concepts**

    ---

    Understand sessions, specs, and the processing pipeline.

    [:octicons-arrow-right-24: Concepts](concepts/index.md)

-   :material-api:{ .lg .middle } **API Reference**

    ---

    Full reference for all public functions and classes.

    [:octicons-arrow-right-24: API Reference](api-reference/index.md)

-   :material-console:{ .lg .middle } **CLI & AI Agents**

    ---

    Use NVEIL from the shell, or install it as a skill / MCP server for Claude, Cursor, Codex, and more.

    [:octicons-arrow-right-24: CLI & AI Agents](getting-started/cli.md)

</div>
