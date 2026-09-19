## Module 2.3: See everything it did with Foundry observability (20 minutes)

The loop you just ran made half a dozen model calls. Which agent took the
longest? How many tokens did the fast model use compared with the smart one?
Did the evaluator's score actually improve round by round? Application Insights
answers all of that from a few lines of code.

Note: the Foundry portal's Traces tab shows agents hosted in Foundry. This
script runs on your laptop and calls Claude directly, so its traces live in
Application Insights in the Azure portal. That is the normal path for any
external application that uses Claude on Foundry.

### Turn tracing on

In '.env', set:

```
ENABLE_OTEL="1"
APPLICATIONINSIGHTS_CONNECTION_STRING="<from your instructor>"
```

That is the only change you make. The scripts already do the rest, in
'sparkles-loop/common.py' — the shared file all three import for the Claude
client, the model names, and the tracing.

- **'setup_tracing()'** runs when the loop starts. It checks those two settings,
  and if either is missing it prints why and carries on without tracing.
- **'span'** is a small wrapper the three scripts put around each call to
  Claude. It starts a timer, records which model ran and how many tokens went
  in and out, and closes when the call returns.
- Each span is named after the script that opened it: 'planner', 'generator',
  or 'evaluator'. Those are the names you will look for in the portal.
- **'session_span()' and 'run_span()'** give the trace its shape: one span
  around the whole run, and one around each round inside it.

#### Step 1: Run the loop again

```
python run_loop.py
```

The first line of output should be `Tracing on: spans go to Application
Insights.`

The whole run becomes one trace, with the planner first and each round nested
underneath. The `POST` rows are captured automatically from the HTTP client;
the rest come from `session_span()`, `run_span()` and `span()` in `common.py`.

```
sparkles-session
  planner          -> POST /anthropic/v1/messages
  sparkles-run (round 1)
    generator      -> POST /anthropic/v1/messages
    evaluator      -> POST /anthropic/v1/messages
  sparkles-run (round 2)
    generator      -> POST /anthropic/v1/messages
    evaluator      -> POST /anthropic/v1/messages
```

The planner sits outside the rounds because it runs once, before any of them.

While the loop runs, take a look at `common.py` and find the `span` class. Note
the three things it attaches to every agent call: the model, the token counts,
and anything the loop passes to `sp.set(...)` such as the evaluator's score.

Traces take 2 to 5 minutes to appear in the portal. Continue to Step 2 once
the loop has finished and a few minutes have passed.

#### Step 2: Look at the run as a trace

1. In the Application Insights resource, open **Investigate > Search**.
2. Set the time range to **Last 30 minutes**.
3. Select **View as traces**. Each `sparkles-session` card is one run of the
   script. Before opening anything, look at the card header: it shows the run's
   duration, the number of spans, and a token badge (for example `12,400t`) for
   the whole run. Azure reads the `gen_ai.usage.*` attributes and totals them
   for you.
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

![Investigate > Search, cards](../images/06-search-cards.png)

![Investigate > Search, one run open](../images/07-search-trace.png)

Questions to answer from this view:

- Which agent is the slowest? Is it the one you expected?
- Compare the generator's tokens with the planner's. Why is the generator on
  the fast model?
- Open the evaluator in each round in turn. Does the score go up?

#### Step 3: Query across rounds

1. Open **Monitoring > Logs**. Two settings take you straight to the KQL
   editor, and both stick for your account:
   - In the **Queries hub** dialog, switch off **Always show Queries hub** and
     close it with the X.
   - Switch off the **Agent** toggle at the top right of the page.

   > Optional, before you switch the Agent off: the **Observability Agent**
   > writes KQL for you. Ask it "show me evaluator spans with their
   > sparkles.score by round" and compare what it produces with the queries
   > below.
2. Paste the following into the editor and select **Run**. It gives the cost
   picture per agent and model.

   ```kusto
   dependencies
   | where timestamp > ago(1h)
   | where name in ("planner", "generator", "evaluator")
   | summarize calls = count(),
       avg_seconds = round(avg(duration) / 1000, 1),
       input_tokens = sum(toint(customDimensions["gen_ai.usage.input_tokens"])),
       output_tokens = sum(toint(customDimensions["gen_ai.usage.output_tokens"]))
       by name, model = tostring(customDimensions["gen_ai.request.model"])
   ```

3. Now the question the whole lab is about: did the loop get better? Run this
   and switch the result to **Chart** if it does not render one automatically.

   ```kusto
   dependencies
   | where timestamp > ago(1h)
   | where name == "evaluator"
   | extend score = todouble(customDimensions["sparkles.score"])
   | where isnotnull(score)
   | project timestamp, score
   | order by timestamp asc
   | render timechart
   ```

   `sparkles.score` is the number of acceptance criteria the evaluator passed,
   and `sparkles.criteria` is how many there were, so a round that fixes one
   problem moves from 3 to 4 out of 4. The evaluator sets both in
   `evaluator.py`, just after it parses the verdict.

   A rising line is the evaluator forcing the generator to improve. A flat line
   means the criteria are too easy or the feedback is not reaching the
   generator.

![Trace tree and the score chart](../images/08-trace-tree-chart.png)


**Checkpoint 10.** Your planner, generator, and evaluator run visible in
Application Insights, and you can name the slowest span.

Traces tell you what the agent did. They do not tell you whether it was any
good. That is the last module.
