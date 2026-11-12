"""Tracing for the kiosk builder: Module 2.3's idea, applied to the Agent SDK.

The Agent SDK runs Claude in a program of its own, so nothing records the
model calls or the file edits unless this code does. Each task becomes one
trace in Application Insights:

  kiosk-builder                 turns, cost, tokens, passed
    chat claude-sonnet-5-5        how much Claude read on this call
    execute_tool Write          index.html
    chat claude-sonnet-5-5
    execute_tool run_checks     what the checks reported
    execute_tool Write (refused)   a file the agent may not touch, and why
    ...

Token totals and cost are on the top span only. The Agent SDK reports them
once, when the task ends; the figures on each message as it streams are not
final, so they are not used for output tokens.

In a hosted agent Foundry has already set up where traces go. On your machine,
set ENABLE_OTEL=1 in .env, as in Module 2.3.
"""

import os
import time

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    _tracer = trace.get_tracer("sparkles-hosted")
except ImportError:          # tracing is optional on your own machine
    _tracer = None

AGENT_NAME = os.environ.get("FOUNDRY_AGENT_NAME", "sparkles-kiosk-builder")


def setup_local() -> None:
    """On your machine, send traces to Application Insights when ENABLE_OTEL=1."""
    if os.environ.get("FOUNDRY_AGENT_NAME"):
        return                # hosted: Foundry did this already
    from common import setup_tracing
    setup_tracing()


def _text(content) -> str:
    if isinstance(content, str):
        return content
    return " ".join(str(part.get("text", "")) for part in content or [] if isinstance(part, dict))


def _read_tokens(usage: dict) -> int:
    """Everything Claude read on a call. Cached tokens are reported separately."""
    return sum(usage.get(key) or 0 for key in
               ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))


class TaskTrace:
    """Turns the Agent SDK's messages into spans as they arrive.

    A message only arrives once its step is over, so each span is given its
    start time after the fact: a model call starts when the step before it
    ended, and lasts until the last piece of that reply has arrived.
    """

    def __init__(self, task: str, model: str):
        self.task, self.model = task, model
        self._root = self._scope = None
        self._call = None         # the model call still arriving, if any
        self._tools = {}          # tool call id -> (span, tool name)
        self._mark = time.time_ns()

    def __enter__(self):
        if _tracer:
            self._scope = _tracer.start_as_current_span("kiosk-builder")
            self._root = self._scope.__enter__()
            self._root.set_attribute("gen_ai.operation.name", "invoke_agent")
            self._root.set_attribute("gen_ai.agent.name", AGENT_NAME)
            self._root.set_attribute("gen_ai.provider.name", "anthropic")
            self._root.set_attribute("gen_ai.request.model", self.model)
            self._root.set_attribute("sparkles.task", self.task[:500])
        return self

    def __exit__(self, *exc):
        now = time.time_ns()
        self._end_call()
        for span, _ in self._tools.values():      # a tool call that never got an answer
            span.set_attribute("sparkles.unfinished", True)
            span.end(end_time=now)
        self._tools.clear()
        if self._scope:
            self._scope.__exit__(*exc)
        return False

    def note(self, **facts) -> None:
        """Facts about the whole task, such as which identity signed in."""
        if self._root:
            for key, value in facts.items():
                self._root.set_attribute(f"sparkles.{key}", value)

    def model_call(self, message) -> None:
        """One piece of a reply from Claude. A reply arrives as several pieces."""
        now = time.time_ns()
        key = message.message_id or id(message)
        if self._call and self._call["key"] != key:
            self._end_call()
        if not self._call:
            self._call = {"key": key, "start": self._mark, "model": message.model,
                          "usage": message.usage or {}}
        self._call["end"] = now
        self._mark = now

    def _end_call(self) -> None:
        call, self._call = self._call, None
        if not (call and _tracer):
            return
        span = _tracer.start_span(f"chat {call['model']}", start_time=call["start"])
        span.set_attribute("gen_ai.operation.name", "chat")
        span.set_attribute("gen_ai.provider.name", "anthropic")
        span.set_attribute("gen_ai.request.model", self.model)
        span.set_attribute("gen_ai.response.model", call["model"])
        span.set_attribute("sparkles.read_tokens", _read_tokens(call["usage"]))
        span.set_attribute("sparkles.read_tokens_from_cache",
                           call["usage"].get("cache_read_input_tokens") or 0)
        span.end(end_time=call["end"])

    def tool_started(self, block) -> None:
        now = time.time_ns()
        if _tracer:
            name = block.name.split("__")[-1]          # mcp__sparkles__run_checks -> run_checks
            span = _tracer.start_span(f"execute_tool {name}", start_time=now)
            span.set_attribute("gen_ai.operation.name", "execute_tool")
            span.set_attribute("gen_ai.tool.name", name)
            span.set_attribute("gen_ai.tool.call.id", block.id)
            target = os.path.basename(str(block.input.get("file_path", "")))
            if target:
                span.set_attribute("sparkles.file", target)
            self._tools[block.id] = (span, name)

    def tool_finished(self, block) -> None:
        now = time.time_ns()
        self._end_call()
        span, name = self._tools.pop(block.tool_use_id, (None, None))
        if span:
            text = _text(block.content)
            if block.is_error:
                # A call the file rule refused, or one that failed. The reason
                # is the evidence. It goes in the name as well, because not
                # every trace viewer marks a failed step.
                outcome = "refused" if "hook" in text or "permission" in text.lower() else "failed"
                span.update_name(f"execute_tool {name} ({outcome})")
                span.set_status(Status(StatusCode.ERROR, text[:200]))
                span.set_attribute("error.type", outcome)
                span.set_attribute("sparkles.refused_or_failed", text[:500])
            elif name == "run_checks":
                span.set_attribute("sparkles.checks", text[:500])
                span.set_attribute("sparkles.checks_clean", "MISSING" not in text)
            span.end(end_time=now)
        self._mark = now

    def finish(self, result, passed: bool, stopped_because: str) -> None:
        """Totals for the whole task, on the top span."""
        self._end_call()
        if not self._root:
            return
        self._root.set_attribute("sparkles.passed", passed)
        self._root.set_attribute("sparkles.stopped_because", stopped_because)
        if result:
            usage = result.usage or {}
            self._root.set_attribute("gen_ai.usage.input_tokens", _read_tokens(usage))
            self._root.set_attribute("gen_ai.usage.output_tokens", usage.get("output_tokens") or 0)
            self._root.set_attribute("gen_ai.usage.cache_read.input_tokens",
                                     usage.get("cache_read_input_tokens") or 0)
            self._root.set_attribute("sparkles.turns", result.num_turns)
            self._root.set_attribute("sparkles.cost_usd", round(result.total_cost_usd or 0.0, 4))
        if not passed:
            self._root.set_status(Status(StatusCode.ERROR, "checks did not pass"))
