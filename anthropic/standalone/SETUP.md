# Set up on your own machine

Use this guide if you are taking the labs on your own, not from a Skillable
workshop seat. In a workshop all of this is done for you and your `.env` is
pre-filled; skip this file. Plan on about 30 minutes, most of it
provisioning time rather than typing.

Then follow `lab1.md` and `lab2.md` in this folder. Two things to know:

- **Your cupcakes are virtual.** Orders show on the dashboard; nothing is baked.
- **Module 2.4 Step B** needs your own eval endpoint (step 5), or skip it.

## What you need

- An Azure subscription where you can create resources, and the
  [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) signed in (`az login`)
- Python 3.10 or later
- VS Code (or any editor) and a terminal

## 1. Get the code

```
git clone <this repo>
cd model-mastery/anthropic
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r foundry-iq/requirements.txt
cp .env.example .env
```

Every script reads the `.env` in `anthropic/`.

> Once this workshop lands in
> [microsoft-foundry/model-mastery](https://github.com/microsoft-foundry/model-mastery),
> clone that repository instead; the path below it is the same.

## 2. Claude in Foundry

1. At [ai.azure.com](https://ai.azure.com), create a Foundry project (or open
   one you have).
2. Deploy two Claude models with Global Standard and keep the default
   deployment names: `claude-sonnet-5` and `claude-haiku-4-5`.
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
a Free-tier Azure AI Search service, build the knowledge base, and create a
query key. Your `.env` then has:

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
