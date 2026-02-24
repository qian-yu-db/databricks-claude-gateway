"""Azure AD authentication using MSAL with PKCE."""

import atexit
from pathlib import Path

import msal

from config.settings import AzureAdConfig

CACHE_DIR = Path.home() / ".databricks-claude-gateway"
CACHE_FILE = CACHE_DIR / "msal_cache.bin"


def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if CACHE_FILE.exists():
        cache.deserialize(CACHE_FILE.read_text())
    atexit.register(_save_cache, cache)
    return cache


def _save_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(cache.serialize())


def create_msal_app(config: AzureAdConfig) -> msal.PublicClientApplication:
    """Create an MSAL public client application with token cache."""
    authority = f"https://login.microsoftonline.com/{config.tenant_id}"
    cache = _load_cache()
    return msal.PublicClientApplication(
        client_id=config.client_id,
        authority=authority,
        token_cache=cache,
    )


def acquire_token(app: msal.PublicClientApplication, scopes: list[str]) -> str:
    """Acquire a JWT ID token, trying silent auth first then interactive."""
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
        if result and "id_token" in result:
            return result["id_token"]

    result = app.acquire_token_interactive(scopes=scopes)
    if "id_token" not in result:
        error = result.get("error_description", result.get("error", "Unknown error"))
        raise RuntimeError(f"Azure AD authentication failed: {error}")

    return result["id_token"]
