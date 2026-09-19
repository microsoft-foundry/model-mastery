"""The whole loop: plan, build, check, judge, fix, until the evaluator passes.

Run:  python run_loop.py                first draft is the seeded buggy kiosk
      python run_loop.py --fresh        generator builds the first draft itself
      python run_loop.py --research     planner does web search first (Module 2.2)

Set ENABLE_OTEL=1 in .env to trace every step (Module 2.3).
"""

import sys
import time

from checks import evidence
from common import WORKSPACE, client, run_span, session_span, setup_tracing
from evaluator import evaluate
from generator import generate, seed
from planner import PROMPT, plan, research

MAX_SPRINTS = 3


def main() -> None:
    setup_tracing()
    c = client()
    t0 = time.time()

    with session_span():
        notes = research(c) if "--research" in sys.argv else ""
        spec = plan(c, PROMPT, notes)

        critique = ""
        for sprint in range(1, MAX_SPRINTS + 1):
            with run_span(sprint):
                print(f"\n\033[1mSprint {sprint}\033[0m")
                if sprint == 1 and "--fresh" not in sys.argv:
                    html = seed()
                else:
                    html = generate(c, spec, critique)
                verdict = evaluate(c, spec, evidence(html))
                if verdict["overall"] == "PASS":
                    print(f"\n\033[32m\033[1mShipped in {time.time() - t0:.0f}s across "
                          f"{sprint} sprint(s).\033[0m  Open {WORKSPACE / 'index.html'}")
                    return
                critique = verdict["critique"]

        print(f"\n\033[33mHit the sprint cap. The build is usually close; open "
              f"{WORKSPACE / 'index.html'} anyway.\033[0m")


if __name__ == "__main__":
    main()
