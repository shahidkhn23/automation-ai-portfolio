"""Rentora support agent: a tool-using LLM loop with guardrails and a trace log.

Run:  python agent.py            (interactive CLI)
      python server.py           (web chat with live tool trace)
"""
import json
import sys
import time
from datetime import date
from pathlib import Path

from llm import get_llm
from tools import TOOLS, run_tool

LOG_DIR = Path(__file__).parent / "logs"

SYSTEM_PROMPT = f"""You are the customer support agent of Rentora, a car rental company in Germany.
Today is {date.today().isoformat()}.

Rules:
- Answer in the customer's language (German or English).
- Only state fees, rules or prices that come from a tool result. Never invent them.
- For any rules or fee question, call search_policies first.
- Never share booking details unless get_booking succeeded with BOTH booking ID and last name.
  If one is missing, ask for it.
- Accidents, damage disputes, complaints, refund requests, or a request for a human:
  call create_handoff (priority high for accidents) and tell the customer the ticket ID.
- Convert relative dates ("next Friday") to YYYY-MM-DD before calling tools.
- Keep answers short: 2-5 sentences or a short list."""


class Agent:
    def __init__(self, llm=None, max_steps=6):
        self.llm = llm or get_llm()
        self.max_steps = max_steps
        self.messages = []
        self.trace = []

    def ask(self, user_text):
        self.messages.append({"role": "user", "content": user_text})
        turn_trace = []
        started = time.time()
        for _ in range(self.max_steps):
            resp = self.llm.complete(SYSTEM_PROMPT, self.messages, TOOLS)
            self.messages.append({"role": "assistant", "content": resp["content"]})
            if not resp["tool_calls"]:
                self._log(user_text, resp["text"], turn_trace, time.time() - started)
                self.trace.extend(turn_trace)
                return resp["text"], turn_trace
            results = []
            for call in resp["tool_calls"]:
                output = run_tool(call["name"], call["input"])
                turn_trace.append({"tool": call["name"], "input": call["input"], "output": output})
                results.append({"type": "tool_result", "tool_use_id": call["id"],
                                "content": json.dumps(output, ensure_ascii=False)})
            self.messages.append({"role": "user", "content": results})
        fallback = "Sorry, I couldn't finish that. I've noted it for a colleague."
        run_tool("create_handoff", {"summary": f"Agent hit step limit on: {user_text}"})
        return fallback, turn_trace

    def _log(self, question, answer, trace, seconds):
        LOG_DIR.mkdir(exist_ok=True)
        entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "llm": type(self.llm).__name__,
                 "question": question, "tools": [t["tool"] for t in trace],
                 "answer": answer, "latency_s": round(seconds, 2)}
        with (LOG_DIR / "conversations.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    agent = Agent()
    print(f"Rentora support agent ({type(agent.llm).__name__}). Type 'quit' to exit.\n")
    while True:
        try:
            q = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"quit", "exit"}:
            break
        if not q:
            continue
        answer, trace = agent.ask(q)
        for t in trace:
            print(f"  [tool] {t['tool']}({json.dumps(t['input'], ensure_ascii=False)})")
        print(f"Agent: {answer}\n")


if __name__ == "__main__":
    sys.exit(main())
