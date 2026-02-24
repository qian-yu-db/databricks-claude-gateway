# Implementation Plan: Databricks Claude Gateway (Approach 2 — OAuth Token Federation)

## Goal

Enable Claude Code to use Databricks AI Gateway with temporary OAuth tokens obtained via Azure AD federation. No long-lived PATs. Developers authenticate once via browser SSO, get a short-lived Databricks token, and Claude Code uses it seamlessly.

---

## Authentication Flow

```
1. Developer runs launcher script
2. MSAL opens browser → Azure AD login (OAuth2 + PKCE)
3. Azure AD returns JWT ID token
4. Credential helper exchanges JWT for Databricks OAuth token:
   POST https://e2-dogfood.staging.cloud.databricks.com/oidc/v1/token
   Body: subject_token=<JWT>&grant_type=token-exchange&scope=all-apis
5. Databricks validates JWT against federation policy, returns Bearer token (~1hr)
6. Launcher sets ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN env vars
7. Launcher starts Claude Code
```

---

## Project Structure

```
databricks-claude-gateway/
├── CLAUDE.md                    # Project context for Claude Code sessions
├── PLAN.md                      # This file
├── pyproject.toml               # Minimal uv project config
├── .python-version              # Python version pin
├── admin/
│   ├── __init__.py
│   ├── setup_endpoint.py        # Create AI Gateway external model endpoint
│   ├── configure_gateway.py     # Rate limits, usage tracking, guardrails
│   └── setup_federation.py      # Create federation policy trusting Azure AD
├── credential_helper/
│   ├── __init__.py
│   ├── __main__.py              # Entry point: get-token / refresh
│   ├── azure_ad_auth.py         # MSAL-based Azure AD OIDC login (PKCE)
│   ├── token_exchange.py        # Databricks /oidc/v1/token exchange
│   └── token_cache.py           # Token caching (keyring or file-based)
├── launcher/
│   ├── launch_claude.sh         # Bash: get token → set env → exec claude
│   └── launch_claude.py         # Python alternative for cross-platform
├── installer/
│   └── install.sh               # Developer setup: write config, install deps
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuration loader (workspace, IdP, endpoint)
├── config.example.json          # Example config for developers
└── tests/
    ├── __init__.py
    ├── test_token_exchange.py   # Mock token exchange
    ├── test_azure_ad_auth.py    # Mock MSAL flows
    └── test_config.py           # Config loading
```

---

## Phase 1: Foundation — Admin Tooling

Set up the Databricks AI Gateway endpoint and federation policy.

### 1.1 Create AI Gateway Endpoint (`admin/setup_endpoint.py`)
- POST /api/2.0/serving-endpoints
- External model pointing to Anthropic (claude-sonnet-4-20250514)
- Anthropic API key stored in Databricks secrets
- Uses dogfood profile credentials for admin operations

### 1.2 Configure AI Gateway (`admin/configure_gateway.py`)
- PUT /api/2.0/serving-endpoints/{name}/ai-gateway
- Rate limits: per-endpoint and per-user QPM
- Usage tracking enabled (system tables)
- Inference table logging enabled
- Guardrails (safety + PII)

### 1.3 Create Federation Policy (`admin/setup_federation.py`)
- POST /api/2.0/accounts/{account_id}/federation-policies
- Trust Azure AD tenant as OIDC issuer
- Map subject_claim to email or oid
- Configure allowed audiences (Azure AD app client_id)

---

## Phase 2: Credential Helper

The core component — authenticates developer and gets a Databricks token.

### 2.1 Azure AD Authentication (`credential_helper/azure_ad_auth.py`)
- Use `msal` library (Microsoft's official auth library)
- MSAL handles OAuth2 + PKCE flow natively
- Interactive browser auth on first login
- Silent token acquisition on subsequent calls (MSAL caches refresh tokens)
- Returns JWT ID token

### 2.2 Databricks Token Exchange (`credential_helper/token_exchange.py`)
- POST {databricks_host}/oidc/v1/token
- RFC 8693 token exchange grant type
- Input: Azure AD JWT
- Output: Databricks OAuth Bearer token + expires_in
- Simple requests.post — no SDK needed

### 2.3 Token Cache (`credential_helper/token_cache.py`)
- Cache Databricks token (not just IdP token — MSAL handles that)
- Check expiry before returning cached token
- Two backends: keyring (preferred) or encrypted file fallback
- Auto-refresh: if Databricks token expired but MSAL has valid refresh token → silent re-auth

### 2.4 CLI Entry Point (`credential_helper/__main__.py`)
- `python -m credential_helper` → print JSON `{"token": "...", "expires_in": ...}`
- `python -m credential_helper --check` → validate token without refreshing
- Consumed by launcher scripts

---

## Phase 3: Launcher & Distribution

### 3.1 Launcher Script (`launcher/launch_claude.sh`)
```bash
#!/bin/bash
TOKEN_JSON=$(python -m credential_helper)
TOKEN=$(echo "$TOKEN_JSON" | python -c "import sys,json; print(json.load(sys.stdin)['token'])")

ANTHROPIC_BASE_URL="https://e2-dogfood.staging.cloud.databricks.com/serving-endpoints/claude-code-gateway/invocations" \
ANTHROPIC_AUTH_TOKEN="$TOKEN" \
ANTHROPIC_MODEL="claude-sonnet-4-20250514" \
exec claude "$@"
```

### 3.2 Python Launcher (`launcher/launch_claude.py`)
- Cross-platform alternative
- Same flow: get token → set env → subprocess.exec claude

### 3.3 Installer (`installer/install.sh`)
- Writes config.json with workspace URL, Azure AD tenant, client_id, endpoint name
- Installs Python deps via uv/pip
- Optionally adds shell alias: `alias claude-db='bash /path/to/launch_claude.sh'`

---

## Phase 4: Polish

### 4.1 Tests
- Mock MSAL auth flows
- Mock Databricks token exchange responses
- Config loading validation
- Integration test: full flow with real credentials (manual)

### 4.2 Error Handling
- Clear messages for: federation policy not configured, endpoint not found, token expired, rate limited
- No excessive try/except — fail fast with actionable error messages

---

## Configuration

### config.example.json
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

---

## Dependencies

Minimal set:
- `requests` — HTTP calls to Databricks APIs
- `msal` — Azure AD authentication (handles PKCE, caching, refresh)
- `keyring` — Secure token storage (optional, file fallback)
- `pytest` — Tests

---

## Key References

- [Databricks OAuth Token Federation](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation)
- [Token Exchange with IdP Token](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation-exchange)
- [Configure a Federation Policy](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation-policy)
- [AI Gateway External Models](https://docs.databricks.com/aws/en/generative-ai/external-models/)
- [MSAL Python Docs](https://learn.microsoft.com/en-us/entra/msal/python/)
- Design doc: ~/workspace/reference_repos/guidance-for-claude-code-with-amazon-bedrock/DATABRICKS_AI_GATEWAY_DESIGN.md
