"""LLM backends.

AnthropicLLM  - real model via the Claude Messages API (stdlib urllib, no SDK needed)
OpenAICompatLLM - any OpenAI-compatible API. Default: Groq, which has a free tier (no card)
MockLLM       - offline rule-based planner with the same interface, so the demo,
                tests and evals run without an API key.

Both take Anthropic-format messages and return:
    {"content": [blocks...], "text": str, "tool_calls": [{"id", "name", "input"}]}
"""
import json
import os
import re
import urllib.error
import urllib.request
import uuid


class AnthropicLLM:
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key, model=None):
        self.api_key = api_key
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

    def complete(self, system, messages, tools):
        body = json.dumps({
            "model": self.model,
            "max_tokens": 1024,
            "system": system,
            "messages": messages,
            "tools": tools,
        }).encode()
        req = urllib.request.Request(self.URL, data=body, method="POST", headers={
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"API error {e.code}: {e.read().decode()[:300]}") from e
        content = data["content"]
        return {
            "content": content,
            "text": "".join(b["text"] for b in content if b["type"] == "text"),
            "tool_calls": [
                {"id": b["id"], "name": b["name"], "input": b["input"]}
                for b in content if b["type"] == "tool_use"
            ],
        }


class OpenAICompatLLM:
    """Talks to OpenAI-style chat APIs (Groq, OpenAI, local Ollama) and converts
    to/from the Anthropic-style messages the agent uses internally."""

    def __init__(self, api_key, base_url=None, model=None):
        self.api_key = api_key
        self.url = (base_url or os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")).rstrip("/") + "/chat/completions"
        self.model = model or os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

    @staticmethod
    def _to_openai(system, messages):
        out = [{"role": "system", "content": system}]
        for m in messages:
            c = m["content"]
            if isinstance(c, str):
                out.append({"role": m["role"], "content": c})
            elif m["role"] == "assistant":
                text = "".join(b["text"] for b in c if b["type"] == "text")
                calls = [{"id": b["id"], "type": "function",
                          "function": {"name": b["name"], "arguments": json.dumps(b["input"], ensure_ascii=False)}}
                         for b in c if b["type"] == "tool_use"]
                msg = {"role": "assistant", "content": text or None}
                if calls:
                    msg["tool_calls"] = calls
                out.append(msg)
            else:  # tool results
                for b in c:
                    if b.get("type") == "tool_result":
                        out.append({"role": "tool", "tool_call_id": b["tool_use_id"], "content": b["content"]})
        return out

    def complete(self, system, messages, tools):
        body = json.dumps({
            "model": self.model,
            "max_tokens": 1024,
            "temperature": 0.2,
            "messages": self._to_openai(system, messages),
            "tools": [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                         "parameters": t["input_schema"]}} for t in tools],
        }).encode()
        req = urllib.request.Request(self.url, data=body, method="POST", headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
            "User-Agent": "rentora-support-agent/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"API error {e.code}: {e.read().decode()[:300]}") from e
        msg = data["choices"][0]["message"]
        text = msg.get("content") or ""
        content = [{"type": "text", "text": text}] if text else []
        calls = []
        for tc in msg.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            calls.append({"id": tc["id"], "name": tc["function"]["name"], "input": args})
            content.append({"type": "tool_use", "id": tc["id"], "name": tc["function"]["name"], "input": args})
        return {"content": content or [{"type": "text", "text": ""}], "text": text, "tool_calls": calls}


# --------------------------------------------------------------------------
GERMAN_HINTS = re.compile(
    r"\b(ich|mein|meine|ist|und|bitte|wie|was|kann|ein|eine|hallo|danke|auto|buchung|gibt|für|habe)\b", re.I)
CITIES = {"munich": "Munich", "münchen": "Munich", "muenchen": "Munich", "berlin": "Berlin",
          "hamburg": "Hamburg", "nuremberg": "Nuremberg", "nürnberg": "Nuremberg", "nuernberg": "Nuremberg"}
CATEGORIES = ["Economy", "Compact", "SUV", "Van", "Premium"]
ESCALATE = re.compile(
    r"\b(accident|crash|damage dispute|complain|complaint|refund|human|person|manager|unfall|"
    r"beschwerde|mitarbeiter|mensch|erstattung|angefahren)\w*", re.I)


def is_german(text):
    return len(GERMAN_HINTS.findall(text)) >= 2


class MockLLM:
    """Deterministic stand-in for a real model. Good enough to demo the agent loop."""

    def complete(self, system, messages, tools):
        last = messages[-1]
        user_text = next(m["content"] for m in reversed(messages) if isinstance(m["content"], str))
        if isinstance(last["content"], list):          # we just got tool results back
            results = [json.loads(b["content"]) for b in last["content"] if b.get("type") == "tool_result"]
            names = self._called_tool_names(messages)
            return self._text(self._answer(user_text, names, results))
        call = self._plan(user_text)
        if call is None:
            de = is_german(user_text)
            return self._text(
                "Gerne! Ich helfe bei Verfügbarkeit, Buchungen und Mietbedingungen. Worum geht es?"
                if de else "Happy to help with availability, bookings and rental policies. What do you need?")
        block = {"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:12], "name": call[0], "input": call[1]}
        return {"content": [block], "text": "", "tool_calls": [{"id": block["id"], "name": call[0], "input": call[1]}]}

    # -- planning ---------------------------------------------------------
    def _plan(self, text):
        booking = re.search(r"\bRNT-\d{4}\b", text, re.I)
        if ESCALATE.search(text):
            return ("create_handoff", {
                "summary": f"Customer message: {text}",
                "priority": "high" if re.search(r"accident|unfall|crash", text, re.I) else "normal",
                **({"booking_id": booking.group(0).upper()} if booking else {}),
            })
        if booking:
            name = re.search(r"(?:last name|surname|name|nachname)\s*(?:is|ist|:)?\s*([A-ZÄÖÜ][a-zäöüß]+)", text, re.I)
            return ("get_booking", {"booking_id": booking.group(0).upper(),
                                    "last_name": name.group(1) if name else ""})
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        city = next((v for k, v in CITIES.items() if k in text.lower()), None)
        if city and len(dates) >= 2:
            args = {"city": city, "start_date": dates[0], "end_date": dates[1]}
            cat = next((c for c in CATEGORIES if c.lower() in text.lower()), None)
            if cat:
                args["category"] = cat
            return ("find_available_cars", args)
        if len(text.split()) >= 3:
            return ("search_policies", {"query": text})
        return None

    # -- answering --------------------------------------------------------
    def _answer(self, text, names, results):
        de = is_german(text)
        r = results[-1]
        tool = names[-1]
        if "error" in r:
            return ("Das konnte ich leider nicht prüfen: " if de else "I couldn't complete that: ") + r["error"]
        if tool == "get_booking":
            return (f"Ihre Buchung {r['booking_id']} ({r['model']}, {r['city']}) vom {r['start_date']} bis "
                    f"{r['end_date']} hat den Status: {r['status']}. Tarif: {r['rate']}."
                    if de else
                    f"Your booking {r['booking_id']} ({r['model']}, {r['city']}) from {r['start_date']} to "
                    f"{r['end_date']} is {r['status']}. Rate: {r['rate']}.")
        if tool == "find_available_cars":
            cars = r["available"]
            if not cars:
                return "Leider ist in diesem Zeitraum kein passendes Auto frei." if de else \
                    "Sorry, no matching car is free for those dates."
            per, tot = ("EUR/Tag", "EUR gesamt") if de else ("EUR/day", "EUR total")
            lines = [f"- {c['model']} ({c['category']}): {c['price_per_day']} {per}, ~{c['estimated_total_eur']} {tot}"
                     for c in cars[:3]]
            city_de = {"Munich": "München", "Nuremberg": "Nürnberg"}.get(r["city"], r["city"])
            head = f"Verfügbar in {city_de}:" if de else f"Available in {r['city']}:"
            return head + "\n" + "\n".join(lines)
        if tool == "create_handoff":
            return (f"Ich habe Ihren Fall an unser Team übergeben (Ticket {r['ticket_id']}). "
                    "Bei einem Unfall: bitte Polizei und Hotline +49 89 000000 anrufen."
                    if de else
                    f"I've passed this to a human colleague (ticket {r['ticket_id']}). "
                    "If there was an accident, please call the police and our 24/7 hotline +49 89 000000.")
        if tool == "search_policies":
            if not r["results"]:
                return "Dazu habe ich keine Regel gefunden." if de else "I couldn't find a policy on that."
            top = r["results"][0]
            return (f"Laut unseren Bedingungen ({top['title']}): " if de else f"Per our {top['title']} policy: ") + top["text"]
        return json.dumps(r)

    @staticmethod
    def _called_tool_names(messages):
        return [b["name"] for m in messages if m["role"] == "assistant" and isinstance(m["content"], list)
                for b in m["content"] if b.get("type") == "tool_use"]

    @staticmethod
    def _text(t):
        return {"content": [{"type": "text", "text": t}], "text": t, "tool_calls": []}


def get_llm():
    """Picks the backend: AGENT_MODE=mock forces offline mode. Otherwise the first key found wins:
    GROQ_API_KEY (free tier) -> LLM_API_KEY (any OpenAI-compatible API) -> ANTHROPIC_API_KEY -> offline mock."""
    if os.getenv("AGENT_MODE", "").lower() == "mock":
        return MockLLM()
    if os.getenv("GROQ_API_KEY"):
        return OpenAICompatLLM(os.environ["GROQ_API_KEY"])
    if os.getenv("LLM_API_KEY"):
        return OpenAICompatLLM(os.environ["LLM_API_KEY"])
    if os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicLLM(os.environ["ANTHROPIC_API_KEY"])
    return MockLLM()
