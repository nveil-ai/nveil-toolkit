# API Reference

## Module-level functions

| Function | Description |
|----------|-------------|
| [`configure()`](nveil.md#nveil.configure) | Initialize the global client with your API key |
| [`generate_spec()`](nveil.md#nveil.generate_spec) | Generate a visualization spec from data and a prompt |
| [`load_spec()`](nveil.md#nveil.load_spec) | Load a spec from a `.nveil` file |
| [`session()`](nveil.md#nveil.session) | Create a scoped session with workspace reuse |
| [`show()`](nveil.md#nveil.show) | Display a figure in the browser |
| [`save_image()`](nveil.md#nveil.save_image) | Export a figure to a static image |
| [`save_html()`](nveil.md#nveil.save_html) | Export a figure to interactive HTML |

## Classes

| Class | Description |
|-------|-------------|
| [`NveilSpec`](nveil-spec.md) | Opaque visualization spec — render, save, load |
| [`Session`](session.md) | Scoped workspace for pipeline reuse |

## Exceptions

| Exception | Description |
|-----------|-------------|
| [`NveilError`](exceptions.md) | Base exception |
| [`AuthenticationError`](exceptions.md) | Invalid or expired API key (401) |
| [`ScopeError`](exceptions.md) | Missing permission scope (403) |
| [`QuotaExceededError`](exceptions.md) | Rate limit exceeded (429) |
| [`SpecGenerationError`](exceptions.md) | Server or local execution error |
| [`IncompatibleDataError`](exceptions.md) | Data schema mismatch |
