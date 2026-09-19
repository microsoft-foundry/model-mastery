# Images

`catering-order.jpg` is the handwritten catering order for Module 1.5.

- **Skillable workshop:** instructors place it here before the event.
- **On your own:** if it is missing, make one. Write it by hand on paper and
  photograph it slightly askew in normal light, then save it here as
  `catering-order.jpg`.

What the note needs:

- A customer name at the top
- Three or four flavor lines with quantities as tally marks. Use flavor names
  exactly as the store's menu shows them (ask your agent "What flavors do you
  have today?").
- One line crossed out with a replacement written beside it
- An allergy note in the margin ("NO NUTS!!" works well)
- A quantity of 25 or more on one line, so the bulk-order policy applies

Test it with `python catering.py images/catering-order.jpg` a few times
before relying on it (instructors: three times on the workshop Sonnet
deployment before shipping the image).

**Instructors: strip the photo's metadata before committing it.** Phone
photos carry EXIF including GPS coordinates, and committing that puts a
location in the repo history permanently:

```
sips -d all your-photo.jpg --out catering-order.jpg
```
