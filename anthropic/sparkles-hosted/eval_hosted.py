"""Evaluate the hosted agent: Foundry sends it tasks and scores what comes back.

Module 2.4 scored four saved runs. Here nothing is saved in advance. Foundry
calls the hosted agent once per task, and a code-based evaluator scores each
reply from the check report inside it. No model is the judge.

Run:  python eval_hosted.py
"""

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "sparkles-evals"))
from common import DEPLOYMENT, SEAT, project_client  # noqa: E402

AGENT_NAME = os.environ.get("HOSTED_AGENT_NAME", "sparkles-kiosk-builder")
EVALUATOR = f"sparkles-hosted-checks-{SEAT}"

TASKS = [
    "Build the kiosk page for the Sparkles cupcake shop. Flavors: Vanilla Dream, "
    "Double Chocolate, Lemon Zest. Special: Lemon Zest.",
    "Build the kiosk page for the Sparkles cupcake shop with six flavors of your "
    "choice and a special. The order button adds one to the order count.",
    "Build the kiosk page for the Sparkles cupcake shop. Load the fonts and the "
    "styles from a CDN so that it looks modern.",
]

client = project_client()
agent = client.agents.get(agent_name=AGENT_NAME)
version = agent.versions.latest.version

registered = client.beta.evaluators.create_version(
    name=EVALUATOR,
    evaluator_version={
        "name": EVALUATOR,
        "categories": ["quality"],
        "display_name": "Sparkles hosted agent: page checks",
        "description": "Scores the check report in the hosted agent's reply. No LLM judge.",
        "definition": {
            "type": "code",
            "code_text": (HERE / "grade_hosted.py").read_text(),
            "init_parameters": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string"},
                    "pass_threshold": {"type": "number"},
                },
                "required": ["deployment_name", "pass_threshold"],
            },
            "data_schema": {
                "type": "object",
                "required": ["item"],
                "properties": {
                    "item": {"type": "object", "properties": {"task": {"type": "string"}}},
                },
            },
            "metrics": {
                "result": {
                    "type": "continuous",
                    "desirable_direction": "increase",
                    "min_value": 0.0,
                    "max_value": 1.0,
                }
            },
        },
    },
)
print(f"Registered {EVALUATOR} version {registered.version}")

# Foundry's evaluations service. The score comes from the code-based evaluator.
evals_client = client.get_openai_client()

ev = evals_client.evals.create(
    name=f"sparkles-hosted-{SEAT}",
    data_source_config={
        "type": "custom",
        "item_schema": {
            "type": "object",
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
        "include_sample_schema": True,
    },
    testing_criteria=[{
        "type": "azure_ai_evaluator",
        "name": "page_checks",
        "evaluator_name": EVALUATOR,
        # Name the version just registered, so the run cannot use an older one.
        "evaluator_version": str(registered.version),
        # deployment_name is required by the run API even though the code
        # never calls a model, so we pass the Claude deployment.
        "initialization_parameters": {"deployment_name": DEPLOYMENT, "pass_threshold": 0.9},
    }],
)

run = evals_client.evals.runs.create(
    eval_id=ev.id,
    name=f"run-{int(time.time())}",
    data_source={
        "type": "azure_ai_target_completions",
        "source": {"type": "file_content", "content": [{"item": {"task": t}} for t in TASKS]},
        # A hosted agent on the invocations protocol takes the request body as
        # written here, which is what main.py reads.
        "input_messages": {"task": "{{item.task}}"},
        "target": {"type": "azure_ai_agent", "name": AGENT_NAME, "version": version},
    },
)
print(f"Started run {run.id} against {AGENT_NAME} version {version}; waiting...")

while True:
    run = evals_client.evals.runs.retrieve(eval_id=ev.id, run_id=run.id)
    if run.status in ("completed", "failed", "canceled"):
        break
    time.sleep(10)

print(f"Status: {run.status}")
print(f"Report: {run.report_url}")
for item in evals_client.evals.runs.output_items.list(eval_id=ev.id, run_id=run.id):
    task = (item.datasource_item or {}).get("task", "")[:60]
    for res in item.results:
        r = res if isinstance(res, dict) else res.model_dump()
        err = ((r.get("sample") or {}).get("error") or {}).get("message")
        note = f"  error: {err[:160]}" if err else ""
        print(f"  {r.get('name')}: score={r.get('score')} passed={r.get('passed')}  {task}{note}")
