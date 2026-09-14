# 7 · Improve the agent with Agent Optimizer

| Time | 8 mins |
|:---|:---|
|_Question:_  | The model's fine, but response quality needs improvement — how can I improve the agent without endless manual tinkering? |
|_Goal:_| Change the other lever — the **instructions** — using Agent Optimizer, guided by the same rubric. |
|||

<br/>

## What is Agent Optimizer?

Instead of you hand-editing the prompt and re-testing over and over, **Agent
Optimizer** proposes new instruction wordings, scores each against your dataset
and rubric, and ranks them. You review the winner and decide. It's a guide that
scouts several steps up the hill — you still choose the step.

Agent Optimizer supports **prompt agents** and runs in the **portal**. Follow the
[optimize a prompt agent quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent).

## Step 1 — Start an optimization

In the portal, open **trailmate** (the router version, v2) and start **Agent
Optimizer**. Point it at:

- **Dataset:** `evaluation-cases.jsonl`
- **Evaluator:** the same `trailmate_quality` rubric from lesson 5

<!-- TODO: screenshot — Agent Optimizer setup: agent, dataset, evaluator -->

> Keeping the **same dataset and rubric** means the optimizer's candidate scores
> are directly comparable to your baseline. That's the frozen yardstick again.

## Step 2 — Review the candidates

The optimizer generates candidate instruction sets and scores each one. Read the
**diffs** and the scores.

<!-- TODO: screenshot — candidate list with scores and instruction diffs -->

Look for the candidate that improves the constraints you care about most —
**grounding, appropriate refusal, and staying in scope** — without regressing the
others. A good candidate typically adds: *search first and cite the product; if
the manuals don't cover it, say so; decline off-topic requests and steer back to
products; keep answers concise.*

> 📄 A reference of what a strong optimized instruction set looks like is checked
> in at [`instructions_optimized.md`](../../src/agent/instructions_optimized.md).
> Your optimizer result should look similar in spirit.

## Step 3 — Apply the winner as v3

Apply the chosen candidate. This creates **TrailMate v3** — same model (router),
same file-search tool, **new instructions**.

<!-- TODO: screenshot — applying the winning candidate / new version created -->

**Expected:** v3 exists as a new version of the same agent.

## Step 4 — Re-run the SAME evaluation

Evaluate **v3** with the same dataset and rubric. Try the off-topic request again
in the playground (the hot-chocolate recipe) — v3 should now **politely decline**
and steer back to product questions instead of answering it.

> 🧭 **Optional (on your own):** Agent Optimizer can also explore **model**
> candidates, not just instructions. After the workshop, try letting it compare
> models too — that's multi-lever optimization.

## ✅ You improved the instructions

By changing only the instructions, TrailMate went from guessing to grounded and
honest. Now let's compare all three versions and decide.

➡️ Next: [Compare and promote](08-compare-and-promote.md)
