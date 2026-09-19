"""Module 2.4a: register the code-based evaluator (no LLM judge).

The shapes follow Microsoft's custom evaluators reference:
https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/custom-evaluators
deployment_name is required by the run API for orchestration even though the
code never calls a model; Microsoft states any valid project deployment name
works, so we pass the Claude deployment.

Run:  python register_code_evaluator.py
"""

from pathlib import Path

from common import CODE_EVALUATOR, project_client

code_text = (Path(__file__).parent / "grade_sparkles.py").read_text()

client = project_client()
evaluator = client.beta.evaluators.create_version(
    name=CODE_EVALUATOR,
    evaluator_version={
        "name": CODE_EVALUATOR,
        "categories": ["quality"],
        "display_name": "Sparkles kiosk + receipt checks",
        "description": "Scores the static kiosk report and the receipt JSON. No LLM judge.",
        "definition": {
            "type": "code",
            "code_text": code_text,
            # These three keys sit inside "definition". Placed beside it, they
            # are not applied and the evaluator has no parameters or metric.
            "init_parameters": {
                "type": "object",
                "properties": {
                    "deployment_name": {"type": "string"},
                    "pass_threshold": {"type": "number"},
                },
                "required": ["deployment_name", "pass_threshold"],
            },
            # Code-based evaluators receive the dataset row as `item`, so the
            # fields are declared under an "item" object (prompt-based ones are flat).
            "data_schema": {
                "type": "object",
                "required": ["item"],
                "properties": {
                    "item": {
                        "type": "object",
                        "properties": {
                            "report": {"type": "string"},
                            "receipt": {"type": "string"},
                        },
                    },
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
print(f"Registered {CODE_EVALUATOR}: {getattr(evaluator, 'version', evaluator)}")
