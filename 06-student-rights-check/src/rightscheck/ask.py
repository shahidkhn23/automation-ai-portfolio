"""'Ask about your rights': answers a free-text question from the verified knowledge base.

Retrieval is a small BM25 index over every rule (title, summary, keywords in
English and German). No external packages, so it runs anywhere and is easy to
test. The answer only contains verified rules. If nothing matches well enough,
the tool says so and points to free advice instead of guessing.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from .report import DISCLAIMER, load_kb

STOPWORDS = set("""
a an the and or but if is are was were be been am i me my mine you your we our it its this that
to of in on at for with from by as about can could do does did have has had not no what when where
which who why how will would should may might there their they them he she his her so than then
der die das ein eine einen und oder ist sind war ich mich mir mein meine du dein wir unser es
zu von im in am an auf für mit aus bei als kann können darf muss was wann wo wie warum nicht kein
best good get got want need please help know tell
munich münchen germany deutschland german bavaria bayern rosenheim
""".split())

TOKEN = re.compile(r"[a-zäöüß0-9]+", re.I)


def tokenize(text: str) -> list[str]:
    out = []
    for t in TOKEN.findall(text.lower()):
        if t in STOPWORDS or len(t) < 2:
            continue
        # tiny stemmer: rooms -> room, exams -> exam (only for longer English words)
        if len(t) > 4 and re.search(r"(ch|sh|x)es$", t):
            t = t[:-2]
        elif len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        out.append(t)
    return out


class RightsIndex:
    K1, B = 1.4, 0.75

    def __init__(self, kb: dict | None = None):
        self.kb = kb or load_kb()
        self.ids = list(self.kb["rules"])
        self.docs = []
        for rid in self.ids:
            r = self.kb["rules"][rid]
            # keywords count three times: they are written for exactly this lookup
            text = " ".join([r["title"], r["summary"], r["law"]] + r.get("keywords", []) * 3)
            self.docs.append(Counter(tokenize(text)))
        self.avgdl = sum(sum(d.values()) for d in self.docs) / len(self.docs)
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def score(self, query: str) -> list[tuple[str, float]]:
        q = tokenize(query)
        ql = query.lower()
        results = []
        for rid, doc in zip(self.ids, self.docs):
            dl = sum(doc.values())
            s = 0.0
            for t in q:
                if t in doc:
                    f = doc[t]
                    s += self.idf[t] * f * (self.K1 + 1) / (f + self.K1 * (1 - self.B + self.B * dl / self.avgdl))
            # bonus when a multi-word keyword appears as a phrase in the question
            for kw in self.kb["rules"][rid].get("keywords", []):
                if " " in kw and kw in ql:
                    s += 3.0
            results.append((rid, s))
        return sorted(results, key=lambda x: -x[1])

    def search(self, query: str, k: int = 3, min_score: float = 3.0) -> list[str]:
        ranked = self.score(query)
        if not ranked or ranked[0][1] < min_score:
            return []
        top = ranked[0][1]
        return [rid for rid, s in ranked[:k] if s >= 0.7 * top]


def answer(question: str, index: RightsIndex | None = None) -> dict:
    index = index or RightsIndex()
    kb = index.kb
    hits = index.search(question)
    rules = [{"id": rid, **{k: kb["rules"][rid][k] for k in ("area", "law", "title", "summary", "source")},
              "region": kb["rules"][rid].get("region")} for rid in hits]
    areas = list(dict.fromkeys(r["area"] for r in rules)) or ["general"]
    help_list = list(dict.fromkeys(h for a in areas for h in kb["free_help"].get(a, kb["free_help"]["general"])))
    return {
        "question": question,
        "found": bool(rules),
        "rules": rules,
        "free_help": help_list,
        "disclaimer": DISCLAIMER,
        "kb_last_verified": kb["_meta"]["last_verified"],
    }


def answer_markdown(a: dict) -> str:
    lines = [f"# Your question", "", f"> {a['question']}", ""]
    if not a["found"]:
        lines += ["I couldn't find a verified rule for this question, so I won't guess.",
                  "Please ask one of the free services below. They can look at your situation.", ""]
    for r in a["rules"]:
        region = f" – {r['region']}" if r.get("region") else ""
        lines += [f"## {r['title']}", "", f"**{r['law']}{region}**", "", r["summary"], "", f"Source: {r['source']}", ""]
    lines += ["## Where to get free help", ""] + [f"- {h}" for h in a["free_help"]]
    lines += ["", "---", f"_{a['disclaimer']}_  ", f"_Knowledge base last verified: {a['kb_last_verified']}_", ""]
    return "\n".join(lines)
