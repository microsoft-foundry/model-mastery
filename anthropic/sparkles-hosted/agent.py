"""The Sparkles kiosk builder as one Claude Agent SDK agent.

The manual loop in sparkles-loop/ calls Claude once per step and Python does
the rest: it saves the file, runs the checks, and decides whether to try
again. Here Claude does that work. It writes and edits index.html with file
tools, runs the same static checks through a tool, and keeps going until the
checks pass or it reaches the turn limit.

Run:  python agent.py                                       build the kiosk page
      python agent.py --keep "Make the order button pink"   carry on with the same page
      python agent.py --max-turns 2                         stop it early, to see the limit work
"""

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    ProcessError,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    create_sdk_mcp_server,
    query,
    tool,
)
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")

# Foundry keeps names starting FOUNDRY_ for itself inside a hosted agent, so
# there the deployment names arrive as SPARKLES_MODEL and SPARKLES_FAST_MODEL.
MODEL = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT") or os.environ.get("SPARKLES_MODEL", "claude-sonnet-5-5")
FAST_MODEL = (os.environ.get("FOUNDRY_HAIKU_DEPLOYMENT")
              or os.environ.get("SPARKLES_FAST_MODEL", "claude-haiku-5-5"))
os.environ.setdefault("FOUNDRY_MODEL_DEPLOYMENT", MODEL)   # common.py reads it on import

# The static checks are the ones the manual loop uses. They sit next to this
# file in the container and in sparkles-loop/ in the repo.
if not (HERE / "checks.py").exists():
    sys.path.insert(0, str(HERE.parent / "sparkles-loop"))
from checks import evidence  # noqa: E402
from common import REQUIRED_TESTIDS  # noqa: E402
from signin import sign_in  # noqa: E402
from tracing import TaskTrace, setup_local  # noqa: E402

setup_local()

MAX_TURNS = int(os.environ.get("SPARKLES_MAX_TURNS", "20"))
MAX_BUDGET_USD = float(os.environ.get("SPARKLES_MAX_BUDGET_USD", "1.00"))
MIN_FLAVORS = 3

SYSTEM = f"""You build one file, index.html, in the current folder: a
self-contained kiosk page for the Sparkles cupcake shop (inline CSS and JS, no
external files, no CDN).

Use exactly these data-testid values on the matching elements:
{", ".join(REQUIRED_TESTIDS)}. List at least {MIN_FLAVORS} flavors. Each flavor must be
its own child element inside the element with data-testid="flavor-list". Tapping a flavor selects and
highlights it. The order button adds one to the order count only when a flavor
is selected.

Work in this order:
1. Write index.html.
2. Call run_checks. It reads the file and reports what is there.
3. If anything is MISSING or wrong, edit the file and call run_checks again.
4. Stop when the checks are clean. Finish with two or three sentences saying
   what you built and what the last run_checks reported.

run_checks is the evidence. Never report a result you have not seen it return."""

# Added to the brief when there is already a page to carry on with.
EXISTING_PAGE = """

index.html already exists. Instead of step 1, read it and use Edit to change
only what the task asks for."""


def foundry_env() -> tuple[dict, dict]:
    """Point the Agent SDK at Claude in Foundry.

    On your machine it signs in with the key from .env. In a hosted agent there
    is no key: Foundry supplies the project endpoint and the agent signs in as
    itself. Returns the settings, and a record of the sign-in for the trace.
    """
    base_url = os.environ.get("FOUNDRY_ENDPOINT")
    if not base_url:
        host = urlparse(os.environ["FOUNDRY_PROJECT_ENDPOINT"]).netloc.split(".")[0]
        base_url = f"https://{host}.services.ai.azure.com/anthropic"
    env = {
        "CLAUDE_CODE_USE_FOUNDRY": "1",
        "ANTHROPIC_FOUNDRY_BASE_URL": base_url,
        # Foundry has no model list to check names against, so say which
        # deployment each model family means.
        "ANTHROPIC_DEFAULT_SONNET_MODEL": MODEL,
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": FAST_MODEL,
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    }
    if os.environ.get("FOUNDRY_API_KEY"):
        env["ANTHROPIC_FOUNDRY_API_KEY"] = os.environ["FOUNDRY_API_KEY"]
        return env, {"identity": "key from .env"}
    token, record = sign_in(base_url, MODEL)
    env["ANTHROPIC_FOUNDRY_AUTH_TOKEN"] = token
    return env, record


def why(content) -> str:
    """The first line of a tool result, which for a refusal is the reason."""
    if not isinstance(content, str):
        content = " ".join(str(part.get("text", "")) for part in content or [] if isinstance(part, dict))
    return (content.strip().splitlines() or [""])[0][:200]


def checks_passed(report: str) -> bool:
    flavors = re.search(r"TESTID flavor-list: present, (\d+) child", report)
    return ("MISSING" not in report and "EXTERNAL RESOURCES: none" in report
            and bool(flavors) and int(flavors.group(1)) >= MIN_FLAVORS)


def stopped_reason(result, early) -> str:
    """Why the agent stopped. A failed API call can arrive marked "success"."""
    subtype = result.subtype if result else getattr(early, "subtype", None)
    if early and subtype in (None, "success"):
        return getattr(early, "terminal_reason", None) or "error"
    return subtype or "no result"


