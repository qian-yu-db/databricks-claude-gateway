# CLAUDE.md

## Project Overview

Databricks AI Gateway integration for Claude Code using OAuth Token Federation (Approach 2).
Replaces long-lived PATs with temporary OAuth tokens obtained via Azure AD OIDC → Databricks token exchange.

## Target Environment

- **IdP**: Azure AD (Entra ID)
- **Databricks Profile**: `dogfood`
- **Databricks Host**: `https://e2-dogfood.staging.cloud.databricks.com`
- **Databricks CLI Config**: `~/.databrickscfg` (profile: dogfood)

## Architecture

```
Developer → Azure AD login (OAuth2+PKCE) → JWT ID Token
         → Databricks token exchange (POST /oidc/v1/token) → OAuth Bearer token
         → Claude Code with ANTHROPIC_BASE_URL pointing to AI Gateway endpoint
```

## Development Commands

```bash
cd ~/workspace/developments/databricks-claude-gateway
uv sync                                    # Install dependencies
uv run python -m credential_helper         # Run credential helper
uv run python -m admin.setup_endpoint      # Admin: create AI Gateway endpoint
uv run pytest tests/                       # Run tests
```

## Project Structure

See PLAN.md for full architecture and implementation plan.

## Key Design Decisions

- Use `uv` for Python environment management (no complex pyproject.toml)
- Minimal dependencies: requests, msal, keyring
- Azure AD auth via MSAL library (handles PKCE, token caching natively)
- Databricks token exchange is a single HTTP POST (RFC 8693)
- Credential helper outputs token for launcher script consumption
- No binary packaging needed — Python script + launcher shell script

## Reference

- Design doc: ~/workspace/reference_repos/guidance-for-claude-code-with-amazon-bedrock/DATABRICKS_AI_GATEWAY_DESIGN.md
- Original AWS Bedrock repo: ~/workspace/reference_repos/guidance-for-claude-code-with-amazon-bedrock/
