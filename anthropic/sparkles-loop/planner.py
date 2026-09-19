"""Planner: one line of intent in, a testable spec out (structured outputs).

Run:  python planner.py
      python planner.py --research     (Module 2.2: web search first)
"""

import json
import sys

from common import first_text, REQUIRED_TESTIDS, SMART_MODEL, WORKSPACE, banner, client, span

PROMPT = ("Build a single-page ordering kiosk for the Sparkles cupcake shop counter: "
          "today's flavors, a special of the day, and a running count of orders placed.")

SPEC_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "features": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "acceptance": {"type": "string"},
                },
                "required": ["id", "name", "acceptance"],
            },
        },
        "done_when": {"type": "string"},
    },
    "required": ["title", "summary", "features", "done_when"],
}

SYSTEM = f"""You are the PLANNER in a long-horizon coding loop. Turn a one-line
product prompt into a concrete, testable spec of 3 or 4 features. Describe WHAT
must exist, not HOW.

The page will be checked by a static analyzer that reads the HTML and reports
which data-testid values exist, how many children each list has, and whether
the page is self-contained (no external scripts). So every acceptance criterion
must be checkable that way. The page MUST use exactly these data-testid values:
{", ".join(REQUIRED_TESTIDS)}. Write at least one criterion for each of:
- title (shows the shop name)
- flavor-list (at least three flavor items inside it)
- special (a special of the day)
- order-btn and order-count (a button and a counter element that exist)
Do not write criteria that require clicking or running the page."""


def research(c) -> str:
    """Module 2.2: ground the spec in what is trending right now."""
    banner("PLANNER research: web search")
    with span("planner-research", SMART_MODEL) as s:
        r = c.messages.create(
            model=SMART_MODEL, max_tokens=800,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
            messages=[{"role": "user", "content":
                       "In three bullets, which cupcake flavors are trending this season?"}])
        s.record(r)
    notes = "\n".join(b.text for b in r.content if b.type == "text")
    print(notes)
    return notes


def plan(c, prompt: str, notes: str = "") -> dict:
    banner("PLANNER: prompt -> spec")
    user = prompt
    if notes:
        user += ("\n\nUse these research notes to choose the flavors and the special:\n"
                 + notes)
    with span("planner", SMART_MODEL) as s:
        r = c.messages.create(
            model=SMART_MODEL, max_tokens=2000, system=SYSTEM,
            output_config={"format": {"type": "json_schema", "schema": SPEC_SCHEMA}},
            messages=[{"role": "user", "content": user}])
        s.record(r)
    spec = json.loads(first_text(r))
    (WORKSPACE / "spec.json").write_text(json.dumps(spec, indent=2))
    print(f"\n\033[1m{spec['title']}\033[0m: {spec['summary']}")
    for f in spec["features"]:
        print(f"  {f['id']}  {f['name']}\n       {f['acceptance']}")
    print(f"  done when: {spec['done_when']}")
    return spec


if __name__ == "__main__":
    c = client()
    notes = research(c) if "--research" in sys.argv else ""
    plan(c, PROMPT, notes)
    print(f"\nSpec saved to {WORKSPACE / 'spec.json'}")
