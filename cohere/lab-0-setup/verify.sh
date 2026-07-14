#!/usr/bin/env bash
set -euo pipefail

# Lab 0 verification script.
# Confirms the four expected deployments exist on the Foundry account, checks
# that their catalog models are visible, and sends one small inference request to
# each deployment so learners know Lab 1 and Lab 2 can start.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Run ./setup-env.sh first." >&2
  exit 1
fi

# Export every key from .env so curl payloads and Azure CLI queries see the same values as the notebooks.
# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION:-2024-10-21}"
AZURE_INFERENCE_API_VERSION="${AZURE_INFERENCE_API_VERSION:-2024-05-01-preview}"
FAILURES=0

pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; FAILURES=$((FAILURES + 1)); }

require_env() {
  local key="$1"
  if [[ -z "${!key:-}" ]]; then
    fail "Missing $key in ../.env"
  fi
}

for key in AZURE_RESOURCE_GROUP FOUNDRY_ACCOUNT_NAME AZURE_AI_ENDPOINT FOUNDRY_PROJECT_ENDPOINT COMMAND_A_DEPLOYMENT EMBED_V4_DEPLOYMENT RERANK_DEPLOYMENT OPENAI_EMBED_DEPLOYMENT; do
  require_env "$key"
done

if [[ "$FAILURES" -gt 0 ]]; then
  exit 1
fi

# Verification uses the account key for simple REST probes; notebooks use Entra credentials.
ACCOUNT_KEY="$(az cognitiveservices account keys list \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$FOUNDRY_ACCOUNT_NAME" \
  --query key1 \
  --output tsv)"

check_deployment() {
  local label="$1"
  # Deployment names are user-configurable, so validate the backing model instead of only the name.
  local deployment_name="$2"
  local model_name="$3"

  local actual_model
  actual_model="$(az cognitiveservices account deployment list \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$FOUNDRY_ACCOUNT_NAME" \
    --query "[?name=='${deployment_name}'].properties.model.name | [0]" \
    --output tsv)"

  if [[ "$actual_model" == "$model_name" ]]; then
    pass "$label deployment exists ($deployment_name -> $model_name)"
  else
    fail "$label deployment missing or points to '$actual_model' instead of '$model_name'"
  fi
}

check_model_catalog() {
  local label="$1"
  # Catalog visibility catches regional/model availability issues before a learner opens Lab 1.
  local model_name="$2"
  local found_model

  if found_model="$(az cognitiveservices account list-models \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$FOUNDRY_ACCOUNT_NAME" \
    --query "[?name=='${model_name}' || model.name=='${model_name}'] | [0].name" \
    --output tsv 2>/dev/null)" && [[ -n "$found_model" ]]; then
    pass "$label catalog lookup completed ($model_name)"
  else
    fail "$label catalog lookup failed ($model_name)"
  fi
}

post_json() {
  local label="$1"
  # A tiny inference call proves the deployment is callable, not merely provisioned.
  local url="$2"
  local body="$3"

  local response http_code
  if ! response="$(curl -sS \
    --request POST "$url" \
    --header "Content-Type: application/json" \
    --header "api-key: $ACCOUNT_KEY" \
    --data "$body" \
    --write-out $'\n%{http_code}')"; then
    fail "$label inference call failed before receiving an HTTP response"
    return
  fi

  http_code="${response##*$'\n'}"
  if [[ "$http_code" =~ ^2 ]]; then
    pass "$label inference returned HTTP $http_code"
  else
    fail "$label inference returned HTTP $http_code"
  fi
}

post_json_bearer() {
  local label="$1"
  # Project-scoped APIs require an Entra bearer token (no api-key support).
  local url="$2"
  local token="$3"
  local body="$4"
  local max_attempts="${5:-1}"

  local response http_code attempt
  for attempt in $(seq 1 "$max_attempts"); do
    if ! response="$(curl -sS \
      --request POST "$url" \
      --header "Content-Type: application/json" \
      --header "Authorization: Bearer $token" \
      --data "$body" \
      --write-out $'\n%{http_code}')"; then
      if [[ "$attempt" -lt "$max_attempts" ]]; then
        sleep 2
        continue
      fi
      fail "$label call failed before receiving an HTTP response"
      return
    fi
    http_code="${response##*$'\n'}"
    if [[ "$http_code" =~ ^2 ]]; then
      if [[ "$attempt" -gt 1 ]]; then
        pass "$label returned HTTP $http_code (succeeded on attempt $attempt/$max_attempts)"
      else
        pass "$label returned HTTP $http_code"
      fi
      return
    fi
    if [[ "$attempt" -lt "$max_attempts" ]]; then
      sleep 2
    fi
  done
  fail "$label returned HTTP $http_code after $max_attempts attempts (body: ${response%$'\n'*})"
}

