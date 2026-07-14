#!/usr/bin/env bash
set -euo pipefail

# Lab 0 environment setup script.
# Reads a provisioned resource group and writes concrete values into ../.env so
# notebooks can authenticate and call Foundry without manual copy/paste.

# Resolve workshop-relative paths so .env is written beside sample.env, not in the caller's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSHOP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SAMPLE_ENV="$WORKSHOP_DIR/sample.env"
TARGET_ENV="$WORKSHOP_DIR/.env"
FORCE=0
RESOURCE_GROUP="${RESOURCE_GROUP:-}"

usage() {
  cat <<USAGE
Usage: ./setup-env.sh [--force] [RESOURCE_GROUP]

Options:
  --force   Overwrite ../.env if it already exists.
USAGE
}

# Keep argument handling tiny: one optional --force flag plus the resource group name.
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -h|--help) usage; exit 0 ;;
    *) RESOURCE_GROUP="$arg" ;;
  esac
done

if [[ -z "$RESOURCE_GROUP" ]]; then
  read -r -p "Existing resource group name: " RESOURCE_GROUP
fi

if [[ -z "$RESOURCE_GROUP" ]]; then
  echo "ERROR: RESOURCE_GROUP is required." >&2
  exit 1
fi

# Refuse to overwrite hand-edited credentials unless the learner opts in.
if [[ -e "$TARGET_ENV" && "$FORCE" -ne 1 ]]; then
  echo "ERROR: $TARGET_ENV already exists. Re-run with --force to replace it." >&2
  exit 1
fi

if ! command -v az >/dev/null 2>&1; then
  echo "ERROR: Azure CLI (az) is required. Install it, then run az login." >&2
  exit 1
fi

# Escape values for sed replacement with a | delimiter.
escape_sed_replacement() {
  printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'
}

set_env_value() {
  local key="$1"
  local value="$2"
  local escaped
  escaped="$(escape_sed_replacement "$value")"
  sed -i "s|^${key}=.*|${key}=${escaped}|" "$TARGET_ENV"
}

require_value() {
  local name="$1"
  local value="$2"
  if [[ -z "$value" ]]; then
    echo "ERROR: Could not resolve $name in resource group $RESOURCE_GROUP." >&2
    exit 1
  fi
}

lookup_deployment_by_model() {
  local model_name="$1"
  # Lab notebooks use deployment names, so derive them from the catalog model names provisioned in Bicep.
  az cognitiveservices account deployment list \
    --resource-group "$RESOURCE_GROUP" \
    --name "$FOUNDRY_ACCOUNT_NAME" \
    --query "[?properties.model.name=='${model_name}'].name | [0]" \
    --output tsv
}

# Capture identity and resource metadata once, then stamp the values into the notebook .env file.
SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
TENANT_ID="$(az account show --query tenantId -o tsv)"

FOUNDRY_ACCOUNT_NAME="$(az cognitiveservices account list \
  --resource-group "$RESOURCE_GROUP" \
  --query "[?kind=='AIServices'].name | [0]" \
  --output tsv)"
require_value "AIServices account" "$FOUNDRY_ACCOUNT_NAME"

AZURE_LOCATION="$(az cognitiveservices account show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FOUNDRY_ACCOUNT_NAME" \
  --query location \
  --output tsv)"

AZURE_AI_ENDPOINT="$(az cognitiveservices account show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FOUNDRY_ACCOUNT_NAME" \
  --query properties.endpoint \
  --output tsv)"
require_value "Foundry account endpoint" "$AZURE_AI_ENDPOINT"

# The AI Foundry API endpoint serves the OpenAI-compatible Responses API that MAF uses.
# The legacy cognitiveservices endpoint does NOT route model deployments correctly.
FOUNDRY_AI_ENDPOINT="$(az cognitiveservices account show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$FOUNDRY_ACCOUNT_NAME" \
  --query "properties.endpoints.\"AI Foundry API\"" \
  --output tsv)"
require_value "AI Foundry API endpoint" "$FOUNDRY_AI_ENDPOINT"

PROJECT_RESOURCE_NAME="$(az resource list \
  --resource-group "$RESOURCE_GROUP" \
  --resource-type "Microsoft.CognitiveServices/accounts/projects" \
  --query "[?contains(id, '/accounts/${FOUNDRY_ACCOUNT_NAME}/projects/')].name | [0]" \
  --output tsv)"
require_value "Foundry project" "$PROJECT_RESOURCE_NAME"
FOUNDRY_PROJECT_NAME="${PROJECT_RESOURCE_NAME##*/}"
FOUNDRY_PROJECT_ENDPOINT="${FOUNDRY_AI_ENDPOINT%/}/api/projects/${FOUNDRY_PROJECT_NAME}"

