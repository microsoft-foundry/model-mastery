"""
Build TrailMate v1 (Basecamp).

What this script does, end to end:
  1. Connects to your Microsoft Foundry project.
  2. Creates a vector store and uploads the 10 product manuals into it.
  3. Creates the TrailMate prompt agent (v1) that uses a file-search tool over
     that vector store, a frontier GPT model, and instructions from a file.
  4. Prints the agent name/version and the vector store id so later steps can
     reuse the SAME vector store (v2 and v3 never re-upload the manuals).

Run it from this folder:  python build_agent.py

Note: the exact azure-ai-projects preview API may evolve. If a call name differs
in your installed version, check the microsoft-foundry skill / quickstart and
adjust — the shape (vector store -> upload -> create_version with file_search)
stays the same.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, PromptAgentDefinition

# --- Paths: where the manuals and instructions live, relative to this file. ---
HERE = Path(__file__).parent
MANUALS_DIR = HERE.parent / "data" / "manuals"
INSTRUCTIONS_FILE = HERE / "instructions.md"
# We record what we created here so v2/v3 can reuse the same vector store.
STATE_FILE = HERE / ".trailmate-state.json"
VECTOR_STORE_NAME = "trailmate-manuals"


def get_or_create_vector_store(openai_client):
    """Return the manuals vector store, uploading only if it doesn't exist yet.

    Idempotent: a store named ``trailmate-manuals`` is reused as-is, so re-running
    this script never re-uploads the manuals.
    """
    for store in openai_client.vector_stores.list():
        if getattr(store, "name", None) == VECTOR_STORE_NAME:
            print(f"Reusing existing vector store {store.id} ({VECTOR_STORE_NAME}) — skipping upload.")
            return store

    print("Creating vector store and uploading manuals...")
    vector_store = openai_client.vector_stores.create(name=VECTOR_STORE_NAME)
    manual_paths = sorted(MANUALS_DIR.glob("*.md"))
    file_streams = [p.open("rb") for p in manual_paths]
    try:
        openai_client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=file_streams,
        )
    finally:
        for stream in file_streams:
            stream.close()
    print(f"  Uploaded {len(manual_paths)} manuals to vector store {vector_store.id}")
    return vector_store


def main() -> None:
    # --- 1. Load config and connect to the Foundry project. ---
    # DefaultAzureCredential uses your `az login` session — no API keys needed.
    # provision.sh wrote the single .env one level up, in the src/ folder.
    load_dotenv(HERE.parent / ".env")
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    model = os.environ["TRAILMATE_MODEL_DEPLOYMENT"]
    agent_name = os.environ.get("TRAILMATE_AGENT_NAME", "trailmate")

    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    openai_client = client.get_openai_client()

    # --- 2. Get (or create) the vector store holding the 10 product manuals. ---
    # A vector store indexes the files so the agent can search them by meaning.
    vector_store = get_or_create_vector_store(openai_client)

    # --- 3. Create the TrailMate prompt agent (v1) with a file-search tool. ---
    # The file_search tool must reference the vector store we just filled.
    # Idempotent: if the agent already has a version, reuse it instead of
    # stacking up a v2/v3 every time the script is re-run.
    try:
        existing = list(client.agents.list_versions(agent_name))
    except Exception:
        existing = []

    if existing:
        version = existing[0]
        print(f"Agent '{agent_name}' already has version(s) — reusing v{getattr(version, 'version', '?')} (no new version created).")
    else:
        instructions = INSTRUCTIONS_FILE.read_text(encoding="utf-8")
        definition = PromptAgentDefinition(
            model=model,
            instructions=instructions,
            tools=[FileSearchTool(vector_store_ids=[vector_store.id])],
        )
        print(f"Creating agent '{agent_name}' (v1) on model '{model}'...")
        version = client.agents.create_version(agent_name, definition=definition)

    # --- 4. Save what we created so v2/v3 can reuse the same vector store. ---
    state = {
        "agent_name": agent_name,
        "vector_store_id": vector_store.id,
        "model": model,
        "version": getattr(version, "version", None),
    }
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print("\nTrailMate v1 is ready.")
    print(f"  Agent:        {agent_name}")
    print(f"  Version:      {state['version']}")
    print(f"  Model:        {model}")
    print(f"  Vector store: {vector_store.id}")
    print("\nTest it in the Agent Playground, then come back for the baseline eval.")


if __name__ == "__main__":
    main()
