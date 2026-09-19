"""Module 1.5 - Claude can see: the catering order.

Three steps, all on Claude in Foundry:
  1. Vision + structured outputs: read the handwritten order photo and
     return a clean order object (corrections and allergy notes honored).
  2. Hand that order to the Sparkles agent, which has both tool servers.
     The counter takes one cupcake per customer, so the agent looks up the
     allergen and catering policy in the knowledge base, checks the menu,
     places ONE safe test order (it asks you for your customer ID and the
     voucher code), and says what the catering team must handle.
  3. Print a schema-valid receipt for the whole catering order.

Run:  python catering.py images/catering-order.jpg
"""

import asyncio
import base64
import json
import os
import sys

from anthropic import AnthropicFoundry
from dotenv import load_dotenv

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import AnthropicFoundryClient

from receipt import first_text, make_receipt

load_dotenv()


def reply(response) -> str:
    """Sparkles' words, with a blank line between what it says before a tool
    call and its answer after (response.text runs them together)."""
    return "\n\n".join(m.text for m in response.messages if m.text)


def knowledge_tool() -> MCPStreamableHTTPTool:
    """The shop's Foundry IQ knowledge base, same as Module 1.3."""
    endpoint = os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/")
    kb = os.environ.get("KNOWLEDGE_BASE_NAME", "cupcake-store-kb")
    key = os.environ["AZURE_SEARCH_QUERY_KEY"]
    return MCPStreamableHTTPTool(
        name="cupcake-knowledge-base",
        url=f"{endpoint}/knowledgebases/{kb}/mcp?api-version=2026-08-01-preview",
        header_provider=lambda _: {"api-key": key},
        load_prompts=False,
    )


ORDER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "customer": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "flavor": {"type": "string"},
                    "qty": {"type": "integer"},
                },
                "required": ["flavor", "qty"],
            },
        },
        "allergy_notes": {"type": "string"},
        "corrections_applied": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["customer", "items", "allergy_notes", "corrections_applied"],
}


def read_order(image_path: str) -> dict:
    """Step 1: vision + structured outputs."""
    media_type = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
    data = base64.standard_b64encode(open(image_path, "rb").read()).decode()

    client = AnthropicFoundry(
        api_key=os.environ["FOUNDRY_API_KEY"],
        base_url=os.environ["FOUNDRY_ENDPOINT"],
    )
    r = client.messages.create(
        model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
        max_tokens=800,
        output_config={"format": {"type": "json_schema", "schema": ORDER_SCHEMA}},
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64",
                                             "media_type": media_type, "data": data}},
                {"type": "text", "text": (
                    "This is a handwritten catering order for Sparkles cupcake shop. "
                    "Read it carefully. Crossed-out items are cancelled; use the "
                    "replacement written next to them. Tally marks are quantities. "
                    "Capture any allergy note exactly. List each correction you applied."
                )},
            ],
        }],
    )
    return json.loads(first_text(r))


async def work_order(order: dict) -> str:
    """Step 2: brief the Sparkles agent and let it place one test order.

    The counter allows one cupcake per customer, so a catering order can never
    be placed in full at the counter. The agent looks up policy in the
    knowledge base, checks the menu, flags conflicts, and asks you for what it
    needs (your customer ID and the voucher code on the screen). Answer its
    questions, then type 'done'.
    """
    chat_client = AnthropicFoundryClient(
        model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
        api_key=os.environ["FOUNDRY_API_KEY"],
        base_url=os.environ["FOUNDRY_ENDPOINT"],
    )
    mcp_tool = MCPStreamableHTTPTool(name="cupcake-store", url=os.environ["CUPCAKE_MCP_URL"])
    kb_tool = knowledge_tool()
    await mcp_tool.connect()
    await kb_tool.connect()
    instructions = await mcp_tool.get_prompt("agent_instructions")
    instructions += ("\n\nUse cupcake-knowledge-base for store policies such as "
                     "allergens, catering, and bulk orders. Do not invent store information.")
    agent = Agent(client=chat_client, name="cupcake-agent",
                  instructions=instructions, tools=[mcp_tool, kb_tool])
    session = agent.create_session()

    brief = (
        "A catering order was read from a handwritten photo: "
        + ", ".join(f"{i['qty']} {i['flavor']}" for i in order["items"])
        + f". Allergy notes: {order['allergy_notes'] or 'none'}. "
        "The counter takes one cupcake per customer, so do not try to order every item. "
        "1) Look up the shop's allergen policy and the rules for catering or bulk orders "
        "in the knowledge base, and tell me what applies to this order. "
        "2) Check the menu and say which flavors on the order are available. "
        "3) Flag anything that conflicts with the allergy notes. "
        "4) Place ONE test order for the first item that is available and safe; "
        "ask me for anything you need first. "
        "5) Say exactly what the catering team must handle and what the customer "
        "needs to do (notice period, deposit)."
    )
    replies = []
    response = await agent.run(brief, session=session)
    replies.append(reply(response))
    print(f"\n\033[1;35mSparkles:\033[0m\n{reply(response)}\n")

    while True:
        user_input = input("\033[1;35mYou (type 'done' when finished):\033[0m\n")
        if user_input.strip().lower() in ("done", "exit", "quit", ""):
            break
        response = await agent.run(user_input, session=session)
        replies.append(reply(response))
        print(f"\n\033[1;35mSparkles:\033[0m\n{reply(response)}\n")

    await kb_tool.close()
    await mcp_tool.close()
    return "\n\n".join(replies)


async def main(image_path: str) -> None:
    print("\033[1;36mStep 1: reading the handwritten order...\033[0m")
    order = read_order(image_path)
    print(json.dumps(order, indent=2), "\n")

    print("\033[1;36mStep 2: Sparkles checks policy and the menu, then places one test order...\033[0m")
    reply = await work_order(order)

    print("\033[1;32mReceipt for the whole catering order (schema-valid):\033[0m")
    # Build the receipt from the order read off the photo plus the store's reply,
    # not the reply alone: the reply may not restate every item.
    print(json.dumps(make_receipt(
        f"Order read from the photo: {json.dumps(order)}\nStore reply: {reply}"), indent=2))


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "images/catering-order.jpg"
    asyncio.run(main(path))
