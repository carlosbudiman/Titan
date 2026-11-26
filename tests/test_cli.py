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
import urllib.error
import urllib.parse
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

            def do_GET(self):  # noqa: N802
                if self.path.rstrip("/").endswith("/models"):
                    body = json.dumps({"object": "list", "data": [
                        {"id": "fake-model"}, {"id": "fake-model-mini"}]}).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_error(404)

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

    def test_console_api(self):
        self.provider.replies = [{"role": "assistant", "content": json.dumps(
            {"goals": ["noop"], "constraints": []})}]
        self.titan("new", "console test", "--scope", "domain=example.com")
        env = self.env()
        env["TITAN_CONSOLE_PORT"] = "19887"
        proc = subprocess.Popen([sys.executable, str(TITAN), "serve"], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        base = "http://127.0.0.1:19887"
        try:
            body = ""
            for _ in range(50):
                try:
                    with urllib.request.urlopen(base + "/api/state?task=1", timeout=2) as r:
                        body = r.read().decode()
                        break
                except OSError:
                    time.sleep(0.1)
            self.assertIn("goals", body)
            state = json.loads(body)
            self.assertEqual(state["task"]["id"], 1)
            self.assertFalse(state["running"])

            with urllib.request.urlopen(base + "/", timeout=2) as r:
                page = r.read().decode()
            self.assertIn("Dewaguard Titan", page)
            self.assertNotIn("ARTEX", page)

            # mutating endpoint: queue a hint, then read it back from the graph
            req = urllib.request.Request(
                base + "/api/hint", method="POST",
                data=json.dumps({"task": 1, "text": "check the upload endpoint"}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                self.assertEqual(r.status, 200)

            with urllib.request.urlopen(base + "/api/state?task=1", timeout=2) as r:
                state = json.loads(r.read().decode())
            hints = [h["text"] for h in state["overview"]["hints"]]
            self.assertIn("check the upload endpoint", hints)

            # report download
            with urllib.request.urlopen(base + "/api/export?task=1", timeout=2) as r:
                md = r.read().decode()
            self.assertIn("Engagement report", md)

            # unknown task must not 500
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(base + "/api/state?task=999", timeout=2)
            self.assertEqual(ctx.exception.code, 404)
        finally:
            proc.terminate()
            proc.wait(timeout=10)


    def test_setup_persists_without_storing_the_key_in_the_db(self):
        self.provider.replies = [{"role": "assistant", "content": "ok"}]
        key = "sk-test-0123456789abcdef"
        env = self.env()
        env.pop("TITAN_LLM_API_KEY", None)          # so the file is the only source
        p = subprocess.run([sys.executable, str(TITAN), "setup",
                            "--url", self.provider.url, "--model", "fake-model",
                            "--api-key-stdin", "--no-test"],
                           input=key + "\n", capture_output=True, text=True, env=env,
                           timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("fake-model", p.stdout)
        self.assertNotIn(key, p.stdout)             # never echoed

        home = self.tmp / "home"
        secrets = home / "secrets.json"
        self.assertTrue(secrets.exists())
        self.assertEqual(secrets.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(secrets.read_text())["llm_api_key"], key)

        db = sqlite3.connect(home / "titan.db")
        rows = db.execute("SELECT key,value FROM settings").fetchall()
        db.close()
        self.assertIn(("llm.model", "fake-model"), rows)
        self.assertNotIn(key, json.dumps(rows))     # the key is not in the database

        out = subprocess.run([sys.executable, str(TITAN), "setup", "--show"], env=env,
                             capture_output=True, text=True, timeout=30).stdout
        self.assertIn("sk-t", out)
        self.assertNotIn(key, out)
        self.assertIn("0600", out)

    def test_console_settings_agents_graph_skills(self):
        self.provider.replies = [{"role": "assistant", "content": json.dumps(
            {"goals": ["noop"], "constraints": []})}]
        self.titan("new", "console surfaces", "--scope", "domain=example.com")
        env = self.env()
        env["TITAN_CONSOLE_PORT"] = "19888"
        proc = subprocess.Popen([sys.executable, str(TITAN), "serve"], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        base = "http://127.0.0.1:19888"

        def get(path):
            with urllib.request.urlopen(base + path, timeout=5) as r:
                return json.loads(r.read().decode())

        def post(path, payload):
            req = urllib.request.Request(base + path, method="POST",
                                         data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())

        try:
            for _ in range(50):
                try:
                    st = get("/api/settings")
                    break
                except OSError:
                    time.sleep(0.1)

            self.assertEqual(st["llm"]["model"], "fake-model")
            self.assertNotIn("sk-test", json.dumps(st))       # only masked
            self.assertIn("key_masked", st["llm"])

            st2 = post("/api/settings", {"llm": {"base_url": self.provider.url,
                                                 "model": "fake-model-mini"},
                                         "run": {"rps": "3", "noise_profile": "quiet"}})
            self.assertEqual(st2["llm"]["model"], "fake-model-mini")
            self.assertEqual(st2["run"]["rps"], "3")

            models = get("/api/models?url=" + urllib.parse.quote(self.provider.url, safe=""))
            self.assertIn("fake-model", models["models"])

            test = post("/api/settings/test", {"base_url": self.provider.url,
                                               "model": "fake-model-mini"})
            self.assertTrue(test["ok"])

            agents = get("/api/agents?task=1")
            self.assertIn("live", agents)
            self.assertIn("usage", agents)

            graph = get("/api/graph?task=1")
            self.assertTrue(any(n["kind"] == "goal" for n in graph["nodes"]))
            node = get("/api/node?id=" + str(graph["nodes"][0]["id"]))
            self.assertIn("kind", node)

            skills = get("/api/skills")["skills"]
            self.assertIn("php2shell", [s["name"] for s in skills])
            body = get("/api/skill?name=php2shell")["body"]
            self.assertIn("session.upload_progress", body)

            page = urllib.request.urlopen(base + "/", timeout=5).read().decode()
            for view in ("Dewaguard Titan", "settings", "agents", "skills", "traffic"):
                self.assertIn(view, page)
            self.assertIn("data-theme", page)          # light / dark switch
            self.assertIn("prefers-color-scheme", page)

            with self.assertRaises(urllib.error.HTTPError) as ctx:
                post("/api/finding", {"id": 999, "status": "nope"})
            self.assertEqual(ctx.exception.code, 400)
        finally:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