COMMAND_A_DEPLOYMENT="$(lookup_deployment_by_model "cohere-command-a")"
EMBED_V4_DEPLOYMENT="$(lookup_deployment_by_model "embed-v-4-0")"
RERANK_DEPLOYMENT="$(lookup_deployment_by_model "Cohere-rerank-v4.0-pro")"
OPENAI_EMBED_DEPLOYMENT="$(lookup_deployment_by_model "text-embedding-3-small")"
require_value "Command A deployment" "$COMMAND_A_DEPLOYMENT"
require_value "Embed v4 deployment" "$EMBED_V4_DEPLOYMENT"
require_value "Rerank deployment" "$RERANK_DEPLOYMENT"
require_value "OpenAI embedding deployment" "$OPENAI_EMBED_DEPLOYMENT"

# Cohere deployments provisioned at the default capacity 1 only allow 1 request per minute, which is
# too low for Lab 1 (each agent invocation does multiple internal tool-orchestration calls) and Lab 2
# (loops over corpora of documents). Idempotently bump each deployment to 100 (100 RPM / 100k TPM).
ensure_capacity() {
  local deployment="$1"; local model_name="$2"; local min_cap="$3"
  local current
  current="$(az cognitiveservices account deployment show \
    --name "$FOUNDRY_ACCOUNT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --deployment-name "$deployment" \
    --query "sku.capacity" -o tsv 2>/dev/null || echo 0)"
  if [ "${current:-0}" -lt "$min_cap" ]; then
    echo "Bumping $deployment capacity from ${current:-0} to $min_cap..."
    az cognitiveservices account deployment create \
      --name "$FOUNDRY_ACCOUNT_NAME" \
      --resource-group "$RESOURCE_GROUP" \
      --deployment-name "$deployment" \
      --model-name "$model_name" \
      --model-version 1 \
      --model-format Cohere \
      --sku-name GlobalStandard \
      --sku-capacity "$min_cap" \
      -o none
  fi
}
ensure_capacity "$COMMAND_A_DEPLOYMENT" "cohere-command-a"      100
ensure_capacity "$EMBED_V4_DEPLOYMENT"  "embed-v-4-0"           100
ensure_capacity "$RERANK_DEPLOYMENT"    "Cohere-rerank-v4.0-pro" 100

ACCOUNT_KEY="$(az cognitiveservices account keys list --resource-group "$RESOURCE_GROUP" --name "$FOUNDRY_ACCOUNT_NAME" --query key1 -o tsv)"
require_value "Foundry account key" "$ACCOUNT_KEY"
COHERE_BASE_URL="${AZURE_AI_ENDPOINT%/}/providers/cohere"
CHROMA_DB_PATH_DEFAULT="./chroma_db"

APP_INSIGHTS_NAME="$(az resource list \
  --resource-group "$RESOURCE_GROUP" \
  --resource-type "Microsoft.Insights/components" \
  --query "[0].name" \
  --output tsv)"
require_value "Application Insights component" "$APP_INSIGHTS_NAME"

APPLICATIONINSIGHTS_CONNECTION_STRING="$(az resource show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_INSIGHTS_NAME" \
  --resource-type "Microsoft.Insights/components" \
  --query properties.ConnectionString \
  --output tsv)"
require_value "Application Insights connection string" "$APPLICATIONINSIGHTS_CONNECTION_STRING"

# Ensure the Foundry project has an App Insights connection so server-side agent
# traces flow into the portal's Tracing/Monitoring tab. The notebook-side
# APPLICATIONINSIGHTS_CONNECTION_STRING only powers client-side OTel; the project
# connection is what wires the Foundry agent runtime to the same App Insights.
APP_INSIGHTS_RID="$(az resource show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_INSIGHTS_NAME" \
  --resource-type "Microsoft.Insights/components" \
  --query id --output tsv)"
PROJ_CONN_BASE="https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$FOUNDRY_ACCOUNT_NAME/projects/$FOUNDRY_PROJECT_NAME/connections"
EXISTING_APPI_CONN="$(az rest --method get \
  --url "$PROJ_CONN_BASE?api-version=2025-04-01-preview" \
  --query "value[?properties.category=='AppInsights']|[0].name" -o tsv 2>/dev/null || true)"
