# 6 · Improve the model with Model Router

| Time | 8 mins |
|:---|:---|
|_Question:_  | My frontier model is accurate but expensive — can I cut cost and latency without losing quality? |
|_Goal:_| Change **one lever** — the model — and re-measure. |
|||

<br/>

## What is Model Router?

Model Router is a deployment that picks a model **per request** instead of you
choosing one up front. Simple questions can go to a small fast model; hard ones
to a stronger one — without changing your agent's tools or instructions.

> ⚠️ **Not a guaranteed win.** Routing might cut cost, hold quality, or trade a
> little of one for the other. Your job is to *measure*, not assume.

## Step 1 — Create v2 (same everything, new model)

From the `src/agent` folder:

```bash
python switch_to_router.py
```

This creates a **new version** of the same agent that changes only the model —
now `model-router`. It reuses the **same** file-search tool and the **same**
vector store (no re-upload) and the **same** instructions.

**Expected:** it prints the new version and confirms the model is `model-router`.

## Step 2 — See what changed in the code

Compare [`switch_to_router.py`](../../src/agent/switch_to_router.py) with
[`build_agent.py`](../../src/agent/build_agent.py). The only difference in the
agent definition is one line: `"model": "model-router"`. **One lever.**

## Step 3 — Re-run the SAME evaluation

Run the **same** evaluation from lesson 5 (same dataset, same `trailmate_quality`
rubric) against **v2**.

<!-- TODO: screenshot — evaluation run targeting trailmate v2 -->

Then compare to your v1 baseline:

| | v1 (frontier) | v2 (router) |
|---|---|---|
| Overall rubric score | | |
| Latency (from traces) | | |
| Which model(s) answered | one | several |

> 💡 Open a v2 trace to see **which** model Model Router picked for a request —
> it can differ question to question.

<!-- TODO: screenshot — v2 trace showing the routed model -->

## Step 4 — The decision rule

**A model change only counts if quality holds.** If the router keeps the rubric
score roughly steady while cutting cost or latency, that's a win. If grounding
drops, the router loses — no matter what it does to cost.

## ✅ You changed the model layer

One line, one lever, re-measured. Next, leave the model alone and improve the
**instructions**.

➡️ Next: [Improve the agent with Agent Optimizer](07-agent-optimizer.md)
