## Module 2.3: See everything it did with Foundry observability (30 minutes)

You've now run the job two ways: a loop your scripts ran, and an agent that
ran its own. Application Insights records every step of both. The more an
agent does on its own, the more this record matters: it's how you know what it
did, and how you show it to someone else.

Note: these scripts run on your machine, so their traces are in Application
Insights in the Azure portal. The Foundry portal's Traces tab shows agents
hosted in Foundry, and you'll see one at the end of this module.

### Turn tracing on

In '.env', in the 'anthropic' folder, find the line 'ENABLE_OTEL="0"' and change
the 0 to a 1. Don't add a new line. It should now read:

```
ENABLE_OTEL="1"
```

Save the file.

'APPLICATIONINSIGHTS_CONNECTION_STRING', on the line below it, is already
filled in for you. If it's empty, tell your instructor.

That's the only change you make. The loop and the agent already do the rest.
Once they've run, you'll be able to answer four questions:

- Which step was slowest?
- How many tokens did each model use?
- Did the score improve from round to round?
- What was the agent refused, and why?

Where the record comes from: 'sparkles-loop/common.py' wraps each call to
Claude in a span. The Claude Agent SDK runs Claude in a program of its own, so
'sparkles-hosted/tracing.py' turns each message the agent sends back into a
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

The first line of output from each should be 'Tracing on: spans go to
Application Insights.'

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
'tracing.py' and find 'tool_finished()'. It's where a refusal is written
onto the span.

#### Step 2: Look at the loop's run (5 minutes)

