"""Instructor step: deploy the kiosk builder as a Foundry hosted agent.

Creates a new version of the agent from a container image that is already in
your registry, waits for Foundry to start it, and sends traffic to it. It then
prints the agent's identity, which needs one role before the agent can call
Claude (see README.md).

Run:  az login && python deploy.py <registry>.azurecr.io/sparkles-hosted:<tag>
"""

import os
import sys
import time
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentEndpointConfig,
    AgentEndpointProtocol,
    ContainerConfiguration,
    FixedRatioVersionSelectionRule,
    HostedAgentDefinition,
    InvocationsProtocolConfiguration,
    ProtocolConfiguration,
    ProtocolVersionRecord,
    VersionSelector,
)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

AGENT_NAME = os.environ.get("HOSTED_AGENT_NAME", "sparkles-kiosk-builder")
image = sys.argv[1]

project = AIProjectClient(endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
                          credential=DefaultAzureCredential())

version = project.agents.create_version(
    agent_name=AGENT_NAME,
    description="Builds and checks the Sparkles kiosk page with the Claude Agent SDK.",
    definition=HostedAgentDefinition(
        container_configuration=ContainerConfiguration(image=image),
        protocol_versions=[ProtocolVersionRecord(protocol=AgentEndpointProtocol.INVOCATIONS,
                                                 version="2.0.0")],
        cpu="1",
        memory="2Gi",
        # Names starting FOUNDRY_ are reserved inside a hosted agent.
        environment_variables={
            "SPARKLES_MODEL": os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
            "SPARKLES_FAST_MODEL": os.environ.get("FOUNDRY_HAIKU_DEPLOYMENT",
                                                  os.environ["FOUNDRY_MODEL_DEPLOYMENT"]),
        },
    ),
)
print(f"Created {AGENT_NAME} version {version.version}; waiting for it to start...")

for _ in range(90):
    details = project.agents.get_version(agent_name=AGENT_NAME, agent_version=version.version)
    status = getattr(details.status, "value", details.status)
    if status in ("active", "failed"):
        break
    time.sleep(10)
print(f"Status: {status}")
if status != "active":
    sys.exit(f"Not started: {details.get('error')}")

project.agents.update_details(
    agent_name=AGENT_NAME,
    agent_endpoint=AgentEndpointConfig(
        version_selector=VersionSelector(version_selection_rules=[
            FixedRatioVersionSelectionRule(agent_version=version.version, traffic_percentage=100),
        ]),
        protocol_configuration=ProtocolConfiguration(invocations=InvocationsProtocolConfiguration()),
    ),
)
identity = (details.instance_identity or {}).get("principal_id")
print(f"Traffic now goes to version {version.version}")
print(f"Agent identity (principal id): {identity}")
