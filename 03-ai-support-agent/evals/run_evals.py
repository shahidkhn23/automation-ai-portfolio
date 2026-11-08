"""Runs the test conversations and scores the agent.

python evals/run_evals.py           (uses real model if ANTHROPIC_API_KEY is set, else mock)
AGENT_MODE=mock python evals/run_evals.py

Checks per case: right tool used, required facts present, forbidden facts absent
(e.g. no booking data leaked with a wrong last name).
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent import Agent  # noqa: E402

cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
rows, passed = [], 0
for case in cases:
    agent = Agent()
    t0 = time.time()
    answer, trace = agent.ask(case["input"])
    used = [t["tool"] for t in trace]
    low = answer.lower()
    checks = {
        "tool": all(t in used for t in case.get("expect_tools", [])),
        "includes": all(s.lower() in low for s in case.get("must_include", [])),
        "excludes": not any(s.lower() in low for s in case.get("must_not_include", [])),
    }
    ok = all(checks.values())
    passed += ok
    rows.append({"id": case["id"], "pass": ok, **checks, "tools_used": used,
                 "latency_s": round(time.time() - t0, 2), "answer": answer})
    print(f"{'PASS' if ok else 'FAIL'}  {case['id']:<26} tools={used}")

backend = type(Agent().llm).__name__
print(f"\n{passed}/{len(cases)} passed ({passed / len(cases):.0%}) with {backend}")
out = ROOT / "evals" / f"results_{backend}.json"
out.write_text(json.dumps({"backend": backend, "passed": passed, "total": len(cases), "cases": rows},
                          indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Details: {out.relative_to(ROOT)}")
sys.exit(0 if passed == len(cases) else 1)
