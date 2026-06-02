# Versioning

The NVEIL Toolkit follows [Semantic Versioning](https://semver.org/).

## What to expect

### PATCH updates (1.0.x)

Bug fixes only. Your code continues to work without changes.

### MINOR updates (1.x.0)

New features added. Your existing code continues to work — we never remove or rename anything in a minor release. You may see:

- New functions or parameters
- New visualization types
- New export formats
- Performance improvements

### MAJOR updates (x.0.0)

May include changes that require code updates. These are rare and announced in advance. Saved `.nveil` files from the previous major version may need to be regenerated.

## Compatibility

### Toolkit and server

The Toolkit and NVEIL server may be on different versions. If your Toolkit is too old, you'll get a clear error:

```
nveil.exceptions.SpecGenerationError: API error (400):
  Your Toolkit version is too old. Run: pip install --upgrade nveil
```

### .nveil files

| Scenario | What happens |
|----------|-------------|
| Saved with older version, loaded with newer | Works (within same major version) |
| Saved with newer version, loaded with older | Error with upgrade instructions |

## Checking your version

```python
import nveil
print(nveil.__version__)
```
