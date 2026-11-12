# Lab 2: Running Claude Agents with Confidence

In Lab 1, you built the Sparkles agent and guided it one message at a
time. In this lab, Claude takes on more of the work. You control what done
looks like, set limits on what the agent can do, and approve results against
evidence, so you can have more confidence in your agent.

**Claude does the work. You approve results, not keystrokes.**

The job: Sparkles needs an ordering kiosk page for the counter. You build it
two ways, first with a loop you run by hand, then with the Claude Agent SDK, an
agent harness that lets Claude decide the steps itself. Then you use Foundry to
see what it did and score the result.

**Running Claude Agents with more confidence.** Each module gives
you more reasons to trust the result: a judge separate from the writer to
catch what it misses, limits the agent can't pass to keep it on task,
records of every step to show what it did, and scores on every run to
measure improvement.

In this lab, you'll:

- Run a planner, generator, and evaluator loop that catches a planted bug and fixes it
- Ground the plan in live web search
- Give Claude an open-ended task with the Claude Agent SDK, limit it to one file, and see it refused when it tries to write a second
- See every model call, tool call, token count, and refusal in Application Insights
- See what it takes to host the same agent in Foundry, with an identity of its own and the same limits and traces (deploying it yourself is optional)
- Register evaluators and score runs in Foundry, with Claude's written reasoning in the results

**How the lab works.** Everything runs from scripts already in
`sparkles-loop/`, `sparkles-hosted/` and `sparkles-evals/`. You read them, run
them, and change what they do. Each module ends with a checkpoint.

**If you're picking this up fresh**, copy
`sparkles-agent/snapshots/agent-module-1.4.py` over `agent.py` and check that
`.env` is still filled in. Everyone else starts at Module 2.1.

---

## Module 2.1: The agent that checks its own work (20 minutes)

An agent that runs for a minute needs a good
prompt. An agent that runs for an hour needs something to check the work and
decide whether it's done or needs another try.

The loop has four steps: write down what "done" looks like, build, check the
result against it, and send back what failed. It repeats until the result
passes or the rounds run out. The rest of this lab builds on this loop.

![Three agents, one loop](images/05.0-loop-visual.png)

One line of intent goes in on the left. The planner turns it into a spec, the
generator builds to it, and the evaluator answers PASS or FAIL with a critique.
FAIL starts another round. PASS ends the loop.

Three scripts, three roles, two Claude deployments:

- **planner.py**: one line of intent in, a testable spec out. Sonnet.
- **generator.py**: spec in, a single-file kiosk page out. Haiku, the faster
  tier. It writes the most tokens by far, and it's working from a
  spec rather than judging anything.
- **evaluator.py**: the spec plus hard evidence in, PASS or FAIL out, with a
  critique. Sonnet, because the work is only ever as good as the judge.

Run each on its own first so you see what it produces, then run the loop.

Your terminal is in `sparkles-agent` from Lab 1. Go up one folder and into
`sparkles-loop`:

```
cd ../sparkles-loop
```

That line works in PowerShell and in bash. If you opened a new terminal and
it's in the `anthropic` folder, use `cd sparkles-loop`.

### Step A: the planner (5 minutes)

**Open `planner.py` before you run it.** Its job is to turn a request into a
list of things that can be checked without a person looking.

- **`PROMPT`** is the request: a kiosk page with today's flavors that customers
  can tap to select, a special, and a running order count. Clear to a human, but there's nothing in it a
  script could test.
- **`SPEC_SCHEMA`** makes the answer come back as fixed JSON rather than prose.
- **`SYSTEM`** tells Claude every acceptance criterion has to name a
  `data-testid` on the page. Those are the names the evaluator looks for
  later.

```
python planner.py
```

Read the spec it prints: three or four features, each with an acceptance
criterion, saved to `workspace/spec.json`.

Each criterion names a part of the page by its `data-testid`. That's a label
in the HTML that lets a script find the part, whatever the page looks like.
The spec always covers these five:

| `data-testid` | The element | What has to be true |
|---|---|---|
| `title` | the shop name at the top | it's there |
| `flavor-list` | today's flavors | it's there, and holds at least three flavors, each its own element |
| `special` | the special of the day | it's there |
| `order-btn` | the Place Order button | it's there |
| `order-count` | the running count of orders | it's there |

Every step in this module uses this list. The generator is told to
use exactly these names, `checks.py` counts them, and the evaluator passes or
fails the page on them. It's also the same list the code evaluator scores in
Module 2.4.

### Step B: the generator, with a planted bug (3 minutes)

The generator turns the spec into one HTML page for the shop counter.

**Open `generator.py`.**

- **`SYSTEM`** is its entire brief: here's the spec, return one
  self-contained HTML file.
