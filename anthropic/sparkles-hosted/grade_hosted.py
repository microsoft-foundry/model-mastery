"""Code-based evaluator for the hosted kiosk builder.

This file's contents are uploaded as the evaluator's code_text. It runs in
Foundry's sandbox (standard library only, no network, no LLM), so it must be
self-contained. It scores one reply from the hosted agent.

The reply is the JSON that main.py returns. The score comes from its "checks"
field, which agent.py fills in by running the static checks itself after the
agent has stopped. What the agent said about its own work is not used.
"""

import json

REQUIRED_TESTIDS = ["title", "flavor-list", "special", "order-btn", "order-count"]


def find_reply(value, depth=0):
    """The agent's reply, wherever Foundry put it.

    Foundry wraps the reply as text inside a message, and the wrapping is JSON
    inside JSON. Look through it for the object that has a "checks" field.
    """
    if depth > 8:
        return None
    if isinstance(value, str) and value.lstrip()[:1] in ("{", "["):
        try:
            value = json.loads(value)
        except ValueError:
            return None
    if isinstance(value, dict):
        if "checks" in value:
            return value
        value = list(value.values())
    if isinstance(value, list):
        for part in value:
            found = find_reply(part, depth + 1)
            if found:
                return found
    return None


def grade(sample: dict, item: dict) -> float:
    # Foundry passes the agent's reply inside item, under "sample".
    reply = find_reply(item) or find_reply(sample) or {}
    checks = str(reply.get("checks", ""))

    present = sum(1 for t in REQUIRED_TESTIDS if f"TESTID {t}: present" in checks)
    score = 0.8 * (present / len(REQUIRED_TESTIDS))
    if "EXTERNAL RESOURCES: none" in checks:
        score += 0.2
    return round(score, 2)
