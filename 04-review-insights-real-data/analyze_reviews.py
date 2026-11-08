"""Turns a CSV of real customer reviews into a one-page insight report (HTML) and a labelled CSV.

Usage:
    python analyze_reviews.py data/reviews.csv --company "AurumCars"
    python analyze_reviews.py data/reviews.csv --company "AurumCars" --lang en

Classification:
    - With ANTHROPIC_API_KEY set: each review is classified by Claude (better quality).
    - Without a key: keyword rules (German + English). The report says which mode was used.

Input columns (see data/reviews_template.csv): date, source, rating, text
No reviewer names are needed or stored.
"""
import argparse
import csv
import html
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

CATEGORIES = {
    "pickup_wait":      {"de": "Wartezeit, Shuttle, Abholung", "en": "Waiting, shuttle, pickup"},
    "car_condition":    {"de": "Zustand des Autos",            "en": "Car condition"},
    "staff":            {"de": "Personal vor Ort",             "en": "Staff at the counter"},
    "upsell_pressure":  {"de": "Druck zu Zusatzversicherungen", "en": "Pressure to buy extra insurance"},
    "card_payment":     {"de": "Kreditkarte & Kaution bei Abholung", "en": "Credit card & deposit at pickup"},
    "deposit_damage":   {"de": "Kaution & Schäden nach Rückgabe", "en": "Deposit & damage after return"},
    "car_availability": {"de": "Auto nicht erhalten / falsche Klasse", "en": "No car / wrong category"},
    "support_refund":   {"de": "Kundenservice & Erstattung",   "en": "Customer service & refunds"},
    "booking_app":      {"de": "Buchung, Preis, Online-Check-in", "en": "Booking, price, online check-in"},
    "return":           {"de": "Rückgabe",                     "en": "Return"},
    "other":            {"de": "Allgemein / ohne Thema",       "en": "General / no topic"},
}

KEYWORDS = {
    "pickup_wait":      r"wart|schlange|shuttle|transfer|stunde|minuten|wait|queue|line|hour|minutes",
    "car_condition":    r"dreckig|schmutzig|verschmutzt|sauber|zustand|kaputt|defekt|reifen|neu|lackschäden|kratzer|dirty|clean|condition|broken|tyre|tire",
    "staff":            r"freundlich|personal|mitarbeiter|hilfsbereit|friendly|rude|staff|helpful",
    "upsell_pressure":  r"zusatzversicherung|zusatzpaket|versicherung.*(angeboten|verkauf|drängt|druck|andrehen)|aufdringlich|druck|upsell|pannendienst|mautpaket|insurance",
    "card_payment":     r"kreditkarte|debit|karte.*(nicht|akzept)|embossed|hochprägung|credit card",
    "deposit_damage":   r"kaution.*(zurück|erstatt|einbehalt|abgebucht)|schaden|kratzer.*bezahl|abgebucht|security|deposit|damage",
    "car_availability": r"nicht ausgehändigt|kein (auto|fahrzeug|mietwagen)|nicht zur verfügung|downgrade|falsche|andere klasse|no car",
    "support_refund":   r"kundenservice|erstattung|rückerstattung|reklamation|nicht erreichbar|antwort|refund|support",
    "booking_app":      r"\bapp\b|website|webseite|buchung|buchen|online|check-?in|preis|günstig|booking|price",
    "return":           r"rückgabe|zurückgeben|abgabe|return|drop-?off",
}