- It has no memory between sprints and never sees the evaluator's reasoning,
  only the critique text fed back in. That's what stops it grading its own
  work.
- **`seed()`** loads a first draft instead of generating one.

**The seed.** `--seed` loads `seeds/kiosk_buggy.html`, a page we wrote with two
mistakes in it. Open it in VS Code and find the two `BUG` comments.

- **Only one flavor is listed.** The spec asks for three.
- **The order counter is missing.** The JavaScript tries to update an element
  called `order-count` that was never added to the page. It checks the element
  exists first, so nothing breaks; the count just never appears.

**Why start broken?** A page we know is wrong fails the first round every
time, so there's always a loop to watch.

```
python generator.py --seed
```

That copies the page to `workspace/index.html`, which is what everything
downstream reads.

### Step C: evidence and the evaluator (4 minutes)

First a script measures the page, then Claude decides whether that's good
enough.

**Open `checks.py`.** No Claude here. It's ordinary Python that opens
`workspace/index.html` and counts what's on the page.

- **`evidence()`** reports which `data-testid` names it found and how many
  items are in each list.
- Run it twice and you get the same answer twice. Ask the generator whether it
  built the page correctly and you get an opinion; this gives you a count.

```
python checks.py
```

The report lists which test ids exist, how many items each list has, and
whether the page pulls in any external scripts. Compare it with the spec from
Step A: the flavor list should have three items and it has one.

**Open `evaluator.py`.** This is Claude again, in a fresh session, and it gets
two things: the spec, and the report you just ran.

- It never sees the HTML, and never sees what the generator said about its own
  work. A reviewer who reads the author's explanation first tends to agree with
  it.
- **`VERDICT_SCHEMA`** makes it answer PASS or FAIL with a written critique, in
  a fixed shape the loop can act on.

```
python evaluator.py
```

It should FAIL on the flavor list and the missing order counter, and write a
critique saying exactly what to change. That critique is what the generator
gets handed in the next step.

### Step D: the whole loop (4 minutes)

**Open `run_loop.py`.** It's short, because the three scripts you just ran
do the work. This one decides what happens next.

- **`MAX_SPRINTS`** stops it after three rounds. Without a limit, a page the
  evaluator never accepts would loop forever.

```
python run_loop.py
```

Sprint 1 loads the seeded draft and fails. Sprint 2 hands the critique to the
generator, which rewrites the page. The evaluator checks again and passes.

**Now look at what it built.** Open `workspace/index.html` in a browser.

> In a Codespace there's no browser on the machine to open the file with.
> Serve the folder instead, in a second terminal:
>
> ```
> python -m http.server 8000 --directory workspace
> ```
>
> The Codespace offers to open port 8000 in your browser. Choose **Open in
> Browser**, then select `index.html`. Leave it running and refresh the tab
> after each change.

![The finished kiosk page](images/05.1-kiosk.png)

- A flavor list with every flavor on its own row, instead of the single one
  the seed had. You may see more than three; the spec sets a minimum, not a
  maximum
- The special of the day, called out on its own
- The order counter next to the button, showing 0
- Tap a flavor and it's highlighted. Click the order button and the count goes
  to 1. Until a flavor is selected, the button does nothing

Open `seeds/kiosk_buggy.html` alongside it to see where it started: one flavor,
and no counter at all.

**This page is a demo. It doesn't take real orders.** What matters is what the
loop showed: it built a page to a spec, caught its own mistake, and fixed it.

> Why this matters. When an agent writes more code than you can review, the
> review becomes the bottleneck. A separate judge with its own evidence helps
> more than a better prompt for the writer, so that's where the effort goes.

> Try it: run `python run_loop.py --fresh` to let the generator build the
> first draft itself instead of using the seed.

### Step E: ground the plan in web search (4 minutes)

In Lab 1 the agent learned what the shop knows, from Foundry IQ. **Web search**,
built into Claude on Foundry, adds what's happening now. Use it when a plan
depends on information newer than the model's training.

**Open `websearch.py`.** `QUESTION` is what gets asked, and you can edit it.
Claude runs the searches and reads the results on the server side, so your
script never fetches a web page itself.

```
python websearch.py
```

Claude searches, reads a few results, and recommends a special with its
sources listed at the bottom. Compare with your neighbor and see whether you
got the same answer.

Now let the planner do the same before it writes the spec, inside the full
loop:

```
python run_loop.py --research
```

The research notes print first, then the spec. The flavors and the special
now come from live results, so your kiosk won't match your neighbor's. The
rest of the loop is unchanged: same generator, same checks, same judge.

