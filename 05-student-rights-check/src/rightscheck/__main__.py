"""Command line.

  python -m rightscheck check samples/wg_mietvertrag.txt [--json] [--ai] [--lang Deutsch]
  python -m rightscheck ask "My landlord entered my room without asking" [--json] [--ai]
  python -m rightscheck topics
  python -m rightscheck agent "Is this okay? Write my landlord a message." --file lease.txt [--trace]
"""

import argparse
import json
import os
import sys

from . import check, to_markdown
from .ask import RightsIndex, answer, answer_markdown
from .extract import read_document
from .llm import explain, explain_answer
from .report import load_kb


def cmd_check(args) -> int:
    try:
        text = read_document(args.file)
    except (OSError, ValueError) as e:
        print(f"Could not read the document: {e}", file=sys.stderr)
        return 1
    report = check(text)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else to_markdown(report))
    if args.ai:
        print("\n## AI explanation\n")
        print(explain(text, report, args.lang) or "Set ANTHROPIC_API_KEY to get a plain-language explanation.")
    return 0


def cmd_ask(args) -> int:
    a = answer(args.question, RightsIndex())
    print(json.dumps(a, ensure_ascii=False, indent=2) if args.json else answer_markdown(a))
    if args.ai and a["found"]:
        print("\n## AI explanation\n")
        print(explain_answer(a, args.lang) or "Set ANTHROPIC_API_KEY to get a plain-language explanation.")
    return 0


def cmd_topics(args) -> int:
    kb = load_kb()
    print("# Student rights covered\n")
    for area, label in kb["areas"].items():
        print(f"## {label}")
        for r in kb["rules"].values():
            if r["area"] == area:
                print(f"- {r['title']}  ({r['law']})")
        print()
    print(f"_{len(kb['rules'])} verified rules, last checked {kb['_meta']['last_verified']}_")
    return 0


def cmd_agent(args) -> int:
    from .agent import anthropic_model, groq_model, run_agent
    if os.getenv("GROQ_API_KEY"):
        model = groq_model
    elif os.getenv("ANTHROPIC_API_KEY"):
        model = anthropic_model
    else:
        print("The agent needs GROQ_API_KEY (free) or ANTHROPIC_API_KEY. Without a key, use 'check' and 'ask'.",
              file=sys.stderr)
        return 1
    document = read_document(args.file) if args.file else None
    out = run_agent(args.message, document, model=model)
    if args.trace:
        for step in out["trace"]:
            print(f"[tool] {step['tool']} {json.dumps(step['input'], ensure_ascii=False)}")
        print(f"[grounded] {out['grounded']}\n")
    print(out["answer"])
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in {"check", "ask", "topics", "agent", "-h", "--help"}:
        argv.insert(0, "check")       # old style: python -m rightscheck file.txt

    p = argparse.ArgumentParser(prog="rightscheck", description="Know your rights as a student in Germany.")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="check a contract or letter (PDF or text)")
    c.add_argument("file")
    a = sub.add_parser("ask", help="ask a question about your rights")
    a.add_argument("question")
    for sp in (c, a):
        sp.add_argument("--json", action="store_true", help="structured output")
        sp.add_argument("--ai", action="store_true", help="plain-language AI explanation (needs ANTHROPIC_API_KEY)")
        sp.add_argument("--lang", default="English", help="language for the AI explanation")
    sub.add_parser("topics", help="list every right the tool knows")
    g = sub.add_parser("agent", help="AI agent that decides which tools to use (needs GROQ_API_KEY or ANTHROPIC_API_KEY)")
    g.add_argument("message")
    g.add_argument("--file", help="contract or letter to check")
    g.add_argument("--trace", action="store_true", help="show which tools the agent called")

    args = p.parse_args(argv)
    return {"check": cmd_check, "ask": cmd_ask, "topics": cmd_topics, "agent": cmd_agent}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
