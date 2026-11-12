## Module 1.6: Model judgment and tiering (10 minutes)

No new code. This module is about what the model does when an order doesn't
add up.

### The hard order

Run your agent ('python agent.py'). The order below has two placeholders to
fill in: your customer ID from Module 1.2 and the voucher code on the order
dashboard. Copy it into any text editor (a new file in VS Code works), replace
both placeholders, then copy the finished line and paste it into the terminal.
It's one long line on purpose: the agent reads a line at a time, so a prompt
split across several lines arrives as several separate messages.

```
My customer ID is @lab.Variable(customerID). One hazelnut cupcake please, as a test order. I'm allergic to nuts. If hazelnut is gone, get me two red velvets instead. Voucher code: <code on the dashboard>. Also, my friend wants 30 cupcakes for a party in two days. What do we need to do?
```

There are four problems hidden in that request. One comes from the store's
live data, three from the shop's policy document:

- Hazelnut is sold out, so it isn't on the menu.
- Hazelnut would be unsafe for a nut allergy even if it were in stock.
- Thirty cupcakes is a bulk order: the knowledge base says 72 hours notice
  and a 50 percent deposit.
- Two days is 48 hours, which doesn't meet the 72 hour requirement.

Watch what Claude does. It should check the menu, catch as many of the four
as it can, and look up the catering rules instead of assuming them.

One more thing to watch, which isn't a problem to catch: the order says to
substitute red velvet if hazelnut is gone. Does it apply that fallback, or stop
and ask first? Either is defensible. What you're looking for is whether it
noticed the instruction at all. Type 'exit' when you're done.

### Same code, different tier

Now run the same order on Claude Haiku, the fast tier, and
see how much of it the smaller tier handles. No code changes; only the
deployment name:

```
$env:FOUNDRY_MODEL_DEPLOYMENT="claude-haiku-5-5"; python agent.py; Remove-Item Env:FOUNDRY_MODEL_DEPLOYMENT
```

(That's PowerShell, which the VS Code terminal in the lab uses. The last part
clears the setting once the agent exits, so later runs go back to Sonnet. In
bash or zsh: 'FOUNDRY_MODEL_DEPLOYMENT=claude-haiku-5-5 python agent.py')

Paste the same order, with the new voucher code from the dashboard. Type
'exit' when you're done.

### Compare the two

Put the two replies side by side:

1. **Speed:** How long did each reply take? Would a customer notice?
2. **Accuracy:** Did either one miss or get wrong any of the four problems?
3. **Judgment:** Did each one substitute red velvet or ask first? With a nut
   allergy in the order, which would you want?

Don't be surprised if Haiku handles this order as well as Sonnet. This is a
small, well-defined task with the rules written down, and that's where a smaller
tier can shine. It doesn't mean a smaller tier is right for everything, and this
lab uses Sonnet and Haiku to keep things quick. Most workloads start with Claude
Opus. Whichever model you start with, test it on your own prompts and data before
you change it. [Choosing the right model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model)
walks through how.

> Foundry hosts several Claude tiers behind the same API. Moving a workload
> from Sonnet to Haiku, or back, is a one-line change: the deployment name.
> That's exactly what you just did.

✅ **Checkpoint 7.** The same order run on two Claude tiers, and the two replies
compared.

### 🎉 Lab 1 Wrap Up

You built a Claude agent on Foundry, gave it tools, a persona, and the shop's
own knowledge, made its output schema-safe, had it read handwriting and apply
policy, and compared tiers. Lab 2 takes the next step: an agent
that verifies its own work, and the Foundry features that let it do more on
its own while you stay in charge of the result.
