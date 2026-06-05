# Sessions

Sessions keep the data pipeline alive across multiple operations, avoiding redundant re-runs.

## The problem

Without a session, every `spec.render()` call creates a temporary workspace, runs the choregraph pipeline, renders, and cleans up. This is correct but slow if you're rendering the same spec multiple times.

## The solution

```python
with nveil.session() as s:
    spec = s.generate_spec("bar chart of revenue", df)

    fig1 = spec.render(df)          # runs pipeline
    fig2 = spec.render(updated_df)  # reuses pipeline outputs
    fig3 = spec.render(another_df)  # still reuses — no re-run
```

The session owns a temporary workspace directory and a Choregraph instance. When the context manager exits, the workspace is cleaned up.

## Timing instrumentation

Enable timing to measure each operation:

```python
nveil.configure(api_key="...", timing=True)

with nveil.session() as s:
    spec = s.generate_spec("scatter plot", df)
    fig = spec.render(df)
    print(s.timer.summary())
```

Output:

```
 build workspace      0.12s
 API: processing plan 1.34s
 pipeline run         0.45s
 API: visualization   0.92s
 render               0.31s
 ─────────────────────────
 total                3.14s
```

## When to use sessions

| Scenario | Use session? |
|----------|:---:|
| Single `generate_spec` + `render` | Optional |
| Multiple renders of the same spec | Yes |
| Generating multiple specs from the same data | Yes |
| One-off script | Not needed |
