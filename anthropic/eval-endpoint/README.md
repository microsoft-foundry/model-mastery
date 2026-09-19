# Eval endpoint (Claude as judge for Module 2.4b)

**Allow about 20 minutes end to end**, most of it build and provisioning time
rather than typing: the image build takes 10 to 15 minutes, and the Container
Apps environment takes a few more. Start section 2 in its own terminal and
carry on with something else while it runs.

## What this is

A small web service that grades one agent response at a time. You deploy it,
and Foundry calls it.

Foundry can score a dataset with its own built-in evaluators, but those come
with their own judge model. To have **Claude** do the judging, Foundry needs an
HTTP endpoint it can call, and that is what this is. You register it as a
custom evaluator; Foundry then POSTs each row of your dataset to it, one at a
time, and records whatever comes back.

What happens on each call:

1. Foundry POSTs one row: the customer's query and the agent's response.
2. The service sends both to your Claude deployment with a rubric, together
   with a copy of the Sparkles store document (`cupcake-store-info.md`, the
   same text behind the Foundry IQ knowledge base).
3. Claude returns a score from 0 to 1 and one sentence of reasoning. Structured
   outputs guarantee it comes back parseable.
4. The service replies with `score`, `reason`, and `passed`, inside Foundry's
   30-second timeout.

The store document is why this beats a rules-based check: the judge can tell a
fluent answer that contradicts store policy from one that does not. An answer
that sounds helpful but quotes the wrong refund window scores 0.0.

Two pieces have to exist for Foundry to reach it: the **service** (step 2) and
a **project connection** holding its URL and key (step 3).

- **Skillable workshop:** instructors deploy it once before the event, and
  attendees register an evaluator against the pre-created connection.
- **On your own:** deploy your own copy with the steps below, or skip
  Module 2.4b. Step A of Module 2.4 (the code-based evaluator) does not need
  it.

## 1. Run and test locally

**Do this in a separate terminal.** The deploy in step 2 builds a container
image in the cloud and can take 10 to 15 minutes. Start it in its own terminal
window and carry on with the rest of the lab while it runs.

Everything here runs from the `eval-endpoint/` folder:

```
cd eval-endpoint          # from the repo root
pip install -r requirements.txt
uvicorn eval_endpoint:app --port 8000
```

It reads the `.env` at the repo root, so there is nothing else to fill in.

Leave that running and open a second terminal for the test:

```
curl -X POST localhost:8000/evaluate -H 'Content-Type: application/json' -d \
 '{"schema_version":"0.0.1","evaluator_name":"t","evaluator_version":"1",
   "evaluation_level":"turn","data":{"item":{"query":"two chocolate please",
   "response":"Two chocolate cupcakes, order 17, ready in five minutes."}}}'
```

Expected: `{"schema_version":"0.0.1","score":...,"reason":"...","status":"Completed","passed":true,...}`
in well under 30 seconds.

## 2. Deploy to Azure Container Apps

Run these from `eval-endpoint/`: the build uploads the folder you are standing
in.

Four steps: create a registry, build the image into it, create a Container
Apps environment, then create the app pointing at that image.

> **Why not `az containerapp up`?** It does all four in one command, and when
> it works it is quicker. On some CLI versions its build step fails with
> `AttributeError: 'NoneType' object has no attribute 'linux'` after creating
> half the resources, which leaves a mess to clean up. The steps below are what
> `up` does anyway.

**Fill in the first three**, then run all five lines:

```
RG=my-sparkles-rg            # resource group: any name you like
REGION=eastus                # any region you can deploy Container Apps in
ACR=mysparklesacr01          # registry: globally unique, letters and digits only
EVAL_SECRET=$(openssl rand -base64 24)
echo "$EVAL_SECRET"
```

`EVAL_SECRET` is a password protecting your endpoint, shared between it and
the Foundry connection that calls it. The line above generates one rather than
you inventing it. Copy what `echo` prints into `.env` as
`EVAL_ENDPOINT_API_KEY`; step 3 reads it from there.

Your `FOUNDRY_ENDPOINT`, `FOUNDRY_API_KEY` and `FOUNDRY_MODEL_DEPLOYMENT` are
read from your shell, not from `.env`, so load them first:

```
set -a; source ../.env; set +a
```

### Create the group and registry

If your subscription requires an `owner` tag on resource groups, add
`--tags owner=$USER` to the first line.

