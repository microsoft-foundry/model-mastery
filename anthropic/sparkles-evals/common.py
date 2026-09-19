"""Shared setup for the eval scripts."""

import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
load_dotenv(HERE.parent / ".env")

PROJECT_ENDPOINT = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
DEPLOYMENT = os.environ["FOUNDRY_MODEL_DEPLOYMENT"]      # the Claude deployment
SEAT = os.environ.get("SEAT_NAME", os.environ.get("USER", "attendee"))

# Evaluator names are per seat so 30 attendees do not collide in one project.
CODE_EVALUATOR = f"sparkles-code-{SEAT}"
ENDPOINT_EVALUATOR = f"sparkles-claude-judge-{SEAT}"


def project_client() -> AIProjectClient:
    # Run `az login` first. No key is stored for this client.
    return AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
