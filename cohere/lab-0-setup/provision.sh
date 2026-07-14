#!/usr/bin/env bash
set -euo pipefail

# Lab 0 provisioning script.
# Creates (or reuses) a resource group, then runs the declarative Bicep template
# that builds the Foundry account, Foundry project, model deployments, and
# observability resources used by the workshop.

# Resolve paths from the script location so learners can run this from any working directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BICEP_FILE="$SCRIPT_DIR/bicep/main.bicep"
PARAM_FILE="$SCRIPT_DIR/bicep/main.parameters.json"
LOCATION="${LOCATION:-eastus2}"
RESOURCE_GROUP="${RESOURCE_GROUP:-${1:-}}"

# Allow RESOURCE_GROUP as either an environment variable or positional argument,
# but prompt interactively when someone runs the script by hand.
if [[ -z "$RESOURCE_GROUP" ]]; then
  read -r -p "Resource group name to create/use: " RESOURCE_GROUP
fi

if [[ -z "$RESOURCE_GROUP" ]]; then
  echo "ERROR: RESOURCE_GROUP is required." >&2
  exit 1
fi

# Fail before deployment work starts if the Azure CLI is missing.
if ! command -v az >/dev/null 2>&1; then
  echo "ERROR: Azure CLI (az) is required. Install it, then run az login." >&2
  exit 1
fi

echo "==> Using resource group: $RESOURCE_GROUP"
echo "==> Using location:       $LOCATION"

# Idempotent: az group create updates metadata if the group already exists.
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output none

# Keep the template reusable: the parameter file has workshop defaults, while
# LOCATION can override the region without editing JSON.
echo "==> Deploying Lab 0 Bicep template. This can take several minutes."
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "$BICEP_FILE" \
  --parameters "@$PARAM_FILE" location="$LOCATION" \
  --query "properties.outputs" \
  --output json

echo
echo "Provisioning complete. Next step:"
echo "  cd $SCRIPT_DIR"
echo "  RESOURCE_GROUP=$RESOURCE_GROUP ./setup-env.sh"
