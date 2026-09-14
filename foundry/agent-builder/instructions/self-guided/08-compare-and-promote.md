# 8 · Compare and promote

| Time | 5 mins |
|:---|:---|
|_Question:_  | I have three versions — which one do I actually ship, and how do I defend that choice? |
|_Goal:_| Put the three versions side by side and promote the one the evidence supports. |
|||

<br/>

## Step 1 — Line up the scores

Fill this from your three evaluation runs (all used the same dataset and rubric):

| Version | Lever changed | Rubric score | Latency | Notes |
|---|---|---|---|---|
| v1 · Basecamp | frontier model + simple instructions | | | baseline |
| v2 · Trailfinder | model → Model Router | | | quality hold? cost/latency? |
| v3 · Summit | instructions → optimized | | | grounding/refusal/scope up? |

<!-- TODO: screenshot — evaluation comparison across v1, v2, v3 -->

## Step 2 — The decision rule

1. Did **quality** hold or improve? (For TrailMate: grounding, honest refusal, and staying in scope.)
2. Did anything else regress? (latency, cost)
3. Is the change small and explainable?

Promote the version the evidence supports — not the newest by default. Usually
that's **v3** (optimized instructions on the router), because it improves the
constraint that matters most while keeping the router's efficiency.

## Step 3 — Promote it

Set the chosen version as the active one for TrailMate.

<!-- TODO: screenshot — setting the active/promoted agent version -->

## The hill you climbed

```text
v1 Basecamp     → measured baseline (your altitude)
v2 Trailfinder  → one lever: model → router   → re-measured
v3 Summit       → one lever: instructions      → re-measured → promote
```

You never changed two things at once, and you never guessed — every step was
measured against the same yardstick. That's hill climbing.

## What you learned

- Pick a model by trying it on the real task, not by reputation.
- An agent = a model + instructions + tools (here, file search over your data).
- Observe (traces) and **measure** (eval + rubric) before you optimize.
- Improve **one lever at a time** — model (Model Router) or instructions (Agent
  Optimizer) — and re-measure each time.
- Promote with evidence.

## Where to go next

- Grow the eval dataset from real questions and run it on every change.
- Let Agent Optimizer explore **model** candidates too (multi-lever).
- Add more products/manuals and watch how grounding scales.

🏁 That's the workshop. Nice work building and climbing with TrailMate.

⬆️ [Back to the steps](README.md) · 🏠 [Workshop overview](../../README.md)
