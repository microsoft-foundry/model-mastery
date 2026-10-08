## Module 1.6: Model judgment and tiering (10 minutes)

No new code. This module is about what the model does when an order does not
add up.

### The hard order

Run your agent ('python agent.py'). The order below has two placeholders to
fill in: your customer ID from Module 1.2 and the voucher code on the order
dashboard. Copy it into any text editor (a new file in VS Code works), replace
both placeholders, then copy the finished line and paste it into the terminal.
It is one long line on purpose: the agent reads a line at a time, so a prompt
split across several lines arrives as several separate messages.

```
My customer ID is @lab.Variable(customerID). One hazelnut cupcake please, as a test order. I'm allergic to nuts. If hazelnut is gone, get me two red velvets instead. Voucher code: <code on the dashboard>. Also, my friend wants 30 cupcakes for a party in two days. What do we need to do?
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

Now run the same order on Claude Haiku, the fast and inexpensive tier, and
see how much of it the smaller tier handles. No code changes; only the
deployment name:

```
$env:FOUNDRY_MODEL_DEPLOYMENT="claude-haiku-4-5"; python agent.py; Remove-Item Env:FOUNDRY_MODEL_DEPLOYMENT
```

(That is PowerShell, which the VS Code terminal in the lab uses. The last part
clears the setting once the agent exits, so later runs go back to Sonnet. In
bash or zsh: 'FOUNDRY_MODEL_DEPLOYMENT=claude-haiku-4-5 python agent.py')

Paste the same order, with the new voucher code from the dashboard. Type
'exit' when you are done.

### Compare the two

Put the two replies side by side and work through these:

1. Which reply felt faster?
2. How many of the four problems did each tier catch? If one was missed,
   which?
3. Does each reply quote the catering rules (72 hours notice, 50 percent
   deposit)? If it does, it looked them up instead of assuming.
4. When hazelnut was unavailable, did each tier substitute red velvet or ask
   first?
5. Compare with a neighbor who ran the same tier. Did you get the same answer?
6. Which requests in your own product are like this order, and which are
   closer to 'What flavors do you have today?'

Do not be surprised if Haiku handles this order as well as Sonnet. That is the
point of trying it. You built the agent and got it working on the more capable
tier first. Once it works, check whether a smaller tier holds up on the same
requests. Where it does, you get the same result faster and for less.

> Foundry hosts several Claude tiers behind the same API. Moving a workload
> from Sonnet to Haiku, or back, is a one-line change: the deployment name.
> That is exactly what you just did.

**Checkpoint 7.** The same order run on two Claude tiers, and the two replies
compared.

### Wrap up

You built a Claude agent on Foundry, gave it tools, a persona, and the shop's
own knowledge, made its output schema-safe, had it read handwriting and apply
policy, and compared tiers. After lunch, Lab 2 takes the next step: an agent
that verifies its own work, and the Foundry features that let you run it
unattended.
