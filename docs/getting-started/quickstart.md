# Quickstart

Generate a visualization from real data in minutes.

## Setup

```python
import nveil
import pandas as pd

nveil.configure(api_key="nveil_...")
```

## From a CSV file

```python
# Load your data
df = pd.read_csv("quarterly_sales.csv")
print(df.head())
#   region  quarter  revenue  units_sold  margin
# 0  North  Q1       42150    312         0.23
# 1  South  Q1       38900    287         0.19
# 2  East   Q1       51200    401         0.27
# ...

# Describe what you want in plain language
spec = nveil.generate_spec("Revenue by region as a bar chart, colored by quarter", df)

# Render locally (no API call, no cost)
fig = spec.render(df)
nveil.show(fig)
```

That's it. The Toolkit extracts metadata from your DataFrame (column names, types, statistics), sends it to the NVEIL server, and returns a specification that renders locally. Your actual data never leaves your machine.

## Working with the result

```python
# Get a description of what was generated
print(spec.explanation)
# "Bar chart showing revenue distribution across regions, grouped by quarter"

# Export to different formats
nveil.save_image(fig, "revenue_chart.png")
nveil.save_image(fig, "revenue_chart.svg")
nveil.save_html(fig, "revenue_chart.html")  # interactive
```

## Save and reuse later

Specs are portable. Save once, render on new data anytime — no API call needed.

```python
# Save the spec
spec.save("revenue_by_region.nveil")

# Later, or on another machine:
spec = nveil.load_spec("revenue_by_region.nveil")

# Render on fresh data (same column names)
new_df = pd.read_csv("quarterly_sales_2025.csv")
fig = spec.render(new_df)
nveil.show(fig)
```

## Sessions for multiple visualizations

If you're building several charts from the same data, use a session. The data pipeline runs once and is reused across all renders.

```python
df = pd.read_csv("quarterly_sales.csv")

with nveil.session() as s:
    # Each generate_spec call talks to the server
    bar = s.generate_spec("Revenue by region, colored by quarter", df)
    scatter = s.generate_spec("Scatter plot of revenue vs margin", df)
    line = s.generate_spec("Revenue trend over quarters by region", df)

    # Renders reuse the pipeline — fast, no re-processing
    fig_bar = bar.render(df)
    fig_scatter = scatter.render(df)
    fig_line = line.render(df)

    nveil.save_image(fig_bar, "bar.png")
    nveil.save_image(fig_scatter, "scatter.png")
    nveil.save_html(fig_line, "trend.html")
```

## Multiple datasets

Pass a dict of DataFrames to work with multiple data sources.

```python
sales = pd.read_csv("actual_sales.csv")
targets = pd.read_csv("sales_targets.csv")

spec = nveil.generate_spec(
    "Compare actual revenue vs targets by region",
    {"sales": sales, "targets": targets},
)

fig = spec.render({"sales": sales, "targets": targets})
nveil.show(fig)
```

## Error handling

```python
from nveil import AuthenticationError, QuotaExceededError, SpecGenerationError

try:
    spec = nveil.generate_spec("bar chart", df)
except AuthenticationError:
    print("Check your API key in Settings at app.nveil.com")
except QuotaExceededError:
    print("Rate limit reached — wait a moment and retry")
except SpecGenerationError as e:
    print(f"Generation failed: {e}")
```

## Next steps

- [Privacy Model](../concepts/privacy-model.md) — understand what data leaves your machine
- [Sessions](../concepts/sessions.md) — optimize performance with workspace reuse
- [Specs & .nveil Files](../concepts/specs.md) — save, load, and render offline
- [API Reference](../api-reference/index.md) — full reference for all functions
