"""CLI + provider integration: real HTTP to an OpenAI-compatible endpoint.

A fake provider serves scripted tool calls; a real local HTTP server is the target.
This proves the parts the MockLLM tests cannot: urllib transport, tool_call parsing,
CLI wiring, SQLite persistence across processes, markdown export and the console.

    python3 tests/test_cli.py
"""
from __future__ import annotations

import functools
import http.server
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TITAN = ROOT / "bin" / "titan"


def _tc(i, name, args):
    return {"id": f"c{i}", "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}


class FakeProvider:
    """Serves /v1/chat/completions from a script, in order."""

    def __init__(self):
        self.replies: list[dict] = []
        self.seen = 0
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):  # noqa: N802
                n = int(self.headers.get("Content-Length") or 0)
                self.rfile.read(n)
                msg = outer.replies.pop(0) if outer.replies else {
                    "role": "assistant", "content": "done"}
                outer.seen += 1
                body = json.dumps({"id": f"x{outer.seen}", "object": "chat.completion",
                                   "choices": [{"index": 0, "message": msg,
                                                "finish_reason": "stop"}],
                                   "usage": {"prompt_tokens": 10, "completion_tokens": 5}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}/v1"

    def stop(self):
        self.srv.shutdown()


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        www = self.tmp / "www"
        www.mkdir()
        (www / "index.html").write_text("<h1>cli demo</h1>")
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(www))
        h.log_message = lambda *a, **k: None
        self.target = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        threading.Thread(target=self.target.serve_forever, daemon=True).start()
        self.target_url = f"http://127.0.0.1:{self.target.server_address[1]}/"
        self.provider = FakeProvider()

    def tearDown(self):
        self.provider.stop()
        self.target.shutdown()

    def env(self):
        e = dict(os.environ)
        e.update({"TITAN_HOME": str(self.tmp / "home"), "TITAN_LLM_BASE_URL": self.provider.url,
                  "TITAN_LLM_MODEL": "fake-model", "TITAN_LLM_API_KEY": "test",
                  "TITAN_RPS": "100", "TITAN_NOISE_PROFILE": "off", "NO_COLOR": "1"})
        return e

    def titan(self, *args, timeout=60):
        p = subprocess.run([sys.executable, str(TITAN), *args], capture_output=True,
                           text=True, env=self.env(), timeout=timeout)
        self.assertEqual(p.returncode, 0, f"{args}\nstdout:{p.stdout}\nstderr:{p.stderr}")
        return p.stdout + p.stderr

    def test_cli_end_to_end(self):
        t = self.target_url
        self.provider.replies = [
            {"role": "assistant", "content": json.dumps(
                {"goals": ["Prove the demo service is reachable"], "constraints": []})},
            {"role": "assistant", "content": "", "tool_calls": [_tc(1, "add_intent", {"intents": [
                {"summary": f"Enumerate {t} and record what it exposes"}]})]},
            {"role": "assistant", "content": "one intent dispatched"},
            {"role": "assistant", "content": "", "tool_calls": [_tc(2, "webfetch", {"url": t})]},
            {"role": "assistant", "content": "", "tool_calls": [_tc(3, "insert_assets", {"items": [
                {"type": "service", "url": t, "service_type": "http", "status_code": 200,
                 "page_title": "cli demo"}]})]},
            {"role": "assistant", "content": "", "tool_calls": [_tc(4, "record_fact", {
                "summary": "Demo service returns 200", "source": "target_response",
                "confidence": "observed", "evidence": "webfetch -> 200"})]},
            {"role": "assistant", "content": "", "tool_calls": [_tc(5, "report_finding", {
                "vulnclass": "information-disclosure", "severity": "low",
                "summary": "Directory index exposed", "evidence": "GET / -> 200 listing",
                "poc": f"curl -s {t}", "endpoint": t, "traffic_refs": [1]})]},
            {"role": "assistant", "content": "intent done"},
            {"role": "assistant", "content": "", "tool_calls": [_tc(6, "prove_goal", {
                "goal_id": 2, "evidence_id": 5, "reason": "finding with bound traffic"})]},
            {"role": "assistant", "content": "goal met"},
        ]

        out = self.titan("init")
        self.assertIn("11 loaded", out)

        out = self.titan("new", f"Assess {t}", "--title", "cli", "--scope", f"url={t}")
        self.assertIn("task #1 created", out)

        out = self.titan("run", "1", "--rounds", "3", "--workers", "1")
        self.assertIn("status=achieved", out)
        self.assertIn("findings=1", out)

        out = self.titan("findings", "1")
        self.assertIn("information-disclosure", out)
        self.assertIn("LOW", out)

        # persistence across processes
        db = sqlite3.connect(self.tmp / "home" / "titan.db")
        self.assertEqual(db.execute("SELECT COUNT(*) FROM findings").fetchone()[0], 1)
        self.assertEqual(db.execute("SELECT COUNT(*) FROM traffic").fetchone()[0], 1)
        self.assertEqual(db.execute("SELECT status FROM explorations").fetchone()[0], "achieved")
        db.close()

        report = self.tmp / "report.md"
        out = self.titan("export", "1", "--out", str(report))
        self.assertTrue(report.exists())
        text = report.read_text()
        self.assertIn("information-disclosure", text)
        self.assertIn("Directory index exposed", text)

    def test_console_is_read_only_and_local(self):
        self.provider.replies = [{"role": "assistant", "content": json.dumps(
            {"goals": ["noop"], "constraints": []})}]
        self.titan("new", "console test")
        env = self.env()
        env["TITAN_CONSOLE_PORT"] = "19887"
        proc = subprocess.Popen([sys.executable, str(TITAN), "serve"], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            body = ""
            for _ in range(40):
                try:
                    with urllib.request.urlopen("http://127.0.0.1:19887/api/overview?task=1",
                                                timeout=2) as r:
                        body = r.read().decode()
                        break
                except OSError:
                    time.sleep(0.1)
            self.assertIn("goals", body)
            with urllib.request.urlopen("http://127.0.0.1:19887/", timeout=2) as r:
                page = r.read().decode()
            self.assertIn("DEWAGUARD TITAN", page)
            self.assertNotIn("ARTEX", page)
        finally:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
