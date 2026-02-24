"""Configure AI Gateway settings (rate limits, guardrails, usage tracking)."""

import json

import requests

from admin.setup_endpoint import get_dogfood_config


def configure_gateway(host: str, token: str, endpoint_name: str) -> dict:
    """Configure AI Gateway on an existing serving endpoint."""
    payload = {
        "rate_limits": [
            {"key": "endpoint", "renewal_period": "minute", "calls": 100},
            {"key": "user", "renewal_period": "minute", "calls": 20},
        ],
        "usage_tracking_config": {"enabled": True},
        "inference_table_config": {
            "catalog_name": "main",
            "schema_name": "claude_gateway_logs",
            "enabled": True,
        },
        "guardrails": {
            "input": {"safety": True, "pii": {"behavior": "BLOCK"}},
            "output": {"safety": True, "pii": {"behavior": "BLOCK"}},
        },
    }

    response = requests.put(
        f"{host}/api/2.0/serving-endpoints/{endpoint_name}/ai-gateway",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to configure gateway (HTTP {response.status_code}): {response.text}"
        )

    return response.json()


def main() -> None:
    from config.settings import load_config

    config = load_config()
    host, token = get_dogfood_config()
    result = configure_gateway(host, token, config.endpoint_name)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
