# Lab 2: Making Your Agent Work over a Long Horizon

This morning you built the Sparkles agent and watched it every step of the
way. This afternoon the shop wants software built with nobody watching, and
then it wants to know whether it can trust what came out.

The job: Sparkles needs an ordering kiosk page for the counter. You will run
a loop where one Claude plans it, another builds it, and a third judges the
result and sends it back until it passes. Then you will use Foundry to run
that pattern properly: a searchable tool catalog, traces of every step, and
evaluations where Claude is the judge.

By the end of this lab you will have:

- Run a planner, generator, and evaluator loop that catches a planted bug and fixes it
- Grounded the plan in web search and let Claude find tools by searching a catalog
- Seen every model call, token count, and latency in the Foundry portal
- Registered evaluators and scored real runs in Foundry, with Claude's written reasoning in the results

**How the lab works.** Everything runs from scripts already in
'sparkles-loop/' and 'sparkles-evals/'. You read them, run them, and change
what they do. Each module ends with a checkpoint.

**If your seat reset over lunch**, copy 'sparkles-agent/snapshots/agent-module-1.4.py'
over 'agent.py' and check that '.env' is still filled in. Everyone else starts
at Module 2.1.

**Idea that runs through the afternoon:** the agent that writes is not the
agent that judges. You will meet that idea three times, at three levels of
polish.
