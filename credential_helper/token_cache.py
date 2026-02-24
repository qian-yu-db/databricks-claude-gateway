"""Token caching with keyring and file fallback."""

import json
import time
from dataclasses import dataclass
from pathlib import Path

from config.settings import TokenCacheConfig

CACHE_DIR = Path.home() / ".databricks-claude-gateway"
CACHE_FILE = CACHE_DIR / "token_cache.json"
KEYRING_SERVICE = "databricks-claude-gateway"
KEYRING_KEY = "databricks_token"
EXPIRY_BUFFER_SECONDS = 300  # 5 minutes


@dataclass
class CachedToken:
    access_token: str
    expires_at: float
    token_type: str = "Bearer"

    @property
    def is_valid(self) -> bool:
        return time.time() < (self.expires_at - EXPIRY_BUFFER_SECONDS)

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "expires_at": self.expires_at,
            "token_type": self.token_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CachedToken":
        return cls(
            access_token=data["access_token"],
            expires_at=data["expires_at"],
            token_type=data.get("token_type", "Bearer"),
        )


def _try_keyring_get() -> CachedToken | None:
    try:
        import keyring

        raw = keyring.get_password(KEYRING_SERVICE, KEYRING_KEY)
        if raw:
            return CachedToken.from_dict(json.loads(raw))
    except Exception:
        pass
    return None


def _try_keyring_set(token: CachedToken) -> bool:
    try:
        import keyring

        keyring.set_password(KEYRING_SERVICE, KEYRING_KEY, json.dumps(token.to_dict()))
        return True
    except Exception:
        return False


def _try_keyring_delete() -> bool:
    try:
        import keyring

        keyring.delete_password(KEYRING_SERVICE, KEYRING_KEY)
        return True
    except Exception:
        return False


def _file_get() -> CachedToken | None:
    if not CACHE_FILE.exists():
        return None
    data = json.loads(CACHE_FILE.read_text())
    return CachedToken.from_dict(data)


def _file_set(token: CachedToken) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(token.to_dict()))


def _file_delete() -> None:
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()


def get_cached_token(config: TokenCacheConfig) -> CachedToken | None:
    """Get a cached token if one exists and is valid."""
    token = None
    if config.method == "keyring":
        token = _try_keyring_get()
    if token is None and config.fallback == "file":
        token = _file_get()
    if token and not token.is_valid:
        return None
    return token


def save_token(config: TokenCacheConfig, token: CachedToken) -> None:
    """Save a token to the cache."""
    if config.method == "keyring":
        if _try_keyring_set(token):
            return
    if config.fallback == "file" or config.method == "file":
        _file_set(token)


def clear_cache(config: TokenCacheConfig) -> None:
    """Clear all cached tokens."""
    if config.method == "keyring":
        _try_keyring_delete()
    _file_delete()
