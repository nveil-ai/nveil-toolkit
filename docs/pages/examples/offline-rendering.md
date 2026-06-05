# Offline Rendering

Generate a spec once, save it, and render on new data later — with no API call.

## Save a spec

```python
import nveil
import pandas as pd

nveil.configure(api_key="nveil_...")

df = pd.read_csv("sales_2024.csv")
spec = nveil.generate_spec("Monthly revenue trend", df)
spec.save("revenue_trend.nveil")
```

## Load and render later

```python
import nveil
import pandas as pd

# No nveil.configure() needed — no API call
spec = nveil.load_spec("revenue_trend.nveil")

df_2025 = pd.read_csv("sales_2025.csv")
fig = spec.render(df_2025)
nveil.show(fig)
```

## Use cases

- **Dashboards** — generate specs once during setup, render on fresh data at display time.
- **Batch exports** — load a spec and render across many datasets in a loop.
- **Sharing** — send `.nveil` files to colleagues who can render without an API key.
- **CI/CD** — generate specs in a pipeline, render in a test or report step.

## Notes

- `.nveil` files store the spec only — never your raw data.
- The spec must be compatible with the data — same column names and types.
- Rendering is 100% local: no network, no API key, no cost.
