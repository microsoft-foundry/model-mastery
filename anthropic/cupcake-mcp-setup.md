# Deploying the Cupcake MCP server to Azure

Reusable runbook for standing up the Cupcake Store MCP server for a workshop.

Source: [GlobalAICommunity/cupcake-mcp](https://github.com/GlobalAICommunity/cupcake-mcp) — Henk Boelman, MIT.
FastAPI + Azure Table Storage, MCP mounted at `/mcp/`.

**This is not a Foundry resource.** It's a plain Container App. The Foundry
project only ever sees it as a URL in `CUPCAKE_MCP_URL`.

Budget 20-30 minutes; most of that is provisioning and build time.

---

## Stage 0 — Prerequisites

Azure CLI, Git, and a subscription you can create resources in.

```
az login
az account show --output table
az account set --subscription "<subscription name or id>"   # if the wrong one
az extension add --name containerapp --upgrade
```

Register the resource providers. **Do this before anything else** — each one
fails the relevant create step if missing, and registration takes a few minutes:

```
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.ContainerRegistry
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
```

Check progress with `az provider show -n Microsoft.Storage --query registrationState -o tsv`
(want `Registered`).

---

## Stage 1 — Pick names

| Thing | Rule | Example |
|---|---|---|
| Region | Near the attendees | `uksouth` / `japaneast` |
| Resource group | Any | `rg-cupcake-mcp` |
| ACR | **Globally unique, alphanumeric only, no hyphens** | `crcupcake01` |
| Storage account | **Globally unique, lowercase alphanumeric, 3–24 chars** | `stcupcake01` |
| Container Apps env | Any | `cae-cupcake-mcp` |
| Container app | Any | `ca-cupcake-mcp` |

Name conflicts on the two globally-unique ones are the usual snag — add digits.

---

## Stage 2 — Get the code

```
git clone https://github.com/GlobalAICommunity/cupcake-mcp
cd cupcake-mcp
```

Build context only. Nothing runs locally; Azure does the build.

---

## Stage 3 — Resource group

```
az group create -n rg-cupcake-mcp -l uksouth
```

---

## Stage 4 — Storage account

```
az storage account create \
  -g rg-cupcake-mcp -n stcupcake01 \
  -l uksouth --sku Standard_LRS --kind StorageV2
```

Get the connection string, needed in Stage 7:

```
az storage account show-connection-string \
  -g rg-cupcake-mcp -n stcupcake01 --query connectionString -o tsv
```

**Holds all store config** — flavours, prices, stock, orders, admin password.
Keep it even if the app is torn down.

---

## Stage 5 — Registry and image build

```
az acr create -g rg-cupcake-mcp -n crcupcake01 --sku Basic --admin-enabled true
az acr build -r crcupcake01 -t cupcake-mcp:latest .
```

Run the build from inside `cupcake-mcp/`. Builds in Azure, no local Docker.
Wait for `Run ID ... succeeded`.

---

## Stage 6 — Container Apps environment

```
az containerapp env create \
  -g rg-cupcake-mcp -n cae-cupcake-mcp \
  -l uksouth --logs-destination none
```

This one takes the longest.

---

## Stage 7 — The app

Set the three secrets as shell variables first. Same terminal window as the
next command — they don't survive a new shell.

```
STORAGE_CONN=$(az storage account show-connection-string \
  -g rg-cupcake-mcp -n stcupcake01 --query connectionString -o tsv)

SESSION_SECRET=$(openssl rand -base64 32)

ACR_PASSWORD=$(az acr credential show -n crcupcake01 \
  --query "passwords[0].value" -o tsv)
```

`SESSION_SECRET` is invented, not looked up — any random string. You never use
it again. Check all three are populated before continuing:

```
echo "storage: ${#STORAGE_CONN}  session: ${#SESSION_SECRET}  acr: ${#ACR_PASSWORD}"
```

Roughly 180 / 44 / 50. A zero means that command returned nothing and the
create below will fail unhelpfully.

Then paste this as-is — no placeholders to fill:

```
az containerapp create \
  -g rg-cupcake-mcp -n ca-cupcake-mcp \
  --environment cae-cupcake-mcp \
  --image crcupcake01.azurecr.io/cupcake-mcp:latest \
  --registry-server crcupcake01.azurecr.io \
  --registry-username crcupcake01 \
  --registry-password "$ACR_PASSWORD" \
  --target-port 8000 --ingress external \
  --secrets storage-conn="$STORAGE_CONN" session-secret="$SESSION_SECRET" \
  --env-vars AZURE_STORAGE_CONNECTION_STRING=secretref:storage-conn \
             SESSION_SECRET=secretref:session-secret \
             SESSION_COOKIE_SECURE=true
```

`SESSION_COOKIE_SECURE=true` is required on HTTPS or the admin login cookie
won't stick.

---

## Stage 8 — URL and smoke test

```
az containerapp show -g rg-cupcake-mcp -n ca-cupcake-mcp \
  --query properties.configuration.ingress.fqdn -o tsv
```

| URL | What |
|---|---|
| `https://<fqdn>/dashboard` | Order queue + rotating voucher (project this) |
| `https://<fqdn>/admin` | Admin portal |
| `https://<fqdn>/mcp/` | Agent endpoint — **trailing slash required** |

Open `/dashboard` first. If it loads, app and storage are both healthy. Tables
are created and `admin`/`admin` seeded on first start.

---

## Stage 9 — Configure the store

Log in at `/admin` (`admin`/`admin`).

1. **Users → change the admin password.** First.
2. **Flavours → add every flavour** on the catering photo and in the Module 1.6 prompt.
3. **Every price to 4.00.**
4. **Hazelnut at stock 0** — zero-stock flavours are hidden from the agent, which is what makes it "sold out".
5. Any non-zero stock for the rest.

Skipping 3 or 4 makes Module 1.6 fail in a way that looks like a model problem.

---

## Stage 10 — Wire into the lab

In the workshop repo's root `.env`:

```
CUPCAKE_MCP_URL="https://<fqdn>/mcp/"
```

---

## Checking it's up

Quickest is to hit the endpoints:

```
FQDN=$(az containerapp show -g rg-cupcake-mcp -n ca-cupcake-mcp \
  --query properties.configuration.ingress.fqdn -o tsv)

for p in /dashboard /cupcakes /mcp/; do
  printf "%-12s %s\n" "$p" "$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://$FQDN$p)"
done
```

| Path | Healthy | Meaning |
|---|---|---|
| `/dashboard` | `200` | App and storage both working |
| `/cupcakes` | `200` | API serving |
| `/mcp/` | **`406`** | Correct. Streamable HTTP needs specific `Accept` headers, so a plain GET is "Not Acceptable". A `404` here is the bad sign. |

Azure's own view:

```
az containerapp show -g rg-cupcake-mcp -n ca-cupcake-mcp \
  --query "{running:properties.runningStatus, provisioning:properties.provisioningState}" -o table

az containerapp revision list -g rg-cupcake-mcp -n ca-cupcake-mcp \
  --query "[].{name:name, active:properties.active, replicas:properties.replicas, health:properties.healthState}" -o table
```

Want `Running` / `Succeeded`, and a revision that is `Active` and `Healthy`.

**Scale to zero is not "down".** Container Apps drops idle apps to zero
replicas and cold-starts on the next request — a few seconds' delay that reads
like an outage but isn't. `replicas: 0` with an `Active`, `Healthy` revision is
fine. Deactivated is the real off state (see below).

## Stage 11 — Security and shutting down

The MCP endpoint has no authentication by design. Don't leave it up between
events.

### What's exposed

| Surface | Risk |
|---|---|
| `list_cupcakes`, `/cupcakes`, `/dashboard` | Read-only, nothing sensitive |
| `register_customer` | Junk records — nuisance |
| `order_cupcake` | Voucher-gated, one per customer, stock-limited, throttled |
| `/docs` | Swagger UI, advertises the whole API |
| `/admin` | bcrypt + signed cookies |

Blast radius is small: no real data, and the storage connection string is a
Container App secret scoped to one storage account. Nothing reaches the
Foundry project. The realistic downside is **cost and nuisance** — Container
Apps scales on demand, so a hammered endpoint runs up a bill and pollutes the
dashboard you're demoing on.

### Lock to your own IP while testing

Solo dry run? Allowlist yourself. No code change, no fork.

```
MY_IP=$(curl -s ifconfig.me)

az containerapp ingress access-restriction set \
  -g rg-cupcake-mcp -n ca-cupcake-mcp \
  --rule-name allow-me --ip-address $MY_IP/32 --action Allow
```

One Allow rule means everything else is denied. Your IP changes with a network
or VPN switch — re-run it then. **Remove the rule before the workshop:**

```
az containerapp ingress access-restriction remove \
  -g rg-cupcake-mcp -n ca-cupcake-mcp --rule-name allow-me
```

### Turning it off

Store config lives in Table Storage, so the app is disposable.

**Use revision deactivate.** There is no `az containerapp stop` (checked on CLI
2.86.0). Deactivating the revision stops the replicas without touching ingress
config, so **the FQDN is preserved** — verified 2026-09-13: 404 while
deactivated, 200 on the same URL after activating.

```
REV=$(az containerapp revision list -g rg-cupcake-mcp -n ca-cupcake-mcp \
  --query "[0].name" -o tsv)

az containerapp revision deactivate -g rg-cupcake-mcp -n ca-cupcake-mcp --revision $REV   # off
az containerapp revision activate   -g rg-cupcake-mcp -n ca-cupcake-mcp --revision $REV   # on
```

Allow ~30s after activating before it serves again.

Heavier options:

| Command | Effect |
|---|---|
| `az containerapp ingress disable -g rg-cupcake-mcp -n ca-cupcake-mcp` | Unreachable. Throws away ingress config — `enable` needs `--type external --target-port 8000` restated. Not tested; no reason to use it over revision deactivate. |
| `az containerapp delete -g rg-cupcake-mcp -n ca-cupcake-mcp` | Gone; recreate with Stage 7 |
| `az group delete -n rg-cupcake-mcp` | Everything, including store config |

Between sessions: **Clear All Orders** in the admin portal — wipes orders,
leaves stock.

### Suggested rhythm

IP-restrict while testing → deactivate the revision overnight → delete the app
when the dry run is done, keeping the storage account so the next region starts
with the flavours already configured.

---

## Running in two regions

Environments and storage accounts can't be moved between regions — deploy a
second stack instead, it's just Stages 3–7 with different names.

- **Separate storage account per region.** Sharing one sends every Table
  Storage call across continents.
- **The FQDN differs**, so `CUPCAKE_MCP_URL` changes — including in the
  Skillable image if attendee `.env` files come from there.
- **Reconfigure the store** in the new region (Stage 9, ~10 min).

Latency matters because every tool call is a round trip from the attendee's
laptop, and the dashboard refreshes every 5s on the projector. Model calls go
to Foundry, not here — if the Foundry project is far away, that dominates.

---

## Gotchas

- `Microsoft.Storage` not registered → storage create fails. Stage 0.
- ACR name with hyphens → rejected. Alphanumeric only.
- `/mcp` without trailing slash → doesn't resolve. `main.py` mounts at `/mcp`
  over `http_app(path="/")`, so the trailing slash is required even though the
  source repo's URL table shows `/mcp`.
- `SESSION_COOKIE_SECURE=false` on HTTPS → admin login appears to succeed then
  bounces back to the login page.
