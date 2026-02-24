"""Tests for credential_helper.token_cache."""

import json
import time

import pytest

from config.settings import TokenCacheConfig
from credential_helper.token_cache import (
    EXPIRY_BUFFER_SECONDS,
    CachedToken,
    clear_cache,
    get_cached_token,
    save_token,
)


@pytest.fixture
def file_config():
    return TokenCacheConfig(method="file", fallback="file")


@pytest.fixture
def valid_token():
    return CachedToken(
        access_token="valid-token",
        expires_at=time.time() + 3600,
        token_type="Bearer",
    )


@pytest.fixture
def expired_token():
    return CachedToken(
        access_token="expired-token",
        expires_at=time.time() - 100,
        token_type="Bearer",
    )


@pytest.fixture
def near_expiry_token():
    return CachedToken(
        access_token="near-expiry-token",
        expires_at=time.time() + (EXPIRY_BUFFER_SECONDS - 10),
        token_type="Bearer",
    )


def test_cached_token_valid(valid_token):
    assert valid_token.is_valid is True


def test_cached_token_expired(expired_token):
    assert expired_token.is_valid is False


def test_cached_token_near_expiry(near_expiry_token):
    assert near_expiry_token.is_valid is False


def test_file_save_and_get(mocker, file_config, valid_token):
    import credential_helper.token_cache as tc

    fake_dir = mocker.MagicMock()
    mocker.patch.object(tc, "CACHE_DIR", fake_dir)

    fake_file = mocker.MagicMock()
    fake_file.exists.return_value = False
    mocker.patch.object(tc, "CACHE_FILE", fake_file)

    # Save
    save_token(file_config, valid_token)
    fake_file.write_text.assert_called_once()

    # Simulate read back
    written_data = fake_file.write_text.call_args[0][0]
    fake_file.exists.return_value = True
    fake_file.read_text.return_value = written_data

    result = get_cached_token(file_config)
    assert result is not None
    assert result.access_token == "valid-token"


def test_get_cached_token_expired_returns_none(mocker, file_config, expired_token):
    import credential_helper.token_cache as tc

    fake_file = mocker.MagicMock()
    fake_file.exists.return_value = True
    fake_file.read_text.return_value = json.dumps(expired_token.to_dict())
    mocker.patch.object(tc, "CACHE_FILE", fake_file)

    result = get_cached_token(file_config)
    assert result is None


def test_clear_cache_deletes_file(mocker, file_config):
    import credential_helper.token_cache as tc

    fake_file = mocker.MagicMock()
    fake_file.exists.return_value = True
    mocker.patch.object(tc, "CACHE_FILE", fake_file)

    clear_cache(file_config)
    fake_file.unlink.assert_called_once()


def test_to_dict_roundtrip(valid_token):
    data = valid_token.to_dict()
    restored = CachedToken.from_dict(data)
    assert restored.access_token == valid_token.access_token
    assert restored.expires_at == valid_token.expires_at
    assert restored.token_type == valid_token.token_type
