"""Tests for credential_helper.azure_ad_auth."""

import pytest

from config.settings import AzureAdConfig
from credential_helper.azure_ad_auth import acquire_token, create_msal_app


@pytest.fixture
def azure_config():
    return AzureAdConfig(
        tenant_id="test-tenant",
        client_id="test-client",
        scopes=["openid", "profile", "email"],
    )


def test_create_msal_app(mocker, azure_config):
    mock_cache = mocker.Mock()
    mock_cache.has_state_changed = False
    mocker.patch("credential_helper.azure_ad_auth._load_cache", return_value=mock_cache)
    mock_app_cls = mocker.patch("credential_helper.azure_ad_auth.msal.PublicClientApplication")

    create_msal_app(azure_config)

    mock_app_cls.assert_called_once_with(
        client_id="test-client",
        authority="https://login.microsoftonline.com/test-tenant",
        token_cache=mock_cache,
    )


def test_acquire_token_silent_success(mocker, azure_config):
    mock_app = mocker.Mock()
    mock_app.get_accounts.return_value = [{"username": "user@test.com"}]
    mock_app.acquire_token_silent.return_value = {"id_token": "jwt-from-cache"}

    result = acquire_token(mock_app, azure_config.scopes)

    assert result == "jwt-from-cache"
    mock_app.acquire_token_interactive.assert_not_called()


def test_acquire_token_silent_fail_interactive_success(mocker, azure_config):
    mock_app = mocker.Mock()
    mock_app.get_accounts.return_value = [{"username": "user@test.com"}]
    mock_app.acquire_token_silent.return_value = None
    mock_app.acquire_token_interactive.return_value = {"id_token": "jwt-from-browser"}

    result = acquire_token(mock_app, azure_config.scopes)

    assert result == "jwt-from-browser"


def test_acquire_token_no_accounts_goes_interactive(mocker, azure_config):
    mock_app = mocker.Mock()
    mock_app.get_accounts.return_value = []
    mock_app.acquire_token_interactive.return_value = {"id_token": "jwt-new"}

    result = acquire_token(mock_app, azure_config.scopes)

    assert result == "jwt-new"
    mock_app.acquire_token_silent.assert_not_called()


def test_acquire_token_interactive_failure_raises(mocker, azure_config):
    mock_app = mocker.Mock()
    mock_app.get_accounts.return_value = []
    mock_app.acquire_token_interactive.return_value = {
        "error": "auth_failed",
        "error_description": "User cancelled",
    }

    with pytest.raises(RuntimeError, match="User cancelled"):
        acquire_token(mock_app, azure_config.scopes)
