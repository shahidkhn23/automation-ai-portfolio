"""Optional AI layer: explains the verified findings in simple language.

Guardrails (this is what keeps the tool on the right side of the
Rechtsdienstleistungsgesetz and stops hallucinated law):
  * The model only receives facts from knowledge_base/laws.json, never asked to "know" the law.
  * It must not tell the user what to do in their specific case.
  * It must not cite any law that is not in the findings.
  * Every answer ends with the free-help list.

Works without any extra package (plain HTTPS call). If no API key is set,
the tool still works and returns the rule-based report.
"""

from __future__ import annotations

import json
import os
import urllib.request

SYSTEM_PROMPT = """You help international students in Germany understand documents.
You receive (1) a document and (2) a list of findings that were checked against German law by hand.

Rules you must follow:
- Explain each finding in simple, friendly English (B1 level). Short sentences.
- Use ONLY the legal facts given in the findings. Never add other laws, paragraphs, numbers or court cases.
- Give general legal information only. Never say what this person should do in their case,
  never say "you will win" or "this clause is definitely invalid for you".
  Say what the law generally says and that exceptions exist.
- If the user's language is given, answer in that language.
- Finish with: who can check it for free (from the free_help list) and the disclaimer, unchanged.
"""


ASK_PROMPT = """You help students in Germany understand their rights.
You receive a question and verified legal rules from a knowledge base.

Rules you must follow:
- Answer ONLY with the facts in the given rules. Never add other laws, numbers, deadlines or court cases.
- If the rules do not answer the question, say so and point to the free help. Do not guess.
- Give general legal information only, never a decision for the person's specific case.
- Simple, friendly language (B1 level), in the requested language. Short sentences.
- End with the free_help list and the disclaimer, unchanged.
"""


def _call(system: str, user: str) -> str | None:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    payload = {
        "model": os.getenv("RIGHTSCHECK_MODEL", "claude-haiku-5-5"),
        "max_tokens": 1500,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        return "".join(b.get("text", "") for b in data.get("content", []))
    except Exception as e:  # network error, bad key ... fall back to the verified answer
        return f"(AI explanation unavailable: {e.__class__.__name__}. Showing the verified answer only.)"


def explain_answer(answer: dict, language: str = "English") -> str | None:
    return _call(ASK_PROMPT, f"Answer language: {language}\n\n<verified>\n"
                             f"{json.dumps(answer, ensure_ascii=False, indent=2)}\n</verified>")


def explain(document: str, report: dict, language: str = "English") -> str | None:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    payload = {
        "model": os.getenv("RIGHTSCHECK_MODEL", "claude-haiku-5-5"),
        "max_tokens": 1500,
        "system": SYSTEM_PROMPT,
        "messages": [{
            "role": "user",
            "content": (
                f"Answer language: {language}\n\n"
                f"<document>\n{document[:15000]}\n</document>\n\n"
                f"<findings>\n{json.dumps(report, ensure_ascii=False, indent=2)}\n</findings>"
            ),
        }],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        return "".join(b.get("text", "") for b in data.get("content", []))
    except Exception as e:  # network error, bad key ... fall back to the rule-based report
        return f"(AI explanation unavailable: {e.__class__.__name__}. Showing the verified report only.)"
