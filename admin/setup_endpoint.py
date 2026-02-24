"""Create AI Gateway external model endpoint on Databricks."""

import configparser
import json
from pathlib import Path

import requests


def get_dogfood_config() -> tuple[str, str]:
    """Read host and token from ~/.databrickscfg [dogfood] profile."""
    cfg = configparser.ConfigParser()
    cfg.read(Path.home() / ".databrickscfg")
    if "dogfood" not in cfg:
        raise RuntimeError("No [dogfood] profile in ~/.databrickscfg")
    profile = cfg["dogfood"]
    host = profile["host"].rstrip("/")
    token = profile["token"]
    return host, token


def create_endpoint(host: str, token: str, endpoint_name: str, model: str) -> dict:
    """Create an external model serving endpoint."""
    payload = {
        "name": endpoint_name,
        "config": {
            "served_entities": [
                {
                    "name": f"{endpoint_name}-entity",
                    "external_model": {
                        "name": model,
                        "provider": "anthropic",
                        "task": "llm/v1/chat",
                        "anthropic_config": {
                            "anthropic_api_key": "{{secrets/claude-gateway/anthropic-api-key}}",
                        },
                    },
                }
            ]
        },
    }

    response = requests.post(
        f"{host}/api/2.0/serving-endpoints",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Failed to create endpoint (HTTP {response.status_code}): {response.text}"
        )

    return response.json()


def main() -> None:
    from config.settings import load_config

    config = load_config()
    host, token = get_dogfood_config()
    result = create_endpoint(host, token, config.endpoint_name, config.model)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
