# TrailMate — versioned changes (for reproducibility)

Every version changes **exactly one lever** from the one before it. The
evaluation dataset (`../data/evaluation-cases.jsonl`) and the rubric
(`../data/evaluators/trailmate-quality.yaml`) stay **frozen** across all
versions, so the scores are directly comparable — that is what makes the hill
climb measurable.

The vector store and the 10 uploaded manuals are created **once** in v1. v2 and
v3 create new agent versions that **reference the same vector store** — the
manuals are never re-uploaded.

| Version | Name | Lever changed | Model | Instructions | Tool | How to reproduce |
|---|---|---|---|---|---|---|
| **v1** | Basecamp | starting point | `gpt-5.4` (frontier) | `instructions.md` (under-specified) | file-search over the manuals | `python build_agent.py` |
| **v2** | Trailfinder | **model** → router | `model-router` | same as v1 | same file-search / same vector store | `python switch_to_router.py` |
| **v3** | Summit | **instructions** → optimized | `model-router` | optimizer output (reference: `instructions_optimized.md`) | same file-search / same vector store | Agent Optimizer in the portal (Step 7), or apply `instructions_optimized.md` as a new version |

## What changed and why

- **v1 → v2 (model lever).** We keep the exact same instructions and tool and
  only swap the model to Model Router. This isolates the question: *can a
  per-request model choice hold quality while improving cost/latency?*
- **v2 → v3 (instructions lever).** We keep the model (router) and only improve
  the instructions. v1's instructions are deliberately vague; the optimized
  instructions add: search first and cite the product, refuse when the manuals
  don't cover it, disambiguate similar products, and keep answers concise.

## Optional exercise (not part of the core 90 minutes)

When you set up Agent Optimizer, it can **also** explore **model** candidates,
not just instructions. Try letting it compare models as a follow-up experiment
on your own — it's a great way to see multi-lever optimization.