check_endpoint_host() {
  local label="$1"
  local url="$2"
  local expected_suffix="$3"
  local host="${url#https://}"
  host="${host%%/*}"
  if [[ "$host" == *"$expected_suffix" ]]; then
    pass "$label host ends with $expected_suffix ($host)"
  else
    fail "$label host '$host' does not end with $expected_suffix — MAF/Responses calls will return 404"
  fi
}

check_deployment "OpenAI embeddings" "$OPENAI_EMBED_DEPLOYMENT" "text-embedding-3-small"
check_deployment "Command A" "$COMMAND_A_DEPLOYMENT" "cohere-command-a"
check_deployment "Embed v4" "$EMBED_V4_DEPLOYMENT" "embed-v-4-0"
check_deployment "Rerank v4" "$RERANK_DEPLOYMENT" "Cohere-rerank-v4.0-pro"

check_model_catalog "OpenAI embeddings" "text-embedding-3-small"
check_model_catalog "Command A" "cohere-command-a"
check_model_catalog "Embed v4" "embed-v-4-0"
check_model_catalog "Rerank v4" "Cohere-rerank-v4.0-pro"

# Normalize away a trailing slash so the endpoint concatenation below is predictable.
BASE_ENDPOINT="${AZURE_AI_ENDPOINT%/}"

post_json \
  "OpenAI embeddings" \
  "$BASE_ENDPOINT/openai/deployments/$OPENAI_EMBED_DEPLOYMENT/embeddings?api-version=$AZURE_OPENAI_API_VERSION" \
  '{"input":"travel policy for hotels"}'

post_json \
  "Command A chat" \
  "$BASE_ENDPOINT/providers/cohere/v2/chat" \
  "{\"model\":\"$COMMAND_A_DEPLOYMENT\",\"messages\":[{\"role\":\"user\",\"content\":\"Say hello in three words.\"}],\"max_tokens\":16}"

post_json \
  "Embed v4" \
  "$BASE_ENDPOINT/providers/cohere/v2/embed" \
  "{\"model\":\"$EMBED_V4_DEPLOYMENT\",\"texts\":[\"hotel near the airport\"],\"input_type\":\"search_document\",\"embedding_types\":[\"float\"]}"

post_json \
  "Rerank v4" \
  "$BASE_ENDPOINT/providers/cohere/v2/rerank" \
  "{\"model\":\"$RERANK_DEPLOYMENT\",\"query\":\"quiet hotel for business travel\",\"documents\":[\"airport hotel with meeting rooms\",\"beach resort with nightlife\"],\"top_n\":2}"

# ---------------------------------------------------------------------------
# MAF chat client probe (account-level /openai/v1)
#
# Lab 1's make_chat_client uses MAF's OpenAIChatClient with the Foundry
# account-level endpoint: AZURE_AI_ENDPOINT + "/openai/v1". That path serves
# both the chat completions and responses APIs and is the same pattern shown
# on the Foundry model card. We deliberately do NOT probe the project-scoped
# path (.../api/projects/<p>/openai/v1) because that route can return
# "Project not found" for many minutes after a freshly provisioned project,
# and even after propagation it returns intermittent 404s at the service
# layer. The lab avoids that path entirely.
# ---------------------------------------------------------------------------
if AI_TOKEN="$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken --output tsv 2>/dev/null)"; then
  post_json_bearer \
    "Command A via MAF OpenAIChatClient path (Responses API)" \
    "$BASE_ENDPOINT/openai/v1/responses" \
    "$AI_TOKEN" \
    "{\"model\":\"$COMMAND_A_DEPLOYMENT\",\"input\":\"Say hello in three words.\",\"max_output_tokens\":16}" \
    3
  post_json_bearer \
    "Command A via /openai/v1/chat/completions" \
    "$BASE_ENDPOINT/openai/v1/chat/completions" \
    "$AI_TOKEN" \
    "{\"model\":\"$COMMAND_A_DEPLOYMENT\",\"messages\":[{\"role\":\"user\",\"content\":\"Say hello in three words.\"}],\"max_tokens\":16}" \
    3
else
  fail "Could not acquire token for account-level /openai/v1 probe"
fi

if [[ "$FAILURES" -gt 0 ]]; then
  echo
  echo "Verification completed with $FAILURES failure(s)."
  exit 1
fi

echo
echo "All Lab 0 checks passed. You are ready for Lab 1."
