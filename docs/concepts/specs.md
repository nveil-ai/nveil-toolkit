# Specs & .nveil Files

## What is an NveilSpec?

An `NveilSpec` is an opaque visualization specification. It contains everything needed to render a figure locally — no API call required after generation.

```python
spec = nveil.generate_spec("bar chart", df)  # API call
fig = spec.render(df)                         # 100% local
fig = spec.render(new_df)                     # still local, new data
```

## The .nveil file format

Specs can be saved to `.nveil` files — portable binary files you can move across machines.

```python
# Save
spec.save("dashboard.nveil")

# Load (no API call)
spec = nveil.load_spec("dashboard.nveil")
fig = spec.render(fresh_data)
```

`.nveil` files are portable: copy one to another machine and reload it with `load_spec()`, no server required.

## What you can access

A spec exposes a human-readable explanation of what was generated:

```python
print(spec.explanation)
# "Bar chart showing revenue by region, sorted descending"
```

The internal representation is opaque — you interact with specs through `render()`, `save()`, and `load()`.

## Rendering on new data

Specs are reusable on any data with compatible columns. "Compatible" means the columns referenced in the spec exist in the new DataFrame.

```python
spec = nveil.generate_spec("revenue by region", df_2024)
spec.save("revenue.nveil")

# Later, with 2025 data:
spec = nveil.load_spec("revenue.nveil")
fig = spec.render(df_2025)  # works if same columns exist
```

## Export formats

```python
# Display in browser
nveil.show(fig)

# Static images (requires Playwright / Chrome for png/jpg/svg/pdf)
nveil.save_image(fig, "chart.png")
nveil.save_image(fig, "chart.svg")
nveil.save_image(fig, "chart.pdf")

# Interactive HTML
nveil.save_html(fig, "chart.html")
```

