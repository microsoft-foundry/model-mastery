"""Module 1.4 - A receipt you can trust.

Turns the agent's last reply into a schema-valid receipt using structured
outputs on Claude in Foundry. Every object in the schema sets
additionalProperties to false; the API requires it.
"""

import json
import os

from anthropic import AnthropicFoundry
from dotenv import load_dotenv

load_dotenv()

RECEIPT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "order_id": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "flavor": {"type": "string"},
                    "qty": {"type": "integer"},
                },
                "required": ["flavor", "qty"],
            },
        },
        "total_cents": {"type": "integer"},
        "pickup_time": {"type": "string"},
    },
    "required": ["order_id", "items", "total_cents", "pickup_time"],
}


def first_text(response) -> str:
    """The first text block of a response.

    Claude may return a thinking block before the answer, so content[0] is not
    reliably the text.
    """
    return next(b.text for b in response.content if getattr(b, "type", None) == "text")


def make_receipt(order_text: str) -> dict:
    """Ask Claude for a receipt that is guaranteed to match RECEIPT_SCHEMA."""
    client = AnthropicFoundry(
        api_key=os.environ["FOUNDRY_API_KEY"],
        base_url=os.environ["FOUNDRY_ENDPOINT"],
    )
    r = client.messages.create(
        model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
        max_tokens=500,
        output_config={"format": {"type": "json_schema", "schema": RECEIPT_SCHEMA}},
        messages=[{
            "role": "user",
            "content": (
                "Produce the receipt for this cupcake order. Cupcakes are 400 cents "
                "each unless the text says otherwise. If no order id is given, "
                "make one up in the form SPK-####.\n\n" + order_text
            ),
        }],
    )
    return json.loads(first_text(r))


if __name__ == "__main__":
    # Quick standalone check
    print(json.dumps(make_receipt(
        "Order placed: 3 vanilla and 2 chocolate cupcakes, pickup at 2pm."), indent=2))
