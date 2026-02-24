"""CLI entry point: python -m credential_helper."""

import argparse
import json
import sys
import time

from config.settings import load_config
from credential_helper.azure_ad_auth import acquire_token, create_msal_app
from credential_helper.token_cache import CachedToken, get_cached_token, save_token
from credential_helper.token_exchange import exchange_token


def main() -> None:
    parser = argparse.ArgumentParser(description="Databricks Claude Gateway credential helper")
    parser.add_argument("--config", help="Path to config.json")
    parser.add_argument("--check", action="store_true", help="Check token validity without refresh")
    args = parser.parse_args()

    config = load_config(args.config)

    cached = get_cached_token(config.token_cache)

    if args.check:
        if cached and cached.is_valid:
            print(json.dumps({"valid": True, "expires_at": cached.expires_at}))
            sys.exit(0)
        else:
            print(json.dumps({"valid": False}), file=sys.stderr)
            sys.exit(1)

    if cached and cached.is_valid:
        print(json.dumps({"token": cached.access_token, "expires_in": int(cached.expires_at - time.time())}))
        return

    # Authenticate via Azure AD
    app = create_msal_app(config.azure_ad)
    jwt = acquire_token(app, config.azure_ad.scopes)

    # Exchange for Databricks token
    db_token = exchange_token(config.token_exchange_url, jwt)

    # Cache the token
    cached_token = CachedToken(
        access_token=db_token.access_token,
        expires_at=time.time() + db_token.expires_in,
        token_type=db_token.token_type,
    )
    save_token(config.token_cache, cached_token)

    print(json.dumps({"token": db_token.access_token, "expires_in": db_token.expires_in}))


if __name__ == "__main__":
    main()
