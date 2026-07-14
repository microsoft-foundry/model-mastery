"""Custom policy-adherence evaluator for the Lab 1 travel concierge."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

POLICY_PATH = Path(__file__).resolve().parents[1] / "data" / "travel-policy.md"
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class PolicyAdherenceEvaluator:
    """Judge whether an agent response follows the corporate travel policy.

    Follows the azure-ai-evaluation custom evaluator protocol: a callable whose
    ``__call__`` takes keyword-only ``query`` and ``response`` and returns a
    JSON-serializable dict. Cohere ``command-a`` is the judge model, reached via
    the Foundry account's OpenAI-compatible endpoint
    (``{AZURE_AI_ENDPOINT}/openai/v1/chat/completions``) — the same path the
    lab's MAF agents use, and the only path that serves Cohere reliably.
    """

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        deployment_name: str | None = None,
        policy_path: str | Path = POLICY_PATH,
        credential: Any | None = None,
    ) -> None:
        load_dotenv(ENV_PATH)
        # Default to AZURE_AI_ENDPOINT (account-level). The legacy
        # FOUNDRY_PROJECT_ENDPOINT routes through .../api/projects/<p>/openai/v1
        # which has propagation delays and ~40% intermittent 404s, so we avoid it.
        self.endpoint = endpoint or os.getenv("AZURE_AI_ENDPOINT")
        self.deployment_name = deployment_name or os.getenv("COMMAND_A_DEPLOYMENT", "command-a")
        self.policy_path = Path(policy_path)
        self.credential = credential or DefaultAzureCredential()
        self.policy_text = self.policy_path.read_text(encoding="utf-8")

    def __call__(self, *, query: str, response: str, **kwargs: Any) -> dict[str, Any]:
        """Score a response for explicit policy violations and adherence quality."""
        if not self.endpoint:
            return {
                "violates_policy": False,
                "policy_adherence_score": 0,
                "reasoning": "AZURE_AI_ENDPOINT is not set, so the judge model could not run.",
            }

        prompt = self._build_prompt(query=query, response=response, kwargs=kwargs)
        try:
            content = self._chat(prompt)
            return self._parse_judge_json(content)
        except Exception as exc:  # pragma: no cover - depends on live Foundry
            return {
                "violates_policy": False,
                "policy_adherence_score": 0,
                "reasoning": f"Policy judge failed to run: {exc}",
            }

    def _build_prompt(self, *, query: str, response: str, kwargs: dict[str, Any]) -> str:
        context = kwargs.get("context") or kwargs.get("ground_truth") or ""
        return f"""
You are a strict but fair corporate-travel policy judge. Read the policy, the
user query, and the concierge response. Return ONLY JSON with these keys:
violates_policy (boolean), policy_adherence_score (integer 0-5), reasoning
(short string). Penalize responses that book or recommend explicitly disallowed
travel without nudging to compliant alternatives.

# Corporate travel policy
{self.policy_text}

# User query
{query}

# Concierge response
{response}

# Additional context
{context}
""".strip()

    def _chat(self, prompt: str) -> str:
        # Build a fresh OpenAI client per call so the bearer token is always
        # current (DefaultAzureCredential.get_token caches internally, so the
        # repeated call is cheap). This is robust to long-running batches that
        # might span beyond a single token's lifetime.
        from openai import OpenAI

        token = self.credential.get_token("https://cognitiveservices.azure.com/.default").token
        base_url = f"{self.endpoint.rstrip('/')}/openai/v1"
        client = OpenAI(base_url=base_url, api_key=token)
        completion = client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are a JSON-only evaluator."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=400,
        )
        return completion.choices[0].message.content or "{}"

    @staticmethod
    def _parse_judge_json(content: str) -> dict[str, Any]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.removeprefix("json").strip()
        data = json.loads(cleaned)
        return {
            "violates_policy": bool(data.get("violates_policy", False)),
            "policy_adherence_score": max(0, min(5, int(data.get("policy_adherence_score", 0)))),
            "reasoning": str(data.get("reasoning", "No reasoning returned.")),
        }
