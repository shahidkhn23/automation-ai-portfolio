"""Tools the support agent can call. Pure Python, no external dependencies."""
import json
import math
import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

DATA = Path(__file__).parent / "data"
HANDOFF_FILE = DATA / "handoffs.jsonl"


def _load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- retrieval
STOPWORDS = set("""a an the is are was be to of in on for at by with and or do does can i my me you your we our it
this that what how much many when where which who there any if not no from have has will would about
der die das ein eine einen ist sind und oder zu im in am an auf für mit von bei wie was wo wann ich mein meine
meinen mir sie ihr es kann darf muss gibt es man den dem des nicht kein keine bitte""".split())


def _tokenize(text):
    # drop filler words, then crude stemming (first 6 letters) so "cancel" matches "cancellation"
    words = re.findall(r"[a-zäöüß0-9]+", text.lower())
    return [w[:6] for w in words if w not in STOPWORDS]


def _load_policy_sections():
    text = (DATA / "policies.md").read_text(encoding="utf-8")
    sections = []
    for block in text.split("\n## ")[1:]:
        title, _, body = block.partition("\n")
        sections.append({"title": title.strip(), "text": body.strip()})
    return sections


def search_policies(query, k=2):
    """Small BM25 ranker over the policy sections (no vector DB needed)."""
    sections = _load_policy_sections()
    docs = [_tokenize(s["title"] + " " + s["text"]) for s in sections]
    q = _tokenize(query)
    n = len(docs)
    avg_len = sum(len(d) for d in docs) / n
    k1, b = 1.5, 0.75
    scored = []
    for sec, doc in zip(sections, docs):
        score = 0.0
        for term in set(q):
            df = sum(1 for d in docs if term in d)
            if df == 0:
                continue
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            tf = doc.count(term)
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(doc) / avg_len))
        if score > 0:
            scored.append((score, sec))
    scored.sort(key=lambda x: -x[0])
    results = [
        {"title": s["title"], "text": s["text"].split("\nStichwörter:")[0], "score": round(sc, 2)}
        for sc, s in scored[:k]
    ]
    return {"results": results} if results else {"results": [], "note": "No matching policy found."}


# ---------------------------------------------------------------- fleet
def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def find_available_cars(city, start_date, end_date, category=None):
    try:
        start, end = _parse_date(start_date), _parse_date(end_date)
    except (TypeError, ValueError):
        return {"error": "Dates must use the format YYYY-MM-DD."}
    if end < start:
        return {"error": "end_date is before start_date."}
    if start < date.today():
        return {"error": "start_date is in the past."}

    bookings = [b for b in _load("bookings.json") if b["status"] == "confirmed"]
    days = (end - start).days or 1
    cars = []
    for car in _load("fleet.json"):
        if car["city"].lower() != city.lower():
            continue
        if category and car["category"].lower() != category.lower():
            continue
        busy = any(
            b["car_id"] == car["car_id"]
            and _parse_date(b["start_date"]) <= end
            and _parse_date(b["end_date"]) >= start
            for b in bookings
        )
        if not busy:
            cars.append({**car, "days": days, "estimated_total_eur": car["price_per_day"] * days})
    cars.sort(key=lambda c: c["price_per_day"])
    return {"city": city, "start_date": start_date, "end_date": end_date, "available": cars}


# ---------------------------------------------------------------- bookings
def get_booking(booking_id, last_name):
    """Returns booking details only if the last name matches (identity check)."""
    for b in _load("bookings.json"):
        if b["booking_id"].upper() == booking_id.strip().upper():
            if b["last_name"].lower() != last_name.strip().lower():
                return {"error": "Booking ID and last name do not match. No details can be shared."}
            car = next(c for c in _load("fleet.json") if c["car_id"] == b["car_id"])
            return {**b, "model": car["model"], "city": car["city"], "category": car["category"]}
    return {"error": f"No booking found with ID {booking_id}."}


# ---------------------------------------------------------------- escalation
def create_handoff(summary, priority="normal", booking_id=None):
    ticket = {
        "ticket_id": "TCK-" + uuid.uuid4().hex[:6].upper(),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "priority": priority if priority in ("low", "normal", "high") else "normal",
        "booking_id": booking_id,
        "summary": summary,
    }
    with HANDOFF_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ticket, ensure_ascii=False) + "\n")
    return {"created": True, **ticket}


# ---------------------------------------------------------------- registry
TOOLS = [
    {
        "name": "search_policies",
        "description": "Search Rentora's rental policies (deposit, cancellation, fuel, age, additional driver, cross-border, damage, late return, mileage). Use for any rules or fees question.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search terms, any language"}},
            "required": ["query"],
        },
    },
    {
        "name": "find_available_cars",
        "description": "List cars free in a city for a date range, cheapest first, with estimated total price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "enum": ["Munich", "Berlin", "Hamburg", "Nuremberg"]},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                "category": {"type": "string", "enum": ["Economy", "Compact", "SUV", "Van", "Premium"]},
            },
            "required": ["city", "start_date", "end_date"],
        },
    },
    {
        "name": "get_booking",
        "description": "Look up an existing booking. Requires booking ID (format RNT-1234) AND the customer's last name.",
        "input_schema": {
            "type": "object",
            "properties": {"booking_id": {"type": "string"}, "last_name": {"type": "string"}},
            "required": ["booking_id", "last_name"],
        },
    },
    {
        "name": "create_handoff",
        "description": "Escalate to a human agent. Use for accidents, damage disputes, complaints, refunds, or when the customer asks for a person.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "One-paragraph case summary for the human agent"},
                "priority": {"type": "string", "enum": ["low", "normal", "high"]},
                "booking_id": {"type": "string"},
            },
            "required": ["summary"],
        },
    },
]

_FUNCTIONS = {
    "search_policies": search_policies,
    "find_available_cars": find_available_cars,
    "get_booking": get_booking,
    "create_handoff": create_handoff,
}


def run_tool(name, args):
    fn = _FUNCTIONS.get(name)
    if not fn:
        return {"error": f"Unknown tool {name}"}
    try:
        return fn(**args)
    except TypeError as exc:
        return {"error": f"Bad arguments for {name}: {exc}"}
