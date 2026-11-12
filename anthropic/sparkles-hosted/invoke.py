"""Send one task to the hosted agent and save the page it built.

The agent runs in Foundry. This script only sends the task, waits, and shows
what came back: the check report, the steps the agent took, and the cost.

Run:  python invoke.py "Build the kiosk page for the Sparkles cupcake shop"
      python invoke.py --session <id> "Make the order button pink"
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")

AGENT_NAME = os.environ.get("HOSTED_AGENT_NAME", "sparkles-kiosk-builder")
args = sys.argv[1:]
session = None
if args[:1] == ["--session"]:
    session, args = args[1], args[2:]
task = " ".join(args) or "Build the kiosk page for the Sparkles cupcake shop."

query = {"api-version": "v1"}
if session:
    query["agent_session_id"] = session
url = (f"{os.environ['AZURE_AI_PROJECT_ENDPOINT']}/agents/{AGENT_NAME}"
       f"/endpoint/protocols/invocations?{urllib.parse.urlencode(query)}")
# Run `az login` first. There is no key for a hosted agent.
token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
request = urllib.request.Request(
    url, data=json.dumps({"task": task}).encode(), method="POST",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})

started = time.time()
try:
    with urllib.request.urlopen(request, timeout=900) as response:
        status, body = response.status, response.read().decode()
        session = response.headers.get("x-agent-session-id", session)
except urllib.error.HTTPError as e:
    status, body = e.code, e.read().decode()
    session = e.headers.get("x-agent-session-id", session)
print(f"HTTP {status} in {time.time() - started:.0f}s, session {session}")

try:
    result = json.loads(body)
except json.JSONDecodeError:
    sys.exit(body[:2000])
html = result.pop("html", "")
print(json.dumps(result, indent=2))
if html:
    page = HERE / "workspace" / "index.html"
    page.parent.mkdir(exist_ok=True)
    page.write_text(html, encoding="utf-8")
    print(f"Saved {page} ({len(html):,} characters)")
