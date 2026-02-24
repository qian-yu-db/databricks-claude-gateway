"""Databricks token exchange via RFC 8693."""

from dataclasses import dataclass

import requests


@dataclass
class DatabricksToken:
    access_token: str
    expires_in: int
    token_type: str


def exchange_token(url: str, jwt: str) -> DatabricksToken:
    """Exchange an Azure AD JWT for a Databricks OAuth token.

    Uses RFC 8693 token exchange grant type.
    """
    response = requests.post(
        url,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": jwt,
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
            "scope": "all-apis",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Token exchange failed (HTTP {response.status_code}): {response.text}"
        )

    data = response.json()
    return DatabricksToken(
        access_token=data["access_token"],
        expires_in=data["expires_in"],
        token_type=data.get("token_type", "Bearer"),
    )
