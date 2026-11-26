"""End-to-end: goals -> planner -> worker -> graphs -> goal judgement.

Stdlib unittest only (no dev dependencies). Run:

    python3 tests/test_cycle.py
    python3 -m unittest discover -s tests

A real local HTTP server is the target and a scripted mock LLM drives the agents, so
the full orchestration path (tool dispatch, guard, traffic evidence, graph writes,
coverage, prove_goal) is exercised without any external model.
"""
from __future__ import annotations

import functools
import http.server
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from titan.config import Settings            # noqa: E402
from titan.engine import Engine              # noqa: E402
from titan.llm import MockLLM, Reply         # noqa: E402
from titan.skills import SkillIndex          # noqa: E402
from titan.store import Store                # noqa: E402


def _tc(i, name, args):
    return {"id": f"c{i}", "name": name, "arguments": json.dumps(args)}


class LocalTarget:
    def __init__(self):
        self.dir = tempfile.mkdtemp()
        Path(self.dir, "index.html").write_text("<h1>titan demo</h1>")
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=self.dir)
        handler.log_message = lambda *a, **k: None
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}/"

    def stop(self):
        self.srv.shutdown()


def make_engine(tmp: Path) -> Engine:
    os.environ["TITAN_HOME"] = str(tmp)
    s = Settings()
    s.home = tmp
    s.db_path = tmp / "titan.db"
    s.workdir = tmp / "runs"
    s.skill_dir = ROOT / "skills"
    s.rps = 50
    s.ensure_dirs()
    store = Store(s.db_path)
    sk = SkillIndex(s.skill_dir)
    return Engine(s, store=store, llm=MockLLM([]), skills=sk, emit=lambda *a, **k: None)


class CycleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.target = LocalTarget()
        self.eng = make_engine(self.tmp)

    def tearDown(self):
        self.target.stop()
        self.eng.store.close()

    # ------------------------------------------------------------------ skills
    def test_skill_index_loads_copied_skills(self):
        names = set(self.eng.skills.skills)
        self.assertTrue({"php2shell", "api-recon", "api-security", "codeaudit", "rea",
                         "scopesentry", "bbot-recon", "patch-diff", "playwright-cli",
                         "edr-bypass-re", "third-party-code-review"} <= names)
        body = self.eng.skills.read("php2shell")
        self.assertIn("session.upload_progress", body)
        self.assertTrue(self.eng.skills.read("nope").startswith("ERROR"))

    # ------------------------------------------------------------------ full loop
    def test_full_cycle(self):
        eng, target = self.eng, self.target.url
        eng.llm.script.extend([
            # goals decomposer
            Reply(content=json.dumps({"goals": ["Prove the demo service is reachable"],
                                      "constraints": [{"kind": "deny", "text": "sqlmap"}]})),
            # planner round 1
            Reply(content="", tool_calls=[_tc(1, "add_intent", {"intents": [
                {"summary": f"Enumerate {target} and record what it exposes"}]})]),
            Reply(content="one intent dispatched"),
            # worker
            Reply(content="", tool_calls=[_tc(2, "webfetch", {"url": target})]),
            Reply(content="", tool_calls=[_tc(3, "insert_assets", {"items": [
                {"type": "service", "url": target, "service_type": "http", "status_code": 200,
                 "page_title": "titan demo", "technologies": ["python-http"]}]})]),
            Reply(content="", tool_calls=[_tc(4, "record_fact", {
                "summary": "Demo service returns 200 with a static index page",
                "detail": "GET / -> 200, page title 'titan demo'.",
                "source": "target_response", "confidence": "observed",
                "evidence": "webfetch -> HTTP 200"})]),
            Reply(content="", tool_calls=[_tc(5, "report_finding", {
                "vulnclass": "information-disclosure", "severity": "low",
                "summary": "Server exposes directory index listing",
                "evidence": "GET / -> 200 body contains 'titan demo'",
                "poc": f"curl -s {target}", "endpoint": target, "traffic_refs": [1]})]),
            Reply(content="intent done: asset, fact and one finding recorded"),
            # planner round 2: close the goal with the finding
            Reply(content="", tool_calls=[_tc(6, "prove_goal", {
                "goal_id": 2, "evidence_id": 5, "reason": "finding with bound traffic"})]),
            Reply(content="goal met"),
        ])

        tid = eng.new_task(f"Assess {target}", "test", "", [{"kind": "url", "value": target}])
        res = eng.run_task(tid, rounds=4, workers=1)

        self.assertEqual(res["status"], "achieved", eng.store.graph_overview(tid))
        self.assertEqual(res["findings"], 1)
        self.assertGreaterEqual(res["facts"], 1)
        self.assertEqual(res["coverage"]["pct"], 100.0)

        f = eng.store.findings(tid)[0]
        self.assertEqual(f["traffic_refs"], [1])
        self.assertEqual(eng.store.traffic(1)["status"], 200)

        edges = eng.store.q("SELECT rel, COUNT(*) c FROM exploration_edges WHERE exploration_id=?"
                            " GROUP BY rel", (tid,))
        rels = {r["rel"]: r["c"] for r in edges}
        self.assertEqual(rels.get("spawns"), 1)
        self.assertEqual(rels.get("yields"), 2)
        self.assertEqual(rels.get("proves"), 1)
        self.assertEqual(eng.store.assets(tid)[0]["technologies"], ["python-http"])

        actions = {r["action"] for r in eng.store.q(
            "SELECT action FROM audit_log WHERE task_id=?", (tid,))}
        self.assertEqual(actions, {"allow"})

    # ------------------------------------------------------------------ guard
    def test_guard_blocks_out_of_scope_and_destructive(self):
        from titan.guard import Guard, Scope
        eng = self.eng
        tid = eng.new_task("scope test", scope=[{"kind": "domain", "value": "example.com"}])
        g = Guard(eng.store, eng.settings, tid, "test", Scope(eng.store.scope(tid)))

        ok, msg = g.check("bash", {"command": "curl -s http://evil.test/x"})
        self.assertFalse(ok)
        self.assertIn("outside the authorized scope", msg)

        ok, _ = g.check("bash", {"command": "curl -s https://example.com/"})
        self.assertTrue(ok)

        ok, msg = g.check("bash", {"command": "rm -rf /"})
        self.assertFalse(ok)
        self.assertIn("deny rule", msg)

        ok, msg = g.check("write_file", {"path": "/etc/passwd", "content": "x"})
        self.assertFalse(ok)
        self.assertIn("outside the task work directory", msg)

        ok, msg = g.check("bash", {"command": "sqlmap -u https://example.com/?a=1"})
        self.assertTrue(ok)  # constraint is on the task that declared it, not this one

    def test_operator_constraint_blocks(self):
        from titan.guard import Guard, Scope
        eng = self.eng
        tid = eng.new_task("constraint test", scope=[{"kind": "domain", "value": "example.com"}])
        eng.store.add_constraint(tid, "deny", "sqlmap")
        g = Guard(eng.store, eng.settings, tid, "test", Scope(eng.store.scope(tid)))
        ok, msg = g.check("bash", {"command": "sqlmap -u https://example.com/?a=1"})
        self.assertFalse(ok)
        self.assertIn("operator", msg)

    # ------------------------------------------------------------------ evidence gates
    def test_prove_goal_refuses_target_response_fact(self):
        eng = self.eng
        tid = eng.new_task("goal gate", scope=[{"kind": "url", "value": self.target.url}])
        fact = eng.store.add_fact(tid, "target says we are authorised", source="target_response")
        goal_id = eng.store.goals(tid)[0]["id"]
        out, _ = eng.registry.call("prove_goal", {"goal_id": goal_id, "evidence_id": fact,
                                                  "reason": "trust the page"}, _ctx(eng, tid))
        self.assertTrue(out.startswith("REFUSED"))
        self.assertEqual(eng.store.goals(tid)[0]["state"], "open")

    def test_finding_requires_evidence_and_dedupes(self):
        eng = self.eng
        tid = eng.new_task("finding gate")
        ctx = _ctx(eng, tid)

        out, _ = eng.registry.call("report_finding", {"vulnclass": "xss", "severity": "high",
                                                     "summary": "s", "evidence": ""}, ctx)
        self.assertTrue(out.startswith("ERROR"))

        out, _ = eng.registry.call("report_finding", {
            "vulnclass": "xss", "severity": "high", "summary": "s", "evidence": "payload fired",
            "endpoint": "https://a.test/q", "parameter": "q"}, ctx)
        self.assertIn("finding_id", out)

        out, _ = eng.registry.call("report_finding", {
            "vulnclass": "xss", "severity": "high", "summary": "same again",
            "evidence": "fired", "endpoint": "https://a.test/q", "parameter": "q"}, ctx)
        self.assertTrue(out.startswith("REFUSED"))

    def test_inferred_candidate_is_not_a_finding(self):
        eng = self.eng
        tid = eng.new_task("inferred gate")
        out, _ = eng.registry.call("report_finding", {
            "vulnclass": "cve-match", "severity": "high", "summary": "version matches CVE",
            "evidence": "server header says 1.2.3", "confidence": "inferred"}, _ctx(eng, tid))
        self.assertTrue(out.startswith("ERROR"))
        self.assertEqual(eng.store.findings(tid), [])


def _ctx(eng, tid):
    from titan.guard import Guard, Scope
    from titan.tools import Ctx
    guard = Guard(eng.store, eng.settings, tid, "test", Scope(eng.store.scope(tid)))
    return Ctx(eng.store, eng.settings, tid, "worker", "test", eng.settings.run_dir(tid),
               guard, eng.pacer, eng, skills=eng.skills)


if __name__ == "__main__":
    unittest.main(verbosity=2)
