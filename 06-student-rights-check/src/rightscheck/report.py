"""Turns findings into a plain-English report, using only the verified knowledge base."""

from __future__ import annotations

import json
from pathlib import Path

from .rules import Analysis, RED, CHECK, INFO

KB_PATH = Path(__file__).resolve().parents[2] / "knowledge_base" / "laws.json"

LABEL = {RED: "RED FLAG", CHECK: "GET IT CHECKED", INFO: "GOOD TO KNOW"}

DISCLAIMER = (
    "This is general legal information, not legal advice for your individual case. "
    "Rules have exceptions. Before you act, get the document checked by one of the free services below."
)

HEURISTIC_TITLES = {
    "scam_pattern": "Typical scam pattern",
    "sign_declaration": "You are asked to sign a binding declaration",
    "deadline": "Deadline in this document",
}


def load_kb(path: Path = KB_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def to_dict(a: Analysis, kb: dict) -> dict:
    items = []
    for f in a.findings:
        rule = kb["rules"].get(f.rule_id)
        items.append({
            "rule_id": f.rule_id,
            "severity": f.severity,
            "title": rule["title"] if rule else HEURISTIC_TITLES.get(f.rule_id, f.rule_id),
            "clause": f.evidence,
            "what_we_found": f.detail,
            "what_the_law_says": rule["summary"] if rule else None,
            "law": rule["law"] if rule else None,
            "source": rule["source"] if rule else None,
            "is_law": rule is not None and not f.heuristic,
        })
    area_of = {"rental": "housing", "work": "work", "consumer": "consumer", "copyright": "copyright"}
    help_keys = [area_of[t] for t in a.doc_types if t in area_of] or ["general"]
    help_list = []
    for k in help_keys:
        for h in kb["free_help"][k]:
            if h not in help_list:
                help_list.append(h)
    return {
        "document_type": a.doc_types,
        "summary": {s: sum(1 for f in a.findings if f.severity == s) for s in (RED, CHECK, INFO)},
        "findings": items,
        "free_help": help_list,
        "disclaimer": DISCLAIMER,
        "kb_last_verified": kb["_meta"]["last_verified"],
    }


def to_markdown(report: dict) -> str:
    s = report["summary"]
    lines = [
        "# Student Rights Check",
        "",
        f"**Document type:** {', '.join(report['document_type'])}  ",
        f"**Result:** {s[RED]} red flag(s), {s[CHECK]} to get checked, {s[INFO]} good to know",
        "",
    ]
    if not report["findings"]:
        lines += ["No known red flags found. That does not mean the document is fine, "
                  "only that none of the rules in this tool matched.", ""]
    for i, f in enumerate(report["findings"], 1):
        lines += [f"## {i}. [{LABEL[f['severity']]}] {f['title']}", "",
                  f"> {f['clause']}", "",
                  f"**What we found:** {f['what_we_found']}", ""]
        if f["what_the_law_says"]:
            lines += [f"**What the law generally says ({f['law']}):** {f['what_the_law_says']}", "",
                      f"Source: {f['source']}", ""]
        elif not f["is_law"]:
            lines += ["_This is a warning pattern, not a legal rule._", ""]
    lines += ["## Where to get free help", ""] + [f"- {h}" for h in report["free_help"]]
    lines += ["", "---", f"_{report['disclaimer']}_  ",
              f"_Knowledge base last verified: {report['kb_last_verified']}_", ""]
    return "\n".join(lines)
