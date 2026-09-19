## Module 1.6: Model judgment and tiering (10 minutes)

No new code. This module is about what the model does when an order does not
add up.

### The hard order

Run your agent ('python agent.py'). Fill in your customer ID from Module 1.2
and the voucher code on the order dashboard, then paste this. It is one long
line on purpose: the agent reads a line at a time, so a prompt split across
several lines arrives as several separate messages.

```
My customer ID is <your ID>. One hazelnut cupcake please, as a test order. I'm allergic to nuts. If hazelnut is gone, get me two red velvets instead. Voucher code: <code on the dashboard>. Also, my friend wants 30 cupcakes for a party in two days. What do we need to do?
```

There are four problems hidden in that request. One comes from the store's
live data, three from the shop's policy document:

- Hazelnut is sold out, so it is not on the menu.
- Hazelnut would be unsafe for a nut allergy even if it were in stock.
- Thirty cupcakes is a bulk order: the knowledge base says 72 hours notice
  and a 50 percent deposit.
- Two days is 48 hours, which does not meet the 72 hour requirement.

Watch what Claude does. It should check the menu, catch as many of the four
as it can, and look up the catering rules instead of assuming them.

One more thing to watch, which is not a problem to catch: the order says to
substitute red velvet if hazelnut is gone. Does it apply that fallback, or stop
and ask first? Either is defensible. What you are looking for is whether it
noticed the instruction at all. Type 'exit' when you are done.

### Same code, different tier

Now run the same order on Claude Haiku, the fast and inexpensive tier. No
code changes; only the deployment name:

```
FOUNDRY_MODEL_DEPLOYMENT=claude-haiku-4-5 python agent.py
```

(On Windows PowerShell: '$env:FOUNDRY_MODEL_DEPLOYMENT="claude-haiku-4-5"; python agent.py')

Paste the same order, with the new voucher code from the dashboard. Compare
speed, count how many of the four problems each tier catches, and note
whether it consulted the knowledge base for the party question.

> Foundry hosts several Claude tiers behind the same API. Routing simple
> traffic to Haiku and hard judgment calls to Sonnet is a one-line change,
> which is exactly what you just did.

**Checkpoint 7.** The same code on two tiers with a visible difference in
judgment.

### Wrap up

You built a Claude agent on Foundry, gave it tools, a persona, and the shop's
own knowledge, made its output schema-safe, had it read handwriting and apply
policy, and compared tiers. After lunch, Lab 2 takes the next step: an agent
that verifies its own work, and the Foundry features that let you run it
unattended.
