"""Shared test fixtures."""

import json

import pytest

from config.settings import AzureAdConfig, GatewayConfig, TokenCacheConfig


@pytest.fixture
def sample_config_dict():
    return {
        "databricks_host": "https://e2-dogfood.staging.cloud.databricks.com",
        "endpoint_name": "claude-code-gateway",
        "model": "claude-sonnet-4-20250514",
        "azure_ad": {
            "tenant_id": "test-tenant-id",
            "client_id": "test-client-id",
            "scopes": ["openid", "profile", "email"],
        },
        "token_cache": {"method": "keyring", "fallback": "file"},
    }


@pytest.fixture
def sample_config():
    return GatewayConfig(
        databricks_host="https://e2-dogfood.staging.cloud.databricks.com",
        endpoint_name="claude-code-gateway",
        model="claude-sonnet-4-20250514",
        azure_ad=AzureAdConfig(
            tenant_id="test-tenant-id",
            client_id="test-client-id",
            scopes=["openid", "profile", "email"],
        ),
        token_cache=TokenCacheConfig(method="keyring", fallback="file"),
    )


@pytest.fixture
def config_file(tmp_path, sample_config_dict):
    """Write a config file and return its path."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps(sample_config_dict))
    return path
