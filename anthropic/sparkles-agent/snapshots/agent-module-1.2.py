"""Sparkles - The Cupcake ordering agent (completed through Module 1.2)"""

import asyncio
import os

from dotenv import load_dotenv

from agent_framework import Agent, MCPStreamableHTTPTool          # 👈 1.2
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

    # 3. Connect to the Cupcake Store MCP server                    👈 1.2
    mcp_tool = MCPStreamableHTTPTool(
        name="cupcake-store",
        url=os.environ["CUPCAKE_MCP_URL"],
    )
    await mcp_tool.connect()

    # 4. Persona and welcome banner come from the MCP server        👈 1.2
    instructions = await mcp_tool.get_prompt("agent_instructions")
    banner = await mcp_tool.get_prompt("welcome_banner")

    # 5. The agent, now with tools and a personality
    agent = Agent(
        client=chat_client,
        name="cupcake-agent",
        instructions=instructions,                                 # 👈 1.2
        tools=mcp_tool,                                            # 👈 1.2
    )

    # 6. A session keeps the conversation history
    session = agent.create_session()
    print(banner)                                                  # 👈 1.2
    print("Type 'exit' to quit.\n")

    # Let Sparkles greet the customer first                        👈 1.2
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

    await mcp_tool.close()                                         # 👈 1.2


if __name__ == "__main__":
    asyncio.run(main())
