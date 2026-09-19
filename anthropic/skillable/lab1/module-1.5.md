## Module 1.5: Claude can see: the catering order (15 minutes)

A catering order just arrived as a photo of a handwritten note. One item is
crossed out with a replacement scribbled next to it, quantities are tally
marks, and there is an allergy note in the margin. Nothing on it is
machine-readable. This module shows what Claude does with it.

### Look at the order

Open 'sparkles-agent/images/catering-order.jpg' in VS Code and read it
yourself. Note the correction and the allergy note; you will check that
Claude honors both.

### How the script works

Open 'sparkles-agent/catering.py'. It chains everything you have built so
far, plus vision:

1. **Vision + structured outputs.** The photo goes to Claude as an image
   block, and the response is forced into an order schema (customer, items,
   allergy notes, corrections applied). This is the part no regex could do.
2. **The agent works the order.** The clean order goes to the Sparkles agent
   with both tool servers from Module 1.3 and a short brief. The counter
   takes one cupcake per customer, so a catering order can never be placed in
   full at the counter. The agent looks up the allergen and catering policy
   in the knowledge base, checks the menu, flags anything that conflicts with
   the allergy note, places **one test order** for the first item that is
   available and safe, and spells out what the catering team must handle and
   what the customer needs to do (notice period, deposit).
3. **The receipt** from Module 1.4, for the whole catering order.

The image is sent like this:

```python-notype
{"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}},
{"type": "text", "text": "This is a handwritten catering order ... Crossed-out items are cancelled ..."}
```

### Run it

Have two things ready: your customer ID from Module 1.2, and the voucher code
on the order dashboard.

```
python catering.py images/catering-order.jpg
```

The agent reads the photo, then asks you for what it needs to place the test
order. Answer it (for example 'My customer ID is ABCD2345, voucher 4KQ7ZP'),
then type 'done' to print the receipt.

Check the output against the photo:

- Did the crossed-out item disappear and the replacement appear?
- Are the tally-mark quantities right?
- Is the allergy note captured, and did the agent quote the shop's allergen
  policy (the facility processes tree nuts) rather than guessing?
- Did it explain the catering rules from the knowledge base (72 hours notice,
  50 percent deposit for 25 or more)?
- Does the receipt list every item on the photo?

**Checkpoint 6.** The photo read correctly, the shop's own policy applied,
one safe test order placed, and a receipt for the whole catering order. No
parser could have read the note.
