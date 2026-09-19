"""Check that the Foundry IQ knowledge base is ready for Module 1.3.

What it does
  1. Builds the Module 1.3 agent: Claude on Foundry plus the Foundry IQ
     knowledge base as an MCP tool, connected exactly like the snapshot
     (query key in the api-key header). The Cupcake Store server is left
     out, so only the knowledge base can answer.
  2. Asks the four policy questions from Module 1.3, each in a new session.
  3. For each answer, checks two things:
       - the agent called the knowledge base tool (knowledge_base_retrieve)
       - the answer contains the facts the store document says it must
  4. Prints PASS or FAIL per check and exits non-zero if anything failed.

Run from the repo root after `pip install -r requirements.txt`. It reads
.env there; .env wins over values already exported in your shell.

    python foundry-iq/verify_knowledge_base.py              # summary only
    python foundry-iq/verify_knowledge_base.py --answers    # also print each reply
"""

import asyncio
import os
import re
import sys

from dotenv import find_dotenv, load_dotenv

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import AnthropicFoundryClient

# Each question, and the facts from docs/cupcake-store-info.md that a
# correct answer has to mention: (label, regex).
CASES = [
    ("Do you deliver to Bellevue, and what does it cost?", [
        ("$6.99 delivery fee", r"\$6\.99"),
        ("free delivery over $50", r"\$50"),
    ]),
    ("What is your refund policy?", [
        ("48-hour window for damaged orders", r"48[- ]hour"),
        ("refund or replacement", r"replacement"),
    ]),
    ("My order arrived squashed. What can I do?", [
        ("report within 48 hours", r"48[- ]hour"),
        ("send a photo", r"photo"),
    ]),
    ("I need 30 cupcakes for a party on Saturday. Anything I should know?", [
        ("72 hours notice for bulk orders", r"72[- ]hour"),
        ("50% deposit", r"50\s*%|50 percent"),
    ]),
]

KB_TOOL = "knowledge_base_retrieve"


def reply_text(response) -> str:
    """The agent's words, with a blank line between the text it writes before
    a tool call and the answer after it (response.text runs them together)."""
    return "\n\n".join(m.text.strip() for m in response.messages if m.text.strip())


def tool_calls(response) -> list[str]:
    return [c.name for m in response.messages for c in (m.contents or [])
            if getattr(c, "type", None) == "function_call"]


def build_agent() -> tuple[Agent, MCPStreamableHTTPTool]:
    chat_client = AnthropicFoundryClient(
        model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
        api_key=os.environ["FOUNDRY_API_KEY"],
        base_url=os.environ["FOUNDRY_ENDPOINT"],
    )
    search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/")
    search_key = os.environ["AZURE_SEARCH_QUERY_KEY"]
    kb_name = os.environ.get("KNOWLEDGE_BASE_NAME", "cupcake-store-kb")
    knowledge_tool = MCPStreamableHTTPTool(
        name="cupcake-knowledge-base",
        url=f"{search_endpoint}/knowledgebases/{kb_name}/mcp?api-version=2026-08-01-preview",
        header_provider=lambda _: {"api-key": search_key},
        load_prompts=False,
    )
    agent = Agent(
        client=chat_client,
        name="cupcake-agent",
        instructions=(
            "You are Sparkles, the Cupcake Store assistant. "
            "Use the cupcake-knowledge-base tool for store policies: hours, "
            "delivery, shipping, returns, allergens, loyalty, and bulk orders. "
            "Do not invent store information; look it up."
        ),
        tools=[knowledge_tool],
    )
    return agent, knowledge_tool


async def main() -> int:
    show_answers = "--answers" in sys.argv
    load_dotenv(find_dotenv(usecwd=True), override=True)

    print(f"Foundry IQ check: model {os.environ['FOUNDRY_MODEL_DEPLOYMENT']}, "
          f"knowledge base {os.environ.get('KNOWLEDGE_BASE_NAME', 'cupcake-store-kb')}\n")

    agent, knowledge_tool = build_agent()
    await knowledge_tool.connect()

    passed = 0
    for i, (question, facts) in enumerate(CASES, 1):
        response = await agent.run(question, session=agent.create_session())
        answer = reply_text(response)

        checks = [("used the knowledge base", KB_TOOL in tool_calls(response))]
        checks += [(f"mentions {label}", re.search(pattern, answer, re.I) is not None)
                   for label, pattern in facts]
        ok = all(result for _, result in checks)
        passed += ok

        print(f"{i}. {question}")
        for label, result in checks:
            print(f"   {'PASS' if result else 'FAIL'}  {label}")
        if show_answers:
            print("\n   " + answer.replace("\n", "\n   "))
        print()

    await knowledge_tool.close()

    print(f"Result: {passed}/{len(CASES)} questions passed")
    if not show_answers:
        print("Run with --answers to print each reply.")
    return 0 if passed == len(CASES) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