✅ **Checkpoint 8.** A planted bug caught by a Claude evaluator and fixed by a
Claude generator, with a written verdict for every round, and a plan grounded
in live web search with its sources.

---

## Module 2.2: An agent harness for open-ended tasks (20 minutes)

In this module, you'll use the **Claude Agent SDK** to build and repair the kiosk
page. We're using it because this kind of work is open-ended: you can't list
every step up front, so Claude needs to decide the next one. That takes an agent
harness: the loop, tools, and permissions around the model that let it do real
work. The Claude Agent SDK gives you that harness, built on the same foundation
as Claude Code.

You've already seen two other ways to run an agent's loop. In Lab 1, Agent
Framework ran it inside your app, with Claude as the model. That's a great fit
when the agent is part of your app, and Agent Framework also supports the Claude
Agent SDK, so you can pick what fits each agent. In Module 2.1, Python ran it:
your scripts called Claude once per step, saved the file, ran the checks, and
decided whether to try again. That's simpler when you already know every step.

With the SDK, you write what's specific to your job: the brief, the checks, and
the limits. **Claude does the work. You approve results, not keystrokes.**

Here it builds the same demo page as Module 2.1.

| In the manual loop | With the Claude Agent SDK |
|---|---|
| `generator.py` returns the page as text and Python saves it | Claude writes and edits `index.html` with file tools |
| `run_loop.py` calls `checks.py` after each build | Claude calls `run_checks`, a tool that wraps the same `checks.py` |
| A Python `for` loop, up to `MAX_SPRINTS` | The Claude Agent SDK's own loop, up to a turn limit |
| Three scripts and three prompts | One agent and one prompt |

```
cd ../sparkles-hosted
```

### Step A: run it (5 minutes)

```
python agent.py
```

It takes 30 to 60 seconds. A line prints for each tool call as it happens:

```
  tool: Write index.html
  tool: mcp__sparkles__run_checks
```

`mcp__sparkles__run_checks` is the tool you gave it: `sparkles` is the server
name and `run_checks` is the tool. Your code didn't call the checks this time. Claude did, because the brief
says to. If the checks had found something missing you would see an `Edit`
and a second `run_checks`.

Then the report prints. Read these fields:

| Field | What it tells you |
|---|---|
| `passed` | whether the page meets the checks |
| `checks` | the report itself: which elements were found, and how many items each list has |
| `steps` | every tool call the agent made, in order |
| `turns` | how many times Claude was called |
| `cost_usd` | the Claude Agent SDK's own estimate, which its spending limit uses |
| `stopped_because` | `success`, the limit it reached, or the error |

**`passed` isn't the agent's opinion.** After the agent stops, `agent.py`
runs the checks once more itself, outside the agent. The `passed` and `checks`
fields come from that run. Find it near the end of `build_kiosk()`. It's the
idea from Module 2.1 again: the one that writes isn't the one that judges. In Module 2.1 a separate Claude
evaluator was the judge. Here your code is.

**Now look at what it built.** Open `workspace/index.html` in a browser. This
is the result you're approving, and the report is the evidence you approve
it on. Tap a flavor, then click the order button. The `summary` field usually
says the agent didn't try this, because `run_checks` only reads the file.

> In a Codespace there's no browser on the machine to open the file with.
> Serve the folder as you did in Module 2.1, from `sparkles-hosted` this time, on a
> different port:
>
> ```
> python -m http.server 8001 --directory workspace
> ```
>
> The Codespace offers to open port 8001 in your browser. Choose **Open in
> Browser**, then select `index.html`. Leave it running and refresh the tab
> after each change.

### Step B: read the agent (5 minutes)

**Now that you've seen it run, open `agent.py`.** Four things to find:

- **`SYSTEM`** is the brief: the same five `data-testid` values, and the order
  to work in. Its last line says the agent must never report a result it hasn't
  seen.
- **`checks_server()`** wraps `evidence()` from `checks.py` as a tool, so the
  agent is measured the same way the loop was.
- **`ClaudeAgentOptions`**, inside `build_kiosk()`, says what the agent may use
  and when it must stop.
- **`foundry_env()`** points the Claude Agent SDK at your Claude deployment, using
  the endpoint and key already in `.env`.

### Step C: ask for something outside its limits (5 minutes)

The task text could come from anyone, so the agent is held to one file
whatever the task says. Ask it for a second file:

```
python agent.py "Build the kiosk page for the Sparkles cupcake shop, and save a second copy as backup.html"
```

Look for these two lines in the output:

```
  tool: Write backup.html
    did not run: PreToolUse:Write hook error: Only index.html in the working folder may be read or changed.
```

Claude tried, the rule refused, and the refusal is in the record. Read the
`summary` field of the report: the agent tells you it couldn't make the
copy, and why. The kiosk page still passes.

