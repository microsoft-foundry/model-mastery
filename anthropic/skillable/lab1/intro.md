# Lab 1: Building an Agent with Claude on Microsoft Foundry

Welcome to Sparkles, the friendliest little cupcake shop on the internet.
Sparkles has more customers than staff, so today you will build the agent
that greets them, takes their orders, answers policy questions from the
shop's own documents, and reads their handwritten catering requests.

By the end of this lab you will have:

- Talked to Claude in the Foundry Playground and changed its behavior with one sentence
- Built a Python agent on Claude in Foundry
- Given it tools and a personality from the Cupcake Store MCP server, and ordered a real cupcake
- Connected the shop's knowledge base in Foundry IQ and watched Claude route between two tool servers
- Produced a schema-valid receipt with structured outputs
- Watched Claude read a handwritten order and place it, applying store policy
- Compared two Claude tiers on the same hard problem

**How the lab works.** Every module ends with a checkpoint. Modules 1.4 through
1.6 are independent, so if you fall behind, skip to the next one. Completed
code for every module is in 'sparkles-agent/snapshots/'; copy the one you
need over 'agent.py' and carry on.

**Your environment.** VS Code with the repo open, a terminal, and the Foundry
portal in a browser tab. The '.env' file in 'sparkles-agent/' is already
filled in for your seat unless the instructor says otherwise.

**Prerequisites**

- The workshop Foundry project (sign-in details from your instructor)
- Python 3.10+ with the packages in 'requirements.txt' (pre-installed)
