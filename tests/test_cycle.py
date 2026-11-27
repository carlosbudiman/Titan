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

        # "kind:value" pasted into the wrong field must still parse
        s2 = Scope([{"kind": "domain", "value": "ip:10.20.30.40"}])
        self.assertTrue(s2.allows_host("10.20.30.40"))
        self.assertNotIn("ip", s2.hosts)          # stored as an address, not a hostname

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

    def test_approval_mode_waits_then_obeys(self):
        import threading as th
        import time as tm
        eng, target = self.eng, self.target.url
        eng.llm.script.extend([
            Reply(content=json.dumps({"goals": ["prove something"], "constraints": []})),
            Reply(content="", tool_calls=[_tc(1, "add_intent", {"intents": [
                {"summary": f"round one against {target}"}]})]),
            Reply(content="dispatched round one"),
            Reply(content="", tool_calls=[_tc(2, "record_fact", {
                "summary": "fact one", "source": "tool_output", "confidence": "observed"})]),
            Reply(content="round one done"),
            Reply(content="", tool_calls=[_tc(3, "add_intent", {"intents": [
                {"summary": f"round two against {target}"}]})]),
            Reply(content="dispatched round two"),
            Reply(content="", tool_calls=[_tc(4, "record_fact", {
                "summary": "fact two", "source": "tool_output", "confidence": "observed"})]),
            Reply(content="round two done"),
        ])
        tid = eng.new_task("approval flow", scope=[{"kind": "url", "value": target}],
                           mode="approval")
        out = {}

        def run():
            out["res"] = eng.run_task(tid, workers=1, mode="approval")

        th.Thread(target=run, daemon=True).start()
        pending = None
        for _ in range(100):
            pending = eng.store.pending_approval(tid)
            if pending:
                break
            tm.sleep(0.05)
        self.assertIsNotNone(pending, "engine never asked for approval")
        self.assertEqual(pending["round_no"], 1)

        eng.approve(tid, "approve")
        second = None
        for _ in range(200):
            second = eng.store.pending_approval(tid)
            if second and second["round_no"] == 2:
                break
            tm.sleep(0.05)
        self.assertIsNotNone(second, "second approval was never requested")
        self.assertEqual(second["round_no"], 2)

        eng.approve(tid, "deny")
        for _ in range(100):
            if out.get("res"):
                break
            tm.sleep(0.05)
        self.assertIn("res", out)
        self.assertEqual(out["res"]["status"], "stopped")
        self.assertIsNone(eng.store.pending_approval(tid))

    def test_autonomous_run_halts_when_nothing_progresses(self):
        eng = self.eng
        tid = eng.new_task("no progress", scope=[{"kind": "url", "value": self.target.url}])
        # each round: planner dispatches, worker writes nothing back
        script = []
        for i in range(6):
            script.append(Reply(content="", tool_calls=[_tc(10 + i, "add_intent", {"intents": [
                {"summary": f"direction {i} on {self.target.url}"}]})]))
            script.append(Reply(content="dispatched"))
            script.append(Reply(content="nothing to report"))
        eng.llm.script.extend(script)
        eng.settings.no_progress_rounds = 2
        res = eng.run_task(tid, workers=1, mode="autonomous")
        self.assertEqual(res["status"], "stopped")
        self.assertLessEqual(res["rounds"], 6)
        row = eng.store.one("SELECT summary FROM activity WHERE task_id=? AND kind='halt'"
                            " ORDER BY id DESC LIMIT 1", (tid,))
        self.assertIsNotNone(row, "no halt was logged")

    def test_enumeration_groups_hosts_services_and_observations(self):
        eng = self.eng
        tid = eng.new_task("enum", scope=[{"kind": "ip", "value": "10.1.2.3"}])
        svc = eng.store.add_asset(tid, {"type": "service", "url": "http://10.1.2.3:8080/",
                                        "status_code": 200, "page_title": "jetty app",
                                        "technologies": ["Jetty 6.x"]})
        eng.store.add_asset(tid, {"type": "endpoint", "url": "http://10.1.2.3:8080/admin",
                                  "status_code": 302})
        eng.store.add_fact(tid, "Jetty 6.x fronting a Jersey app", detail="Server header Jetty(6.1)",
                           source="tool_output", confidence="observed", asset_ids=[svc])
        eng.store.add_fact(tid, "unattached general observation", source="inference")

        e = eng.store.enumeration(tid)
        self.assertEqual(e["counts"]["hosts"], 1)
        self.assertEqual(e["counts"]["services"], 1)
        self.assertEqual(e["counts"]["endpoints"], 1)
        host = [h for h in e["hosts"] if h["key"] == "10.1.2.3"][0]
        self.assertEqual(host["services"][0]["title"], "jetty app")
        self.assertEqual(host["services"][0]["tech"], ["Jetty 6.x"])
        paths = [x["url"] for x in host["services"][0]["endpoints"]]
        self.assertIn("http://10.1.2.3:8080/admin", paths)
        self.assertEqual(host["observations"][0]["summary"], "Jetty 6.x fronting a Jersey app")
        self.assertEqual(host["observations"][0]["confidence"], "observed")
        general = [h for h in e["hosts"] if h["key"] == "(unattached)"][0]
        self.assertEqual(general["observations"][0]["summary"], "unattached general observation")

    def test_activity_rows_carry_local_time_and_deltas(self):
        import time as tm
        eng = self.eng
        tid = eng.new_task("timing", scope=[{"kind": "url", "value": self.target.url}])
        eng.store.log(tid, "w1", "tool", "first")
        tm.sleep(0.05)
        eng.store.log(tid, "w1", "tool", "second")
        rows = eng.store.activity(tid)
        self.assertGreaterEqual(len(rows), 2)
        first, second = rows[-2], rows[-1]
        self.assertRegex(first["at_local"], r"^\d{2}:\d{2}:\d{2}$")
        self.assertIsNotNone(second["delta_s"])
        self.assertGreaterEqual(second["delta_s"], 0)
        self.assertEqual(second["summary"], "second")
        # intents expose start/finish and a duration
        nid = eng.store.add_intent(tid, "timed intent")
        view = eng.store.open_intents(tid)[0]
        self.assertRegex(view["started"], r"^\d{2}:\d{2}:\d{2}$")
        self.assertIsInstance(view["took_s"], int)
        eng.store.set_state(nid, "done")
        done = eng.store.recent_done(tid)[0]
        self.assertRegex(done["finished"], r"^\d{2}:\d{2}:\d{2}$")

    def test_scope_allows_resolved_address_and_ports(self):
        from titan.guard import Scope

        sc = Scope([{"kind": "domain", "value": "pelican.local"},
                    {"kind": "url", "value": "https://pi.example.com:8443/"}],
                   resolver=lambda h: [(None, None, None, "", ("192.168.168.98", 0))])
        self.assertTrue(sc.allows_host("192.168.168.98"))       # resolved from the domain
        self.assertTrue(sc.allows_host("pelican.local", 8080))
        self.assertFalse(sc.allows_host("10.1.2.3"))
        self.assertTrue(sc.allows_host("pi.example.com", 8443))
        self.assertFalse(sc.allows_host("pi.example.com", 80))
        ex = Scope([{"kind": "domain", "value": "example.com"},
                    {"kind": "exclude", "value": "staging.example.com"}])
        self.assertFalse(ex.allows_host("staging.example.com"))
        self.assertTrue(ex.allows_host("app.example.com"))

    def test_scope_candidate_is_queued_then_approved(self):
        from titan.guard import Guard, Scope

        tid = self.eng.new_task("scope flow", scope=[{"kind": "domain", "value": "example.com"}])
        store, settings = self.eng.store, self.eng.settings
        g = Guard(store, settings, tid, "w1", Scope(store.scope(tid)))
        ok, msg = g.check("bash", {"command": "curl http://203.0.113.9/status"})
        self.assertFalse(ok)
        self.assertIn("waiting for the operator", msg)
        cands = store.scope_candidates(tid)
        self.assertEqual([c["host"] for c in cands], ["203.0.113.9"])
        self.assertEqual(store.scope_candidates(tid, "pending")[0]["state"], "pending")

        res = store.decide_scope_candidate(cands[0]["id"], True)
        self.assertEqual(res["state"], "approved")
        kinds = {(e["kind"], e["value"]) for e in store.scope(tid)}
        self.assertIn(("ip", "203.0.113.9"), kinds)
        g2 = Guard(store, settings, tid, "w1", Scope(store.scope(tid)))
        self.assertTrue(g2.check("bash", {"command": "curl http://203.0.113.9/status"})[0])

    def test_subdomain_of_approved_domain_is_auto_allowed(self):
        from titan.guard import Guard, Scope

        tid = self.eng.new_task("auto sub", scope=[{"kind": "domain", "value": "example.com"}])
        store, settings = self.eng.store, self.eng.settings
        g = Guard(store, settings, tid, "w1", Scope(store.scope(tid)))
        ok, _ = g.check("bash", {"command": "curl https://api.example.com/health"})
        self.assertTrue(ok)
        self.assertFalse(store.scope_candidates(tid))

    def test_artifacts_tree_is_written(self):
        from titan.artifacts import Artifacts

        tid = self.eng.new_task("artifact flow", scope=[{"kind": "domain", "value": "example.com"}])
        root = self.eng.run_workdir(tid)
        self.eng.store.add_fact(tid, "port 8080 open on 127.0.0.1", source="nmap",
                                confidence="observed")
        res = Artifacts(root).write_all(self.eng.store, tid)
        self.assertGreater(res["files"], 2)
        for rel in ("00-meta.json", "enumeration/hosts.json", "report/report.md"):
            self.assertTrue((root / rel).is_file(), rel)

    def test_dead_process_intents_are_reclaimed(self):
        tid = self.eng.new_task("stale runs", scope=[{"kind": "url", "value": self.target.url}])
        iid = self.eng.store.add_intent(tid, "probe the target", priority=0)
        self.eng.store.x("UPDATE exploration_nodes SET state='running' WHERE id=?", (iid,))
        self.eng.store.db.commit()
        self.assertEqual(self.eng.store.reclaim_running(tid), 1)
        row = self.eng.store.one("SELECT state FROM exploration_nodes WHERE id=?", (iid,))
        self.assertEqual(row["state"], "stale")

    def test_scope_values_are_normalised(self):
        from titan.store import Store
        cases = [
            ("domain", "ip:192.168.168.98", ("ip", "192.168.168.98")),
            ("domain", "10.0.0.0/24", ("cidr", "10.0.0.0/24")),
            ("domain", "https://app.example.com", ("url", "https://app.example.com")),
            ("domain", "example.com", ("domain", "example.com")),
            ("", "10.1.1.1", ("ip", "10.1.1.1")),
        ]
        for kind, value, want in cases:
            self.assertEqual(Store.normalise_scope(kind, value), want, f"{kind}:{value}")
        tid = self.eng.new_task("scope normalisation")
        self.eng.store.add_scope(tid, "domain", "ip:10.9.9.9", "operator")
        scope = self.eng.store.scope(tid)
        self.assertIn({"kind": "ip", "value": "10.9.9.9", "reason": "operator"}, scope)

    def test_live_settings_release_and_apply(self):
        import threading as th
        import time as tm
        eng = self.eng
        eng.llm.script.extend([
            Reply(content=json.dumps({"goals": ["go"], "constraints": []})),
            Reply(content="", tool_calls=[_tc(1, "add_intent", {"intents": [
                {"summary": f"r1 {self.target.url}"}]})]),
            Reply(content="r1 dispatched"),
            Reply(content="", tool_calls=[_tc(2, "record_fact", {
                "summary": "f1", "source": "tool_output", "confidence": "observed"})]),
            Reply(content="r1 done"),
            Reply(content="", tool_calls=[_tc(3, "add_intent", {"intents": [
                {"summary": f"r2 {self.target.url}"}]})]),
            Reply(content="r2 dispatched"),
            Reply(content="", tool_calls=[_tc(4, "record_fact", {
                "summary": "f2", "source": "tool_output", "confidence": "observed"})]),
            Reply(content="r2 done"),
        ])
        tid = eng.new_task("live settings", scope=[{"kind": "url", "value": self.target.url}],
                           mode="approval")
        out = {}
        th.Thread(target=lambda: out.update(res=eng.run_task(tid, workers=1)), daemon=True).start()
        for _ in range(120):
            if eng.store.pending_approval(tid):
                break
            tm.sleep(0.05)
        self.assertIsNotNone(eng.store.pending_approval(tid))

        # switching to autonomous must release the paused run immediately
        eng.set_runtime(tid, workers=2, mode="autonomous")
        self.assertIsNone(eng.store.pending_approval(tid))
        for _ in range(200):
            if eng.store.get_task(tid)["round_no"] >= 2:
                break
            tm.sleep(0.05)
        self.assertGreaterEqual(eng.store.get_task(tid)["round_no"], 2)
        eng.request_stop(tid)
        for _ in range(100):
            if out.get("res"):
                break
            tm.sleep(0.05)
        self.assertEqual(out["res"]["status"], "stopped")

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
