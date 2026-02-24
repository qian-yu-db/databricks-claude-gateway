"""Tests for config.settings."""

import json

import pytest

from config.settings import load_config


def test_load_from_explicit_path(config_file):
    config = load_config(str(config_file))
    assert config.databricks_host == "https://e2-dogfood.staging.cloud.databricks.com"
    assert config.endpoint_name == "claude-code-gateway"
    assert config.model == "claude-sonnet-4-20250514"
    assert config.azure_ad.tenant_id == "test-tenant-id"
    assert config.azure_ad.client_id == "test-client-id"


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/config.json")


def test_invalid_json_raises(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("not json")
    with pytest.raises(json.JSONDecodeError):
        load_config(str(path))


def test_missing_required_field_raises(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"databricks_host": "https://example.com"}))
    with pytest.raises(ValueError, match="Missing required config field"):
        load_config(str(path))


def test_missing_azure_ad_field_raises(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "databricks_host": "https://example.com",
                "endpoint_name": "ep",
                "model": "m",
                "azure_ad": {"tenant_id": "t"},
            }
        )
    )
    with pytest.raises(ValueError, match="Missing required azure_ad field"):
        load_config(str(path))


def test_base_url_property(config_file):
    config = load_config(str(config_file))
    assert (
        config.base_url
        == "https://e2-dogfood.staging.cloud.databricks.com/serving-endpoints/claude-code-gateway/invocations"
    )


def test_token_exchange_url_property(config_file):
    config = load_config(str(config_file))
    assert (
        config.token_exchange_url
        == "https://e2-dogfood.staging.cloud.databricks.com/oidc/v1/token"
    )


def test_trailing_slash_stripped(tmp_path, sample_config_dict):
    sample_config_dict["databricks_host"] = "https://example.com/"
    path = tmp_path / "config.json"
    path.write_text(json.dumps(sample_config_dict))
    config = load_config(str(path))
    assert "example.com//" not in config.base_url


def test_default_token_cache(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "databricks_host": "https://example.com",
                "endpoint_name": "ep",
                "model": "m",
                "azure_ad": {"tenant_id": "t", "client_id": "c"},
            }
        )
    )
    config = load_config(str(path))
    assert config.token_cache.method == "keyring"
    assert config.token_cache.fallback == "file"
