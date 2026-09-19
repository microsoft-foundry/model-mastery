# Instructor notes

## Two ways to run the day

Work out which one you are running before you prepare anything. The prep is
very different, and most of "Before the event" only applies to the first.

**Skillable.** Every attendee gets a prepared seat and the image already has
working values in it, so attendees never open SETUP.md. Everything in "Before
the event" has to be done before handover, because that is what those values
are.

If you want the room on something other than what the image is set to — your
own cupcake MCP server, your own search service — you cannot edit the image to
do it. You coach them through changing it live. See "Changing the Skillable
image".

**Standalone.** Attendees use their own Azure subscription and work through
SETUP.md themselves. You are not required to prepare anything.

In practice, prepare some of it anyway as a backup. A shared cupcake MCP server
and a shared knowledge base cost you little and cover the two things most
likely to go wrong on someone else's subscription: a deployment that fails, and
a region without Claude models or without quota. Someone who is stuck can point
at yours and keep moving rather than lose the morning.

Decide before the day whether you are offering that backup, and say so at the
start. Attendees who know there is a safety net will attempt their own setup;
attendees who do not know will either not try or will not ask when it breaks.

If the room is mixed, say at the start which instructions apply to whom. The
lab pages are the same either way; only setup differs.

## Two-minute intros (talk, then hands on)

**SETUP.md — standalone rooms only.** Skip this entirely on Skillable; the
seat is already set up. What they are building: a Foundry project, two model
deployments, a knowledge base, and an MCP server address. The one idea worth
saying out loud is that every lab reads its settings from a single `.env` at
the top of the repo, so everything they do here is filling in that one file.

Two things to say before they start, because both cost real time in the room.
`FOUNDRY_ENDPOINT` ends at `/anthropic` — the portal shows a longer URL and the
SDK appends the rest itself, and pasting the portal's version verbatim is the
most common way to fail the first call. And most of the half hour is provisioning
time rather than typing, so tell them to start the search service first and
carry on with the rest while it builds.

**1.0 — Meet your model.** Model versus deployment. The Playground is making
the same call your code makes.

**1.1 — Hello world agent.** Model, session and tools in one
object.

**1.2 — Tools and a personality.** MCP in one sentence: the server publishes
tools and prompts, and the agent only needs the URL. Point at the dashboard
screen before they order.

**1.3 — Knowledge with Foundry IQ.** The store server knows stock; the shop's
policies live in a document. Foundry IQ turns that document into an MCP
endpoint, so it is just a second tool server. Claude does the routing, and
nobody writes an if statement.

**1.4 — A receipt you can trust.** "You no longer parse JSON out of prose on
Foundry." Mention `additionalProperties: false` — it is the first error they
will hit on their own schemas.

**1.5 — Claude can see.** Nothing on the photo is machine-readable. Watch for
the correction, the allergy note, and whether the agent quotes the allergen
policy. The counter takes one cupcake per customer, so the agent places one
test order and hands the rest to the catering team with the rules from the
knowledge base. That is the right answer.

**1.6 — Model judgment and tiering.** Four problems hidden in a one-cupcake
order: one from the store's live data, three from the policy document. Plus one
behaviour to watch rather than count: does it apply the red velvet fallback?
Then the same code on Haiku.

**2.1 — The agent that checks its own work.** The agent that writes is not the
agent that judges, and the loop is only ever as good as that judge. Explain why
the first draft is seeded: a reliable FAIL beats a random one.

**2.2 — Fresh research and a bigger toolbox.** This morning the agent learned
what the shop knows; now it learns what the world knows. Pinned versions. Two
new capabilities, same loop shape.

**2.3 — See everything it did.** OpenTelemetry instruments your code, not the
model, so Foundry tracing works with Claude as-is. Say up front that traces lag
by a minute or two.

**2.4 — Evaluations, judged by Claude.** Built-in AI-assisted evaluators come
with their own judge model; custom evaluators are how you bring your own, and
today the judge is Claude. The wrong-refund row is the point: the rules pass
it, and the Claude judge with the policy document fails it.

