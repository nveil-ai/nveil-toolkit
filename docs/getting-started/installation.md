# Installation

## Requirements

- Python 3.10 or later
- An NVEIL API key

## Install from PyPI

```bash
pip install nveil
```

This installs the Toolkit and all required dependencies including the data pipeline and visualization engine.

## Verify the installation

```python
import nveil
print("nveil installed successfully")
```

## API Key

You need an API key to generate visualization specs.

1. Create an account at [app.nveil.com](https://app.nveil.com)
2. Go to **Settings** in your account
3. Generate an API key (starts with `nveil_`)

Configure it in your code:

```python
nveil.configure(api_key="nveil_...")
```

Or set it as an environment variable:

```bash
export NVEIL_API_KEY="nveil_..."
```

!!! tip
    Store your API key in a `.env` file or secret manager — never commit it to source control.

## What's installed

The `nveil` package bundles two internal libraries:

- **choregraph** — data pipeline engine (transforms, metadata extraction)
- **dive** — visualization engine (spec models, multi-backend rendering)

You don't need to interact with these directly — the Toolkit wraps them into a simple API.
