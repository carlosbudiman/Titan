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
        self.assertIn("work directory", msg)

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


    def test_final_judgement_closes_a_goal_from_existing_evidence(self):
        eng = self.eng
        tid = eng.new_task("judge gate", scope=[{"kind": "url", "value": self.target.url}])
        fact = eng.store.add_fact(tid, "root returned 200", source="tool_output",
                                  confidence="observed", evidence="GET / -> 200")
        goal_id = eng.store.goals(tid)[0]["id"]
        eng.llm.script.extend([
            Reply(content="", tool_calls=[_tc(9, "prove_goal", {
                "goal_id": goal_id, "evidence_id": fact, "reason": "observed tool output"})]),
            Reply(content="goal met from existing evidence"),
        ])
        verdict = eng.final_judgement(tid)
        self.assertIn("goal met", verdict.lower())
        self.assertEqual(eng.store.goals(tid)[0]["state"], "met")
        self.assertEqual(eng.store.get_task(tid)["status"], "achieved")
        # this pass must not be able to dispatch work
        names = {t["function"]["name"] for t in
                 eng.registry.specs("planner") if t["function"]["name"] in eng.JUDGE_ONLY}
        self.assertNotIn("add_intent", names)


    def test_ip_targets_are_allowed_in_scope(self):
        """Regression: an IP given as url=/domain= used to land in the domain set and
        was then refused, which pushed every worker onto 127.0.0.1."""
        from titan.guard import Guard, Scope
        eng = self.eng
        tid = eng.new_task("ip scope", scope=[{"kind": "url", "value": "http://10.10.14.7:8080/"},
                                              {"kind": "domain", "value": "192.168.1.50"}])
        s = Scope(eng.store.scope(tid))
        g = Guard(eng.store, eng.settings, tid, "t", s)
        for cmd in ("curl -s http://10.10.14.7:8080/", "nmap -sV -p80 10.10.14.7",
                    "curl -s http://192.168.1.50:3000/api", "curl -s http://127.0.0.1:8080/"):
            ok, msg = g.check("bash", {"command": cmd})
            self.assertTrue(ok, f"{cmd} was refused: {msg}")
        ok, msg = g.check("bash", {"command": "curl -s http://10.10.14.8/"})
        self.assertFalse(ok)
        self.assertIn("Authorized scope", msg)

    def test_messy_scope_strings_are_split(self):
        """Regression: "https://a.com/, *.a.com/*" and an IP typed as domain= used to
        parse into "a.com," / a domain-set IP and refuse every real target."""
        from titan.guard import Scope
        s = Scope([{"kind": "domain", "value": "https://zing-id.com/, *.zing-id.com/*"},
                   {"kind": "domain", "value": "192.168.168.98"},
                   {"kind": "ip", "value": "10.0.0.0/24"}])
        self.assertTrue(s.allows_host("zing-id.com"))
        self.assertTrue(s.allows_host("api.zing-id.com"))
        self.assertTrue(s.allows_host("192.168.168.98"))
        self.assertTrue(s.allows_host("10.0.0.42"))
        self.assertFalse(s.allows_host("zing-id.com.evil.test"))
        self.assertFalse(s.allows_host("192.168.168.99"))

    def test_engagement_workdir_is_used_and_enforced(self):
        eng = self.eng
        target = self.tmp / "case" / "pelican"
        tid = eng.new_task("workdir", scope=[{"kind": "url", "value": self.target.url}],
                           workdir=str(target))
        self.assertTrue(target.is_dir())
        self.assertEqual(eng.task_workdir(tid), target)
        self.assertEqual(eng.run_workdir(tid, 12), target / "i12")
        self.assertTrue((target / "i12").is_dir())

        from titan.guard import Guard, Scope
        g = Guard(eng.store, eng.settings, tid, "t", Scope(eng.store.scope(tid)),
                  eng.run_workdir(tid, 12))
        ok, _ = g.check("write_file", {"path": str(target / "i12" / "notes.md"), "content": "x"})
        self.assertTrue(ok)
        ok, msg = g.check("write_file", {"path": "/etc/passwd", "content": "x"})
        self.assertFalse(ok)
        self.assertIn("engagement work directory", msg)

    def test_delete_task_removes_derived_rows(self):
        eng = self.eng
        keep = eng.new_task("keep me", scope=[{"kind": "url", "value": self.target.url}])
        drop = eng.new_task("drop me", scope=[{"kind": "url", "value": self.target.url}])
        eng.store.add_asset(drop, {"type": "service", "url": self.target.url})
        eng.store.add_fact(drop, "fact", source="tool_output")
        eng.store.add_traffic(drop, "GET", self.target.url, 200, {}, "", {}, "ok")
        eng.store.add_finding(drop, "xss", "high", "s", "evidence", endpoint="e")
        eng.store.add_scope(drop, "domain", "example.org")

        self.assertTrue(eng.store.rename_task(drop, "renamed"))
        self.assertEqual(eng.store.get_task(drop)["title"], "renamed")

        self.assertTrue(eng.store.delete_task(drop))
        self.assertIsNone(eng.store.get_task(drop))
        for table, col in (("exploration_nodes", "exploration_id"), ("findings", "task_id"),
                           ("traffic", "task_id"), ("task_scope", "task_id"),
                           ("activity", "task_id")):
            left = eng.store.one(f"SELECT COUNT(*) c FROM {table} WHERE {col}=?", (drop,))
            self.assertEqual(left["c"], 0, table)
        # the other engagement is untouched
        self.assertIsNotNone(eng.store.get_task(keep))
        self.assertTrue(eng.store.goals(keep))
        self.assertFalse(eng.store.delete_task(drop))


def _ctx(eng, tid):
    from titan.guard import Guard, Scope
    from titan.tools import Ctx
    guard = Guard(eng.store, eng.settings, tid, "test", Scope(eng.store.scope(tid)))
    return Ctx(eng.store, eng.settings, tid, "worker", "test", eng.settings.run_dir(tid),
               guard, eng.pacer, eng, skills=eng.skills)


if __name__ == "__main__":
    unittest.main(verbosity=2)
