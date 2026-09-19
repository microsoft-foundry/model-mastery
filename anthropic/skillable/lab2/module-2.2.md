## Module 2.2: Fresh research and a bigger toolbox (15 minutes)

Two more Claude on Foundry capabilities make the loop smarter without
changing its shape.

### Fresh knowledge: web search

This morning the agent learned what the shop knows (Foundry IQ). Now it
learns what the world knows. **Web search** is built into Claude on Foundry.

**Open 'websearch.py' first.** 'QUESTION' is what gets asked, and you can edit
it. Claude runs the searches and reads the results on the server side, so your
script never fetches a web page itself.

```
python websearch.py
```

Claude searches, reads a few results, and recommends a special with sources
listed at the bottom. Compare with your neighbor: see if anyone gets something
different.

### Research before planning

Now let the planner do the same before it writes the spec:

```
python planner.py --research
```

The research notes print first, then the spec. The flavors and the special
now come from live results, so your kiosk will not match your neighbor's.
'python run_loop.py --research' does the same inside the full loop.

### Tool search

Sparkles' tool catalog keeps growing. Loading every tool into every request
costs context and confuses the model. With **tool search**, tools are marked
'defer_loading' and Claude searches for the ones it needs:

**Open 'toolsearch.py'** and look at **'CATALOG'**: twelve tools, each with a
name and a one-line description.

- Sending all twelve with every request uses context and gives the model more
  wrong options to pick from.
- **'defer_loading'** holds them back. Claude searches the descriptions and
  loads only the tools the question needs.

```
python toolsearch.py "How many loyalty points does Priya have?"
```

Output shows three lines: what Claude searched for, which tools the search
returned, and which one it called. Try a different question, for example
'Is the shop open on Sunday?' and watch it pick a different tool.

**Checkpoint 9.** A recommendation with live citations, a research-grounded
schema-valid spec, and an agent that finds the right tool out of twelve
without holding them all in context.