**Open `agent.py` and find `only_the_page()`.** It's a hook: a function the
Claude Agent SDK calls before every file tool runs. It allows `index.html` in the
working folder and refuses everything else.

This limit is a guardrail. It holds no matter what the task says or what the agent decides, so
you can give the agent longer tasks with more confidence.

The hook isn't the only limit. The agent also has a fixed tool list, with no
terminal or web access, a turn limit and a spending limit for each task, and
final checks run by your code.

> Try it: see a limit work. `python agent.py --max-turns 1` stops the agent
> after one turn. `stopped_because` reads `error_max_turns`, and the report
> still tells you what state the page was left in.

### Step D: hand it the broken page (5 minutes)

In Module 2.1, your script ran the loop on a page with two planted bugs. Now
give the agent that same page, with the `BUG` comments taken out, so it has to
find the problems itself:

```
cp ../sparkles-loop/seeds/kiosk_unmarked.html workspace/index.html
python agent.py --keep "This page was built to the brief but has problems. Find them and fix them."
```

`--keep` carries on with the page that's already there. Without it, the agent
starts from an empty folder.

Watch the tool lines:

```
  tool: Read index.html
  tool: mcp__sparkles__run_checks
  tool: Edit index.html
  tool: mcp__sparkles__run_checks
```

It reads the page, runs the checks to find out what's wrong, makes its edit,
and checks again. Read the `summary` field: it names both bugs. Your flavors
may not match your neighbor's, because the brief sets a minimum of three and
the agent picks the rest.

Refresh the browser, tap a flavor, and click the order button. `passed` tells
you the right parts are on the page. It can't tell you the button works, so
that part is yours to approve.

> Why this matters. You didn't review the HTML. You set what done means and
> the limits, then read the evidence. The checks prove the page has the right
> parts, and they can't prove the button works, so you tried it yourself.
> Knowing what your evidence covers is how you can trust an agent with more
> than you can read line by line.

