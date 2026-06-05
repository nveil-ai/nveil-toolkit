# Authentication

## API Keys

Every call to `generate_spec()` requires an API key. Keys start with `nveil_` and are scoped to your account.

### Configuring your key

```python
nveil.configure(api_key="nveil_...")
```

Call `configure()` once at the start of your script or application. All subsequent `generate_spec()` calls use this key.

### Error handling

```python
from nveil import AuthenticationError, ScopeError, QuotaExceededError

try:
    spec = nveil.generate_spec("bar chart", df)
except AuthenticationError:
    print("Invalid or expired API key")
except ScopeError:
    print("Your key doesn't have permission for this operation")
except QuotaExceededError:
    print("Rate limit exceeded — try again later")
```

### Key scopes

API keys can be scoped to specific operations. If you receive a `ScopeError`, check that your key has the required permissions in your NVEIL dashboard.

## What requires an API key

| Operation | API key required |
|-----------|:---:|
| `nveil.generate_spec()` | Yes |
| `spec.render()` | No |
| `spec.save()` / `nveil.load_spec()` | No |
| `nveil.show()` / `nveil.save_image()` | No |

Once a spec is generated, all rendering and export operations are fully local and free.
