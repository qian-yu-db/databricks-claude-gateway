"""Tests for credential_helper.token_exchange."""

import pytest

from credential_helper.token_exchange import DatabricksToken, exchange_token


def test_exchange_token_success(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "db-token-123",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    mocker.patch("credential_helper.token_exchange.requests.post", return_value=mock_response)

    result = exchange_token("https://db.com/oidc/v1/token", "jwt-abc")

    assert isinstance(result, DatabricksToken)
    assert result.access_token == "db-token-123"
    assert result.expires_in == 3600
    assert result.token_type == "Bearer"


def test_exchange_token_correct_params(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "tok",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    mock_post = mocker.patch(
        "credential_helper.token_exchange.requests.post", return_value=mock_response
    )

    exchange_token("https://db.com/oidc/v1/token", "my-jwt")

    mock_post.assert_called_once_with(
        "https://db.com/oidc/v1/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": "my-jwt",
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
            "scope": "all-apis",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


@pytest.mark.parametrize("status_code", [400, 401, 403, 500])
def test_exchange_token_error(mocker, status_code):
    mock_response = mocker.Mock()
    mock_response.status_code = status_code
    mock_response.text = "error body"
    mocker.patch("credential_helper.token_exchange.requests.post", return_value=mock_response)

    with pytest.raises(RuntimeError, match=f"HTTP {status_code}"):
        exchange_token("https://db.com/oidc/v1/token", "jwt")
