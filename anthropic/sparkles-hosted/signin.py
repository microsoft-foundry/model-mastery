"""Sign the hosted agent in to Claude with its own identity.

A hosted agent has no key. It asks Azure for a token as itself and Foundry
decides whether that identity may call Claude. This file gets the token,
checks Claude accepts it before any work starts, and tries again if not.

Without the check, a refused sign-in only shows up three minutes later, after
the Agent SDK has given up retrying.
"""

import base64
import json
import os
import time
import urllib.error
import urllib.request

SCOPE = "https://cognitiveservices.azure.com/.default"
ATTEMPTS = int(os.environ.get("SPARKLES_SIGNIN_ATTEMPTS", "6"))
WAIT_SECONDS = float(os.environ.get("SPARKLES_SIGNIN_WAIT", "5"))


def principal(token: str) -> str:
    """The identity a token was issued to. This is safe to log; the token is not."""
    try:
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return str(claims.get("oid", "unknown"))
    except (IndexError, ValueError):
        return "unknown"


def accepted(base_url: str, token: str, model: str) -> int:
    """Ask Claude to count the tokens in one word. Returns the HTTP status.

    Counting tokens runs no model and costs nothing, so it is a cheap way to
    find out whether this identity is allowed in.
    """
    request = urllib.request.Request(
        f"{base_url}/v1/messages/count_tokens", method="POST",
        data=json.dumps({"model": model, "messages": [{"role": "user", "content": "hi"}]}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status
    except urllib.error.HTTPError as e:
        return e.code
    except OSError:
        return 0


def sign_in(base_url: str, model: str) -> tuple[str, dict]:
    """A token Claude accepts, and a record of how it went for the trace."""
    from azure.identity import DefaultAzureCredential

    token, status, attempt = "", 0, 0
    for attempt in range(1, ATTEMPTS + 1):
        # A new credential each time, so a retry gets a new token and not the
        # one Azure's library remembered from the attempt before.
        token = DefaultAzureCredential().get_token(SCOPE).token
        status = accepted(base_url, token, model)
        print(f"sign-in attempt {attempt}: identity {principal(token)}, status {status}", flush=True)
        if status not in (0, 401, 403):
            break
        if attempt < ATTEMPTS:
            time.sleep(WAIT_SECONDS)
    return token, {"identity": principal(token), "signin_attempts": attempt,
                   "signin_status": status}
