## Module 2.2: An agent harness for open-ended tasks (20 minutes)

In this module, you'll use the **Claude Agent SDK** to build and repair the kiosk
page. We're using it because this kind of work is open-ended: you can't list
every step up front, so Claude needs to decide the next one. That takes an agent
harness: the loop, tools, and permissions around the model that let it do real
work. The Claude Agent SDK gives you that harness, built on the same foundation
as Claude Code.

You've already seen two other ways to run an agent's loop. In Lab 1, Agent
Framework ran it inside your app, with Claude as the model. That's a great fit
when the agent is part of your app, and Agent Framework also supports the Claude
Agent SDK, so you can pick what fits each agent. In Module 2.1, Python ran it:
your scripts called Claude once per step, saved the file, ran the checks, and
decided whether to try again. That's simpler when you already know every step.

With the SDK, you write what's specific to your job: the brief, the checks, and
the limits. **Claude does the work. You approve results, not keystrokes.**

Here it builds the same demo page as Module 2.1.

| In the manual loop | With the Claude Agent SDK |
|---|---|
| 'generator.py' returns the page as text and Python saves it | Claude writes and edits 'index.html' with file tools |
| 'run_loop.py' calls 'checks.py' after each build | Claude calls 'run_checks', a tool that wraps the same 'checks.py' |
| A Python 'for' loop, up to 'MAX_SPRINTS' | The Claude Agent SDK's own loop, up to a turn limit |
| Three scripts and three prompts | One agent and one prompt |

```
cd ../sparkles-hosted
```

### Step A: run it (5 minutes)

```
python agent.py
```

It takes 30 to 60 seconds. A line prints for each tool call as it happens:

```
  tool: Write index.html
  tool: mcp__sparkles__run_checks
```

'mcp__sparkles__run_checks' is the tool you gave it: 'sparkles' is the server
name and 'run_checks' is the tool. Your code didn't call the checks this time. Claude did, because the brief
says to. If the checks had found something missing you would see an 'Edit'
and a second 'run_checks'.

Then the report prints. Read these fields:

| Field | What it tells you |
|---|---|
| 'passed' | whether the page meets the checks |
| 'checks' | the report itself: which elements were found, and how many items each list has |
| 'steps' | every tool call the agent made, in order |
| 'turns' | how many times Claude was called |
| 'cost_usd' | the Claude Agent SDK's own estimate, which its spending limit uses |
| 'stopped_because' | 'success', the limit it reached, or the error |

**'passed' isn't the agent's opinion.** After the agent stops, 'agent.py'
runs the checks once more itself, outside the agent. The 'passed' and 'checks'
fields come from that run. Find it near the end of 'build_kiosk()'. It's the
idea from Module 2.1 again: the one that writes isn't the one that judges. In Module 2.1 a separate Claude
evaluator was the judge. Here your code is.

**Now look at what it built.** In the terminal, run this to open the page in
your browser:

```
Invoke-Item workspace\index.html
```

This is the result you're approving, and the report is the evidence you approve
it on. Tap a flavor, then click the order button. The 'summary' field usually
says the agent didn't try this, because 'run_checks' only reads the file.

### Step B: read the agent (5 minutes)

**Now that you've seen it run, open 'agent.py'.** Four things to find:

- **'SYSTEM'** is the brief: the same five 'data-testid' values, and the order
  to work in. Its last line says the agent must never report a result it hasn't
  seen.
- **'checks_server()'** wraps 'evidence()' from 'checks.py' as a tool, so the
  agent is measured the same way the loop was.
- **'ClaudeAgentOptions'**, inside 'build_kiosk()', says what the agent may use
  and when it must stop.
- **'foundry_env()'** points the Claude Agent SDK at your Claude deployment, using
  the endpoint and key already in '.env'.

### Step C: ask for something outside its limits (5 minutes)

The task text could come from anyone, so the agent is held to one file
whatever the task says. Ask it for a second file:

```
python agent.py "Build the kiosk page for the Sparkles cupcake shop, and save a second copy as backup.html"
```

Look for these two lines in the output:

```
  tool: Write backup.html
    did not run: PreToolUse:Write hook error: Only index.html in the working folder may be read or changed.
```

Claude tried, the rule refused, and the refusal is in the record. Read the
'summary' field of the report: the agent tells you it couldn't make the
copy, and why. The kiosk page still passes.

**Open 'agent.py' and find 'only_the_page()'.** It's a hook: a function the
Claude Agent SDK calls before every file tool runs. It allows 'index.html' in the
working folder and refuses everything else.

This limit is a guardrail. It holds no matter what the task says or what the agent decides, so
you can give the agent longer tasks with more confidence.

The hook isn't the only limit. The agent also has a fixed tool list, with no
terminal or web access, a turn limit and a spending limit for each task, and
final checks run by your code.

> Try it: see a limit work. 'python agent.py --max-turns 1' stops the agent
> after one turn. 'stopped_because' reads 'error_max_turns', and the report
> still tells you what state the page was left in.

### Step D: hand it the broken page (5 minutes)

In Module 2.1, your script ran the loop on a page with two planted bugs. Now
give the agent that same page, with the 'BUG' comments taken out, so it has to
find the problems itself:

```
cp ../sparkles-loop/seeds/kiosk_unmarked.html workspace/index.html
python agent.py --keep "This page was built to the brief but has problems. Find them and fix them."
```

'--keep' carries on with the page that's already there. Without it, the agent
starts from an empty folder.

Watch the tool lines:

```
  tool: Read index.html
  tool: mcp__sparkles__run_checks
  tool: Edit index.html
  tool: mcp__sparkles__run_checks
```

It reads the page, runs the checks to find out what's wrong, makes its edit,
and checks again. Read the 'summary' field: it names both bugs. Your flavors
may not match your neighbor's, because the brief sets a minimum of three and
the agent picks the rest.

Refresh the browser, tap a flavor, and click the order button. 'passed' tells
you the right parts are on the page. It can't tell you the button works, so
that part is yours to approve.

> Why this matters. You didn't review the HTML. You set what done means and
> the limits, then read the evidence. The checks prove the page has the right
> parts, and they can't prove the button works, so you tried it yourself.
> Knowing what your evidence covers is how you can trust an agent with more
> than you can read line by line.

> To learn more, see [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

✅ **Checkpoint 9.** A kiosk page built, checked, and repaired by one agent,
with a report of every step it took, and one step refused because it was
outside the limits you set.
