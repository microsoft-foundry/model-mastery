# Lab 1: Building Agents with Claude on Microsoft Foundry

In this lab, you'll build a customer agent with Claude on Microsoft Foundry, one
capability at a time. You start with a single prompt in the Foundry playground
and finish with a Python agent that takes orders, answers questions from the
shop's own policies, and reads handwritten catering orders.

The agent is for Sparkles, a small cupcake shop with more customers than staff.
Each module starts with something the agent can't do yet, then adds what it
needs: tools for live data, a knowledge base for policies, structured outputs for
receipts, and vision for handwriting. The last module compares two Claude tiers
on the same hard order.

In this lab, you'll:

- Talk to Claude in the Foundry Playground and change its behavior with one sentence
- Build a Python agent on Claude in Foundry
- Give it tools and a personality from the Cupcake Store MCP server, and order a real cupcake
- Connect the shop's knowledge base in Foundry IQ and watch Claude route between two tool servers
- Let Claude find the right tool in a catalog of twelve with tool search
- Produce a schema-valid receipt with structured outputs
- Watch Claude read a handwritten order and place it, applying store policy
- Compare two Claude tiers on the same hard problem

**How the lab works.** Every module ends with a checkpoint. Modules 1.4 through
1.6 are independent, so if you fall behind, skip to the next one. Completed
code for every module is in 'sparkles-agent/snapshots/'; copy the one you
need over 'agent.py' and carry on.

**Your environment.** You'll use VS Code with the repo open, its terminal,
and the Foundry portal in a browser tab. The modules tell you when to open
each one. The '.env' file in the 'anthropic' folder is already filled in for you
unless the instructor says otherwise.
