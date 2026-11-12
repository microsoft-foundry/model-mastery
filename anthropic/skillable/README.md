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

Attendees run code from four folders and edit files in place, so these have to
be present and writable:

- `sparkles-agent/` — `agent.py` is edited across modules 1.1 to 1.6
- `sparkles-loop/` — the Lab 2 loop
- `sparkles-hosted/` — Module 2.2. The agent writes its page to
  `sparkles-hosted/workspace/`
- `sparkles-evals/` — Module 2.4

`foundry-iq/` and `eval-endpoint/` are also needed: setup installs
`foundry-iq/requirements.txt`, and a Lab 2 page links to
`eval-endpoint/README.md`.

Two things make a seat work:

```
pip install -r requirements.txt
```

and a filled-in `.env` in the `anthropic` folder, not in `sparkles-agent/`.
Every script reads it from there. `.env.example` lists the settings.

At the end of Module 2.3 attendees send a task to a hosted agent in the
workshop's Foundry project and open its trace in the Foundry portal. They
sign in with `az login`, as they do for Module 2.4. Their accounts need to
be allowed to call agents in that project and to see its traces.

The instructors supply the values. Every setting in `.env.example` down to
`EVAL_ENDPOINT_CONNECTION` needs one, plus `EVAL_ENDPOINT_URL`. Leave
`ENABLE_OTEL` at `"0"`; attendees change it in Module 2.3. Leave
`EVAL_ENDPOINT_API_KEY` empty: it is a secret and no attendee step reads it.

`requirements.txt` includes `claude-agent-sdk`, which Module 2.2 needs. It is
about 240 MB because it includes the program it runs (`claude.exe` on
Windows). That program has to be allowed to run on the seat, and it calls only
the seat's own Foundry endpoint.

To check a seat, run this from `sparkles-hosted/`. It should print
`"passed": true` within a minute:

```
python agent.py
```

## Changes after handover

If a page in this folder is updated after you have taken your copy, we will
tell you which one.