```
az group create -n $RG -l $REGION

az acr create -g $RG -n $ACR --sku Basic --admin-enabled true
```

### Build the image

This runs in Azure, so you do not need Docker. Takes a few minutes; wait for
`Run ID ... succeeded`.

```
az acr build -r $ACR -t eval-endpoint:latest .
```

### Create the environment and the app

The environment takes a few minutes on its own.

```
az containerapp env create -g $RG -n my-sparkles-env -l $REGION --logs-destination none

# Load .env again: the build above takes 10 minutes, and these have to be in
# the shell when the app is created.
set -a; source ../.env; set +a

# Stop here if any of them is empty, rather than deploying an endpoint that
# cannot reach Claude.
: "${FOUNDRY_ENDPOINT:?empty - run: set -a; source ../.env; set +a}"
: "${FOUNDRY_API_KEY:?empty - run: set -a; source ../.env; set +a}"
: "${FOUNDRY_MODEL_DEPLOYMENT:?empty - run: set -a; source ../.env; set +a}"

ACR_PASSWORD=$(az acr credential show -n $ACR --query "passwords[0].value" -o tsv)

az containerapp create \
  -g $RG -n mm-eval-endpoint \
  --environment my-sparkles-env \
  --image $ACR.azurecr.io/eval-endpoint:latest \
  --registry-server $ACR.azurecr.io \
  --registry-username $ACR \
  --registry-password "$ACR_PASSWORD" \
  --target-port 8000 --ingress external \
  --env-vars FOUNDRY_ENDPOINT="$FOUNDRY_ENDPOINT" FOUNDRY_API_KEY="$FOUNDRY_API_KEY" \
             FOUNDRY_MODEL_DEPLOYMENT="$FOUNDRY_MODEL_DEPLOYMENT" \
             EVAL_ENDPOINT_API_KEY="$EVAL_SECRET"
```

### Get the address and check it

`create` prints the app's address, but it scrolls past. Read it back:

```
FQDN=$(az containerapp show -g $RG -n mm-eval-endpoint \
  --query properties.configuration.ingress.fqdn -o tsv)

echo $FQDN
```

Put what it prints in `.env`, with `https://` in front and `/evaluate` on the
end:

```
EVAL_ENDPOINT_URL="https://<fqdn>/evaluate"
```

Both parts matter. Foundry POSTs to exactly this URL, and `/evaluate` is the
only path the service answers on.

Now check it is working:

```
curl https://$FQDN/health
```

Expect the model name back:

```
{"ok":true,"model":"claude-sonnet-5"}
```

> ### ✅ Got the model name?
>
> **You are done with step 2. Skip to step 3.**
>
> If it came back empty instead, see **Troubleshooting** at the end of
> this file.

---

## 3. Create the project connection

The service is running, but Foundry does not know it exists. A **connection**
is the record in your Foundry project holding the endpoint's URL and key, so an
evaluator can call it. `create_connection.py` creates one with a single ARM
request.

### Fill in six settings in `.env`

The same `.env` at the top of the repo you have been using all along. Do not
make a second one.

Nothing earlier in the labs fills these six in, and they are only used here.
Open `.env` and look for this block at the bottom:

```
# Module 2.4b only: creating the eval endpoint connection (eval-endpoint/README.md)
AZURE_SUBSCRIPTION_ID=""
AZURE_RESOURCE_GROUP=""
FOUNDRY_ACCOUNT_NAME=""
FOUNDRY_PROJECT_NAME=""
EVAL_ENDPOINT_URL=""
EVAL_ENDPOINT_API_KEY=""
```

If it is there, fill in the values. If your `.env` predates it, paste the block
at the end of the file rather than editing any existing line.

Where each value comes from. Run these and copy what they print:

```
# AZURE_SUBSCRIPTION_ID
az account show --query id -o tsv

# AZURE_RESOURCE_GROUP, FOUNDRY_ACCOUNT_NAME
# Your Foundry resource and the group it is in, not the eval endpoint's group
az cognitiveservices account list --query "[].{account:name, rg:resourceGroup}" -o table

# FOUNDRY_PROJECT_NAME
# The project inside that resource, listed in the Foundry portal

# EVAL_ENDPOINT_URL
echo "https://$(az containerapp show -g $RG -n mm-eval-endpoint \
  --query properties.configuration.ingress.fqdn -o tsv)/evaluate"

# EVAL_ENDPOINT_API_KEY
# The secret from step 2. If it is still in this terminal:
echo "$EVAL_SECRET"
```

