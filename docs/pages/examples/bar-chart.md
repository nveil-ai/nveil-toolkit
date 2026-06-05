# Bar Chart

Generate a bar chart from a simple DataFrame.

```python
import nveil
import pandas as pd

nveil.configure(api_key="nveil_...")

df = pd.DataFrame({
    "product": ["Widget A", "Widget B", "Widget C", "Widget D"],
    "sales": [340, 520, 180, 410],
    "category": ["Electronics", "Electronics", "Home", "Home"],
})

spec = nveil.generate_spec("Bar chart of sales by product, colored by category", df)

fig = spec.render(df)
nveil.show(fig)

# Export
nveil.save_image(fig, "sales_by_product.png")
nveil.save_html(fig, "sales_by_product.html")
```

## From a CSV file

```python
df = pd.read_csv("quarterly_sales.csv")
spec = nveil.generate_spec("Revenue by quarter", df)
fig = spec.render(df)
nveil.show(fig)
```

## With a session (for multiple renders)

```python
with nveil.session() as s:
    spec = s.generate_spec("Sales by product", df)

    fig_2024 = spec.render(df_2024)
    fig_2025 = spec.render(df_2025)  # no pipeline re-run

    nveil.save_image(fig_2024, "sales_2024.png")
    nveil.save_image(fig_2025, "sales_2025.png")
```
