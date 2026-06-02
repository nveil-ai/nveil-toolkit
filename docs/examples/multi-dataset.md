# Multiple Datasets

Pass a dict of DataFrames to work with multiple data sources.

```python
import nveil
import pandas as pd

nveil.configure(api_key="nveil_...")

datasets = {
    "revenue": pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "amount": [120_000, 98_000, 145_000, 87_000],
    }),
    "targets": pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "target": [100_000, 100_000, 130_000, 90_000],
    }),
}

spec = nveil.generate_spec(
    "Compare actual revenue vs targets by region",
    datasets,
)

fig = spec.render(datasets)
nveil.show(fig)
```

## How it works

When you pass a dict, each key becomes a named dataset in the processing pipeline. The Toolkit extracts metadata from each DataFrame independently and sends all dataset metadata to the server.

The prompt can reference datasets by name or by the columns they contain.
