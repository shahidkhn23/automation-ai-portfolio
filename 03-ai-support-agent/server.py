"""Tiny web chat for demos. Shows each tool call next to the answer.

python server.py  ->  open http://localhost:8000
"""
import json
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from agent import Agent

PAGE = (Path(__file__).parent / "web" / "index.html").read_bytes()
SESSIONS = {}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PAGE)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404)
            return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        sid = body.get("session") or uuid.uuid4().hex
        agent = SESSIONS.setdefault(sid, Agent())
        try:
            answer, trace = agent.ask(body["message"][:2000])
            payload = {"session": sid, "answer": answer, "trace": trace}
        except Exception as exc:  # show errors in the UI instead of crashing
            payload = {"session": sid, "answer": f"Error: {exc}", "trace": []}
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("Open http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
