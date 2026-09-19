"""Run a cloud evaluation over sample_runs.jsonl and open the report.

Run:  python run_cloud_eval.py code        (Module 2.4a: code-based evaluator)
      python run_cloud_eval.py endpoint    (Module 2.4b: Claude-judged endpoint)
      python run_cloud_eval.py both

Cloud evaluations use the project's evals API surface.
"""

import json
import sys
import time
from pathlib import Path

from common import CODE_EVALUATOR, DEPLOYMENT, ENDPOINT_EVALUATOR, SEAT, project_client

which = sys.argv[1] if len(sys.argv) > 1 else "both"
rows = [json.loads(l) for l in (Path(__file__).parent / "sample_runs.jsonl").read_text().splitlines() if l.strip()]

criteria = []
if which in ("code", "both"):
    criteria.append({
        "type": "azure_ai_evaluator",
        "name": "sparkles_code",
        "evaluator_name": CODE_EVALUATOR,
        # 0.9: every required test id present and a receipt that parses. A single
        # missing element scores 0.88, so at 0.5 the buggy kiosk passed.
        "initialization_parameters": {"deployment_name": DEPLOYMENT, "pass_threshold": 0.9},
        # No data_mapping: a code-based evaluator receives the whole row as `item`.
    })
if which in ("endpoint", "both"):
    criteria.append({
        "type": "azure_ai_evaluator",
        "name": "claude_judge",
        "evaluator_name": ENDPOINT_EVALUATOR,
        "data_mapping": {"query": "{{item.query}}", "response": "{{item.response}}"},
    })

evals_client = project_client().get_openai_client()

ev = evals_client.evals.create(
    name=f"sparkles-{which}-{SEAT}",
    data_source_config={
        "type": "custom",
        "item_schema": {
            "type": "object",
            "properties": {k: {"type": "string"} for k in ("query", "response", "report", "receipt")},
        },
        "include_sample_schema": False,
    },
    testing_criteria=criteria,
)

run = evals_client.evals.runs.create(
    eval_id=ev.id,
    name=f"run-{int(time.time())}",
    data_source={
        "type": "jsonl",
        "source": {"type": "file_content", "content": [{"item": r} for r in rows]},
    },
)
print(f"Started run {run.id}; waiting...")

while True:
    run = evals_client.evals.runs.retrieve(eval_id=ev.id, run_id=run.id)
    if run.status in ("completed", "failed", "canceled"):
        break
    time.sleep(5)

print(f"Status: {run.status}")
print(f"Report: {run.report_url}")
for item in evals_client.evals.runs.output_items.list(eval_id=ev.id, run_id=run.id):
    for res in item.results:
        r = res if isinstance(res, dict) else res.model_dump()
        err = ((r.get("sample") or {}).get("error") or {}).get("message")
        note = f"  error: {err[:120]}" if err else f"  reason: {str(r.get('reason') or '')[:120]}"
        print(f"  {r.get('name')}: score={r.get('score')} passed={r.get('passed')}{note}")