## Setup on the day

**Skillable.** No setup slot. Ten minutes at the start: everyone opens their
seat, confirms the `.env` at the top of the repo has values in it, and runs one
command that proves the agent reaches Foundry. Do this before the first talk,
not after, so a bad seat surfaces while there is still time to move someone.

**Standalone.** Budget real time for this. SETUP.md says about 30 minutes, and
most of it is provisioning rather than typing. Front-load the long-running parts: get
the search service and any container deployment started before the first talk,
so they provision while you are talking rather than in silence afterwards.

Either way the check that matters is the same, and it is worth doing out loud:
one call to Foundry succeeds, and the MCP URL answers. Everything in Lab 1
depends on those two, and both fail in ways that look like a broken lab rather
than a broken setting.

## Before the event

**Running Skillable: all of it, and it has to be finished before handover.**
**Running standalone: none of it is required.** Pick the pieces you want as a
backup, and skip the rest — steps 1 and 2 are the two worth having.

`SETUP.md` covers all of this in detail, with the actual commands — it is the
attendee-facing version of the same work. Follow it where you need the steps;
what is below is the list of what has to be true at the end, plus the bits that
only matter when you are preparing for other people.

The image's `.env` goes at the top of the repo, not in `sparkles-agent/`. The
labs point attendees there.

