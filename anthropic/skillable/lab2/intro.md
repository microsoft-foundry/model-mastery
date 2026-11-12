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
- Call the same agent, hosted in Foundry, with an identity of its own and the same limits and traces
- Register evaluators and score runs in Foundry, with Claude's written reasoning in the results

**How the lab works.** Everything runs from scripts already in
'sparkles-loop/', 'sparkles-hosted/' and 'sparkles-evals/'. You read them, run
them, and change what they do. Each module ends with a checkpoint.

**If your lab environment reset between labs**, copy 'sparkles-agent/snapshots/agent-module-1.4.py'
over 'agent.py' and check that '.env' is still filled in. Everyone else starts
at Module 2.1.
