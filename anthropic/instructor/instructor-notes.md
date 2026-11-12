# Instructor notes

## Two ways to run the workshop

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

If you offer Codespaces: attendees need a GitHub account, and they sign in
with `az login --use-device-code`. Some organizations block that; anyone
blocked does Module 2.4 on their own laptop or watches it on screen.

In practice, prepare some of it anyway as a backup. A shared cupcake MCP server
and a shared knowledge base cost you little and cover the two things most
likely to go wrong on someone else's subscription: a deployment that fails, and
a region without Claude models or without quota. Someone who is stuck can point
at yours and keep moving rather than lose Lab 1.

Decide before the event whether you are offering that backup, and say so at the
start. Attendees who know there is a safety net will attempt their own setup;
attendees who do not know will either not try or will not ask when it breaks.

If the room is mixed, say at the start which instructions apply to whom. The
lab pages are the same either way; only setup differs.

## Two-minute intros (talk, then hands on)

**SETUP.md — standalone rooms only.** Skip this entirely on Skillable; the
seat is already set up. What they are building: a Foundry project, two model
deployments, a knowledge base, and an MCP server address. The one idea worth
saying out loud is that every lab reads its settings from a single `.env` in the `anthropic` folder, so everything they do here is filling in that one file.

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
there is no if statement to write. The module ends with tool search: two tool
servers today, two hundred tools next year, and Claude searches for the ones
it needs. Pinned version.

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

**Lab 2 as a whole.** The title is "Running Claude Agents with Confidence",
and the line for this lab is "Claude does the work. You approve results, not
keystrokes." Say what that buys: their time goes on the brief and the result,
where their judgment changes the outcome. Each module adds one reason to
trust the result, and it is worth naming as you start each one: a judge
separate from the writer (2.1), limits the agent can't pass (2.2), records of
every step (2.3), and scores on every run (2.4). Do not describe it as
walking away from the agent. The point is doing more while staying in charge
of the result.

**2.1 — The agent that checks its own work.** The agent that writes is not the
agent that judges, and the loop is only ever as good as that judge. Explain why
the first draft is seeded: a reliable FAIL beats a random one. The last step
adds web search: in Lab 1 the agent learned what the shop knows, and now
the planner learns what the world knows. Pinned version.

**2.2 — An agent harness for open-ended tasks.** In 2.1 Python ran the loop and
Claude wrote text. With the Claude Agent SDK, Claude runs the loop: it writes
the file, runs the checks, and fixes what is missing. Same checks, same five
test ids. Spend the time on Step C. The refused `backup.html` is the moment
the room sees that more independence came with a limit, and that the refusal
is on the record.

**2.3 — See everything it did.** OpenTelemetry instruments your code, not the
model, so Foundry tracing works with Claude as-is. The Claude Agent SDK runs Claude in
a program of its own, so the agent's spans are written by `tracing.py`. Say up
front that traces lag by a few minutes.

**2.3, the last ten minutes — the same agent in Foundry.** Attendees send a
task to the hosted agent you deployed and open their own trace; see "The
hosted agent step" below. The message: `agent.py` did not change. What
changed is who runs it, how it signs in, and where you look.

**2.4 — Evaluations, judged by Claude.** Built-in AI-assisted evaluators come
with their own judge model; custom evaluators are how you bring your own, and
here the judge is Claude. The wrong-refund row is the point: the rules pass
it, and the Claude judge with the policy document fails it.

## Setup at the event

**Skillable.** No setup slot. Ten minutes at the start: everyone opens their
seat, confirms the `.env` in the `anthropic` folder has values in it, and runs one
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

The image's `.env` goes in the `anthropic` folder, not in `sparkles-agent/`. The
labs point attendees there.

**Regions.** Pick the region nearest the room from the list at the top of
[SETUP.md](../standalone/SETUP.md) and use it for everything you create. The
Search service decides: several large regions, East US among them, currently
refuse new Search services. The Foundry project, the Search service and the
cupcake server do not have to be in the same region.

