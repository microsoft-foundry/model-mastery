# For the Skillable team

This folder holds the lab text.

| Path | What it is |
| --- | --- |
| `lab1/` | Lab 1, one page per module: `intro.md`, then `module-1.0.md` to `module-1.6.md` |
| `lab2/` | Lab 2, one page per module: `intro.md`, then `module-2.1.md` to `module-2.4.md` |
| `images/` | Every screenshot the pages reference, numbered in reading order |

Pages reference screenshots as `../images/…`.

## The seat image

Build it from the root of the repo, everything except `instructor/`.

Attendees run code from three folders and edit files in place, so these have to
be present and writable:

- `sparkles-agent/` — `agent.py` is edited across modules 1.1 to 1.6
- `sparkles-loop/` — the Lab 2 loop
- `sparkles-evals/` — Module 2.4

`foundry-iq/` and `eval-endpoint/` are also needed: setup installs
`foundry-iq/requirements.txt`, and a Lab 2 page links to
`eval-endpoint/README.md`.

Two things make a seat work:

```
pip install -r requirements.txt -r foundry-iq/requirements.txt
```

and a filled-in `.env` at the root of the repo, not in `sparkles-agent/`.
Every script reads it from there. `.env.example` lists the settings.

## Changes after handover

If a page in this folder is updated after you have taken your copy, we will
tell you which one.
