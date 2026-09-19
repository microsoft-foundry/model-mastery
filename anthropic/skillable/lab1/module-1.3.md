## Module 1.3: Give it knowledge with Foundry IQ (10 minutes)

### Find the gap

Run your agent and ask two questions:

1. 'What flavors do you have today?' It answers, calling the store's tools.
2. 'Do you bake with tree nuts?' It cannot, and says so.

Same agent, same session. One question served, one not. It has tools; they
just do not cover policy. The shop's policies live in a document, and this
module gives the agent that document through **Foundry IQ**.

> **What is Foundry IQ?** The managed knowledge layer in Microsoft Foundry,
> built on Azure AI Search. Your instructors loaded the Sparkles store
> information (hours, delivery, returns, allergens, loyalty, bulk-order rules)
> into a knowledge base. Every Foundry IQ knowledge base exposes an **MCP
> endpoint**, so to your agent it is just another tool server, the same kind
> you connected in Module 1.2.

### Add the knowledge base

Your '.env' already has three lines for it:

```
AZURE_SEARCH_ENDPOINT="https://<service>.search.windows.net"
AZURE_SEARCH_QUERY_KEY="<query key>"
KNOWLEDGE_BASE_NAME="cupcake-store-kb"
```

A second MCP tool, pointed at the knowledge base's MCP endpoint with the
Search key in a header. Make the edits marked 👈 1.3 in the box below.

```python-notype
"""Sparkles - The Cupcake ordering agent"""

import asyncio
import os

from dotenv import load_dotenv

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import AnthropicFoundryClient

# 1. Load settings from .env
load_dotenv()


def reply(response) -> str:
    """Sparkles' words, with a blank line between what it says before a tool
    call and its answer after (response.text runs them together)."""
    return "\n\n".join(m.text for m in response.messages if m.text)


async def main() -> None:
    # 2. The chat model: Claude on Microsoft Foundry
    chat_client = AnthropicFoundryClient(
        model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
        api_key=os.environ["FOUNDRY_API_KEY"],
        base_url=os.environ["FOUNDRY_ENDPOINT"],
    )

    # 3. Connect to the Cupcake Store MCP server (orders, stock)
    mcp_tool = MCPStreamableHTTPTool(
        name="cupcake-store",
        url=os.environ["CUPCAKE_MCP_URL"],
    )
    await mcp_tool.connect()

    # 4. Connect to the shop's knowledge base in Foundry IQ (policies)   👈 1.3
    search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/")
    search_key = os.environ["AZURE_SEARCH_QUERY_KEY"]
    kb_name = os.environ.get("KNOWLEDGE_BASE_NAME", "cupcake-store-kb")
    knowledge_tool = MCPStreamableHTTPTool(
        name="cupcake-knowledge-base",
        url=f"{search_endpoint}/knowledgebases/{kb_name}/mcp?api-version=2026-08-01-preview",
        header_provider=lambda _: {"api-key": search_key},
        load_prompts=False,
    )
    await knowledge_tool.connect()

    # 5. Persona and welcome banner come from the MCP server
    instructions = await mcp_tool.get_prompt("agent_instructions")
    banner = await mcp_tool.get_prompt("welcome_banner")
    instructions += (                                              # 👈 1.3
        "\n\nUse the cupcake-store tool for orders, stock, and order status. "
        "Use the cupcake-knowledge-base tool for store policies: hours, "
        "delivery, shipping, returns, allergens, loyalty, and bulk orders. "
        "Do not invent store information; look it up."
    )

    # 6. The agent, now with two tool servers and a personality
    agent = Agent(
        client=chat_client,
        name="cupcake-agent",
        instructions=instructions,
        tools=[mcp_tool, knowledge_tool],                           # 👈 1.3
    )

    # 7. A session keeps the conversation history
    session = agent.create_session()
    print(banner)
    print("Type 'exit' to quit.\n")

    response = await agent.run("hello", session=session)
    print(f"\033[1;35mSparkles:\033[0m\n{reply(response)}\n")

    while True:
        user_input = input("\033[1;35mYou:\033[0m\n")
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input.strip():
            continue
        response = await agent.run(user_input, session=session)
        print(f"\n\033[1;35mSparkles:\033[0m\n{reply(response)}\n")

    await knowledge_tool.close()                                    # 👈 1.3
    await mcp_tool.close()


if __name__ == "__main__":
    asyncio.run(main())
```

You can also just replace the file contents with everything in the box.

### Watch it choose

Run 'python agent.py' and ask, in this order:

1. 'Do you bake with tree nuts?'
2. 'What flavors do you have today?'
3. 'My order arrived squashed. What can I do?'
4. 'I need 30 cupcakes for a party on Saturday. Anything I should know?'

Question 1 is the one it could not answer a few minutes ago. Questions 1, 3,
and 4 go to the knowledge base; question 2 goes to the store.
Nothing in your code routes them. Claude reads the two tools' descriptions
and decides per question. Question 4 should turn up the bulk-order rules
(72 hours notice, 50 percent deposit); remember that for Module 1.6.

**Checkpoint 4.** Your agent answers policy questions from the shop's own
document, and picks the right server without being told.

> Where this goes in real life: swap the store document for your product
> docs, your support runbook, or your contracts, and the agent pattern is
> the same.
