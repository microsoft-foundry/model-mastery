"""Module 2.4b: register the endpoint-based evaluator (Claude is the judge).

In the workshop, Skillable sets up the endpoint and the project connection to
it for each attendee (see eval-endpoint/). Attendees only register an evaluator
that references the connection by name.

Run:  python register_endpoint_evaluator.py
"""

import os

from common import ENDPOINT_EVALUATOR, project_client

connection = os.environ.get("EVAL_ENDPOINT_CONNECTION", "mm-eval-endpoint")

client = project_client()
evaluator = client.beta.evaluators.create_version(
    name=ENDPOINT_EVALUATOR,
    evaluator_version={
        "name": ENDPOINT_EVALUATOR,
        "categories": ["quality"],
        "display_name": "Sparkles answer quality, judged by Claude",
        "description": "Delegates scoring to the workshop eval endpoint, which grades with Claude.",
        "definition": {
            "type": "endpoint",
            "connection_name": connection,
        },
    },
)
print(f"Registered {ENDPOINT_EVALUATOR} against connection '{connection}'")
