# Foundry IQ knowledge base

Module 1.3 gives the Sparkles agent a second MCP tool: a Foundry IQ knowledge
base holding the shop's policies (hours, delivery, returns, allergens,
loyalty program, bulk-order rules). Foundry IQ is the managed knowledge
layer in Microsoft Foundry, built on Azure AI Search, and every knowledge
base exposes an MCP endpoint. The agent only needs that endpoint and a key.

Who runs the steps below:

- **Skillable workshop:** instructors, once, before the event. Attendees get
  the endpoint and a query key in their seat's `.env`.
- **On your own:** you, as step 4 of [SETUP.md](../standalone/SETUP.md).

Derived in part from Shilpa Jain's Foundry IQ sample; see
[THIRD-PARTY-NOTICES.md](../THIRD-PARTY-NOTICES.md).

## Retrieval settings

The knowledge base is created with retrieval reasoning effort `minimal` and
output mode `extractiveData`. It returns matching passages only, and Claude
does the query planning and answer synthesis in the agent. Those two steps
are otherwise performed by the knowledge base itself, which needs its own
model deployment in the project.

Leaving the effort unset is not the same thing: the service then defaults to
`low`, which plans queries with its own model. The index is text only (no
vectorizer), so retrieval makes no embedding calls either. The script asserts
both settings took; if an assertion fails, the SDK is older than 12.1.0b2
(see `requirements.txt`).

## 1. Create an Azure AI Search service

The Free tier is enough: it supports knowledge bases (3 per service) and
semantic ranking with a monthly free allowance, and each subscription gets
one Free service. Basic is only needed for managed identity. On Free,
knowledge retrieval and semantic ranker are offered only in some regions
(East US, West Europe, and Sweden Central among them); check Azure AI Search
region support before you pick one.

**Choose two names.** Edit these two lines, then run them. Everything below
uses them, so keep the same terminal window open.

```
RG=my-sparkles-rg          # resource group: any name you like
SEARCH=my-sparkles-search  # search service: globally unique, lowercase letters, digits, dashes
```

Then paste the rest unchanged:

```
az group create -n $RG -l eastus
az search service create -n $SEARCH -g $RG -l eastus --sku free \
  --auth-options aadOrApiKey --aad-auth-failure-mode http401WithBearerChallenge
```

If your subscription requires an `owner` tag on resource groups, add
`--tags owner=$USER` to the first command. If the second fails with
`InsufficientResourcesAvailable`, the region is out of capacity; try another
region from the list.

## 2. Build the knowledge base

```
pip install -r foundry-iq/requirements.txt
AZURE_SEARCH_ENDPOINT="https://$SEARCH.search.windows.net" \
AZURE_SEARCH_ADMIN_KEY="$(az search admin-key show --service-name $SEARCH -g $RG --query primaryKey -o tsv)" \
  python foundry-iq/ingest_foundry_iq.py
```

The admin key is passed to this one command and not saved anywhere. (The
script also reads both values from `.env`; with no admin key it signs in
with `az login`, which needs the Search Service Contributor and Search Index
Data Contributor roles on the service.)

It prints the MCP endpoint URL at the end. The knowledge base also appears in
the Foundry portal under Build, then Knowledge. The MCP URL's `api-version`
must be `2026-08-01-preview`, the same version the script creates the
knowledge base with; the agent code uses that version.

`docs/cupcake-store-info.md` is the source document. Modules 1.5 and 1.6
depend on three facts in it: the facility processes tree nuts, bulk orders of
25 or more need 72 hours notice, and bulk orders carry a 50 percent deposit.
Keep those if you edit it.

## 3. Create a query key

The agent connects with a read-only query key, never the admin key:

```
az search query-key create --name sparkles-agent --service-name $SEARCH -g $RG --query key -o tsv
```

If you have opened a new terminal since step 1, set `RG` and `SEARCH` again
first.

Put it in `.env` with the endpoint (in a workshop, in the Skillable image
`.env`):

```
AZURE_SEARCH_ENDPOINT="https://<service>.search.windows.net"
AZURE_SEARCH_QUERY_KEY="<query key>"
KNOWLEDGE_BASE_NAME="cupcake-store-kb"
```

Never put the admin key in an attendee image, and never commit a key.

## 4. Verify

From the repo root, after `pip install -r requirements.txt`:

```
python foundry-iq/verify_knowledge_base.py
```

It builds the Module 1.3 agent with only the knowledge base (no Cupcake
Store server), asks the four policy questions from Module 1.3, and checks
that each answer used the knowledge base and contains the required facts:
$6.99 delivery and free over $50; a 48-hour window with a photo for damaged
orders; 72 hours notice and a 50 percent deposit for 25 or more. Expect
`Result: 4/4 questions passed`. Add `--answers` to read the replies.
