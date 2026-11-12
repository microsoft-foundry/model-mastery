# Set up on your own

Use this guide if you are taking the labs on your own, not in a Skillable
workshop. In a workshop all of this is done for you and your `.env` is
pre-filled; skip this file. Plan on about 30 minutes, most of it
provisioning time rather than typing.

Then follow `lab1.md` and `lab2.md` in this folder. Two things to know:

- **Your cupcakes are virtual.** Orders show on the dashboard; nothing is baked.
- **Module 2.4 Step B** needs your own eval endpoint (step 5), or skip it.

## What you need

- An Azure subscription where you can create resources
- Either Python 3.10 or later, the
  [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli), and an
  editor on your own machine, **or** a GitHub account to use a Codespace

## Before you start: choose a region

Choose one Azure region now, and use it for everything this guide creates
with the Azure CLI: the Search service, Application Insights, and the
container apps. Pick the one nearest to you.

| Where you are | Use | Avoid |
| --- | --- | --- |
| US and Canada | `southcentralus`, `northcentralus`, `westcentralus`, `canadacentral` | `eastus`, `eastus2` and `westus`: they currently refuse new Search services |
| UK and Europe | `uksouth`, `westeurope`, `swedencentral`, `francecentral`, `switzerlandnorth`, `polandcentral` | `northeurope` and `germanywestcentral`, for the same reason |
| Japan, Korea, Taiwan | `japaneast`, `koreacentral` | `eastasia` and `southeastasia`: the knowledge base features are not on the Free tier there |
| Australia | `australiaeast` | |

**Why the list is short.** The knowledge base in step 4 runs on the Free tier
of Azure AI Search, and only some regions offer what it needs on Free.
Everything else this guide creates is offered almost everywhere, so Search
decides.

**Your Foundry project does not have to be in the same region.** Create it
wherever the Claude models are offered to you, and if you already have one,
keep it. The agent reaches Foundry, Search, and the Cupcake Store each by its
own address, so they can be in three different regions.

The later steps say "the region you chose". Keep a note of it.

> This list was checked against
> [Azure AI Search region support](https://learn.microsoft.com/azure/search/search-region-support)
> on 2026-09-17. Capacity changes. If creating the Search service fails with
> `InsufficientResourcesAvailable`, use the next region on your row.

## 1. Get the code

Pick one. The rest of this guide is the same either way.

### On your own machine

```
git clone <this repo>
cd model-mastery/anthropic
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows, in PowerShell, the same steps are:

```
git clone <this repo>
cd model-mastery\anthropic
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell refuses to run `Activate.ps1`, run
`Set-ExecutionPolicy -Scope Process RemoteSigned` and try again. It applies
to that window only.

Every script reads the `.env` in `anthropic/`. Run everything from the
`anthropic/` folder: the `requirements.txt` at the top of the repo is for
the other workshops, not this one.

> Once this workshop lands in
> [microsoft-foundry/model-mastery](https://github.com/microsoft-foundry/model-mastery),
> clone that repository instead; the path below it is the same.

### Or in a Codespace

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/amandaw-ant/model-mastery?ref=anthropic-workshop&devcontainer_path=.devcontainer%2Fanthropic%2Fdevcontainer.json)

The packages and `.env` are set up for you. When it opens, run:

```
cd anthropic
az login --use-device-code
```

## 2. Claude in Foundry

1. At [ai.azure.com](https://ai.azure.com), create a Foundry project (or open
   one you have).
2. Deploy two Claude models with Global Standard and keep the default
   deployment names: `claude-sonnet-5-5` and `claude-haiku-5-5`.
3. Open the Sonnet deployment's **Details** tab and copy **Endpoint** and
   **Key** into `.env`:

```
FOUNDRY_ENDPOINT="https://<resource>.services.ai.azure.com/anthropic"
FOUNDRY_API_KEY="<key>"
```

**NOTE:** The portal may show the endpoint with `/v1/messages` on the end. **Trim that
off** and keep everything up to and including `/anthropic`; the SDK appends
the rest. Leaving it on produces a 404 on the first call.

`FOUNDRY_MODEL_DEPLOYMENT` and `FOUNDRY_HAIKU_DEPLOYMENT` already match the
default names; change them only if you named the deployments differently.

## 3. The Cupcake Store server

**In a workshop**, everyone shares one hosted Cupcake Store MCP server and you
do not deploy anything: ask your instructor for the address.

**On your own**, run your own copy from
[GlobalAICommunity/cupcake-mcp](https://github.com/GlobalAICommunity/cupcake-mcp)
(Henk Boelman, MIT). [cupcake-mcp-setup.md](../cupcake-mcp-setup.md) is a
step-by-step runbook for deploying it to Azure Container Apps, including how to
configure the store afterwards and how to shut it down when you are done.
Allow 20 to 30 minutes, most of it provisioning and build time.

Either way, set the address in `.env`:

```
CUPCAKE_MCP_URL="<Cupcake Store MCP URL>"
```

Its order dashboard is the same address with `/dashboard` in place of
`/mcp/`. Keep it open in a browser tab: it shows your orders and the voucher
code the labs ask for, which rotates every few minutes. In a workshop that
dashboard is on screen in the room; the cupcakes you order on your own are
virtual.

## 4. The shop's knowledge base (Foundry IQ)

Follow sections 1 to 3 of [foundry-iq/README.md](../foundry-iq/README.md): create
a Free-tier Azure AI Search service in the region you chose, build the
knowledge base, and create a query key. Your `.env` then has:

```
AZURE_SEARCH_ENDPOINT="https://<service>.search.windows.net"
AZURE_SEARCH_QUERY_KEY="<query key>"
KNOWLEDGE_BASE_NAME="cupcake-store-kb"
```

Check it:

```
python foundry-iq/verify_knowledge_base.py
```

You should see `Result: 4/4 questions passed`.

## 5. Extra settings for Lab 2

You can do these when you reach Lab 2.

- **Module 2.3 (tracing).** Needs an Application Insights resource and its
  connection string in `APPLICATIONINSIGHTS_CONNECTION_STRING`. Creating a
  Foundry project usually makes one for you; Module 2.3 walks through finding
  it, or creating one if you have none.
- **Module 2.4 (evaluations).** Set `AZURE_AI_PROJECT_ENDPOINT` to your
  project endpoint from the project's overview page
  (`https://<resource>.services.ai.azure.com/api/projects/<project>`).
  Step A needs nothing else. Step B, where Claude is the judge, needs your
  own eval endpoint and project connection: follow
  [eval-endpoint/README.md](../eval-endpoint/README.md) and set
  `EVAL_ENDPOINT_CONNECTION` to the connection's name. If you skip that, skip
  Step B.

  **Allow about 20 minutes for that endpoint**, most of it the container build
  and deploy. Start it in a separate terminal and carry on with something else
  while it runs, or do it before you reach Lab 2.

## 6. Check you are ready

```
cd sparkles-agent
python agent.py
```

Type `Hello!` and you should get a friendly reply; type `exit` to stop. You
are ready for Module 1.0.

## When you are done

Delete what you created, for example `az group delete -n <rg>` for the
resource group holding the Search service (and the eval endpoint, if you
deployed it). A subscription gets only one Free Search service, so delete it
if you want to reuse the Free tier elsewhere.
