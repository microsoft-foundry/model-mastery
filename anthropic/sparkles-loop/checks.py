"""Static checks: read workspace/index.html and report what is actually there.

This replaces a browser for the workshop. It is the evaluator's evidence:
plain facts about the file, never the generator's own claims.

Run:  python checks.py
"""

import re
from html.parser import HTMLParser

from common import REQUIRED_TESTIDS, WORKSPACE


class _Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.testids = {}          # testid -> text collected inside it
        self.children = {}         # testid -> number of direct child elements
        self.external = []         # external script/style sources
        self._stack = []           # open testids
        self._depth = {}           # testid -> depth at which it was opened
        self._d = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._d += 1
        if tag == "script" and a.get("src"):
            self.external.append(a["src"])
        if tag == "link" and a.get("href", "").endswith(".css"):
            self.external.append(a["href"])
        for tid in self._stack:
            if self._d == self._depth[tid] + 1:
                self.children[tid] = self.children.get(tid, 0) + 1
        tid = a.get("data-testid")
        if tid:
            self.testids.setdefault(tid, "")
            self.children.setdefault(tid, 0)
            self._stack.append(tid)
            self._depth[tid] = self._d
        if tag in ("br", "img", "input", "meta", "link", "hr"):
            self._d -= 1

    def handle_endtag(self, tag):
        if self._stack and self._depth[self._stack[-1]] == self._d:
            self._stack.pop()
        self._d -= 1

    def handle_data(self, data):
        for tid in self._stack:
            self.testids[tid] += data.strip() + " "


def evidence(html: str) -> str:
    s = _Scan()
    s.feed(html)
    lines = [f"FILE: {len(html):,} characters, {html.count(chr(10)) + 1} lines"]
    lines.append(f"EXTERNAL RESOURCES: {s.external or 'none'}")
    lines.append(f"INLINE SCRIPT: {'yes' if re.search(r'<script(?![^>]*src)', html) else 'no'}")
    for tid in REQUIRED_TESTIDS:
        if tid in s.testids:
            text = s.testids[tid].strip()[:60]
            lines.append(f"TESTID {tid}: present, {s.children.get(tid, 0)} child elements, "
                         f"text starts '{text}'")
        else:
            lines.append(f"TESTID {tid}: MISSING")
    extra = sorted(set(s.testids) - set(REQUIRED_TESTIDS))
    if extra:
        lines.append(f"OTHER TESTIDS: {extra}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(evidence((WORKSPACE / "index.html").read_text(encoding="utf-8")))