1. In Edge, open [https://portal.azure.com](https://portal.azure.com). If it
   asks you to sign in, use the same workshop account as in Module 1.0:

   **Username**: `@lab.CloudPortalCredential(User1).Username`  
   **Access Pass**: `@lab.CloudPortalCredential(User1).AccessToken`

2. In the search bar at the top of the portal, type 'Application Insights',
   select it, and open the workshop's resource from the list.
3. In the resource's left menu, open **Investigate > Search**.
4. Set the time range to **Last 30 minutes**.
5. Select **View as traces**. Each card is one run of a script. The header of a
   'sparkles-session' card shows the run's duration, spans, and tokens.
6. Click the header line of the card (the trace ID and 'sparkles-session' name,
   not the "Matching Dependency" box underneath). The end-to-end transaction
   page opens as a timeline: the planner at the top, then each round below it,
   with the generator and evaluator inside and the actual Claude call underneath
   each.
7. In that timeline, click the **evaluator** bar (not the POST beneath it). The
   panel on the right lists that span's properties: the model,
   'gen_ai.usage.input_tokens', 'gen_ai.usage.output_tokens', and the
   'sparkles.*' values the loop recorded. If the panel looks short, look for a
   "show all" or "leave simple view" link on it.

![Investigate > Search, cards](../images/06-search-cards.png)

![Investigate > Search, one run open](../images/07-search-trace.png)

Questions to answer from this view:

- Which agent is the slowest? Is it the one you expected?
- Compare the generator's tokens with the planner's. Why is the generator on
  the fast model?
- Open the evaluator in each round in turn. Does the score go up?

#### Step 3: Look at the agent's run (5 minutes)

1. Go back to **Search** and open the 'kiosk-builder' card the same way.
2. Read the timeline from top to bottom. Model calls and tool calls take
   turns: Claude decides, a tool runs, Claude reads the result and decides
   again.
3. Click the top **kiosk-builder** bar. Its properties are the totals for the
   task: 'sparkles.turns', 'sparkles.cost_usd', 'sparkles.passed',
   'sparkles.stopped_because', and the 'gen_ai.usage.*' token counts.
4. Find the bar named **execute_tool Write (refused)** and click it.
   'sparkles.file' is 'backup.html', and 'sparkles.refused_or_failed' is the
   reason the rule gave. The refusal is in the step's name so that it stands
   out in any trace viewer.

Questions to answer from this view:

- Where did the time go: the model calls, or the tools?
- The loop needed a planner, a generator, and an evaluator. How many model
  calls did the agent need for the same page?
- Could someone who wasn't in the room tell from this trace what the agent
  was refused, and why?

#### Step 4: Query across runs (5 minutes)

1. In the same Application Insights resource, open **Monitoring > Logs** in the
   left menu. If the editor opens in **Simple mode** (a dropdown at the top
   right), switch it to **KQL mode**. Two settings take you straight to the KQL
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

   'sparkles.score' is the number of acceptance criteria the evaluator passed,
   and 'sparkles.criteria' is how many there were, so a round that fixes one
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

![Trace tree and the score chart](../images/08-trace-tree-chart.png)

### Call the same agent, hosted in Foundry (10 minutes)

So far the agent has run on your machine. Your instructor has deployed the
same 'agent.py' as a **hosted agent** in the workshop's Foundry project.
Foundry keeps it running, gives it an identity, and takes requests for it.
You'll send it a task and read its trace.

**Why host it?** On your machine, this agent stops when you close the terminal,
and it depends on a key in '.env'. Hosted in Foundry, it's available whenever
it's called, it has its own identity with no key to leak, and you control who
can call it.

**Why the two fit together.** The Claude Agent SDK decides what the agent can do.
Foundry decides who it is, where it runs, and who can call it. An agent that
works on files needs a real working folder, and each hosted session gets its
own. The limits are in the code, so they travel with it.

| On your machine | Hosted in Foundry |
|---|---|
| You start it from a terminal | Foundry runs it, and anything with permission can send it a task |
| It signs in with the key in '.env' | It has an identity of its own, and there's no key to store or leak |
| The page is in 'workspace/' | Each session gets a folder of its own, and the page is still there on the next request |
| You turned tracing on in '.env' | Foundry records every request, with the agent's own spans underneath |

What had to be added is small: 'main.py', a web server of 60 lines that
receives a task and calls 'build_kiosk()', and a 'Dockerfile'. 'agent.py' is
the file you just ran.

1. Sign in. A hosted agent takes no key, so it needs to know who you are:

   ```
   az login --use-device-code
   ```

   The command prints a code and a web address. Open the address in Edge, enter
   the code, and sign in with the same workshop account as in Module 1.0. Then
   come back to the terminal. If it asks you to select a subscription, press
   Enter to keep the default.

2. From 'sparkles-hosted', send the task that asks for a second file:

   ```
   python invoke.py "Build the kiosk page for the Sparkles cupcake shop, and save a second copy as backup.html"
   ```

   It takes 30 to 60 seconds. The first line is 'HTTP 200', the time, and a
   session. Then the same report you read in Module 2.2 prints, this time
   from Foundry. Find 'did_not_run' in 'steps': the agent was refused the
   second file there too. The limits travel with the agent.

3. Open the trace. In the Foundry portal, open the project, find the agent
   'sparkles-kiosk-builder', and open its traces. Everyone in the room is
   calling the same agent, so pick the trace with the time you sent yours.
   Traces take a few minutes to appear.

   It opens on a tab called **Trajectories**, and reads from top to bottom
   like the one you opened in Application Insights:
   - **invoke_agent** at the top is Foundry's own record of the request.
   - **kiosk-builder** under it's the agent's record, from 'tracing.py'.
   - Each step below is labelled **Chat** for a model call or **Execute
     Tool** for a tool call.
   - The badges at the top right total the spans, chat calls, tool calls,
     time, and tokens for the whole request.

4. Find the step named **execute_tool Write (refused)**. It's the same
   refusal, recorded the same way. It shows as failed, which is expected:
   that's how a refusal is recorded.

![The hosted agent's trace in the Foundry portal](../images/08.1-hosted-agent-trace.png)

> Try it: keep working on the same page. Copy the session from the first
> line of step 2 and run 'python invoke.py --session <session> "Make the
> order button pink"'. The page from your first request is still there to
> change.

> If step 2 prints 'HTTP 401' or 'HTTP 403', your account isn't allowed to
> call the agent. Tell your instructor, and follow this part on the main
> screen.

**How it was deployed.** Your instructor built a container image from 'agent.py',
'main.py', and the checks, created the hosted agent with 'deploy.py', and gave its
identity permission to call Claude.

> Do it yourself after the workshop. 'sparkles-hosted/README.md' has the commands.
> You need your own Azure subscription, a container registry, and the right to
> assign roles. Allow about 30 minutes. The commands are written for bash, so on
> Windows, run them in a GitHub Codespace.

✅ **Checkpoint 10.** The loop and the agent both visible in Application
Insights. You can name the slowest span, and you can show what the agent was
refused. You've also called the same agent hosted in Foundry.

Traces tell you what the agent did. They don't tell you whether it was any
good. That's the last module.
