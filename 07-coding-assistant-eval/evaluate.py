"""Scores code written by AI coding assistants on the same tasks with hidden tests.

    python evaluate.py --self-test                 check the harness with reference and broken solutions
    python evaluate.py submissions/copilot         score one assistant
    python evaluate.py submissions/*               score several and print a comparison table

A submission folder holds one file per task: <task_id>.py (e.g. 01_iban_validation.py).
Optionally it holds notes.csv with the manual criteria from RUBRIC.md.
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS = sorted(p for p in (ROOT / "tasks").iterdir() if p.is_dir())
TIMEOUT_S = 20

# Patterns that need a human look in enterprise code. A hit is a flag, not proof of a bug.
SECURITY_PATTERNS = {
    "eval/exec": r"\b(eval|exec)\s*\(",
    "shell=True": r"shell\s*=\s*True",
    "SQL built from strings": r"(?i)(f\"[^\"\n]*\b(select|insert|update|delete|where|and)\b[^\"\n]*\{"
                              r"|f'[^'\n]*\b(select|insert|update|delete|where|and)\b[^'\n]*\{"
                              r"|\"[^\"\n]*\b(select|insert|update|delete|where)\b[^\"\n]*\"\s*(%|\+|\.format))",
    "pickle/marshal load": r"\b(pickle|marshal)\.loads?\s*\(",
    "hard-coded secret": r"(api_key|password|secret|token)\s*=\s*[\"'][^\"']{8,}[\"']",
    "bare except": r"except\s*:",
}

RUNNER = r"""
import io, json, unittest
result = unittest.TextTestRunner(stream=io.StringIO()).run(
    unittest.defaultTestLoader.discover(".", pattern="test_task.py"))
print(json.dumps({"run": result.testsRun, "failed": len(result.failures), "errors": len(result.errors)}))
"""


def run_tests(task_dir, solution_file):
    """Runs the hidden tests of one task against one solution file in an isolated temp folder."""
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(task_dir / "test_task.py", tmp)
        shutil.copy(solution_file, Path(tmp) / "solution.py")
        try:
            out = subprocess.run([sys.executable, "-I", "-c", RUNNER], cwd=tmp, capture_output=True,
                                 text=True, timeout=TIMEOUT_S)
            stats = json.loads(out.stdout.strip().splitlines()[-1])
        except subprocess.TimeoutExpired:
            return {"run": 0, "passed": 0, "error": "timeout"}
        except (json.JSONDecodeError, IndexError):
            return {"run": 0, "passed": 0, "error": (out.stderr.strip().splitlines() or ["no output"])[-1]}
    stats["passed"] = stats["run"] - stats["failed"] - stats["errors"]
    return stats


def security_flags(code):
    return [name for name, pattern in SECURITY_PATTERNS.items() if re.search(pattern, code)]


def score_submission(folder):
    folder = Path(folder)
    tasks = []
    for task in TASKS:
        file = folder / f"{task.name}.py"
        if not file.exists():
            tasks.append({"task": task.name, "missing": True, "passed": 0, "run": 0, "flags": []})
            continue
        stats = run_tests(task, file)
        tasks.append({"task": task.name, **stats, "flags": security_flags(file.read_text(encoding="utf-8"))})
    total_run = sum(t["run"] for t in tasks) or 1
    summary = {
        "assistant": folder.name,
        "tasks_solved": sum(1 for t in tasks if t["run"] and t["passed"] == t["run"]),
        "tests_passed_pct": round(100 * sum(t["passed"] for t in tasks) / total_run, 1),
        "security_flags": sum(len(t["flags"]) for t in tasks),
        "tasks": tasks,
    }
    notes = folder / "notes.csv"
    if notes.exists():
        summary["manual"] = list(csv.DictReader(notes.open(encoding="utf-8")))
    return summary


def print_table(results):
    print(f"\n{'Assistant':<20}{'Tasks solved':>14}{'Tests passed':>14}{'Security flags':>16}")
    for r in results:
        print(f"{r['assistant']:<20}{r['tasks_solved']:>9}/{len(TASKS):<4}{r['tests_passed_pct']:>13}%"
              f"{r['security_flags']:>16}")
    for r in results:
        print(f"\n{r['assistant']}:")
        for t in r["tasks"]:
            status = "missing" if t.get("missing") else t.get("error") or f"{t['passed']}/{t['run']} tests"
            flags = f"  flags: {', '.join(t['flags'])}" if t["flags"] else ""
            print(f"  {t['task']:<24}{status}{flags}")


def self_test():
    """Reference solutions must pass every test; deliberately broken ones must fail at least one."""
    ok = True
    for task in TASKS:
        good = run_tests(task, task / "reference" / "solution.py")
        bad = run_tests(task, task / "reference" / "broken.py")
        good_ok = good["run"] > 0 and good["passed"] == good["run"]
        bad_caught = bad["passed"] < bad["run"] or bad["run"] == 0
        ok &= good_ok and bad_caught
        print(f"{'OK  ' if good_ok and bad_caught else 'FAIL'} {task.name:<24}"
              f"reference {good['passed']}/{good['run']}   broken {bad['passed']}/{bad['run']} (must fail)")
    flagged = security_flags((ROOT / "tasks/03_safe_order_query/reference/broken.py").read_text())
    clean = security_flags((ROOT / "tasks/03_safe_order_query/reference/solution.py").read_text())
    scan_ok = "SQL built from strings" in flagged and not clean
    ok &= scan_ok
    print(f"{'OK  ' if scan_ok else 'FAIL'} security scan flags string-built SQL and passes the safe version")
    print("\nHarness self-test passed." if ok else "\nHarness self-test FAILED.")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("submissions", nargs="*", help="one folder per assistant")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", help="also write the full results to this file")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(0 if self_test() else 1)
    if not args.submissions:
        ap.error("give at least one submission folder, or --self-test")
    results = [score_submission(s) for s in args.submissions]
    print_table(results)
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
