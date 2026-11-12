"""Shared setup for the eval scripts."""

import os
import re
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
load_dotenv(HERE.parent / ".env")

PROJECT_ENDPOINT = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
DEPLOYMENT = os.environ["FOUNDRY_MODEL_DEPLOYMENT"]      # the Claude deployment
# Windows sets USERNAME where macOS and Linux set USER.
SEAT = (os.environ.get("SEAT_NAME") or os.environ.get("USER")
        or os.environ.get("USERNAME") or "attendee")
SEAT = re.sub(r"[^A-Za-z0-9-]+", "-", SEAT).strip("-") or "attendee"

# Evaluator names are per attendee so 30 of them do not collide in one project.
CODE_EVALUATOR = f"sparkles-code-{SEAT}"
ENDPOINT_EVALUATOR = f"sparkles-claude-judge-{SEAT}"


def project_client() -> AIProjectClient:
    # Run `az login` first. No key is stored for this client.
    return AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
