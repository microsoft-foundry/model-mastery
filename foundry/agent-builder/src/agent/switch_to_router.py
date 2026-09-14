"""
Switch TrailMate to Model Router (v2 — Trailfinder).

What this script does:
  - Reads what build_agent.py created (the same agent name + vector store).
  - Creates a NEW version of the SAME agent that changes exactly ONE thing:
    the model becomes your `model-router` deployment instead of the frontier GPT.
  - Keeps the SAME file-search tool and the SAME instructions, and reuses the
    SAME vector store — so no manuals are re-uploaded.

This is the "one lever at a time" idea: v2 differs from v1 only by its model,
so any change in cost, latency, or quality can be attributed to the model.

Run it from this folder:  python switch_to_router.py
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

HERE = Path(__file__).parent
INSTRUCTIONS_FILE = HERE / "instructions.md"
STATE_FILE = HERE / ".trailmate-state.json"

# The router deployment name from your provisioning step.
ROUTER_MODEL = "model-router"


def main() -> None:
    # --- 1. Load config and the state saved by build_agent.py. ---
    load_dotenv(HERE.parent / ".env")
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    if not STATE_FILE.exists():
        raise SystemExit("Run build_agent.py first — no v1 state found.")
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

    # --- 2. Create a new version: same tool + instructions, new model. ---
    # We reuse the SAME vector_store_id, so the manuals are not uploaded again.
    instructions = INSTRUCTIONS_FILE.read_text(encoding="utf-8")
    definition = {
        "kind": "prompt",
        "model": ROUTER_MODEL,  # <-- the ONLY change from v1
        "instructions": instructions,
        "tools": [
            {
                "type": "file_search",
                "vector_store_ids": [state["vector_store_id"]],
            }
        ],
    }
    print(f"Creating v2 of '{state['agent_name']}' on model '{ROUTER_MODEL}'...")
    version = client.agents.create_version(state["agent_name"], definition)

    # --- 3. Record the new version for reference. ---
    state["model"] = ROUTER_MODEL
    state["version"] = getattr(version, "version", None)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print("\nTrailMate v2 (Model Router) is ready.")
    print(f"  Version: {state['version']}")
    print(f"  Model:   {ROUTER_MODEL}")
    print("Re-run the SAME evaluation and compare v2 with v1.")


if __name__ == "__main__":
    main()
