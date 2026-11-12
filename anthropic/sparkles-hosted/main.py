"""Hosted agent entry point: one task in, one JSON result out.

Foundry runs this file in a container and sends each request to
POST /invocations on port 8088. The reply is a single JSON document, not a
stream, so that Foundry evaluations can call the agent too.

Run locally:  python main.py
Then:         curl -X POST localhost:8088/invocations -d "Build the kiosk page"
"""

import hashlib
import json
import os
from pathlib import Path

from azure.ai.agentserver.invocations import InvocationAgentServerHost
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from agent import build_kiosk

app = InvocationAgentServerHost()

# Each session gets its own folder under $HOME, which Foundry keeps between
# requests in the same session. A follow-up request finds the page still there.
WORKSPACES = Path(os.environ.get("HOME", "/tmp")) / "sparkles"


def read_task(body: str) -> str:
    """Accept plain text, or JSON with the task under a common key."""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return body
    if isinstance(data, dict):
        for key in ("task", "input", "message", "query"):
            if isinstance(data.get(key), str):
                return data[key]
    return body


@app.invoke_handler
async def handle_invoke(request: Request) -> Response:
    task = read_task((await request.body()).decode("utf-8", errors="replace").strip())
    if not task:
        return JSONResponse({"error": "Send the task as the request body."}, status_code=400)

    session = str(request.state.session_id)
    # The folder name is a hash, so nothing the caller typed reaches the file system.
    folder = hashlib.sha256(session.encode("utf-8")).hexdigest()[:32]
    try:
        result = await build_kiosk(task, WORKSPACES / folder)
    except Exception as e:  # the caller should get a reason, not a dropped connection
        print(f"agent failed: {e!r}", flush=True)
        return JSONResponse({"error": str(e)[:500], "session": session}, status_code=500)
    return JSONResponse({"session": session, **result})


if __name__ == "__main__":
    app.run()