def load_reviews(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        text = (r.get("text") or "").strip()
        if len(text) < 3:
            continue
        try:
            rating = int(float(r.get("rating") or 0)) or None
        except ValueError:
            rating = None
        item = {"date": (r.get("date") or "").strip(), "source": (r.get("source") or "").strip(),
                "rating": rating, "text": text}
        # optional human-checked labels: columns "categories" (a|b) and "sentiment"
        cats = [c for c in (r.get("categories") or "").split("|") if c in CATEGORIES]
        if cats:
            item["categories"] = cats
            item["sentiment"] = (r.get("sentiment") or "").strip() or None
            item["summary"] = ""
            item["checked"] = True
        out.append(item)
    return out


# ------------------------------------------------------------------ classifiers
def classify_rules(review):
    low = review["text"].lower()
    cats = [c for c, pat in KEYWORDS.items() if re.search(pat, low)]
    rating = review["rating"]
    if rating is not None:
        sentiment = "negative" if rating <= 2 else "positive" if rating >= 4 else "neutral"
    else:
        sentiment = "neutral"
    return {"categories": cats or ["other"], "sentiment": sentiment, "summary": ""}


def classify_claude(review, key):
    prompt = (
        "Classify this car rental customer review. Return ONLY JSON with keys: "
        f"categories (list, 1-3 of {list(CATEGORIES)}), sentiment (positive|neutral|negative), "
        "summary (max 12 words, English).\n\n"
        f"Rating: {review['rating']}\nReview: {review['text'][:3000]}"
    )
    body = json.dumps({"model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"), "max_tokens": 200,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, method="POST", headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        text = json.loads(resp.read())["content"][0]["text"]
    data = json.loads(text[text.find("{"): text.rfind("}") + 1])
    cats = [c for c in data.get("categories", []) if c in CATEGORIES] or ["other"]
    sent = data.get("sentiment") if data.get("sentiment") in ("positive", "neutral", "negative") else "neutral"
    return {"categories": cats, "sentiment": sent, "summary": data.get("summary", "")}


def classify_all(reviews):
    key = os.getenv("ANTHROPIC_API_KEY")
    if reviews and all(r.get("checked") for r in reviews):
        for r in reviews:
            if not r["sentiment"]:
                r["sentiment"] = classify_rules(r)["sentiment"]
        return "von Hand gelesen und eingeordnet / labelled by hand"
    mode = "Claude API" if key else "keyword rules / Stichwortregeln"
    for i, r in enumerate(reviews, 1):
        if key:
            try:
                r.update(classify_claude(r, key))
                continue
            except Exception as exc:  # keep going, mark the review
                print(f"  review {i}: AI failed ({exc}), using rules", file=sys.stderr)
        r.update(classify_rules(r))
    return mode


# ------------------------------------------------------------------ analysis
def analyse(reviews):
    n = len(reviews)
    rated = [r["rating"] for r in reviews if r["rating"]]
    sentiment = Counter(r["sentiment"] for r in reviews)
    neg = [r for r in reviews if r["sentiment"] == "negative"]
    neg_cats = Counter(c for r in neg for c in r["categories"])
    pos_cats = Counter(c for r in reviews if r["sentiment"] == "positive" for c in r["categories"])
    return {
        "n": n,
        "avg_rating": round(sum(rated) / len(rated), 2) if rated else None,
        "rated_n": len(rated),
        "sentiment": sentiment,
        "neg_n": len(neg),
        "neg_cats": neg_cats.most_common(),
        "pos_cats": pos_cats.most_common(3),
        "sources": Counter(r["source"] or "unknown" for r in reviews),
        "dates": sorted(r["date"] for r in reviews if r["date"]),
        "examples": _examples(neg, neg_cats),
    }


def _examples(neg, neg_cats):
    used, out = set(), {}
    for c, _ in neg_cats.most_common(3):
        cand = [r for r in neg if c in r["categories"] and id(r) not in used]
        cand.sort(key=lambda r: r["categories"].index(c))
        picks = cand[:2]
        used.update(id(r) for r in picks)
        if picks:
            out[c] = picks
    return out


T = {
    "de": {"title": "Kundenbewertungen: Analyse", "reviews": "Bewertungen", "avg": "Ø Bewertung",
           "neg": "negativ", "pos": "positiv", "neu": "neutral", "top_problems": "Die häufigsten Probleme",
           "share_neg": "der negativen Bewertungen", "strengths": "Was Kunden loben", "examples": "Beispiele (gekürzt)",
           "method": "Methode", "method_txt": "{n} öffentliche Bewertungen, von Hand gesammelt ({sources}), Zeitraum {span}. "
           "Klassifiziert mit: {mode}. Eine Bewertung kann mehrere Themen haben. Kleine Stichprobe: Tendenzen, keine Statistik.",
           "next": "Meine Ideen dazu", "by": "Erstellt von",
           "deep": "Vertiefung: Worum geht es in den Beschwerden?",
           "small_n": "Nur {n} negative Bewertungen in dieser Stichprobe, zu wenig für Prozente. Themen:",
           "deep_method": " Vertiefung: {n} Bewertungen mit 1–2 Sternen, Zeitraum {span}, ebenfalls von Hand gesammelt.",
           "deep_txt": "Zweite Stichprobe: nur die neuesten 1- und 2-Sterne-Bewertungen. Zeigt, was schiefgeht, wenn etwas schiefgeht. Nicht repräsentativ für alle Kunden.", "fill": "Hier 2–3 eigene Vorschläge eintragen, z. B. zum häufigsten Problem."},
    "en": {"title": "Customer reviews: analysis", "reviews": "reviews", "avg": "Avg. rating",
           "neg": "negative", "pos": "positive", "neu": "neutral", "top_problems": "Most common problems",
           "share_neg": "of negative reviews", "strengths": "What customers praise", "examples": "Examples (shortened)",
           "method": "Method", "method_txt": "{n} public reviews collected by hand ({sources}), period {span}. "
           "Classified with: {mode}. One review can have several topics. Small sample: trends, not statistics.",
           "next": "My ideas", "by": "Prepared by",
           "deep": "Deep dive: what are the complaints about?",
           "small_n": "Only {n} negative reviews in this sample, too few for percentages. Topics:",
           "deep_method": " Deep dive: {n} reviews with 1–2 stars, period {span}, also collected by hand.",
           "deep_txt": "Second sample: only the most recent 1 and 2 star reviews. Shows what goes wrong when something goes wrong. Not representative of all customers.", "fill": "Add 2–3 of your own suggestions here, e.g. for the top problem."},
}


def render(a, company, author, mode, lang, deep=None, ideas=None):
    t = T[lang]
    e = html.escape
    label = lambda c: CATEGORIES[c][lang]
    span = f"{a['dates'][0]} – {a['dates'][-1]}" if a["dates"] else "n/a"
    sources = ", ".join(f"{e(s)}: {c}" for s, c in a["sources"].most_common())
    bars = ""
    if 0 < a["neg_n"] < 10:
        items = ", ".join(f"{e(label(c))} ({cnt})" for c, cnt in a["neg_cats"][:5])
        bars = f'<p>{t["small_n"].format(n=a["neg_n"])} {items}</p>'
    for c, cnt in (a["neg_cats"][:5] if a["neg_n"] >= 10 else []):
        pct = round(100 * cnt / a["neg_n"]) if a["neg_n"] else 0
        bars += (f'<div class="bar"><span class="l">{e(label(c))}</span><span class="track"><span class="fill" '
                 f'style="width:{pct}%"></span></span><span class="v">{cnt} · {pct}%</span></div>')
    examples = ""
    for c, revs in a["examples"].items():
        for r in revs:
            quote = r["text"] if len(r["text"]) <= 160 else r["text"][:157] + "…"
            examples += f'<li><b>{e(label(c))}</b> ({r["rating"] or "?"}★): „{e(quote)}“</li>'
    strengths = ", ".join(f"{e(label(c))} ({n})" for c, n in a["pos_cats"]) or "–"
    s = a["sentiment"]
    deep_html = ""
    if deep:
        dspan = f"{deep['dates'][0]} – {deep['dates'][-1]}" if deep["dates"] else "n/a"
        dbars = ""
        for c, cnt in deep["neg_cats"][:6]:
            pct = round(100 * cnt / deep["n"])
            dbars += (f'<div class="bar"><span class="l">{e(label(c))}</span><span class="track"><span class="fill" '
                      f'style="width:{pct}%"></span></span><span class="v">{cnt} · {pct}%</span></div>')
        dex = ""
        for c, revs in deep["examples"].items():
            r = revs[0]
            quote = r["text"] if len(r["text"]) <= 170 else r["text"][:167] + "…"
            dex += f'<li><b>{e(label(c))}</b>: „{e(quote)}“</li>'
        deep_html = (f'<h2>{t["deep"]} <span class="muted">({deep["n"]} {t["reviews"]}, 1–2★, {e(dspan)})</span></h2>'
                     f'<p class="muted">{t["deep_txt"]}</p>{dbars}<ul>{dex}</ul>')
    deep_method = t["deep_method"].format(n=deep["n"], span=e(dspan)) if deep else ""
    notes = [i for i in (ideas or []) if i.lower().startswith(("einschränkung", "limitation"))]
    items = [i for i in (ideas or []) if i not in notes]
    ideas_html = ("<ol>" + "".join(f"<li>{e(i)}</li>" for i in items) + "</ol>"
                  + "".join(f'<p class="muted">{e(n)}</p>' for n in notes)) if items else f'<div class="todo">{t["fill"]}</div>'
    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8"><title>{e(company)} – {t['title']}</title>
<style>
body{{font-family:Arial,Helvetica,sans-serif;color:#1d1f23;max-width:800px;margin:28px auto;padding:0 24px;font-size:14px;line-height:1.45}}
h1{{font-size:22px;margin:0}} h2{{font-size:15px;margin:22px 0 8px;border-bottom:1px solid #e3e6eb;padding-bottom:4px}}
.sub{{color:#667;margin:2px 0 16px}} .kpis{{display:flex;gap:12px}} .k{{flex:1;background:#f4f6f9;border-radius:8px;padding:10px 12px}}
.k b{{display:block;font-size:22px}} .k span{{color:#667;font-size:12px}}
.bar{{display:flex;align-items:center;gap:10px;margin:6px 0}} .l{{width:200px}} .track{{flex:1;height:12px;background:#eef0f4;border-radius:6px;overflow:hidden}}
.fill{{display:block;height:100%;background:#d9534f}} .v{{width:70px;text-align:right;color:#445;font-size:12px}}
ul{{padding-left:18px}} li{{margin:4px 0}} .muted{{color:#778;font-size:12px}} .todo{{background:#fff8e1;border:1px dashed #e0b400;padding:10px;border-radius:6px}}
@media print{{body{{margin:0}}}}
</style></head><body>
<h1>{e(company)} – {t['title']}</h1>
<p class="sub">{t['by']}: {e(author)} · {date.today().isoformat()}</p>
<div class="kpis">
 <div class="k"><b>{a['n']}</b><span>{t['reviews']}</span></div>
 <div class="k"><b>{a['avg_rating'] if a['avg_rating'] is not None else '–'}</b><span>{t['avg']} ({a['rated_n']})</span></div>
 <div class="k"><b>{s.get('negative',0)}</b><span>{t['neg']}</span></div>
 <div class="k"><b>{s.get('positive',0)}</b><span>{t['pos']}</span></div>
</div>
<h2>{t['top_problems']}{f' <span class="muted">(% {t["share_neg"]})</span>' if a['neg_n'] >= 10 else ''}</h2>
{bars or '<p>–</p>'}
<h2>{t['examples']}</h2><ul>{examples or '<li>–</li>'}</ul>
<h2>{t['strengths']}</h2><p>{strengths}</p>
{deep_html}
<h2>{t['next']}</h2>{ideas_html}
<h2>{t['method']}</h2><p class="muted">{t['method_txt'].format(n=a['n'], sources=sources, span=e(span), mode=mode)}{deep_method}</p>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--company", required=True)
    ap.add_argument("--author", default="Shahid")
    ap.add_argument("--lang", choices=["de", "en"], default="de")
    ap.add_argument("--out", default="output")
    ap.add_argument("--deep-dive", help="second CSV with only negative reviews, shown as an extra section")
    ap.add_argument("--ideas", help="text file, one idea per line, shown under 'Meine Ideen dazu'")
    args = ap.parse_args()

    reviews = load_reviews(args.csv)
    if not reviews:
        sys.exit("No reviews found. Check the CSV columns: date, source, rating, text")
    mode = classify_all(reviews)
    a = analyse(reviews)
    deep = None
    if args.deep_dive:
        deep_reviews = load_reviews(args.deep_dive)
        classify_all(deep_reviews)
        deep = analyse(deep_reviews)
    ideas = None
    if args.ideas:
        ideas = [l.strip() for l in Path(args.ideas).read_text(encoding="utf-8").splitlines() if l.strip()]

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    slug = re.sub(r"\W+", "-", args.company.lower()).strip("-")
    report = out / f"{slug}-report-{args.lang}.html"
    report.write_text(render(a, args.company, args.author, mode, args.lang, deep, ideas), encoding="utf-8")
    with (out / f"{slug}-labelled.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "source", "rating", "sentiment", "categories", "summary", "text"])
        for r in reviews:
            w.writerow([r["date"], r["source"], r["rating"], r["sentiment"], "|".join(r["categories"]), r["summary"], r["text"]])

    print(f"{a['n']} reviews · mode: {mode} · avg rating {a['avg_rating']}")
    for c, cnt in a["neg_cats"][:3]:
        print(f"  top problem: {CATEGORIES[c]['en']} ({cnt})")
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