if [[ -z "$EXISTING_APPI_CONN" ]]; then
  APPI_CONN_BODY="$(mktemp)"
  jq -n \
    --arg target "$APP_INSIGHTS_RID" \
    --arg key "$APPLICATIONINSIGHTS_CONNECTION_STRING" \
    '{properties:{category:"AppInsights",target:$target,authType:"ApiKey",isSharedToAll:true,credentials:{key:$key},metadata:{ApiType:"Azure",ResourceId:$target}}}' \
    > "$APPI_CONN_BODY"
  az rest --method put \
    --url "$PROJ_CONN_BASE/appinsights-default?api-version=2025-04-01-preview" \
    --body @"$APPI_CONN_BODY" --output none
  rm -f "$APPI_CONN_BODY"
  echo "Created project App Insights connection: appinsights-default -> $APP_INSIGHTS_NAME"
else
  echo "Project App Insights connection already exists: $EXISTING_APPI_CONN"
fi

# Start from sample.env so heavily commented guidance is preserved while concrete values are inserted.
cp "$SAMPLE_ENV" "$TARGET_ENV"

set_env_value "AZURE_SUBSCRIPTION_ID" "$SUBSCRIPTION_ID"
set_env_value "AZURE_TENANT_ID" "$TENANT_ID"
set_env_value "AZURE_LOCATION" "$AZURE_LOCATION"
set_env_value "AZURE_RESOURCE_GROUP" "$RESOURCE_GROUP"
set_env_value "FOUNDRY_ACCOUNT_NAME" "$FOUNDRY_ACCOUNT_NAME"
set_env_value "FOUNDRY_PROJECT_NAME" "$FOUNDRY_PROJECT_NAME"
set_env_value "AZURE_AI_ENDPOINT" "$AZURE_AI_ENDPOINT"
set_env_value "FOUNDRY_PROJECT_ENDPOINT" "$FOUNDRY_PROJECT_ENDPOINT"
set_env_value "COMMAND_A_DEPLOYMENT" "$COMMAND_A_DEPLOYMENT"
set_env_value "EMBED_V4_DEPLOYMENT" "$EMBED_V4_DEPLOYMENT"
set_env_value "RERANK_DEPLOYMENT" "$RERANK_DEPLOYMENT"
set_env_value "OPENAI_EMBED_DEPLOYMENT" "$OPENAI_EMBED_DEPLOYMENT"
set_env_value "APPLICATIONINSIGHTS_CONNECTION_STRING" "$APPLICATIONINSIGHTS_CONNECTION_STRING"
set_env_value "EMBED_BASE_URL" "$COHERE_BASE_URL"
set_env_value "EMBED_API_KEY" "$ACCOUNT_KEY"
set_env_value "EMBED_MODEL" "$EMBED_V4_DEPLOYMENT"
set_env_value "RERANK_BASE_URL" "$COHERE_BASE_URL"
set_env_value "RERANK_API_KEY" "$ACCOUNT_KEY"
set_env_value "RERANK_MODEL" "$RERANK_DEPLOYMENT"
set_env_value "CHROMA_DB_PATH" "$CHROMA_DB_PATH_DEFAULT"

cat <<SUMMARY

.env populated at: $TARGET_ENV

Key                                Value
---                                -----
AZURE_SUBSCRIPTION_ID              $SUBSCRIPTION_ID
AZURE_TENANT_ID                    $TENANT_ID
AZURE_LOCATION                     $AZURE_LOCATION
AZURE_RESOURCE_GROUP               $RESOURCE_GROUP
FOUNDRY_ACCOUNT_NAME               $FOUNDRY_ACCOUNT_NAME
FOUNDRY_PROJECT_NAME               $FOUNDRY_PROJECT_NAME
AZURE_AI_ENDPOINT                  $AZURE_AI_ENDPOINT
FOUNDRY_PROJECT_ENDPOINT           $FOUNDRY_PROJECT_ENDPOINT
COMMAND_A_DEPLOYMENT               $COMMAND_A_DEPLOYMENT
EMBED_V4_DEPLOYMENT                $EMBED_V4_DEPLOYMENT
RERANK_DEPLOYMENT                  $RERANK_DEPLOYMENT
OPENAI_EMBED_DEPLOYMENT            $OPENAI_EMBED_DEPLOYMENT
APPLICATIONINSIGHTS_CONNECTION_STRING  [set]
EMBED_BASE_URL                     $COHERE_BASE_URL
EMBED_API_KEY                      [set]
EMBED_MODEL                        $EMBED_V4_DEPLOYMENT
RERANK_BASE_URL                    $COHERE_BASE_URL
RERANK_API_KEY                     [set]
RERANK_MODEL                       $RERANK_DEPLOYMENT
CHROMA_DB_PATH                     $CHROMA_DB_PATH_DEFAULT
SUMMARY
