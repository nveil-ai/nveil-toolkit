# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in the NVEIL SDK, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email us at **security@nveil.com** with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact

We will acknowledge your report within 48 hours and provide a timeline for a fix.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |
| < 1.0   | No        |

## Security Design

- **Data privacy**: Raw data never leaves your machine. Only metadata (column names, types, aggregate statistics) is sent to the NVEIL server.
- **Transport security**: All API communication uses HTTPS/TLS.
- **API keys**: Keys are scoped and revocable from your [account settings](https://app.nveil.com).
