"""Python launcher: get token → set env → exec claude."""

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_dir = Path(__file__).resolve().parent.parent

    # Get token from credential helper
    result = subprocess.run(
        [sys.executable, "-m", "credential_helper"],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )
    if result.returncode != 0:
        print(f"Credential helper failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    token_data = json.loads(result.stdout)
    token = token_data["token"]

    # Load config
    config_path = project_dir / "config.json"
    if not config_path.exists():
        config_path = Path.home() / ".databricks-claude-gateway" / "config.json"
    if not config_path.exists():
        print("Error: config.json not found", file=sys.stderr)
        sys.exit(1)

    config = json.loads(config_path.read_text())
    host = config["databricks_host"].rstrip("/")
    endpoint = config["endpoint_name"]
    model = config["model"]

    # Set environment and exec claude
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = f"{host}/serving-endpoints/{endpoint}/invocations"
    env["ANTHROPIC_AUTH_TOKEN"] = token
    env["ANTHROPIC_MODEL"] = model

    os.execvpe("claude", ["claude"] + sys.argv[1:], env)


if __name__ == "__main__":
    main()
