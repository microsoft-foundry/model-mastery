"""Code-based evaluator for Module 2.4a.

This file's contents are uploaded as the evaluator's code_text. It runs in
Foundry's sandbox (standard library only, no network, no LLM), so it must be
self-contained. It scores one row of the dataset.

Row fields (mapped through data_mapping when the eval runs):
  item["report"]   the static-analysis report from sparkles-loop/checks.py
  item["receipt"]  the receipt JSON string from Lab 1's receipt.py

The signature follows the Foundry python grader contract.
"""

import json

REQUIRED_TESTIDS = ["title", "flavor-list", "special", "order-btn", "order-count"]
RECEIPT_KEYS = ["order_id", "items", "total_cents", "pickup_time"]


def grade(sample: dict, item: dict) -> float:
    score = 0.0

    # 1. Kiosk report: one point per required test id that is present
    report = item.get("report", "") or ""
    present = sum(1 for t in REQUIRED_TESTIDS
                  if f"TESTID {t}: present" in report)
    score += 0.6 * (present / len(REQUIRED_TESTIDS))

    # 2. Receipt: parses and carries every required key
    try:
        receipt = json.loads(item.get("receipt", "") or "{}")
        if all(k in receipt for k in RECEIPT_KEYS) and receipt["total_cents"] > 0:
            score += 0.4
    except (ValueError, TypeError, KeyError):
        pass

    return round(score, 2)
