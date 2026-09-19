"""Claude-as-judge evaluation endpoint for Foundry endpoint-based evaluators.

Foundry POSTs one item at a time using its custom-evaluator contract
(schema_version 0.0.1) and records what comes back. This service grades the
agent's response with the Claude deployment and returns score, reason, and
passed. It must answer inside Foundry's 30-second timeout.

Local run:   uvicorn eval_endpoint:app --port 8000
Deploy:      see README.md in this folder
"""

import json
import os

from anthropic import AnthropicFoundry
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

load_dotenv()

app = FastAPI(title="Sparkles eval endpoint")
client = AnthropicFoundry(
    api_key=os.environ["FOUNDRY_API_KEY"],
    base_url=os.environ["FOUNDRY_ENDPOINT"],
)
MODEL = os.environ["FOUNDRY_MODEL_DEPLOYMENT"]
API_KEY = os.environ.get("EVAL_ENDPOINT_API_KEY")   # optional shared secret
THRESHOLD = 0.7

# The same store document that feeds the Foundry IQ knowledge base, so the
# judge can check policy claims against the source (groundedness).
_doc = os.path.join(os.path.dirname(__file__), os.environ.get("REFERENCE_DOC", "cupcake-store-info.md"))
REFERENCE = open(_doc, encoding="utf-8").read() if os.path.exists(_doc) else ""

GRADE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "score": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["score", "reason"],
}

RUBRIC = """You are grading a cupcake-shop ordering agent. Score the RESPONSE to the
QUERY from 0 to 1:
- 1.0: correct, checks stock when relevant, surfaces every conflict (budget,
  allergies, stock, bulk-order rules) instead of guessing, states store policy
  accurately, and confirms clearly.
- 0.5: helpful but misses a conflict or skips a check it should have done.
- 0.0: wrong, unsafe (ignores an allergy), contradicts store policy, or off topic.
Any claim about store policy (hours, delivery, refunds, allergens, loyalty,
bulk orders) must match the STORE POLICY document below. A fluent answer that
contradicts it scores 0.0. Give one sentence of reasoning that names the
policy when one is involved.

STORE POLICY:
""" + REFERENCE


def first_text(response) -> str:
    """The first text block of a response.

    Claude may return a thinking block before the answer, so content[0] is not
    reliably the text.
    """
    return next(b.text for b in response.content if getattr(b, "type", None) == "text")


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL}


@app.post("/evaluate")
async def evaluate(req: Request, api_key: str | None = Header(default=None, alias="api-key"),
                   authorization: str | None = Header(default=None)):
    if API_KEY and API_KEY not in (api_key, (authorization or "").replace("Bearer ", "")):
        raise HTTPException(status_code=401, detail="bad api key")

    body = await req.json()
    data = body.get("data", {})
    item, sample = data.get("item", {}), data.get("sample", {})
    query = item.get("query", "")
    response = item.get("response") or sample.get("response", "")

    try:
        r = client.messages.create(
            # Generous: Claude may emit a thinking block before the JSON, and
            # that comes out of the same budget. Too low and the JSON is
            # truncated mid-string, which surfaces as a parse error per row.
            model=MODEL, max_tokens=2000, system=RUBRIC,
            output_config={"format": {"type": "json_schema", "schema": GRADE_SCHEMA}},
            messages=[{"role": "user", "content": f"QUERY:\n{query}\n\nRESPONSE:\n{response}"}],
        )
        g = json.loads(first_text(r))
        score = max(0.0, min(1.0, float(g["score"])))
        return {
            "schema_version": "0.0.1",
            "score": score,
            "reason": g["reason"],
            "status": "Completed",   # Foundry rejects lowercase: Completed | Error | Skipped
            "threshold": THRESHOLD,
            "passed": score >= THRESHOLD,
            "properties": {"judge_model": MODEL},
        }
    except Exception as e:  # any failure must still be a valid response
        return {
            "schema_version": "0.0.1",
            "status": "Error",
            "error": {"code": "500", "message": str(e)[:200]},
        }