def checks_server(workspace: Path):
    @tool("run_checks", "Read index.html and report which required elements are present.", {})
    async def run_checks(args):
        page = workspace / "index.html"
        if not page.exists():
            return {"content": [{"type": "text", "text": "index.html does not exist yet."}]}
        return {"content": [{"type": "text", "text": evidence(page.read_text(encoding="utf-8"))}]}

    return create_sdk_mcp_server(name="sparkles", tools=[run_checks])


def only_the_page(workspace: Path):
    """A hook that refuses any file tool call that is not on index.html.

    The task text comes from whoever calls the agent, so the file tools are
    held to the one file the agent is here to produce. The hook runs before
    every Read, Write and Edit, whatever the permission settings say.
    """
    page = (workspace / "index.html").resolve()

    async def check(input_data, tool_use_id, context):
        target = str(input_data.get("tool_input", {}).get("file_path", ""))
        path = Path(target) if os.path.isabs(target) else workspace / target
        if target and path.resolve() == page:
            return {}
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Only index.html in the working folder may be read or changed.",
        }}

    return HookMatcher(matcher="Read|Write|Edit", hooks=[check])


async def build_kiosk(task: str, workspace: Path, on_event=print, max_turns: int = MAX_TURNS) -> dict:
    """Run the agent on one task and return what it did, with the evidence."""
    workspace.mkdir(parents=True, exist_ok=True)
    workspace = workspace.resolve()
    # Signing in can wait and retry, so it runs off the main thread.
    env, signed_in = await asyncio.to_thread(foundry_env)
    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=SYSTEM + (EXISTING_PAGE if (workspace / "index.html").exists() else ""),
        cwd=str(workspace),
        tools=["Read", "Write", "Edit"],
        mcp_servers={"sparkles": checks_server(workspace)},
        allowed_tools=["Read(./index.html)", "Edit(./index.html)", "Write(./index.html)",
                       "mcp__sparkles__run_checks"],
        # Anything not on the list above is refused without asking: a hosted
        # agent has no terminal to show a permission prompt in.
        permission_mode="dontAsk",
        hooks={"PreToolUse": [only_the_page(workspace)]},
        setting_sources=[],
        max_turns=max_turns,
        max_budget_usd=MAX_BUDGET_USD,
        env=env,
    )

    steps, by_id, summary, result, early = [], {}, "", None, None
    with TaskTrace(task, MODEL) as trace:
        trace.note(**signed_in)
        try:
            async for message in query(prompt=task, options=options):
                if isinstance(message, AssistantMessage):
                    trace.model_call(message)
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            trace.tool_started(block)
                            target = Path(block.input.get("file_path", "")).name
                            by_id[block.id] = {"tool": block.name, "target": target}
                            steps.append(by_id[block.id])
                            on_event(f"  tool: {block.name} {target}".rstrip())
                        elif isinstance(block, TextBlock) and block.text.strip():
                            summary = block.text.strip()
                elif isinstance(message, UserMessage) and isinstance(message.content, list):
                    for block in message.content:
                        if isinstance(block, ToolResultBlock):
                            trace.tool_finished(block)
                            step = by_id.get(block.tool_use_id)
                            if block.is_error and step:
                                # A call the file rule refused, or one that failed.
                                step["did_not_run"] = why(block.content)
                                on_event(f"    did not run: {step['did_not_run']}")
                elif isinstance(message, ResultMessage):
                    result = message
        except ProcessError as stopped:
            # The agent stopped early: it reached a limit, or a call failed.
            # Report why, with whatever it had built, instead of crashing.
            early = stopped
            on_event(f"  stopped early: {stopped_reason(result, early)}")

        page = workspace / "index.html"
        html = page.read_text(encoding="utf-8") if page.exists() else ""
        # Run the checks once more here, outside the agent. What comes back to
        # the caller is this report, not the agent's account of it.
        report = evidence(html) if html else "index.html was not written."
        passed = bool(html) and checks_passed(report)
        trace.finish(result, passed, stopped_reason(result, early))
    return {
        "passed": passed,
        "checks": report,
        "summary": (result.result if result and result.result else summary) or (str(early) if early else ""),
        "steps": steps,
        "turns": result.num_turns if result else None,
        "cost_usd": result.total_cost_usd if result else None,
        "stopped_because": stopped_reason(result, early),
        "session_id": result.session_id if result else None,
        "html": html,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the Sparkles kiosk page with one agent.")
    parser.add_argument("task", nargs="*", help="what to build or change")
    parser.add_argument("--keep", action="store_true", help="carry on with the page already in workspace/")
    parser.add_argument("--max-turns", type=int, default=MAX_TURNS, help="stop after this many turns")
    args = parser.parse_args()
    task = " ".join(args.task) or "Build the kiosk page for the Sparkles cupcake shop."
    workspace = HERE / "workspace"
    if not args.keep:                  # start from an empty folder unless told to carry on
        (workspace / "index.html").unlink(missing_ok=True)
    out = asyncio.run(build_kiosk(task, workspace, max_turns=args.max_turns))
    html = out.pop("html")
    print(json.dumps(out, indent=2))
    print(f"Open {workspace / 'index.html'}  ({len(html):,} characters)")
