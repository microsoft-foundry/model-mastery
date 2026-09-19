"""Shared pieces for the Sparkles loop: client, models, paths, tracing."""

import os
import time
from contextlib import contextmanager
from pathlib import Path

from anthropic import AnthropicFoundry
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE / "workspace"
SEEDS = HERE / "seeds"
WORKSPACE.mkdir(exist_ok=True)

load_dotenv(HERE / ".env")
load_dotenv(HERE.parent / ".env")

SMART_MODEL = os.environ["FOUNDRY_MODEL_DEPLOYMENT"]          # planner, evaluator
FAST_MODEL = os.environ.get("FOUNDRY_HAIKU_DEPLOYMENT", SMART_MODEL)  # generator

# Every kiosk the generator builds must expose these test ids. The static
# checks look for them and the planner is told to write criteria around them.
REQUIRED_TESTIDS = ["title", "flavor-list", "special", "order-btn", "order-count"]


def client() -> AnthropicFoundry:
    return AnthropicFoundry(
        api_key=os.environ["FOUNDRY_API_KEY"],
        base_url=os.environ["FOUNDRY_ENDPOINT"],
    )


def first_text(response) -> str:
    """The first text block of a response.

    Claude may return a thinking block before the answer, so content[0] is not
    reliably the text.
    """
    return next(b.text for b in response.content if getattr(b, "type", None) == "text")


def banner(text: str) -> None:
    print(f"\n\033[1m--- {text} {'-' * max(3, 60 - len(text))}\033[0m", flush=True)


# ---- tracing (Module 2.3) ---------------------------------------------------
# Set ENABLE_OTEL=1 and APPLICATIONINSIGHTS_CONNECTION_STRING in .env to send
# one trace per run of the script to Application Insights:
#
#   sparkles-session
#     planner          -> POST /anthropic/v1/messages
#     sparkles-run (round 1)
#       generator      -> POST /anthropic/v1/messages
#       evaluator      -> POST /anthropic/v1/messages
#     sparkles-run (round 2)
#       ...
#
# Each agent span carries model, token counts, latency, and whatever the loop
# records on it (score, pass/fail, criteria count). Read them in the Azure
# portal under the Application Insights resource: Investigate > Search
# (View as traces) or Monitoring > Logs. The Foundry portal's Traces tab lists
# Foundry-hosted agents only, not this script.
#
# Optional: set OTEL_SERVICE_NAME=sparkles-loop in .env so the Cloud role name
# in Application Insights is recognisable instead of "unknown_service".

_tracer = None


def setup_tracing() -> bool:
    global _tracer
    if os.environ.get("ENABLE_OTEL", "0").lower() not in ("1", "true", "yes"):
        return False
    conn = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not conn:
        print("ENABLE_OTEL is set but APPLICATIONINSIGHTS_CONNECTION_STRING is empty.")
        return False
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry import trace

    configure_azure_monitor(
        connection_string=conn,
        # Keep every span. Without this the portal shows a sampling warning.
        sampling_ratio=1.0,
        # The Anthropic SDK uses httpx, so that instrumentation stays on and
        # gives us a child span per model call. The standard-library clients
        # only carry the distro's own housekeeping calls (VM metadata lookup,
        # settings fetch), which are noise in the Search view.
        instrumentation_options={
            "urllib": {"enabled": False},
            "urllib3": {"enabled": False},
            "requests": {"enabled": False},
        },
    )
    _tracer = trace.get_tracer("sparkles-loop")
    print("Tracing on: spans go to Application Insights.")
    return True


@contextmanager
def session_span():
    """Root span for one whole run of the script: planner plus every round.

    Wrap the entire loop in this so the Search view shows one trace per run,
    with the planner and each round nested underneath it.
    """
    if not _tracer:
        yield None
        return
    with _tracer.start_as_current_span("sparkles-session") as s:
        yield s


@contextmanager
def run_span(round_no: int):
    """Span for one iteration of the loop, nested inside session_span()."""
    if not _tracer:
        yield None
        return
    with _tracer.start_as_current_span("sparkles-run") as s:
        s.set_attribute("sparkles.round", round_no)
        yield s


class span:
    """Context manager: a named agent span with model, tokens, and latency.

    Usage:
        with span("evaluator", SMART_MODEL) as sp:
            resp = client().messages.create(...)
            sp.record(resp)
            sp.set(score=score, passed=passed)
    """

    def __init__(self, name: str, model: str):
        self.name, self.model, self.usage = name, model, None
        self._span = None
        self._ctx = None

    def __enter__(self):
        self.t0 = time.time()
        if _tracer:
            self._ctx = _tracer.start_as_current_span(self.name)
            self._span = self._ctx.__enter__()
            self._span.set_attribute("gen_ai.operation.name", "invoke_agent")
            self._span.set_attribute("gen_ai.agent.name", self.name)
            self._span.set_attribute("gen_ai.provider.name", "anthropic")
            self._span.set_attribute("gen_ai.request.model", self.model)
        return self

    def record(self, response):
        """Attach token usage (and the model that actually answered)."""
        self.usage = response.usage
        if self._span:
            self._span.set_attribute("gen_ai.response.model", getattr(response, "model", self.model))
            self._span.set_attribute("gen_ai.usage.input_tokens", response.usage.input_tokens)
            self._span.set_attribute("gen_ai.usage.output_tokens", response.usage.output_tokens)

    def set(self, **attrs):
        """Attach loop-specific attributes, e.g. sp.set(score=7, passed=False).

        Keys are prefixed "sparkles." so they are easy to find in Logs.
        Strings are truncated so a long feedback message does not bloat the span.
        """
        if not self._span:
            return
        for key, value in attrs.items():
            if value is None:
                continue
            if isinstance(value, str) and len(value) > 500:
                value = value[:500] + "..."
            if not isinstance(value, (str, int, float, bool)):
                value = str(value)
            self._span.set_attribute(f"sparkles.{key}", value)

    def __exit__(self, *exc):
        secs = time.time() - self.t0
        toks = f", {self.usage.input_tokens} in / {self.usage.output_tokens} out" if self.usage else ""
        print(f"\033[2m[{self.name}: {secs:.1f}s{toks}]\033[0m")
        if self._span:
            self._span.set_attribute("duration_s", round(secs, 2))
            self._ctx.__exit__(*exc)
        return False