> To learn more, see [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

✅ **Checkpoint 9.** A kiosk page built, checked, and repaired by one agent,
with a report of every step it took, and one step refused because it was
outside the limits you set.

---

## Module 2.3: See everything it did with Foundry observability (20 minutes)

You've now run the job two ways: a loop your scripts ran, and an agent that
ran its own. Application Insights records every step of both. The more an
agent does on its own, the more this record matters: it's how you know what it
did, and how you show it to someone else.

Note: these scripts run on your machine, so their traces are in Application
Insights in the Azure portal. The Foundry portal's Traces tab shows agents
hosted in Foundry, and the end of this module shows how to host this one.

### Find your Application Insights resource

You may already have one: creating a Foundry project can create an Application
Insights resource alongside it. Look before you make another.

```
az monitor app-insights component show --query "[].{name:name, rg:resourceGroup}" -o table
```

**If exactly one came back**, read its connection string:

```
az monitor app-insights component show --query "[0].connectionString" -o tsv
```

**If several came back**, pick the one in the same resource group as your
Foundry project and name it. Replace both values with yours:

```
az monitor app-insights component show --app my-appi -g my-rg --query connectionString -o tsv
```

**If nothing came back**, create one in the resource group your Foundry project
is in. Replace the name, the resource group, and the region with yours. Use
the region you chose in [SETUP.md](SETUP.md):

```
az extension add --name application-insights --upgrade

az monitor app-insights component create --app my-appi -g my-rg -l southcentralus --application-type web

az monitor app-insights component show --app my-appi -g my-rg --query connectionString -o tsv
```

The connection string is one long line starting `InstrumentationKey=`. That's
the value you need next.

### Turn tracing on

In `.env`, set:

```
ENABLE_OTEL="1"
APPLICATIONINSIGHTS_CONNECTION_STRING="the connection string you just read"
```

That's the only change you make. The loop and the agent already do the rest.
Once they've run, you'll be able to answer four questions:

- Which step was slowest?
- How many tokens did each model use?
- Did the score improve from round to round?
- What was the agent refused, and why?

Where the record comes from: `sparkles-loop/common.py` wraps each call to
Claude in a span. The Claude Agent SDK runs Claude in a program of its own, so
`sparkles-hosted/tracing.py` turns each message the agent sends back into a
span, and records a refused tool call as failed, with the reason.

#### Step 1: Run both again (5 minutes)

```
cd ../sparkles-loop
python run_loop.py
```

```
cd ../sparkles-hosted
python agent.py "Build the kiosk page for the Sparkles cupcake shop, and save a second copy as backup.html"
```

The first line of output from each should be `Tracing on: spans go to
Application Insights.`

Each run becomes one trace, which you'll open in the next steps. There's nothing
to run here. This is what the loop's trace will look like:

```
sparkles-session
  planner          -> POST /anthropic/v1/messages
  sparkles-run (round 1)
    evaluator      -> POST /anthropic/v1/messages
  sparkles-run (round 2)
    generator      -> POST /anthropic/v1/messages
    evaluator      -> POST /anthropic/v1/messages
```

Round 1 has no generator because it starts from the seeded draft.

The agent's trace will show what it decided to do, in order:

```
kiosk-builder                   turns, cost, tokens, passed
  chat claude-sonnet-5-5
  execute_tool Write            index.html
  chat claude-sonnet-5-5
  execute_tool run_checks       what the checks reported
  chat claude-sonnet-5-5
  execute_tool Write (refused)  backup.html, and why
  chat claude-sonnet-5-5
```

Traces take 2 to 5 minutes to appear in the portal. While you wait, open
`tracing.py` and find `tool_finished()`. It's where a refusal is written
onto the span.

#### Step 2: Look at the loop's run (5 minutes)

1. In the Application Insights resource, open **Investigate > Search**.
2. Set the time range to **Last 30 minutes**.
3. Select **View as traces**. Each card is one run of a script. The header of a
   `sparkles-session` card shows the run's duration, spans, and tokens.
4. Click the header line of the card (the trace ID and `sparkles-session` name,
   not the "Matching Dependency" box underneath). The end-to-end transaction
   page opens as a timeline: the planner at the top, then each round below it,
   with the generator and evaluator inside and the actual Claude call underneath
   each.
5. In that timeline, click the **evaluator** bar (not the POST beneath it). The
   panel on the right lists that span's properties: the model,
   `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, and the
   `sparkles.*` values the loop recorded. If the panel looks short, look for a
   "show all" or "leave simple view" link on it.

![Investigate > Search, cards](images/06-search-cards.png)

![Investigate > Search, one run open](images/07-search-trace.png)

Questions to answer from this view:

- Which agent is the slowest? Is it the one you expected?
- Compare the generator's tokens with the planner's. Why is the generator on
  the fast model?
- Open the evaluator in each round in turn. Does the score go up?

#### Step 3: Look at the agent's run (5 minutes)

1. Go back to **Search** and open the `kiosk-builder` card the same way.
2. Read the timeline from top to bottom. Model calls and tool calls take
   turns: Claude decides, a tool runs, Claude reads the result and decides
   again.
3. Click the top **kiosk-builder** bar. Its properties are the totals for the
   task: `sparkles.turns`, `sparkles.cost_usd`, `sparkles.passed`,
   `sparkles.stopped_because`, and the `gen_ai.usage.*` token counts.
4. Find the bar named **execute_tool Write (refused)** and click it.
   `sparkles.file` is `backup.html`, and `sparkles.refused_or_failed` is the
   reason the rule gave. The refusal is in the step's name so that it stands
   out in any trace viewer.

Questions to answer from this view:

- Where did the time go: the model calls, or the tools?
- The loop needed a planner, a generator, and an evaluator. How many model
  calls did the agent need for the same page?
- Could someone who wasn't in the room tell from this trace what the agent
  was refused, and why?

#### Step 4: Query across runs (5 minutes)

1. Open **Monitoring > Logs**. Two settings take you straight to the KQL
   editor, and both stick for your account:
   - In the **Queries hub** dialog, switch off **Always show Queries hub** and
     close it with the X.
   - Switch off the **Agent** toggle at the top right of the page.

   > Optional, before you switch the Agent off: the **Observability Agent**
   > writes KQL for you. Ask it "show me evaluator spans with their
   > sparkles.score by round" and compare what it produces with the queries
   > below.
2. Paste the following into the editor and select **Run**. It shows the
calls, average time and tokens for each role in the loop, with the agent on a
row of its own.

   ```kusto
   let spans = union isfuzzy=true
       (dependencies | project timestamp, name, duration, props = customDimensions),
       (AppDependencies | project timestamp = TimeGenerated, name = Name, duration = DurationMs, props = Properties);
   spans
   | where timestamp > ago(1h)
   | where name in ("planner", "generator", "evaluator", "kiosk-builder")
   | summarize runs = count(),
       avg_seconds = round(avg(duration) / 1000, 1),
       input_tokens = sum(toint(props["gen_ai.usage.input_tokens"])),
       output_tokens = sum(toint(props["gen_ai.usage.output_tokens"]))
       by name, model = tostring(props["gen_ai.request.model"])
   ```

   **Every query here starts with the same three lines.** They let the query
   run whether you opened Logs from Application Insights or Log Analytics.

3. Did the loop get better? Run this and switch the result to **Chart** if it
   doesn't render one automatically.

   ```kusto
   let spans = union isfuzzy=true
       (dependencies | project timestamp, name, duration, props = customDimensions),
       (AppDependencies | project timestamp = TimeGenerated, name = Name, duration = DurationMs, props = Properties);
   spans
   | where timestamp > ago(1h)
   | where name == "evaluator"
   | extend score = todouble(props["sparkles.score"])
   | where isnotnull(score)
   | project timestamp, score
   | order by timestamp asc
   | render timechart
   ```

   `sparkles.score` is the number of acceptance criteria the evaluator passed,
   and `sparkles.criteria` is how many there were, so a round that fixes one
   problem moves from 3 to 4 out of 4.

   A rising line is the evaluator forcing the generator to improve. A flat line
   means the criteria are too easy or the feedback isn't reaching the
   generator.

4. What was the agent refused? This is the question to ask of any agent
   before you give it more to do.

   ```kusto
   let spans = union isfuzzy=true
       (dependencies | project timestamp, name, duration, props = customDimensions),
       (AppDependencies | project timestamp = TimeGenerated, name = Name, duration = DurationMs, props = Properties);
   spans
   | where timestamp > ago(1h)
   | where name startswith "execute_tool"
   | where isnotempty(props["sparkles.refused_or_failed"])
   | project timestamp, name,
       file = tostring(props["sparkles.file"]),
       why = tostring(props["sparkles.refused_or_failed"])
   ```

![Trace tree and the score chart](images/08-trace-tree-chart.png)

✅ **Checkpoint 10.** The loop and the agent both visible in Application
Insights. You can name the slowest span, and you can show what the agent was
refused.

### Next: the same agent, running in Foundry (optional, about 30 minutes)

So far the agent has run on your machine. The same `agent.py` can run as a
**hosted agent** in Foundry. Foundry keeps it running, gives it an identity,
and takes requests for it.

**Why host it?** On your machine, this agent stops when you close the terminal,
and it depends on a key in `.env`. Hosted in Foundry, it's available whenever
it's called, it has its own identity with no key to leak, and you control who
can call it.

**Why the two fit together.** The Claude Agent SDK decides what the agent can do.
Foundry decides who it is, where it runs, and who can call it. An agent that
works on files needs a real working folder, and each hosted session gets its
own. The limits are in the code, so they travel with it.

| On your machine | Hosted in Foundry |
|---|---|
| You start it from a terminal | Foundry runs it, and anything with permission can send it a task |
| It signs in with the key in `.env` | It has an identity of its own, and there's no key to store or leak |
| The page is in `workspace/` | Each session gets a folder of its own, and the page is still there on the next request |
| You turned tracing on in `.env` | Foundry records every request, with the agent's own spans underneath |

What has to be added is small: `main.py`, a web server of 60 lines that
receives a task and calls `build_kiosk()`, and a `Dockerfile`. `agent.py` is
the file you just ran.

[sparkles-hosted/README.md](../sparkles-hosted/README.md) has the six steps.
Allow about 30 minutes, most of it waiting for the image to build and for two
permissions to take effect. You need a container registry, and the right to
assign roles in your subscription. Nothing in Module 2.4 depends on it, so it
can wait until after the lab.

Once it's running, look for four things:

1. A task sent with `invoke.py`, and the same report coming back.
2. A second request on the same session: 'Make the order button pink'. The
   page from the first request is still there to change.
3. The trace, this time in the Foundry portal. It opens on a tab called
   **Trajectories**, and reads from top to bottom like the one you just
   opened:
   - **invoke_agent** at the top is Foundry's own record of the request.
   - **kiosk-builder** under it's the agent's record, from `tracing.py`.
   - Each step below is labelled **Chat** for a model call or **Execute
     Tool** for a tool call.
   - The badges at the top right total the spans, chat calls, tool calls,
     time, and tokens for the whole request.
4. The same refusal, as a step named **execute_tool Write (refused)**. It shows
   as failed, which is expected: that's how a refusal is recorded. The limits
   travel with the agent.

![The hosted agent's trace in the Foundry portal](images/08.1-hosted-agent-trace.png)

Traces tell you what the agent did. They don't tell you whether it was any
good. That's the last module.

---

## Module 2.4: Evaluations, judged by Claude (20 minutes)

One good run doesn't tell you an agent is good. **Evaluations** score every run
and keep the history, so you can see whether a change helped. In Module 2.1 you
built a judge by hand, and in Module 2.2 your code checked the agent's work.
Foundry has a built-in version of both: you register an evaluator, point it at a
dataset of runs, and the portal scores every row. This module registers two
evaluators, one with no model at all and one where Claude is the judge, and
scores four real Sparkles runs.

> Foundry also ships built-in AI-assisted evaluators (relevance, task
> adherence, and so on), which come with their own judge model. We use custom
> evaluators here so that Claude is the judge, and so you see how to bring
> your own, which is what most teams end up doing.

### Setup

```
cd ../sparkles-evals
az login
```

In a Codespace, use `az login --use-device-code` instead: it prints a code to
enter at a sign-in page in your own browser.

Check `.env` has `AZURE_AI_PROJECT_ENDPOINT` and `EVAL_ENDPOINT_CONNECTION`;
you set both up in [SETUP.md](SETUP.md) step 5.

Look at `sample_runs.jsonl`. Four rows, each one a saved Sparkles run with
four fields: what the customer asked, what the agent replied, a static report
of the kiosk page that run produced, and the receipt it printed.

**The two evaluators read different halves of each row.** The code-based one in
Step A only sees `report` and `receipt`. The Claude judge in Step B only sees
`query` and `response`. Neither sees the other's evidence, which is why they
can disagree about the same run.

| Row | The conversation | The kiosk page | The receipt | Planted problem |
|---|---|---|---|---|
| 1 | Party order: 40 cupcakes, over budget, nut allergies, hazelnut. The agent catches the total, the budget, the allergy and the bulk-order rules | all five elements present | valid | nothing: this is what good looks like |
| 2 | Two chocolate cupcakes. The agent checks stock and flags the tree-nut policy before ordering | **the order counter is missing** | valid | a broken page |
| 3 | What flavors do you have today? The agent lists flavors, some of which the shop doesn't sell | **the special of the day is missing**, and the page loads a script from another site | **`not an order`**, so nothing to parse | a broken page and a wrong answer |
| 4 | Cupcakes arrived crushed, can I get a refund? The agent says all sales are final | all five elements present | valid | **the answer is wrong**: the shop's policy gives a refund for damaged orders |

### Step A: a code-based evaluator (10 minutes)

Open `grade_sparkles.py`. It's a plain Python `grade()` function: 60 percent of
the score for required test ids present in the kiosk report, 40 percent for a
receipt that parses and has every required key. No model is involved.

Two scripts: **`register_code_evaluator.py`** uploads `grade_sparkles.py` to your
Foundry project, which you do once. **`run_cloud_eval.py code`** sends the rows
to the project and waits while Foundry scores them in the cloud. When it's done,
it prints each row's score and a report URL.

```
python register_code_evaluator.py
python run_cloud_eval.py code
```

The run prints a report URL. Open it in the portal.

![Code evaluator report](images/09-eval-code-report.png)

**How the score is worked out.** `grade_sparkles.py` gives each row a number
from 0 to 1, in two parts:

- **0.6 for the kiosk**, split across the five required test ids. Each one
  present is worth 0.12.
- **0.4 for the receipt**, all or nothing: it has to parse as JSON, carry every
  required key, and total more than zero.

**The threshold is separate from the score.** It's set to 0.9 in
`run_cloud_eval.py`, and it decides where pass turns into fail. It changes no
scores; it only moves the line. At 0.9 a row has to have every test id *and* a
valid receipt, which is the same standard the loop in Module 2.1 enforced.

**What you should see:**

| Row | Score | Why | |
|---|---|---|---|
| 1 party order | 1.00 | all five elements on the page, receipt parses | pass |
| 2 chocolate | 0.88 | `order-count` missing, costing 0.12. Receipt fine | **fail** |
| 3 flavors | 0.48 | `special` missing, and `not an order` won't parse, losing the whole 0.4 | **fail** |
| 4 refund | 1.00 | nothing structurally wrong | pass |

Two of four, so the report reads 50%.

The chocolate row is worth pausing on. It's missing the order counter, the
same fault the evaluator caught in Module 2.1, and it still scores 0.88. Set
the threshold at 0.5 and this kiosk ships. A weighted score makes one missing
element look like a rounding error.

And the refund row passes at 1.00 while telling the customer something false,
because the checks never read the answer.

### Step B: an endpoint-based evaluator, Claude as judge (10 minutes)

Some things can't be graded by rules. Did the agent tell the customer the
truth about the refund policy? No static check can answer that. For it you
need a model that has read the same policy document the agent should have.

In [SETUP.md](SETUP.md) step 5 you deployed a small service (see
`eval-endpoint/` in the repo). It receives each row, asks the Claude
deployment to grade the response against a rubric, and returns a score and a
one-sentence reason. The judge is given the same store document that feeds
the Foundry IQ knowledge base, so it can check policy claims against the
source. Foundry calls it through a project connection.

> **Not deployed it yet?** Allow about 20 minutes, most of it the container
> build and deploy. Start it in a separate terminal and carry on reading while
> it runs.

The same two scripts, pointed at the endpoint, score the same four rows, so you
can compare the two judges on identical data.

Check the endpoint is working before you run anything. This is the single
most common reason Step B fails:

In PowerShell:

```
$url = (Select-String -Path ..\.env -Pattern '^EVAL_ENDPOINT_URL="(.*)"').Matches[0].Groups[1].Value
Invoke-RestMethod ($url -replace '/evaluate$', '/health')
```

In bash:

```
curl $(grep EVAL_ENDPOINT_URL ../.env | cut -d'"' -f2 | sed 's|/evaluate|/health|')
```

You want the model name back, for example `claude-sonnet-5-5`. That shows the
service is up and has a model set. It doesn't prove the call to Claude works,
so if every row comes back as **Error** rather than a score, use the
Troubleshooting section in
[eval-endpoint/README.md](../eval-endpoint/README.md) before going on.

```
python register_endpoint_evaluator.py
python run_cloud_eval.py endpoint
```

Open the report. Each row now carries a score and a **reason**, and the reason
is Claude's own sentence about the response.

![Claude-judged report](images/10-eval-llm-report.png)

> **Your numbers may not match these exactly.** A model judge isn't
> deterministic: run the same row twice and the score can move, and a row near
> the threshold can land either side of it. The party order is the one most
> likely to differ, because there's more in it to get right. If a row scores
> differently for you, read the reason rather than the number — that's the
> part that tells you what the judge actually objected to.
>
> If you needed this steadier in production, the levers are a more capable
> judge model, a rubric with less room for interpretation, or scoring each row
> two or three times and taking the median.

Put it next to the Step A report:

| Row | Code evaluator | Claude judge | |
|---|---|---|---|
| 1 party order | pass, 1.00 | pass | the kiosk page and receipt are complete, and the answer is right |
| 2 two chocolate | **fail, 0.88** | pass, 0.85 | the page is missing its order counter, but the agent answered well |
| 3 flavors | fail, 0.48 | fail, 0.00 | the page and receipt are broken, and the agent listed flavors the shop doesn't have |
| 4 refund | pass, 1.00 | **fail, 0.00** | the page is fine, but the agent gave the wrong refund policy |

Every combination is represented: one row both accept, one each that only one
of them objects to, and one they both reject.

**They aren't two opinions about the same thing.** Each one looks at a
different part of the run:

- the code evaluator checks **the kiosk page and the receipt**: are the five
  elements on the page, and does the receipt parse
- the Claude judge checks **what the agent said to the customer**: is it true,
  and does it match the store's policy

So a run is good when both pass, and when one fails you know which part to fix:
the page, the agent, or both. The table above shows which for each row.

The refund row is the one to remember. No static check could have caught it,
because nothing about the page or the receipt is wrong. The only way to find it
is to have something read the answer against the policy.

✅ **Checkpoint 11.** Two evaluators registered and the same four sample
conversations scored by each, in the
Foundry portal, with Claude's written reasoning in the results.

> Take it home. These four rows were saved in advance. Foundry can also call
> a hosted agent itself and score what comes back, so every new version is
> tested before anyone relies on it. `sparkles-hosted/eval_hosted.py` does
> that for the kiosk builder, once you've hosted it (end of Module 2.3).

### 🎉 Lab 2 Wrap Up

You've now met the same idea four times, each with more of the platform
behind it:

1. Module 2.1: a Claude evaluator you ran by hand inside a loop
2. Module 2.2: checks your code ran on the agent's work after it stopped
3. Step A: rule-based checks, registered in Foundry, run at scale, history kept
4. Step B: Claude as judge, behind an endpoint you own, inside Foundry's evaluation service

The same evaluators can also run continuously on sampled production traffic, so the question "is the agent still good?"
gets answered every day, and your team reads the rows that failed instead of
every transcript.

**For your own agents.** These five habits carry over to any agent you build:

1. Write down what done means before the agent starts.
2. Limit what it can touch, with rules it can't talk its way around.
3. Check the result with something other than the agent's own account.
4. Keep a record of what it did.
5. Know what your checks don't prove, and look at that part yourself.

**To compare models on your own work after this lab:**

1. Build a small test set from your real prompts.
2. Run it on each model you're considering.
3. Score every run with the same evaluators, then compare the results and the
   speed.

To go further, see [Define success criteria and build evaluations](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)
and [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).

In Lab 1 you built an agent. In Lab 2 you ran agents with confidence: a
judge caught what the writer missed, limits kept the agent on task, records
showed every step it took, and scores measured the result. Autonomy without
evaluations is hope. Autonomy with evaluations is engineering.
