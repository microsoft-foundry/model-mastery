#!/usr/bin/env bash
#
# One-command setup for the TrailMate workshop.
#
# Run from this folder:  ./provision.sh
#
# It will:
#   1. Make sure you're signed in to Azure (runs `az login` if needed).
#   2. Ask whether you already have a pre-provisioned Foundry project:
#        - Yes  -> it just refreshes .env from your resource group (setenv.sh).
#        - No   -> it provisions the resource, project, RBAC, models, and
#                  Application Insights tracing, then writes .env.
#   3. Leave you with ../src/.env that every lab reads.
#
# Customize the provision path by exporting any of these first (see sample.env):
#   AZURE_LOCATION, AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP,
#   AZURE_AI_PROJECT_NAME, AZURE_AI_ACCOUNT_NAME, SKU_CAPACITY

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Foundry RBAC role definition IDs. The roles were recently renamed (Foundry
# User was "Azure AI User"), so we assign by ID to survive the rename rollout.
FOUNDRY_USER_ROLE_ID="53ca6127-db72-4b80-b1b0-d745d6d5456d"

# Retry a command a few times to ride out transient Azure errors (e.g. 503s).
retry() {
  local n=0 max=4
  until "$@"; do
    n=$((n + 1))
    [[ $n -ge $max ]] && return 1
    echo "    transient error — retry $n/$((max - 1)) in 12s..."
    sleep 12
  done
}

command -v az >/dev/null || { echo "Azure CLI (az) is required."; exit 1; }
command -v jq >/dev/null || { echo "jq is required."; exit 1; }

# --- 1. Make sure we're signed in. ---
if ! az account show >/dev/null 2>&1; then
  echo "You're not signed in to Azure. Launching 'az login'..."
  az login >/dev/null
fi
if [[ -n "${AZURE_SUBSCRIPTION_ID:-}" ]]; then
  az account set --subscription "$AZURE_SUBSCRIPTION_ID"
fi
SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
SUBSCRIPTION_NAME="$(az account show --query name -o tsv)"
echo "Signed in. Subscription: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"

# --- 2. Pre-provisioned? Then just refresh .env and stop. ---
read -r -p "Do you already have a pre-provisioned Foundry project (e.g. a Skillable lab)? [y/N] " pre
if [[ "$pre" =~ ^[Yy]$ ]]; then
  read -r -p "Resource group name: " RESOURCE_GROUP
  exec "$SCRIPT_DIR/setenv.sh" "$RESOURCE_GROUP"
fi

# ---- Provision path: create everything. ----
LOCATION="${AZURE_LOCATION:-eastus}"
SKU_CAPACITY="${SKU_CAPACITY:-60}"
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-rg-model-mastery}"
PROJECT_NAME="${AZURE_AI_PROJECT_NAME:-foundry-workshop}"
ACCOUNT_NAME="${AZURE_AI_ACCOUNT_NAME:-aif-$(openssl rand -hex 4)}"

read -r -p "Region for new resources [$LOCATION]: " loc
LOCATION="${loc:-$LOCATION}"

# Validate the region so a stray keystroke (e.g. 'N') can't reach Azure.
VALID_REGIONS="$(az account list-locations --query "[].name" -o tsv)"
while ! grep -qxF "$LOCATION" <<<"$VALID_REGIONS"; do
  echo "  '$LOCATION' isn't a valid Azure region. Examples: eastus, westus3, westeurope."
  read -r -p "Region for new resources [eastus]: " loc
  LOCATION="${loc:-eastus}"
done

