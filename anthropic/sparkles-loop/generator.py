"""Generator: spec (and, on later sprints, a critique) in, one index.html out.

Run:  python generator.py            builds workspace/index.html from workspace/spec.json
      python generator.py --seed     copies the seeded first draft instead (has a planted bug)
"""

import json
import sys

from common import first_text, FAST_MODEL, REQUIRED_TESTIDS, SEEDS, WORKSPACE, banner, client, span

SYSTEM = f"""You are the GENERATOR. Produce ONE self-contained index.html (inline CSS
and JS, no external files, no CDN) that satisfies every acceptance criterion in
the spec. Use exactly these data-testid values on the matching elements:
{", ".join(REQUIRED_TESTIDS)}. Each flavor must be its own child element inside
the element with data-testid="flavor-list". Respond with the file contents only:
no prose, no code fences."""


def generate(c, spec: dict, critique: str = "") -> str:
    banner("GENERATOR: rewriting index.html" if critique else "GENERATOR: spec -> index.html")
    user = f"SPEC:\n{json.dumps(spec, indent=2)}"
    if critique:
        user += (f"\n\nThe evaluator checked your previous build and reported:\n{critique}"
                 "\n\nFix every failing criterion. Return the full updated index.html.")
    with span("generator", FAST_MODEL) as s:
        r = c.messages.create(model=FAST_MODEL, max_tokens=8000, system=SYSTEM,
                              messages=[{"role": "user", "content": user}])
        s.record(r)
    code = first_text(r).strip()
    if code.startswith("```"):
        code = "\n".join(l for l in code.splitlines() if not l.strip().startswith("```"))
    (WORKSPACE / "index.html").write_text(code, encoding="utf-8")
    print(f"wrote {len(code):,} characters to workspace/index.html")
    return code


def seed() -> str:
    banner("GENERATOR: first draft (seeded)")
    code = (SEEDS / "kiosk_buggy.html").read_text(encoding="utf-8")
    (WORKSPACE / "index.html").write_text(code, encoding="utf-8")
    print(f"loaded a first-pass build to evaluate ({len(code):,} characters)")
    return code


if __name__ == "__main__":
    if "--seed" in sys.argv:
        seed()
    else:
        spec = json.loads((WORKSPACE / "spec.json").read_text())
        generate(client(), spec)
    print(f"\nOpen {WORKSPACE / 'index.html'} in a browser to see it.")
