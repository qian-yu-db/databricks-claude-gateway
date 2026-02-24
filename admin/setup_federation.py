"""Create federation policy to trust Azure AD as OIDC issuer."""

import json

import requests

from admin.setup_endpoint import get_dogfood_config


def create_federation_policy(
    host: str, token: str, account_id: str, tenant_id: str, client_id: str
) -> dict:
    """Create a federation policy trusting Azure AD."""
    payload = {
        "name": "azure-ad-claude-gateway",
        "oidc_policy": {
            "issuer": f"https://login.microsoftonline.com/{tenant_id}/v2.0",
            "audiences": [client_id],
            "subject_claim": "email",
        },
    }

    response = requests.post(
        f"{host}/api/2.0/accounts/{account_id}/federation-policies",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Failed to create federation policy (HTTP {response.status_code}): {response.text}"
        )

    return response.json()


def main() -> None:
    import argparse

    from config.settings import load_config

    parser = argparse.ArgumentParser(description="Setup Databricks federation policy")
    parser.add_argument("--account-id", required=True, help="Databricks account ID")
    args = parser.parse_args()

    config = load_config()
    host, token = get_dogfood_config()
    result = create_federation_policy(
        host, token, args.account_id, config.azure_ad.tenant_id, config.azure_ad.client_id
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
