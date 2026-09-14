<p align="center">
  <img src="./assets/workshop-banner.svg" alt="From Model Selection to Agent Optimization" width="100%">
</p>

# Model Mastery Workshop: Select, Build, Optimize

Build, run, and improve a grounded AI agent in 90 minutes with Microsoft Foundry.
You'll pick a model, build **TrailMate** (a product expert for Contoso Outdoors),
measure it, then climb the hill — improving one lever at a time with Model Router
and Agent Optimizer, and promoting the version the evidence supports.

## What you will build

**TrailMate** — a **prompt agent** that answers questions about Contoso Outdoors
gear using the product manuals (via a **file-search** tool), and refuses to
invent anything the manuals don't say.

<table>
<tr>
<td width="38%" valign="top">
<img src="./assets/products/alpine-explorer-tent.png" alt="Alpine Explorer Tent" width="100%">
</td>
<td width="62%" valign="top">

**You ask:**

> "Heavy rain is coming — Alpine Explorer or TrailMaster X4 tent?"

**TrailMate answers (grounded):**

> "For heavy rain, the **Alpine Explorer Tent** is the better pick — its rainfly
> is rated **3000mm** vs the **TrailMaster X4**'s **2000mm**. Both are 3-season,
> freestanding tents."

It cites the right manual for each product, and if you ask something the manuals
don't cover (like a warranty), it says so instead of guessing. Getting it to do
that **reliably** — and proving it — is the workshop.

</td>
</tr>
</table>

You'll evolve TrailMate through three measured versions, each changing **one
thing**:

| Version | One change | Lesson |
|---------|-----------|--------|
| **v1 · Basecamp** | Frontier GPT + simple instructions + file search | Build a grounded agent; measure a baseline |
| **v2 · Trailfinder** | Model → Model Router | Cut cost/latency without losing quality? |
| **v3 · Summit** | Instructions → optimized (Agent Optimizer) | Improve grounding and honesty |

## Repository layout

```text
foundry/agent-builder/
├── README.md                      you are here
├── assets/                        banner, product images, attribution
├── instructions/
│   ├── self-guided/               the workshop steps (start here)
│   └── skillable/                 Windows lab version (coming soon)
├── scripts/
│   ├── provision.sh               Azure CLI: resource, project, RBAC, models, tracing
│   ├── setenv.sh                  (re)generate src/.env from an existing resource group
│   └── sample.env                 optional provisioning overrides
└── src/
    ├── data/
    │   ├── manuals/               10 Contoso product manuals (grounding)
    │   ├── evaluation-cases.jsonl the frozen test set
    │   └── evaluators/            the frozen quality rubric
    └── agent/
        ├── build_agent.py         v1: vector store + upload + prompt agent
        ├── switch_to_router.py    v2: new version on Model Router
        ├── instructions.md        v1 instructions (simple on purpose)
        ├── instructions_optimized.md  v3 reference instructions
        ├── VERSIONS.md            documented v1/v2/v3 changes
        └── requirements.txt
```

## Prerequisites

- An Azure subscription with access to Microsoft Foundry
- GitHub Codespaces or a dev container (Python 3.13 is set up for you)
- Azure CLI (`az`) for signing in and provisioning

Models used (the [`provision.sh`](scripts/provision.sh) script deploys the
Azure-direct ones; Claude is optional and prompted):

| Deployment | Role |
|---|---|
| `gpt-5-4` | Frontier reasoning; TrailMate v1 model |
| `gpt-5-4-mini` | Fast/cheap contrast in model selection |
| `model-router` | TrailMate v2 model lever |
| `mai-image-2-6` | Image task in model selection |
| `claude-sonnet-4-6`, `claude-haiku-4-5` | Optional GPT-vs-Claude comparison |

Model names, versions, and quota vary by region — your instructor confirms them
before the workshop.

## Workshop outline

Start with **[0 · Getting started](instructions/self-guided/00-getting-started.md)**,
then work through the steps in order. Each opens with a developer question the
step answers.

| # | Step | Where | Time |
|---|------|-------|------|
| 0 | [Getting started](instructions/self-guided/00-getting-started.md) | VS Code | before you start |
| 1 | [Set up and validate](instructions/self-guided/01-setup-and-validate.md) | VS Code + Portal | 15 min |
| 2 | [Select the right model for the task](instructions/self-guided/02-model-selection.md) | Portal | 30 min |
| 3 | [Build TrailMate](instructions/self-guided/03-build-trailmate.md) | VS Code | 10 min |
| 4 | [Test and observe](instructions/self-guided/04-test-and-observe.md) | Portal | 6 min |
| 5 | [Measure a baseline](instructions/self-guided/05-baseline-eval.md) | Portal | 8 min |
| 6 | [Improve the model with Model Router](instructions/self-guided/06-model-router.md) | VS Code + Portal | 8 min |
| 7 | [Improve the agent with Agent Optimizer](instructions/self-guided/07-agent-optimizer.md) | Portal | 8 min |
| 8 | [Compare and promote](instructions/self-guided/08-compare-and-promote.md) | Portal | 5 min |

## Related resources

- [Microsoft Foundry documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [Foundry models](https://learn.microsoft.com/azure/ai-foundry/concepts/foundry-models-overview)
- [File search tool](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/tools/file-search)
- [Model Router](https://learn.microsoft.com/azure/ai-foundry/openai/concepts/model-router)
- [Agent Optimizer overview](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview)
- [Optimize a prompt agent (quickstart)](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent)
- [Evaluation in Microsoft Foundry](https://learn.microsoft.com/azure/ai-foundry/concepts/evaluation-approach-gen-ai)

Part of [Model Mastery](../../README.md) · [Browse Foundry workshops](../README.md)