1. Deploy the cupcake MCP server and the order dashboard from
   [GlobalAICommunity/cupcake-mcp](https://github.com/GlobalAICommunity/cupcake-mcp)
   (Henk Boelman, MIT). [cupcake-mcp-setup.md](../cupcake-mcp-setup.md) is a
   step-by-step runbook for this — Azure resources, the deploy, how to check it
   is up, how to turn it off between events. Put the URL in the Skillable image
   `.env` as `CUPCAKE_MCP_URL` (it ends in `/mcp/`). **Pin it to one replica**
   (`--min-replicas 1 --max-replicas 1`, Stage 7 of the runbook), or attendees
   lose their sessions part-way through a lab. Then, in `/admin`:
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
3. Confirm Skillable has set up an eval endpoint for each seat, running on the
   same Claude deployment as the lab, with `EVAL_ENDPOINT_CONNECTION` and
   `EVAL_ENDPOINT_URL` in each seat's `.env`. Leave `EVAL_ENDPOINT_API_KEY` out
   of the `.env`: it is a secret, and no attendee step reads it. Check one seat
   before Module 2.4 (replace `<fqdn>`); you want the model name back. In bash,
   `curl https://<fqdn>/health`; in PowerShell,
   `Invoke-RestMethod https://<fqdn>/health`.
4. Connect Application Insights to the project; put the connection string in
   the image `.env` with `ENABLE_OTEL="0"` (attendees flip it in 2.3).
5. Verify the supplied catering photo
   (`sparkles-agent/images/catering-order.jpg`) against your flavor list. Run
   `python catering.py` three times and check it passes each run. The photo
   names Lemon Drop, Vanilla, Salted Caramel and Cookies & Cream, so those
   have to be on the store menu from step 1. To use your own photo instead,
   see "The catering-order photo" below.
6. Deploy `claude-sonnet-5-5` and `claude-haiku-5-5` (Global Standard) with
   those exact names.
7. Check Module 2.2 on a seat: from `sparkles-hosted/`, `python agent.py`
   prints `"passed": true` within a minute. The Claude Agent SDK starts a program of
   its own (`claude.exe` on Windows), so this is the check that the seat
   allows it to run.
8. Deploy the hosted agent for the end of Module 2.3. Deploy it **in the
   workshop's Foundry project**, the one `AZURE_AI_PROJECT_ENDPOINT` in the
   image `.env` points at, because attendees call it from their lab
   environment. Follow
   [sparkles-hosted/README.md](../sparkles-hosted/README.md), steps 2 to 6.
   Do it the day before the event, not during it: two permissions each take several
   minutes to take effect.
9. Check the hosted agent from a lab environment, signed in as an attendee
   and not as yourself: `az login`, then from `sparkles-hosted/`,
   `python invoke.py`. You want `HTTP 200` and `"passed": true`. `HTTP 401`
   or `403` means attendee accounts cannot call agents in the project. Then
   open the agent's traces in the Foundry portal with the same account.

## The hosted agent step

Ten minutes, at the end of Module 2.3. Attendees send a task to the agent
you deployed, see the same refusal come back from Foundry, and open their own
trace in the Foundry portal. They all call the same agent. Each request gets
a session of its own, so they do not see each other's pages.

Thirty tasks sent at the same moment all came back in 23 to 37 seconds each
(tested 2026-09-30, Sonnet). Your Claude deployment
needs the quota for a room's worth of requests at once.

Run it on the main screen as well, a step ahead of the room, using the steps
below. If attendee accounts cannot call the agent, this becomes a demo and
the room watches.

Deploying their own is the take-home. Their page lists the six steps you did
to deploy it, and says that doing it themselves needs their own subscription
and is for after the workshop. If someone asks to deploy one in their lab
environment, that is the answer: deploying needs a container registry and
the right to assign roles, and the lab environment is not set up for either.

Before the event:

- The agent is deployed and `python invoke.py "Build the kiosk page for the
  Sparkles cupcake shop"` returns `"passed": true`. Expect 30 to 60 seconds.
- You are signed in with `az login` on the demo machine. A hosted agent takes
  no key.
- In the Foundry portal, open the project, find the agent
  `sparkles-kiosk-builder`, and open one of its traces. The portal changes
  often, so do this once before you are in front of the room.

At the event, in this order:

1. `python invoke.py "Build the kiosk page for the Sparkles cupcake shop"`.
   While it runs, say that this is the file they ran ten minutes ago.
2. `python invoke.py --session <session> "Make the order button pink"`, with
   the session the first call printed. The page from the first request is
   still there.
3. `python invoke.py "Build the kiosk page, and save a second copy as
   backup.html"`. Point at `did_not_run` in the reply.
4. Show the trace for the third request in the Foundry portal. It opens on
   the **Trajectories** tab. Point at, in this order:
   - The badges at the top right: spans, chat calls, tool calls, seconds, and
     tokens for the whole request.
   - The two rows labelled **Invoke Agent**. `invoke_agent` is Foundry's
     record of the request. `kiosk-builder` is the agent's own.
   - The rows labelled **Chat** and **Execute Tool**, which take turns.
     Attendees have just read the same rows in Application Insights.
   - The row named `execute_tool Write (refused)`, near the bottom. Select it
     and find `sparkles.refused_or_failed` in the **Metadata** panel on the
     right. This view gives every row a green tick, refused or not, which is
     why the refusal is in the name.

   Three things in that view that people ask about:
   - `run_checks` appears twice. `execute_tool run_checks` is the call as the
     agent made it. `tools/call run_checks` is the same call as the tool
     server received it. Foundry records the second one itself.
   - The rows labelled **Other** (`initialize`, `notifications/initialized`,
     `tools/list`) are the agent connecting to its own tool server when it
     starts. They take no time.
   - The first **Chat** row is the longest. That is Claude writing the whole
     page. The later ones are short because they are small decisions.

If there is time, `python eval_hosted.py` shows Foundry calling the agent and
scoring what comes back. It takes a few minutes, so start it before you
begin talking and come back to it.

## Changing the Skillable image

The Skillable image is built ahead of the event from what we hand over, and it
ships with working values already in it. Once it is built you cannot edit it.

So putting the room on something else — your own MCP server, your own knowledge
base — is a live instruction, not a configuration change. Tell them what to set
in `.env`, say it at the point in the module where that value is first used,
and put the exact line somewhere they can copy from. Announced at the start of
the event it will be forgotten by the time it matters.

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
| "Session was terminated" from the agent | The cupcake server is not pinned to one replica, so it scaled to zero or to two | Attendee runs `agent.py` again. You pin it: `az containerapp update -n ca-cupcake-mcp -g rg-cupcake-mcp --min-replicas 1 --max-replicas 1` |
| "You have already had your one real cupcake" | One order per customer, by design | Register a new customer ID |
| Creating the Search service fails with `InsufficientResourcesAvailable` | That region refuses new Search services | Use another region from the list in SETUP.md |
| Traces not in the Foundry portal | Expected: the loop is a local script | Use Application Insights, Transaction search; the Foundry Traces tab lists hosted agents only |
| Traces not in Application Insights | Ingestion lag or empty connection string | Wait up to three minutes; check `.env` |
| A KQL query fails with "Failed to resolve table or column" | It was typed or edited, and uses a table name that does not exist where Logs was opened (`dependencies` in Application Insights, `AppDependencies` in a Log Analytics workspace) | Paste the query from the page as it is. Its first three lines make it work in both |
| `cd sparkles-loop` says the folder does not exist | The terminal is still in `sparkles-agent` from Lab 1 | `cd ../sparkles-loop` |
| 400 "name: Input should be 'tool_search_tool_bm25'" | Tool search tool renamed | The name is fixed by the API; use `tool_search_tool_bm25` |
| Every row in an attendee's Step B report says `Error` | Foundry could not get a usable answer from the eval endpoint. A low score is not an error | Run `/health`, then follow Troubleshooting in [eval-endpoint/README.md](../eval-endpoint/README.md). If it's not a quick fix, do Step B from a recorded run |
| Every eval row errors, "status must be one of Completed" | Endpoint returns lowercase status | Return `Completed` / `Error` / `Skipped` |
| "base_url and resource are mutually exclusive" | `ANTHROPIC_FOUNDRY_RESOURCE` is set in the shell | Unset it; this repo uses `FOUNDRY_ENDPOINT` |
| Knowledge base tool fails to connect | Wrong Search endpoint, key, or knowledge base name | Check the three `AZURE_SEARCH_*` / `KNOWLEDGE_BASE_NAME` values; the endpoint has no trailing slash |
| "MCP server failed to initialize: 401" with correct values | agent-framework-core 1.18.0 does not send `header_provider` headers on the MCP handshake | `pip install "agent-framework-core>=1.17.0,<1.18"` (the requirements pin this); lift the pin only after a later release passes Module 1.3 |
| Agent answers policy questions without the knowledge base | Instructions not extended, or tool not passed in the list | Compare with `snapshots/agent-module-1.3.py` |
| Evaluator registration permission error | Seat account lacks rights on the project | Instructor registers on the shared screen; attendees run `run_cloud_eval.py` only |
| `No module named 'claude_agent_sdk'` | The image was built before it was added to `requirements.txt` | `pip install claude-agent-sdk` |
| Module 2.2 agent does not start, or the seat blocks a program | The Claude Agent SDK starts `claude.exe`, and the seat does not allow it | Pair the attendee with a neighbor for 2.2, or run it on the main screen. Report it to Skillable |
| Agent output shows `did not run: ... Only index.html` | Expected in Module 2.2 Step C | That line is the point of the step |
| Agent report says `"stopped_because": "error_max_turns"` | It reached the turn limit | Expected with `--max-turns 1`. Otherwise run it again |
| Tool search prints three empty lists | Claude answered without searching | Run it again, or ask a question about the shop's orders, hours or loyalty points |
| `invoke.py` prints `HTTP 401` or `403` straight away | The attendee's account cannot call agents in the project, or they have not run `az login` | `az login`, then try again. If it still fails, they follow the step on the main screen. Report it to Skillable |
| Hosted agent: every task fails after about three minutes with 401 | The agent's identity lacks the Foundry User role, or the role is minutes old | README step 5, then wait up to eight minutes |
| No `kiosk-builder` card in Application Insights after Module 2.3 Step 1 | Tracing was off for that run | Check `ENABLE_OTEL="1"`, and that the first line printed was `Tracing on` |

## Fallbacks

- MCP server down: Modules 1.2 and 1.5 stop, and 1.6 loses its menu check.
  Run 1.3 and 1.4. For 1.6, the allergy and catering-policy problems still show
  without the server; say the menu check is missing.
- Search service down: skip 1.3, and run 1.5 and 1.6 from
  `snapshots/agent-module-1.2.py` logic (the agent still orders; it just
  cannot quote policy). Tell the room what they are missing.
- Eval endpoint down: do 2.4 Step A hands-on, Step B from a recorded run.
- Hosted agent down: run `python agent.py` on the main screen and walk through
  the comparison table on the page. Everything except who runs it is the same.
- A seat cannot run the Claude Agent SDK: that attendee follows 2.2 on the main
  screen or with a neighbor. 2.3 and 2.4 still work for them, because the loop
  does not need it.
- Portal slow: everything in Lab 2 prints to the terminal; the portal is
  confirmation, not the only view.
