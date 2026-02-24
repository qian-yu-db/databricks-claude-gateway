# Databricks Claude Gateway

Claude Code integration with Databricks AI Gateway using OAuth Token Federation. Replaces long-lived PATs with temporary OAuth tokens obtained via Azure AD OIDC and Databricks token exchange.

## How It Works

```
Developer runs launcher
  → MSAL opens browser → Azure AD login (OAuth2 + PKCE)
  → Azure AD returns JWT ID token
  → Credential helper exchanges JWT for Databricks OAuth token (RFC 8693)
  → Launcher sets ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN
  → Claude Code starts with AI Gateway endpoint
```

## Quick Start

### 1. Install

```bash
bash installer/install.sh
```

This will prompt for your Databricks host, Azure AD tenant/client IDs, install dependencies via `uv`, and optionally create a `claude-db` shell alias.

### 2. Configure (manual alternative)

Copy and edit the example config:

```bash
mkdir -p ~/.databricks-claude-gateway
cp config.example.json ~/.databricks-claude-gateway/config.json
# Edit with your Azure AD tenant_id, client_id, and Databricks host
```

### 3. Launch Claude Code

```bash
# Using the shell launcher
bash launcher/launch_claude.sh

# Or the Python launcher
uv run python launcher/launch_claude.py

# Or via alias (if installed)
claude-db
```

## Project Structure

```
├── config/
│   └── settings.py              # Configuration loader (dataclasses + JSON)
├── credential_helper/
│   ├── __main__.py              # CLI: python -m credential_helper
│   ├── azure_ad_auth.py         # MSAL-based Azure AD OIDC login (PKCE)
│   ├── token_exchange.py        # Databricks /oidc/v1/token exchange (RFC 8693)
│   └── token_cache.py           # Token caching (keyring → file fallback)
├── admin/
│   ├── setup_endpoint.py        # Create AI Gateway serving endpoint
│   ├── configure_gateway.py     # Set rate limits, guardrails, usage tracking
│   └── setup_federation.py      # Create federation policy trusting Azure AD
├── launcher/
│   ├── launch_claude.sh         # Bash: get token → set env → exec claude
│   └── launch_claude.py         # Python alternative
├── installer/
│   └── install.sh               # Interactive setup script
├── tests/                       # Unit tests (pytest + pytest-mock)
├── config.example.json          # Example configuration
└── pyproject.toml               # Dependencies
```

## Admin Setup

Before developers can authenticate, an admin must configure the Databricks workspace:

```bash
# 1. Create the AI Gateway endpoint (requires dogfood profile in ~/.databrickscfg)
uv run python -m admin.setup_endpoint

# 2. Configure rate limits, guardrails, usage tracking
uv run python -m admin.configure_gateway

# 3. Create federation policy trusting Azure AD
uv run python -m admin.setup_federation --account-id <ACCOUNT_ID>
```

## Credential Helper CLI

```bash
# Get a fresh token (authenticates if needed)
uv run python -m credential_helper

# Check if cached token is still valid
uv run python -m credential_helper --check

# Use a specific config file
uv run python -m credential_helper --config /path/to/config.json
```

Output format:
```json
{"token": "dapi...", "expires_in": 3600}
```

## Configuration

See `config.example.json`:

```json
{
  "databricks_host": "https://e2-dogfood.staging.cloud.databricks.com",
  "endpoint_name": "claude-code-gateway",
  "model": "claude-sonnet-4-20250514",
  "azure_ad": {
    "tenant_id": "<azure-ad-tenant-id>",
    "client_id": "<azure-ad-app-client-id>",
    "scopes": ["openid", "profile", "email"]
  },
  "token_cache": {
    "method": "keyring",
    "fallback": "file"
  }
}
```

Config is loaded from (in order): explicit `--config` path, `./config.json`, `~/.databricks-claude-gateway/config.json`.

## Development

```bash
uv sync --all-extras          # Install all dependencies
uv run pytest tests/ -v       # Run unit tests (27 tests)
```

## Dependencies

- `requests` — HTTP calls to Databricks APIs
- `msal` — Azure AD authentication (PKCE, caching, refresh)
- `keyring` — Secure token storage (optional, file fallback)
- `pytest` + `pytest-mock` — Testing (dev only)
