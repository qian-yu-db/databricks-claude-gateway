"""Configuration loader for Databricks Claude Gateway."""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AzureAdConfig:
    tenant_id: str
    client_id: str
    scopes: list[str] = field(default_factory=lambda: ["openid", "profile", "email"])


@dataclass
class TokenCacheConfig:
    method: str = "keyring"
    fallback: str = "file"


@dataclass
class GatewayConfig:
    databricks_host: str
    endpoint_name: str
    model: str
    azure_ad: AzureAdConfig
    token_cache: TokenCacheConfig = field(default_factory=TokenCacheConfig)

    @property
    def base_url(self) -> str:
        host = self.databricks_host.rstrip("/")
        return f"{host}/serving-endpoints/{self.endpoint_name}/invocations"

    @property
    def token_exchange_url(self) -> str:
        host = self.databricks_host.rstrip("/")
        return f"{host}/oidc/v1/token"


def load_config(path: str | None = None) -> GatewayConfig:
    """Load config from explicit path, CWD, or ~/.databricks-claude-gateway/config.json."""
    if path:
        config_path = Path(path)
    else:
        cwd_path = Path.cwd() / "config.json"
        home_path = Path.home() / ".databricks-claude-gateway" / "config.json"
        if cwd_path.exists():
            config_path = cwd_path
        elif home_path.exists():
            config_path = home_path
        else:
            raise FileNotFoundError(
                "No config.json found in current directory or ~/.databricks-claude-gateway/"
            )

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw = json.loads(config_path.read_text())

    for required in ("databricks_host", "endpoint_name", "model", "azure_ad"):
        if required not in raw:
            raise ValueError(f"Missing required config field: {required}")

    azure_ad_raw = raw["azure_ad"]
    for required in ("tenant_id", "client_id"):
        if required not in azure_ad_raw:
            raise ValueError(f"Missing required azure_ad field: {required}")

    azure_ad = AzureAdConfig(
        tenant_id=azure_ad_raw["tenant_id"],
        client_id=azure_ad_raw["client_id"],
        scopes=azure_ad_raw.get("scopes", ["openid", "profile", "email"]),
    )

    token_cache_raw = raw.get("token_cache", {})
    token_cache = TokenCacheConfig(
        method=token_cache_raw.get("method", "keyring"),
        fallback=token_cache_raw.get("fallback", "file"),
    )

    return GatewayConfig(
        databricks_host=raw["databricks_host"],
        endpoint_name=raw["endpoint_name"],
        model=raw["model"],
        azure_ad=azure_ad,
        token_cache=token_cache,
    )
