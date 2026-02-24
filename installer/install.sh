#!/bin/bash
set -euo pipefail

echo "=== Databricks Claude Gateway Installer ==="

INSTALL_DIR="${HOME}/.databricks-claude-gateway"
CONFIG_FILE="${INSTALL_DIR}/config.json"

# Create config directory
mkdir -p "$INSTALL_DIR"

# Prompt for configuration
if [ ! -f "$CONFIG_FILE" ]; then
    echo ""
    read -rp "Databricks host URL: " DB_HOST
    read -rp "Endpoint name [claude-code-gateway]: " ENDPOINT_NAME
    ENDPOINT_NAME="${ENDPOINT_NAME:-claude-code-gateway}"
    read -rp "Model [claude-sonnet-4-20250514]: " MODEL
    MODEL="${MODEL:-claude-sonnet-4-20250514}"
    read -rp "Azure AD tenant ID: " TENANT_ID
    read -rp "Azure AD client ID: " CLIENT_ID

    cat > "$CONFIG_FILE" <<EOF
{
  "databricks_host": "${DB_HOST}",
  "endpoint_name": "${ENDPOINT_NAME}",
  "model": "${MODEL}",
  "azure_ad": {
    "tenant_id": "${TENANT_ID}",
    "client_id": "${CLIENT_ID}",
    "scopes": ["openid", "profile", "email"]
  },
  "token_cache": {
    "method": "keyring",
    "fallback": "file"
  }
}
EOF
    echo "Config written to ${CONFIG_FILE}"
else
    echo "Config already exists at ${CONFIG_FILE}"
fi

# Install dependencies
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "Installing dependencies..."
cd "$PROJECT_DIR" && uv sync

# Offer shell alias
echo ""
read -rp "Add shell alias 'claude-db'? [y/N]: " ADD_ALIAS
if [[ "${ADD_ALIAS}" =~ ^[Yy]$ ]]; then
    SHELL_RC="${HOME}/.zshrc"
    if [ -n "${BASH_VERSION:-}" ]; then
        SHELL_RC="${HOME}/.bashrc"
    fi
    ALIAS_LINE="alias claude-db='bash ${PROJECT_DIR}/launcher/launch_claude.sh'"
    if ! grep -q "claude-db" "$SHELL_RC" 2>/dev/null; then
        echo "$ALIAS_LINE" >> "$SHELL_RC"
        echo "Alias added to ${SHELL_RC}. Run 'source ${SHELL_RC}' to activate."
    else
        echo "Alias already exists in ${SHELL_RC}"
    fi
fi

echo ""
echo "Installation complete! Run 'claude-db' or 'bash ${PROJECT_DIR}/launcher/launch_claude.sh'"
