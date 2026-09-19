"""Evaluator: a separate Claude session judges the evidence against the spec.

It never sees the generator's reasoning or the HTML itself, only the facts
the static checks reported. Structured outputs guarantee a parseable verdict.

Run:  python evaluator.py     (uses workspace/spec.json and workspace/index.html)
"""

import json

from checks import evidence
from common import first_text, SMART_MODEL, WORKSPACE, banner, client, span

VERDICT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
                    "evidence": {"type": "string"},
                },
                "required": ["id", "verdict", "evidence"],
            },
        },
        "overall": {"type": "string", "enum": ["PASS", "FAIL"]},
        "critique": {"type": "string"},
    },
    "required": ["results", "overall", "critique"],
}

SYSTEM = """You are the EVALUATOR. You receive acceptance criteria and a report from a
static analyzer that read the generated page. Judge each criterion using ONLY the
report:
1. If the report shows the criterion is met, PASS.
2. If the report shows it is not met (a required test id is MISSING, a list has too
   few items, an external resource is used), FAIL and say exactly what is wrong.
3. If the report cannot tell either way, PASS and write "not checkable" as evidence.
overall is FAIL if any criterion is FAIL. critique tells the generator precisely
what to change; empty when everything passes."""


def evaluate(c, spec: dict, report: str) -> dict:
    banner("EVALUATOR: judging the evidence")
    print(f"\033[2m{report}\033[0m\n")
    with span("evaluator", SMART_MODEL) as s:
        r = c.messages.create(
            model=SMART_MODEL, max_tokens=1500, system=SYSTEM,
            output_config={"format": {"type": "json_schema", "schema": VERDICT_SCHEMA}},
            messages=[{"role": "user", "content":
                       f"ACCEPTANCE CRITERIA:\n{json.dumps(spec['features'], indent=2)}"
                       f"\n\nSTATIC ANALYSIS REPORT:\n{report}"}])
        s.record(r)
        verdict = json.loads(first_text(r))
        passed = verdict["overall"] == "PASS"
        s.set(score=sum(1 for res in verdict["results"] if res["verdict"] == "PASS"),
              criteria=len(verdict["results"]),
              passed=passed,
              feedback=verdict["critique"])
    for res in verdict["results"]:
        mark = "\033[32mPASS\033[0m" if res["verdict"] == "PASS" else "\033[31mFAIL\033[0m"
        print(f"  {res['id']}  {mark}  \033[2m{res['evidence'][:70]}\033[0m")
    color = "\033[32m" if verdict["overall"] == "PASS" else "\033[31m"
    print(f"  overall: {color}{verdict['overall']}\033[0m")
    if verdict["critique"]:
        print(f"\n\033[33mCritique for the generator:\033[0m {verdict['critique']}")
    (WORKSPACE / "verdict.json").write_text(json.dumps(verdict, indent=2))
    return verdict


if __name__ == "__main__":
    spec = json.loads((WORKSPACE / "spec.json").read_text())
    html = (WORKSPACE / "index.html").read_text(encoding="utf-8")
    evaluate(client(), spec, evidence(html))
