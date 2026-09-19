"""Module 2.2 - Fresh knowledge: web search on Claude in Foundry.

Pinned to web_search_20250305, the version this lab is tested on. A version
string that does not exist returns HTTP 400 listing the valid ones.

Run:  python websearch.py        (from sparkles-loop; reads the repo .env)
"""

import os

from anthropic import AnthropicFoundry
from dotenv import load_dotenv

load_dotenv()
load_dotenv(__import__("pathlib").Path(__file__).resolve().parent.parent / ".env")

# Edit this line to research something else.
QUESTION = ("What cupcake flavors are trending this fall? Recommend one as "
            "tomorrow's Sparkles special and say why. Cite your sources.")

client = AnthropicFoundry(
    api_key=os.environ["FOUNDRY_API_KEY"],
    base_url=os.environ["FOUNDRY_ENDPOINT"],
)

r = client.messages.create(
    model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
    max_tokens=2048,   # 1024 cuts the cited answer off mid-sentence
    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
    messages=[{"role": "user", "content": QUESTION}],
)

sources = []
for block in r.content:
    if block.type == "text":
        print(block.text)
        for c in getattr(block, "citations", None) or []:
            url = getattr(c, "url", None)
            if url and url not in sources:
                sources.append(url)

if sources:
    print("\nSources:")
    for url in sources:
        print(" -", url)