1. Deploy the cupcake MCP server and the order dashboard from
   [GlobalAICommunity/cupcake-mcp](https://github.com/GlobalAICommunity/cupcake-mcp)
   (Henk Boelman, MIT). [cupcake-mcp-setup.md](../cupcake-mcp-setup.md) is a
   step-by-step runbook for this — Azure resources, the deploy, how to check it
   is up, how to turn it off between events. Put the URL in the Skillable image
   `.env` as `CUPCAKE_MCP_URL` (it ends in `/mcp/`). Then, in `/admin`:
   - Change the `admin` password first. The server seeds `admin`/`admin`.
   - Add every flavor the catering photo and the Module 1.6 prompt name.
   - Set every price to 4.00.
   - Add Hazelnut with stock 0. A flavor at 0 is hidden from the agent, which
     is what makes it "sold out" in Module 1.6.
   - Set the other stock to the number of real cupcakes you have.
2. Create the Azure AI Search service, run `foundry-iq/ingest_foundry_iq.py`,
   issue a query key, and verify Module 1.3 with it (see `foundry-iq/README.md`).
   Put `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_QUERY_KEY`, and
   `KNOWLEDGE_BASE_NAME` in the image `.env`. Never the admin key.
3. Deploy `eval-endpoint/` (it ships a copy of the store document for the
   judge), create the project connection (`create_connection.py`), and set
   `EVAL_ENDPOINT_CONNECTION` in `.env`.
4. Connect Application Insights to the project; put the connection string in
   the image `.env` with `ENABLE_OTEL="0"` (attendees flip it in 2.3).
5. Verify the supplied catering photo
   (`sparkles-agent/images/catering-order.jpg`) against your flavor list. Run
   `python catering.py` three times and check it passes each run. The photo
   names Lemon Drop, Vanilla, Salted Caramel and Cookies & Cream, so those
   have to be on the store menu from step 1. To use your own photo instead,
   see "The catering-order photo" below.
6. Deploy `claude-sonnet-5` and `claude-haiku-4-5` (Global Standard) with
   those exact names.

## Changing the Skillable image

The Skillable image is built ahead of the event from what we hand over, and it
ships with working values already in it. Once it is built you cannot edit it.

So putting the room on something else — your own MCP server, your own knowledge
base — is a live instruction, not a configuration change. Tell them what to set
in `.env`, say it at the point in the module where that value is first used,
and put the exact line somewhere they can copy from. Announced at the start of
the day it will be forgotten by the time it matters.

Two things follow. Anything that can only live in the image has a hard deadline
at handover. And if a lab page changes after Skillable has taken their copy,
tell them: they consume the markdown, and a later edit will not reach the room
on its own.

## The catering-order photo

A photo ships with the repo and most rooms should just use it (prep step 5).
Make your own only if you want different flavors. Handwritten on paper,
photographed slightly askew in normal light:

- Customer name at the top
- Three or four flavor lines with quantities as tally marks. Use flavor
  names exactly as they appear on the store's menu.
- One line crossed out with a replacement written beside it
- An allergy note in the margin ("NO NUTS!!" works well)
- Keep a second, messier version as a spare

Pass condition, three runs out of three on Sonnet: `python catering.py` reads
the corrected items, the right quantities, and the allergy note; quotes the
allergen and catering rules from the knowledge base; places one test order
after you give it a customer ID and the voucher code; and prints a receipt
that lists every item on the photo.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| 401 from any script | Wrong key or endpoint | Re-copy from Playground Details |
| DeploymentNotFound | Deployment name mismatch | Copy the name from Models > Deployments exactly |
| 400 "additionalProperties must be explicitly set to false" | A schema object without it | Add `"additionalProperties": False` to every object |
| 400 on web search or tool search | Wrong version string | Use `web_search_20250305` / `tool_search_tool_bm25_20251119` |
| SyntaxError: invalid character U+201C | Curly quotes from copying out of a document | Copy code from the repo files, not from a doc |
| Script runs but prints nothing | Missing print after the call | The provided scripts print; check they copied the whole file |
| Evaluator PASSes the seeded bug | Report not passed to the evaluator | Run `python checks.py` and confirm `order-count: MISSING` appears |
| Agent says it cannot take catering or bulk orders at the counter | Expected: the store allows one cupcake per customer | Modules 1.5 and 1.6 are written around this rule; the knowledge base carries the catering rules |
| "Voucher code wrong or expired" | The code rotates every 3 minutes | Read the code off the screen again, right before sending |
| Traces not in the Foundry portal | Expected: the loop is a local script | Use Application Insights, Transaction search; the Foundry Traces tab lists hosted agents only |
| Traces not in Application Insights | Ingestion lag or empty connection string | Wait up to three minutes; check `.env` |
| 400 "name: Input should be 'tool_search_tool_bm25'" | Tool search tool renamed | The name is fixed by the API; use `tool_search_tool_bm25` |
| Every eval row errors, "status must be one of Completed" | Endpoint returns lowercase status | Return `Completed` / `Error` / `Skipped` |
| "base_url and resource are mutually exclusive" | `ANTHROPIC_FOUNDRY_RESOURCE` is set in the shell | Unset it; this repo uses `FOUNDRY_ENDPOINT` |
| Knowledge base tool fails to connect | Wrong Search endpoint, key, or knowledge base name | Check the three `AZURE_SEARCH_*` / `KNOWLEDGE_BASE_NAME` values; the endpoint has no trailing slash |
| "MCP server failed to initialize: 401" with correct values | agent-framework-core 1.18.0 does not send `header_provider` headers on the MCP handshake | `pip install "agent-framework-core>=1.17.0,<1.18"` (the requirements pin this); lift the pin only after a later release passes Module 1.3 |
| Agent answers policy questions without the knowledge base | Instructions not extended, or tool not passed in the list | Compare with `snapshots/agent-module-1.3.py` |
| Evaluator registration permission error | Seat account lacks rights on the project | Instructor registers on the shared screen; attendees run `run_cloud_eval.py` only |

## Fallbacks

- MCP server down: Modules 1.2 and 1.5 stop, and 1.6 loses its menu check.
  Run 1.3 and 1.4. For 1.6, the allergy and catering-policy problems still show
  without the server; say the menu check is missing.
- Search service down: skip 1.3, and run 1.5 and 1.6 from
  `snapshots/agent-module-1.2.py` logic (the agent still orders; it just
  cannot quote policy). Tell the room what they are missing.
- Eval endpoint down: do 2.4 Step A hands-on, Step B from a recorded run.
- Portal slow: everything in Lab 2 prints to the terminal; the portal is
  confirmation, not the only view.