**Lost the secret?** If `echo "$EVAL_SECRET"` prints nothing, the terminal has
been closed since step 2. It is not stored anywhere readable, so make a new one
and set it on the running app:

```
EVAL_SECRET=$(openssl rand -base64 24)
echo "$EVAL_SECRET"

az containerapp update -g $RG -n mm-eval-endpoint \
  --set-env-vars EVAL_ENDPOINT_API_KEY="$EVAL_SECRET"
```

Then use that value for `EVAL_ENDPOINT_API_KEY` in `.env`. The endpoint and the
connection only have to agree with each other, so replacing both is fine.

`AZURE_RESOURCE_GROUP` is the one people get wrong. `create_connection.py`
builds a path to your Foundry project:

```
/subscriptions/<id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>/projects/<project>
```

so it needs the group your Foundry resource lives in. Giving it the eval
endpoint's group returns a 404 that reads as though the script is broken.

The last two are already in your `.env` in another form:
`AZURE_AI_PROJECT_ENDPOINT` is
`https://<account>.services.ai.azure.com/api/projects/<project>`, so the
account and project names can be read straight off it. Or list them:

```
az cognitiveservices account list --query "[].{account:name, rg:resourceGroup}" -o table
```

### Create it

```
python create_connection.py
```

It signs in with your existing `az login`. Expect
`Created connection 'mm-eval-endpoint' -> https://<fqdn>/evaluate`.

The connection name comes from `EVAL_ENDPOINT_CONNECTION` in `.env`, which is
already set to `mm-eval-endpoint`. Module 2.4b looks it up by that name, so
leave it alone unless you change both.

## Notes

- `cupcake-store-info.md` here is a copy of `foundry-iq/docs/cupcake-store-info.md`.
  If you edit the store document, copy it here again before deploying; the
  judge grades policy claims against it.

- Custom evaluators are public preview. Re-run the curl test and one full
  cloud eval the week of the event.
- The 30-second timeout is per item. Keep the rubric short and max_tokens low.
- Every object in `GRADE_SCHEMA` sets `additionalProperties` to false; the
  structured outputs API requires it.
- `status` must be `Completed`, `Error`, or `Skipped`, capitalized. A local curl
  accepts anything, but Foundry marks every row as an error on lowercase.
- The curl test does not exercise the contract. Only a cloud eval run does.


## Troubleshooting

### Every row in the eval report says `Error`

Foundry could not get a usable answer out of the endpoint. It is not the judge
disagreeing: a judge that scores a row badly returns `0.0`, not an error. Check
`/health` first, then the key:

```
curl https://$FQDN/health
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://$FQDN/evaluate \
  -H 'Content-Type: application/json' -H "api-key: $EVAL_ENDPOINT_API_KEY" \
  -d '{"schema_version":"0.0.1","evaluator_name":"t","evaluator_version":"1",
       "evaluation_level":"turn","data":{"item":{"query":"hi","response":"hello"}}}'
```

- Empty `model` from `/health`: see below.
- `401` from the POST: the key in `.env` does not match the one on the
  container. Set both to the same value, using the update command below with
  `EVAL_ENDPOINT_API_KEY="$EVAL_ENDPOINT_API_KEY"`, then re-run
  `python create_connection.py` so the connection carries it too.
- `200`: the endpoint is fine and the problem is the connection. Check
  `EVAL_ENDPOINT_URL` ends in `/evaluate`.

### `/health` returns an empty model

**Only read this if `/health` gave you no model name:**

```
{"ok":true,"model":""}
```

The app is running, but your settings never reached it: the `FOUNDRY_*` values
were empty in your shell when you ran `create`. Nothing is broken, and you do
not need to redeploy. Load the values and push them into the running app:

```
set -a; source ../.env; set +a

az containerapp update -g $RG -n mm-eval-endpoint \
  --set-env-vars FOUNDRY_ENDPOINT="$FOUNDRY_ENDPOINT" \
                 FOUNDRY_API_KEY="$FOUNDRY_API_KEY" \
                 FOUNDRY_MODEL_DEPLOYMENT="$FOUNDRY_MODEL_DEPLOYMENT" \
                 EVAL_ENDPOINT_API_KEY="$EVAL_SECRET"
```

Wait a minute for the new revision, then check `/health` again.
