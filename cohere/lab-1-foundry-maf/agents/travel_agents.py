"""Factory helpers for the local multi-agent travel concierge.

This module wires four Microsoft Agent Framework (MAF) ``Agent`` instances:

* ``flight_agent`` — searches and books flights using the the workshop's booking tools.
* ``hotel_agent`` — searches and books hotels.
* ``car_agent`` — searches and books rental cars.
* ``concierge`` — orchestrator that delegates to the three specialists by
  calling them as tools.

All four agents share a single :class:`OpenAIChatClient` pointed at the
Cohere Command A deployment in your Microsoft Foundry project. MAF lets you
build this with an open-source framework using a model deployed in Foundry —
the client calls the account-level ``/openai/v1`` endpoint exposed by your
Foundry account, which serves both the chat completions and responses APIs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from agent_framework import Agent, tool
from agent_framework_openai import OpenAIChatClient
from azure.identity import DefaultAzureCredential

# The booking tools and catalog data live alongside this lab so the folder is
# self-contained. Inject the lab root onto sys.path so the `tools` package is
# importable from notebooks and from this helper module.
LAB_DIR = Path(__file__).resolve().parents[1]
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))

from tools.booking_tools import (  # noqa: E402  (import after sys.path tweak)
    book_car,
    book_flight,
    book_hotel,
    search_cars,
    search_flights,
    search_hotels,
)


# ---------------------------------------------------------------------------
# Chat client
# ---------------------------------------------------------------------------

def make_chat_client(
    *,
    endpoint: str | None = None,
    model: str | None = None,
    credential: Any | None = None,
) -> OpenAIChatClient:
    """Return an :class:`OpenAIChatClient` pointed at the Cohere deployment.

    The lab uses MAF's ``OpenAIChatClient`` with the Foundry account-level
    ``/openai/v1`` endpoint (e.g. ``https://<account>.services.ai.azure.com/openai/v1``).
    This matches the inference pattern Microsoft Foundry shows on the model
    card and is more reliable than the project-scoped Responses API path used
    by Foundry's project-scoped ``FoundryChatClient``: the project-scoped path can return 404
    "Project not found" / "DeploymentNotFound" for many minutes after a fresh
    project is provisioned, and even after propagation completes it returns
    intermittent 404s at the service layer. The account-level path avoids
    both issues.

    Reads ``AZURE_AI_ENDPOINT`` and ``COMMAND_A_DEPLOYMENT`` from the
    environment when arguments are omitted, matching the env-var contract
    Lab 0 establishes for the rest of the workshop.
    """
    base = endpoint or os.environ["AZURE_AI_ENDPOINT"]
    base_url = f"{base.rstrip('/')}/openai/v1"
    deployment = model or os.getenv("COMMAND_A_DEPLOYMENT", "command-a")
    cred = credential or DefaultAzureCredential()
    return OpenAIChatClient(
        model=deployment,
        base_url=base_url,
        credential=cred,
    )


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

SPECIALIST_INSTRUCTIONS: dict[str, str] = {
    "flight": (
        "You are the flight specialist on an enterprise travel desk. "
        "Use search_flights to find compliant options and book_flight only "
        "after the traveler has clearly accepted one. Prefer the lowest fare "
        "that meets policy and explain any nudges (cabin, refundable, carrier) "
        "in one short sentence."
    ),
    "hotel": (
        "You are the hotel specialist on an enterprise travel desk. "
        "Use search_hotels with the traveler's city, dates, and any nightly "
        "cap. Call book_hotel only after explicit acceptance. Flag rates that "
        "exceed the tier cap and offer compliant alternatives."
    ),
    "car": (
        "You are the rental-car specialist on an enterprise travel desk. "
        "Use search_cars and prefer economy or standard classes unless the "
        "traveler explains a policy exception. Call book_car only after the "
        "traveler accepts a vehicle."
    ),
}

BASELINE_INSTRUCTIONS = (
    "You are a helpful travel assistant. Answer the user's request as best you "
    "can."
)


CONCIERGE_INSTRUCTIONS = (
    "You are the enterprise travel concierge. You coordinate three "
    "specialists: flight_agent, hotel_agent, and car_agent. For each user "
    "request, decide which specialist tools to call and in what order, then "
    "summarize a compliant itinerary in plain language. Never invent fares, "
    "hotels, or cars; always rely on the specialist tools. If the traveler "
    "asks for something policy disallows (for example first class), explain "
    "the policy briefly and offer a compliant alternative."
)


# ---------------------------------------------------------------------------
# Single-agent factory (used by the evaluation progression in notebooks 04-06)
# ---------------------------------------------------------------------------

def build_baseline_agent(
    client: OpenAIChatClient,
    instructions: str = BASELINE_INSTRUCTIONS,
    *,
    name: str = "travel_concierge_baseline",
    description: str = "Single MAF agent without tools, used for the baseline and grounded evaluation rounds.",
) -> Agent:
    """Return a single MAF :class:`Agent` with no tools.

    Notebooks 04 (baseline) and 05 (grounded) reuse this helper with different
    ``instructions`` to isolate the effect of grounding on the same evaluator
    suite. Notebook 07 swaps to :func:`build_concierge` to add the multi-agent
    + tool-use round on top.
    """
    return Agent(
        client,
        instructions=instructions,
        name=name,
        description=description,
        tools=[],
    )


# ---------------------------------------------------------------------------
# Specialist agents
# ---------------------------------------------------------------------------

def build_flight_agent(client: OpenAIChatClient) -> Agent:
    """Return the flight specialist agent."""
    return Agent(
        client,
        instructions=SPECIALIST_INSTRUCTIONS["flight"],
        name="flight_agent",
        description="Finds and books policy-compliant flights from the corporate catalog.",
        tools=[search_flights, book_flight],
    )


def build_hotel_agent(client: OpenAIChatClient) -> Agent:
    """Return the hotel specialist agent."""
    return Agent(
        client,
        instructions=SPECIALIST_INSTRUCTIONS["hotel"],
        name="hotel_agent",
        description="Finds and books policy-compliant hotels from the corporate catalog.",
        tools=[search_hotels, book_hotel],
    )


def build_car_agent(client: OpenAIChatClient) -> Agent:
    """Return the rental-car specialist agent."""
    return Agent(
        client,
        instructions=SPECIALIST_INSTRUCTIONS["car"],
        name="car_agent",
        description="Finds and books policy-compliant rental cars from the corporate catalog.",
        tools=[search_cars, book_car],
    )


# ---------------------------------------------------------------------------
# Concierge orchestrator
# ---------------------------------------------------------------------------

def build_concierge(client: OpenAIChatClient) -> Agent:
    """Return the concierge orchestrator that delegates to the three specialists.

    Each specialist is exposed to the concierge as a single async tool. The
    tool simply forwards the user's natural-language request to the specialist
    agent and returns its text answer. This "agents-as-tools" pattern is the
    simplest multi-agent shape in MAF and keeps the orchestration logic in the
    concierge's own reasoning loop.
    """
    flight_agent = build_flight_agent(client)
    hotel_agent = build_hotel_agent(client)
    car_agent = build_car_agent(client)

    @tool(
        name="flight_agent",
        description=(
            "Delegate flight research or booking to the flight specialist. "
            "Pass a complete natural-language request (origin, destination, "
            "dates, budget, traveler preferences)."
        ),
    )
    async def call_flight_agent(request: str) -> str:
        response = await flight_agent.run(request)
        return response.text or ""

    @tool(
        name="hotel_agent",
        description=(
            "Delegate hotel research or booking to the hotel specialist. "
            "Pass a complete natural-language request (city, dates, nightly "
            "cap, traveler preferences)."
        ),
    )
    async def call_hotel_agent(request: str) -> str:
        response = await hotel_agent.run(request)
        return response.text or ""

    @tool(
        name="car_agent",
        description=(
            "Delegate rental-car research or booking to the car specialist. "
            "Pass a complete natural-language request (city, pickup and "
            "dropoff dates, preferred class)."
        ),
    )
    async def call_car_agent(request: str) -> str:
        response = await car_agent.run(request)
        return response.text or ""

    return Agent(
        client,
        instructions=CONCIERGE_INSTRUCTIONS,
        name="travel_concierge",
        description="Coordinates flight, hotel, and car specialists for a compliant itinerary.",
        tools=[call_flight_agent, call_hotel_agent, call_car_agent],
    )
