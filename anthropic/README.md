# Claude + Microsoft Foundry Hands-On Workshop (Model Mastery)

Two 90-minute hands-on labs for the joint Anthropic + Microsoft Model Mastery
workshop. Attendees build the Sparkles cupcake shop agent on Claude in
Microsoft Foundry in the morning (tools, a Foundry IQ knowledge base, vision,
structured outputs), then make it run unattended in the afternoon: a
self-verifying build loop, web search and tool search, tracing, and
evaluations judged by Claude.

Built on earlier work by Henk Boelman and Shilpa Jain — see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## Two ways to take the labs

| | Skillable workshop | On your own |
| --- | --- | --- |
| Guide | `skillable/lab1/`, `skillable/lab2/` (one page per module) | `standalone/lab1.md`, `standalone/lab2.md` |
| Setup | Done for you; your seat's `.env` is pre-filled | [SETUP.md](standalone/SETUP.md), about 30 minutes |
| Foundry project and knowledge base | The workshop's | Your own |
| Cupcake Store server | Shared | The shared address, or deploy your own ([cupcake-mcp-setup.md](cupcake-mcp-setup.md), 20 to 30 min) |
| Eval endpoint (Module 2.4b) | Deployed by instructors | Deploy your own, or skip Step B |
| Instructor notes | `instructor/` | Not needed |

## Repo layout

| Path | What it is |
| --- | --- |
| `standalone/` | Everything for taking the labs on your own: `SETUP.md`, `lab1.md`, `lab2.md`, and `images/` |
| `skillable/` | The lab pages for the Skillable import, one per module, plus its own copy of `images/` |
| `sparkles-agent/` | Lab 1 working folder. Attendees edit `agent.py`; `snapshots/` holds the completed file after each module for catch-up |
| `sparkles-loop/` | Lab 2 planner / generator / evaluator loop with the seeded buggy kiosk and static checks |
| `sparkles-evals/` | Module 2.4: evaluator registration and cloud eval run scripts |
| `eval-endpoint/` | The Claude-as-judge eval endpoint service for Module 2.4b (instructors deploy it once per workshop; on your own, optional) |
| `foundry-iq/` | Module 1.3: the store document, the ingest script that builds the Foundry IQ knowledge base, and a script that verifies it (run once per workshop, or by you in SETUP.md) |
| `cupcake-mcp-setup.md` | Runbook for deploying the Cupcake Store MCP server to Azure: resources, deploy, store config, and how to turn it off |
| `instructor/` | Instructor notes. Ships with neither zip |

## Setup (baked into the Skillable image)

On your own machine, follow [SETUP.md](standalone/SETUP.md) instead.

Python 3.10+, then:

```
pip install -r requirements.txt
cp .env.example .env   # fill in per-seat values
```

The labs read everything from `.env`. No URLs or deployment names are
hardcoded in the code, so pointing the labs at a new Foundry resource or a
new Cupcake Store MCP deployment is a `.env` change only.

## Azure resources expected

- The Foundry project with the two Claude deployments below
- The Cupcake Store MCP server (Container Apps)
- An Azure AI Search service holding the Foundry IQ knowledge base (see `foundry-iq/`)
- The eval endpoint (Container Apps) and its project connection (see `eval-endpoint/`)
- Application Insights connected to the project

## Model deployments expected

- A Sonnet deployment (default agent model, `FOUNDRY_MODEL_DEPLOYMENT`)
- A Haiku deployment (tiering comparison and the loop generator, `FOUNDRY_HAIKU_DEPLOYMENT`)

## Version pinning (important)

Claude on Azure hosted currently only supports specific tool versions. This
repo pins the versions it is tested on. A version that does not exist returns
HTTP 400 listing the valid ones:

- Web search: `web_search_20250305`
- Tool search: `tool_search_tool_bm25_20251119`, and its name must be `tool_search_tool_bm25`
- Structured outputs: `output_config.format` with `json_schema`, and every
  object in a schema must set `"additionalProperties": false`

## Placeholders to fill before the event

1. `sparkles-agent/images/catering-order.jpg`: the handwritten catering
   order photo (see `instructor/instructor-notes.md` for what it must contain).
2. Screenshots in `standalone/images/` and `skillable/images/`: the two folders
   hold the same set, so replace a file in both.
3. `CUPCAKE_MCP_URL`, `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_QUERY_KEY`, and
   `EVAL_ENDPOINT_CONNECTION` in the Skillable image `.env`.
4. The Cupcake Store MCP URL in `standalone/SETUP.md`, step 3, before the repo
   goes to people taking the labs on their own. Change the server's default
   `admin` password first; its dashboard needs no sign-in.

## Acknowledgements

Built on the Code with Claude Foundry workshop by Henk Boelman, and on Shilpa
Jain's Foundry IQ sample. Both are used under the MIT License; see
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) for what is derived from
which.