echo
echo "About to create:"
echo "  Resource group : $RESOURCE_GROUP"
echo "  Foundry acct   : $ACCOUNT_NAME"
echo "  Project        : $PROJECT_NAME"
echo "  Location       : $LOCATION"
read -r -p "Proceed? [y/N] " reply
[[ "$reply" =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 0; }

echo "==> Registering resource providers"
az provider register --namespace Microsoft.CognitiveServices --wait
az provider register --namespace Microsoft.Insights --wait
az provider register --namespace Microsoft.OperationalInsights --wait

echo "==> Creating the resource group"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

echo "==> Creating the Foundry (AI Services) resource"
# --assign-identity + --allow-project-management are required for projects.
az cognitiveservices account create \
  --name "$ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" \
  --kind AIServices --sku S0 --location "$LOCATION" \
  --custom-domain "$ACCOUNT_NAME" \
  --assign-identity --allow-project-management true \
  --yes --output none

echo "==> Creating the project (with its own managed identity)"
az cognitiveservices account project create \
  --name "$ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" \
  --project-name "$PROJECT_NAME" --location "$LOCATION" \
  --assign-identity --output none

ACCOUNT_ID="$(az cognitiveservices account show --name "$ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" --query id -o tsv)"
USER_PRINCIPAL_ID="$(az ad signed-in-user show --query id -o tsv)"
PROJECT_PRINCIPAL_ID="$(az cognitiveservices account project show \
  --name "$ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" \
  --project-name "$PROJECT_NAME" --query identity.principalId -o tsv)"

echo "==> Assigning the Foundry User role (you + the project identity)"
az role assignment create --assignee-object-id "$USER_PRINCIPAL_ID" \
  --assignee-principal-type User --role "$FOUNDRY_USER_ROLE_ID" \
  --scope "$ACCOUNT_ID" --output none 2>/dev/null || echo "    (already assigned to you)"
az role assignment create --assignee-object-id "$PROJECT_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal --role "$FOUNDRY_USER_ROLE_ID" \
  --scope "$ACCOUNT_ID" --output none 2>/dev/null || echo "    (already assigned to the project)"

# Deploy one model, resolving version/format from the regional catalog.
deploy_model() {
  local deployment="$1" model="$2" capacity="$3" catalog version format
  catalog="$(az cognitiveservices model list --location "$LOCATION" -o json)"
  version="$(echo "$catalog" | jq -r --arg m "$model" \
    '[.[] | select(.model.name==$m)] | (map(select(.model.isDefaultVersion=="true"))[0] // .[0]) | .model.version // empty')"
  format="$(echo "$catalog" | jq -r --arg m "$model" \
    '[.[] | select(.model.name==$m)] | (.[0].model.format) // empty')"
  if [[ -z "$version" || -z "$format" ]]; then
    echo "    [skip] '$model' not in the $LOCATION catalog — deploy it in the portal."
    return
  fi
  echo "==> Deploying $deployment ($model $version, $format)"
  az cognitiveservices account deployment create \
    --name "$ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" \
    --deployment-name "$deployment" --model-name "$model" \
    --model-version "$version" --model-format "$format" \
    --sku-name GlobalStandard --sku-capacity "$capacity" \
    --output none 2>/dev/null && echo "    done" || echo "    [warn] failed — check quota in $LOCATION"
}

echo "==> Deploying the Azure-direct models (GPT, Router, Image)"
# Deployment names match what the notebooks expect (and the Skillable lab).
deploy_model "gpt-5.4"            "gpt-5.4"            "$SKU_CAPACITY"
deploy_model "gpt-5.4-mini"       "gpt-5.4-mini"       "$SKU_CAPACITY"
deploy_model "model-router"       "model-router"       "$SKU_CAPACITY"
deploy_model "MAI-Image-2.5-Pro"  "MAI-Image-2.5-Pro"  1

echo
read -r -p "Also deploy Claude (Sonnet + Haiku) for the GPT-vs-Claude comparison? [y/N] " claude
if [[ "$claude" =~ ^[Yy]$ ]]; then
  echo "==> Deploying Claude models (may require accepting Marketplace terms)"
  deploy_model "claude-sonnet-4-6" "claude-sonnet-4.6" "$SKU_CAPACITY"
  deploy_model "claude-haiku-4-5"  "claude-haiku-4.5"  "$SKU_CAPACITY"
else
  echo "Skipping Claude. Add it later in the portal if you want the comparison."
fi

# --- Application Insights for agent tracing. ---
echo "==> Setting up Application Insights for tracing"
# The log-analytics/app-insights commands live in the 'application-insights'
# CLI extension, which won't auto-install because it's preview. Add it quietly.
az extension add --name application-insights --allow-preview true --yes >/dev/null 2>&1 \
  || az extension add --name application-insights --yes >/dev/null 2>&1 || true
WORKSPACE_NAME="log-${ACCOUNT_NAME}"
APPINSIGHTS_NAME="appi-${ACCOUNT_NAME}"

retry az monitor log-analytics workspace create \
  --resource-group "$RESOURCE_GROUP" --workspace-name "$WORKSPACE_NAME" \
  --location "$LOCATION" --output none
WORKSPACE_ID="$(az monitor log-analytics workspace show \
  --resource-group "$RESOURCE_GROUP" --workspace-name "$WORKSPACE_NAME" \
  --query id -o tsv)"

retry az monitor app-insights component create \
  --app "$APPINSIGHTS_NAME" --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" --kind web --workspace "$WORKSPACE_ID" --output none
APPINSIGHTS_ID="$(az monitor app-insights component show \
  --app "$APPINSIGHTS_NAME" --resource-group "$RESOURCE_GROUP" \
  --query id -o tsv)"

echo "==> Granting tracing roles"
# Project identity publishes traces; you read them in the Foundry Traces tab.
az role assignment create --assignee-object-id "$PROJECT_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal --role "Monitoring Metrics Publisher" \
  --scope "$APPINSIGHTS_ID" --output none 2>/dev/null || echo "    (publisher already assigned)"
# Project identity also READS traces for the code-free server-side path; without
# this the portal shows "Setup incomplete: assign Monitoring Reader" in Traces.
az role assignment create --assignee-object-id "$PROJECT_PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal --role "Monitoring Reader" \
  --scope "$APPINSIGHTS_ID" --output none 2>/dev/null || echo "    (reader already assigned to the project)"
az role assignment create --assignee-object-id "$USER_PRINCIPAL_ID" \
  --assignee-principal-type User --role "Log Analytics Reader" \
  --scope "$APPINSIGHTS_ID" --output none 2>/dev/null || echo "    (reader already assigned)"

echo "==> Application Insights ready for tracing"
# The az CLI can't yet connect App Insights with Project Managed Identity auth
# (the code-free server-side path). We'll connect it in the portal later, in the
# build-the-agent lab, so tracing is introduced where it's first used.
echo "    Created '$APPINSIGHTS_NAME' with the roles tracing needs."
echo "    You'll turn tracing on when you build the agent — see the lab steps."

# --- Write ../src/.env from what we just created. ---
echo
exec "$SCRIPT_DIR/setenv.sh" "$RESOURCE_GROUP"
