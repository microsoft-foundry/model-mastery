# Sparkles kiosk builder, hosted in Foundry

The manual loop in `sparkles-loop/` calls Claude once per step, and Python
does the rest: it saves the file, runs the checks, and decides whether to
try again. This folder is the same job done by one agent built with the
Claude Agent SDK.

Lab 2, Module 2.2 runs the agent on your machine, which is step 1 below.
Steps 2 to 6 run the same agent as a Foundry hosted agent. They are the
take-home: allow about 30 minutes, most of it waiting for the image to build
and for two permissions to take effect.

You need the Azure CLI signed in, a container registry, and the right to
assign roles in your subscription. The commands in steps 2 to 5 are written
for bash, so they run as they are on a Mac, on Linux, and in a Codespace. On
Windows, run them in a Codespace.

| In the manual loop | Here |
|---|---|
| `generator.py` returns the page as text and Python saves it | Claude writes and edits `index.html` with file tools |
| `run_loop.py` calls `checks.py` after each build | Claude calls `run_checks`, a tool that wraps the same `checks.py` |
| A Python `for` loop, up to `MAX_SPRINTS` | The Claude Agent SDK's own loop, up to `SPARKLES_MAX_TURNS` |
| You run it on your machine | Foundry runs it; you send a task and read the result |

What keeps it in bounds:

- **One file.** A hook refuses any read or write that is not `index.html` in
  the agent's working folder.
- **A fixed tool list.** Read, Write, Edit and `run_checks`. Anything else is
  refused without asking, because a hosted agent has no terminal to ask in.
- **Limits.** A turn limit and a spending limit per task. When one is reached
  the reply says so in `stopped_because`.
- **Evidence from outside the agent.** After the agent stops, `agent.py` runs
  the checks itself. The `passed` and `checks` fields in the reply come from
  that run, not from what the agent said.

## Files

| File | What it is |
|---|---|
| `agent.py` | The agent. Runs on your machine as well as in Foundry. |
| `tracing.py` | Records each model call and tool call as a span (Module 2.3). |
| `signin.py` | Signs the hosted agent in as itself, and retries if Foundry is not ready. |
| `main.py` | The web server Foundry talks to: `POST /invocations` on port 8088. |
| `Dockerfile`, `requirements.txt` | The container. |
| `deploy.py` | Creates the hosted agent from an image in your registry. |
| `invoke.py` | Sends a task to the hosted agent and saves the page. |
| `eval_hosted.py`, `grade_hosted.py` | A Foundry evaluation that calls the hosted agent and scores what comes back. |

## 1. Run it on your machine

From `sparkles-hosted/`, with the `.env` you already have. The Claude Agent SDK is
in the repo's `requirements.txt`, so there is nothing more to install.

```
python agent.py
```

Expect a line per tool call, then a JSON report with `"passed": true`, in
30 to 60 seconds. The page is saved to `workspace/index.html`.

```
python agent.py --keep "Make the order button pink"
```

`--keep` carries on with the page that is already there.

## 2. Build the image

The container needs `checks.py` and `common.py` from `sparkles-loop/`. Copy
them into a clean folder with the files from here, and build in your registry.
Building from a clean folder keeps your `.env` out of the image.

```
ACR=<your registry name>

mkdir -p /tmp/sparkles-build
cp agent.py main.py signin.py tracing.py requirements.txt Dockerfile \
   ../sparkles-loop/checks.py ../sparkles-loop/common.py /tmp/sparkles-build/

az acr build -r $ACR -t sparkles-hosted:v1 --platform linux/amd64 /tmp/sparkles-build
```

## 3. Let the project pull the image

The Foundry project pulls the image with its own identity, which needs read
access to the registry.

```
RG=<resource group of your Foundry resource>
ACCOUNT=<Foundry resource name>
PROJECT=<Foundry project name>

PROJECT_IDENTITY=$(az rest --method get --query identity.principalId -o tsv --url \
  "https://management.azure.com/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$ACCOUNT/projects/$PROJECT?api-version=2025-06-01")

az role assignment create --role AcrPull \
  --assignee-object-id $PROJECT_IDENTITY --assignee-principal-type ServicePrincipal \
  --scope $(az acr show -n $ACR --query id -o tsv)
```

## 4. Deploy

```
python deploy.py $ACR.azurecr.io/sparkles-hosted:v1
```

It prints `Status: active` and the agent's identity. Copy the identity.

## 5. Let the agent call Claude

The agent has its own identity and no key. Until that identity has the
**Foundry User** role on the Foundry resource, every task fails after a few
minutes with `401 Principal does not have access to API/Operation`.

```
az role assignment create --role "Foundry User" \
  --assignee-object-id <agent identity> --assignee-principal-type ServicePrincipal \
  --scope $(az cognitiveservices account show -g $RG -n $ACCOUNT --query id -o tsv)
```

Wait five to eight minutes for the role to take effect.

## 6. Send it a task

```
python invoke.py "Build the kiosk page for the Sparkles cupcake shop"
```

The page is saved to `workspace/index.html`. To keep working on the same
page, pass the session the first call printed:

```
python invoke.py --session <session> "Make the order button pink"
```

## 7. Score it with a Foundry evaluation

Module 2.4 scored four runs that were saved in advance. Foundry can also call
the hosted agent itself and score what comes back:

```
python eval_hosted.py
```

It sends three tasks to the agent, scores each page with the checks from
`grade_hosted.py`, and prints a report URL. No model does the scoring.

## If something goes wrong

| What you see | Why | What to do |
|---|---|---|
| Every task fails after a few minutes with `401 Principal does not have access` | The agent's identity does not have the role yet | Do step 5, then wait up to eight minutes |
| The agent never becomes `active` | The project cannot pull the image | Do step 3, then deploy again |
| `"stopped_because": "error_max_turns"` | The agent reached its turn limit | Expected if you set a low limit. The reply still says what state the page is in |
| A step shows `did_not_run` | The file rule refused it | Expected for anything that is not `index.html` |
