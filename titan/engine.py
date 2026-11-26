"""Orchestrator: goals -> planner rounds -> workers -> goal judgement.

One process, threads per worker (default 2). SQLite is the shared blackboard, so a
crashed run resumes: open intents stay claimable and stale claims expire.
"""
from __future__ import annotations

import json
import queue
import threading
import time
import uuid
from pathlib import Path

from .agents import (GOALS_PROMPT, PLANNER_PROMPT, TRAFFIC_BLOCK, WORKER_PROMPT,
                     constraints_block, noise_block, parse_json_block, render, run_loop)
from .guard import Guard, Pacer, Scope
from .config import load_api_key
from .llm import LLM, MockLLM, Reply
from .skills import SkillIndex
from .store import Store
from .tools import Ctx, Registry


class Engine:
    def __init__(self, settings, store: Store | None = None, llm=None,
                 skills: SkillIndex | None = None, emit=print, interactive: bool = False):
        self.settings = settings
        self.settings.ensure_dirs()
        self.store = store or Store(settings.db_path)
        self._llm_override = llm
        self.llm = None
        self.reload_llm()
        self.skills = skills or SkillIndex(settings.skill_dir)
        self.skills.register(self.store)
        self.registry = Registry(self.skills)
        self.emit = emit
        self.interactive = interactive
        self.pacer = Pacer(settings.rps, settings.max_per_host)
        self.inboxes: dict[int, queue.Queue] = {}
        self.kill_flags: dict[int, threading.Event] = {}
        self.stop_flags: dict[int, threading.Event] = {}
        self.lock = threading.Lock()
        self.stalls = 0
        self.live: dict[str, dict] = {}
        self.live_lock = threading.Lock()
        self._live_task: dict[str, int] = {}

    # ------------------------------------------------------------------ llm config
    def llm_config(self) -> dict:
        """DB settings win over env, so the GUI can reconfigure without a restart."""
        s = self.store.settings()

        def pick(key, fallback):
            v = s.get(key)
            return fallback if v is None or v == "" else v

        return {
            "base_url": pick("llm.base_url", self.settings.base_url),
            "model": pick("llm.model", self.settings.model),
            "api_key": load_api_key(self.settings),
            "timeout": int(pick("llm.timeout", self.settings.request_timeout)),
            "max_tokens": int(pick("llm.max_tokens", self.settings.max_tokens)),
            "temperature": float(pick("llm.temperature", self.settings.temperature)),
        }

    def reload_llm(self) -> None:
        if self._llm_override is not None:
            self.llm = self._llm_override
            return
        cfg = self.llm_config()
        self.llm = LLM(cfg["base_url"], cfg["model"], cfg["api_key"], cfg["timeout"],
                       cfg["max_tokens"], cfg["temperature"])

    def apply_runtime_settings(self) -> None:
        """Pacing/limits from the settings page, refreshed at the start of a run."""
        s = self.store.settings()
        if s.get("run.rps"):
            try:
                self.settings.rps = float(s["run.rps"])
                self.pacer = Pacer(self.settings.rps, self.settings.max_per_host)
            except ValueError:
                pass
        if s.get("run.noise_profile"):
            self.settings.noise_profile = s["run.noise_profile"]
        if s.get("run.max_workers"):
            try:
                self.settings.max_workers = max(1, min(int(s["run.max_workers"]), 8))
            except ValueError:
                pass

    # ------------------------------------------------------------------ live agents
    def live_update(self, key: str, **fields) -> None:
        task_id = fields.pop("task", None)
        if task_id:
            self._live_task[key] = task_id
        task_id = task_id or self._live_task.get(key, 0)
        if not task_id:
            return
        turn = bool(fields.pop("turn", False))
        try:
            self.store.agent_upsert(key, task_id, turn=turn, **fields)
        except Exception:  # noqa: BLE001 - telemetry must never break a run
            pass

    def live_drop(self, key: str) -> None:
        self._live_task.pop(key, None)
        try:
            self.store.agent_drop(key)
        except Exception:  # noqa: BLE001
            pass

    def live_snapshot(self, task_id: int = 0) -> list[dict]:
        return self.store.agents(task_id)

    # ------------------------------------------------------------------ run control
    def request_stop(self, task_id: int) -> None:
        with self.lock:
            self.stop_flags.setdefault(task_id, threading.Event()).set()

    def stop_requested(self, task_id: int) -> bool:
        ev = self.stop_flags.get(task_id)
        return bool(ev and ev.is_set())

    def clear_stop(self, task_id: int) -> None:
        with self.lock:
            self.stop_flags.pop(task_id, None)

    # ------------------------------------------------------------------ runtime API (tools)
    def steer(self, intent_id: int, message: str) -> bool:
        q = self.inboxes.get(intent_id)
        if not q:
            return False
        q.put(f"[steer from planner] {message}")
        return True

    def kill(self, intent_id: int, reason: str = "") -> bool:
        ev = self.kill_flags.get(intent_id)
        if not ev:
            return False
        ev.set()
        return True

    def ask(self, question: str, command: str = "") -> str:
        if not self.interactive:
            return ""
        try:
            print(f"\n[operator needed] {question}\n[run this] {command}\n")
            return input("paste result (empty to skip): ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    # ------------------------------------------------------------------ tasks
    def task_workdir(self, task_id: int) -> Path:
        """Per-engagement artifact root: the path chosen at creation, else the default."""
        t = self.store.get_task(task_id)
        base = Path(t["workdir"]).expanduser() if (t and t["workdir"]) else \
            Path(self.settings.workdir) / "tasks" / str(task_id)
        base.mkdir(parents=True, exist_ok=True)
        return base

    def run_workdir(self, task_id: int, intent_id: int = 0) -> Path:
        base = self.task_workdir(task_id)
        p = base if not intent_id else base / f"i{intent_id}"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def new_task(self, goal: str, title: str = "", description: str = "",
                 scope: list[dict] | None = None, workdir: str = "") -> int:
        tid = self.store.create_task(goal, title, description, scope, workdir)
        self.task_workdir(tid)
        goals, constraints = self.decompose(goal, description)
        self._apply_goals(tid, goals)
        for c in constraints:
            self.store.add_constraint(tid, c.get("kind", "deny"), c.get("text", ""))
        self.store.log(tid, "goals", "goals", f"{len(goals)} goals, {len(constraints)} constraints",
                       detail=json.dumps(goals))
        return tid

    def _apply_goals(self, task_id: int, goals: list[str]) -> None:
        existing = self.store.goals(task_id)
        goals = [g.strip() for g in goals if isinstance(g, str) and g.strip()][:6]
        if not goals:
            return
        if not existing:
            for g in goals:
                self.store.add_node(task_id, "goal", {"text": g}, origin="goals")
            return
        first = existing[0]
        payload = json.loads(self.store.node(first["id"])["payload"])
        payload["text"] = goals[0]
        self.store.x("UPDATE exploration_nodes SET payload=?, updated_at=strftime('%Y-%m-%dT%H:%M:%SZ','now')"
                     " WHERE id=?", (json.dumps(payload), first["id"]))
        for g in goals[1:]:
            self.store.add_node(task_id, "goal", {"text": g}, origin="goals")

    def decompose(self, goal: str, description: str = "") -> tuple[list[str], list[dict]]:
        user = f"Engagement request:\n{goal}\n\nAdditional context:\n{description or '(none)'}"
        try:
            reply: Reply = self.llm.chat(
                [{"role": "system", "content": GOALS_PROMPT},
                 {"role": "user", "content": user}], tools=None)
            self.store.usage(0, "goals", getattr(self.llm, "name", ""),
                             reply.tokens_in, reply.tokens_out)
            data = parse_json_block(reply.content)
        except Exception as e:  # noqa: BLE001 - never block task creation on the decomposer
            self.emit(f"[goals] decomposition failed ({e}); using the raw goal")
            return [goal], []
        goals = data.get("goals") or [goal]
        cons = [c for c in (data.get("constraints") or []) if isinstance(c, dict) and c.get("text")]
        return goals, cons

    # ------------------------------------------------------------------ planner
    def plan_round(self, task_id: int) -> tuple[str, int]:
        ov = self.store.graph_overview(task_id)
        before = self.store.pending_intents(task_id)
        task = self.store.get_task(task_id)
        scope = Scope(self.store.scope(task_id))
        wd = self.run_workdir(task_id)
        guard = Guard(self.store, self.settings, task_id, "planner", scope, wd)
        ctx = Ctx(self.store, self.settings, task_id, "planner", "planner",
                  wd, guard, self.pacer, self)
        ctx.skills = self.skills

        system = (render(PLANNER_PROMPT, goal=task["goal"],
                         constraints=constraints_block(self.store, task_id))
                  + "\n\n" + self.skills.index() + noise_block(self.settings)
                  + "\n\nIntermediate files go in " + str(ctx.workdir) + ". Never /tmp.")
        if ov["frontier_open"] == 0 and not ov["running_intents"]:
            lead = ("No open or running intent and the goal is unmet: exploration has stalled. "
                    "You MUST dispatch at least one new non-duplicate intent this round.")
        else:
            lead = "Plan the next step from the situation below."
        user = lead + "\n\nSITUATION (graph_overview):\n" + json.dumps(ov, ensure_ascii=False, indent=1)

        def log(kind, text):
            self.store.log(task_id, "planner", kind, text[:2000])

        lk = "planner"
        model = getattr(self.llm, "name", "")
        self.live_update(lk, role="planner", task=task_id, state="thinking", tool=None,
                         model=model, intent=None, note="planning")

        def step(kind, p):
            if kind == "llm":
                self.live_update(lk, state="thinking", note=p.get("note"),
                                 turn=p.get("turn"), tokens_in=p.get("tokens_in"),
                                 tokens_out=p.get("tokens_out"))
            elif kind == "tool_start":
                self.live_update(lk, state="tool", tool=p.get("tool"), note=p.get("args"))
            elif kind == "tool_end":
                self.live_update(lk, state="thinking", tool=p.get("tool"), note=p.get("note"))

        try:
            final = run_loop(self.llm, self.registry, "planner", system, user, ctx, guard,
                             self.settings.planner_turns, log=log, step=step)
        finally:
            self.live_update(lk, state="idle", tool=None, note="round finished")
        after = self.store.pending_intents(task_id)
        return final, max(0, after - before)

    # ------------------------------------------------------------------ final judgement
    JUDGE_ONLY = ["graph_overview", "list_goals", "list_facts", "list_findings",
                  "node_detail", "prove_goal"]

    def final_judgement(self, task_id: int) -> str:
        """One last planner pass with no dispatch tools, so a run whose budget ended
        can still close the goals its evidence already proves."""
        task = self.store.get_task(task_id)
        ov = self.store.graph_overview(task_id)
        if not task or (ov["facts_total"] == 0 and ov["findings_total"] == 0):
            return ""
        scope = Scope(self.store.scope(task_id))
        wd = self.run_workdir(task_id)
        guard = Guard(self.store, self.settings, task_id, "planner", scope, wd)
        ctx = Ctx(self.store, self.settings, task_id, "planner", "planner",
                  wd, guard, self.pacer, self)
        ctx.skills = self.skills
        system = (render(PLANNER_PROMPT, goal=task["goal"],
                         constraints=constraints_block(self.store, task_id))
                  + "\n\nFINAL JUDGEMENT PASS. The round budget is exhausted and no worker is "
                    "running. add_intent is NOT available. Judge every goal strictly on the "
                    "evidence already in the graph: call prove_goal(goal_id, evidence_id, reason) "
                    "for each goal whose evidence exists (a fact with source=tool_output, or a "
                    "finding with bound traffic). If a goal is genuinely unmet, reply with one "
                    "sentence naming what is missing and leave it open.")
        self.live_update("planner", role="planner", task=task_id, state="judging",
                         tool=None, note="final judgement pass",
                         model=getattr(self.llm, "name", ""))
        try:
            final = run_loop(self.llm, self.registry, "planner", system,
                             "SITUATION (graph_overview):\n"
                             + json.dumps(ov, ensure_ascii=False, indent=1),
                             ctx, guard, max(2, self.settings.planner_turns // 2),
                             only=self.JUDGE_ONLY,
                             log=lambda k, t: self.store.log(task_id, "planner", k, t[:2000]))
        finally:
            self.live_update("planner", state="idle", tool=None, note="final pass done")
        if self.store.goal_met(task_id):
            self.store.set_task_status(task_id, "achieved")
        return final

    # ------------------------------------------------------------------ workers
    def _worker(self, task_id: int, intent, token: str, workers_guard) -> None:
        iid = int(intent["id"])
        summary = json.loads(intent["payload"]).get("summary", "")
        scope = Scope(self.store.scope(task_id))
        wd = self.run_workdir(task_id, iid)
        guard = Guard(self.store, self.settings, task_id, f"w{iid}", scope, wd)
        ctx = Ctx(self.store, self.settings, task_id, "worker", f"w{iid}",
                  wd, guard, self.pacer, self, node_id=iid)
        ctx.skills = self.skills
        inbox: queue.Queue = queue.Queue()
        stop = threading.Event()
        with self.lock:
            self.inboxes[iid] = inbox
            self.kill_flags[iid] = stop

        assets = []
        for aid in self.store.anchors(iid):
            a = self.store.asset(aid)
            if a:
                assets.append({k: a[k] for k in ("id", "type", "domain", "ip", "port", "url",
                                                 "status_code", "page_title", "technologies")})
        system = (render(WORKER_PROMPT, intent=summary) + TRAFFIC_BLOCK
                  + "\n\nOPERATOR CONSTRAINTS\n" + constraints_block(self.store, task_id)
                  + "\n\n" + noise_block(self.settings)
                  + "\n\nASSETS ANCHORED TO THIS INTENT\n" + json.dumps(assets, ensure_ascii=False)
                  + "\n\nSkills index:\n" + self.skills.index()
                  + f"\n\nWork directory: {ctx.workdir}")

        def poll():
            msgs = []
            while True:
                try:
                    msgs.append(inbox.get_nowait())
                except queue.Empty:
                    break
            if stop.is_set():
                msgs.append("[operator] This work is being stopped. Land what you have now and stop.")
            if self.stop_requested(task_id):
                msgs.append("[operator] The whole task is being stopped. Land what you have now and stop.")
            return msgs

        facts_before = self._yield_count(iid)
        status, note = "done", ""
        lk = f"w{iid}"
        self.live_update(lk, role="worker", task=task_id, intent=iid, state="thinking",
                         tool=None, model=getattr(self.llm, "name", ""),
                         note=summary[:120])

        def step(kind, p):
            if kind == "llm":
                self.live_update(lk, state="thinking", note=p.get("note"),
                                 turn=p.get("turn"), tokens_in=p.get("tokens_in"),
                                 tokens_out=p.get("tokens_out"))
            elif kind == "tool_start":
                self.live_update(lk, state="tool", tool=p.get("tool"), note=p.get("args"))
            elif kind == "tool_end":
                self.live_update(lk, state="thinking", tool=p.get("tool"), note=p.get("note"))

        try:
            run_loop(self.llm, self.registry, "worker", system,
                     f"Execute this intent now: {summary}", ctx, guard,
                     self.settings.worker_turns, poll=poll, step=step,
                     log=lambda k, t: self.store.log(task_id, f"w{iid}", k, t[:2000], node_id=iid))
        except Exception as e:  # noqa: BLE001
            status, note = "blocked", f"worker error: {type(e).__name__}: {e}"
        if stop.is_set():
            status, note = "stopped", "stopped by planner"
        elif status == "done" and self._yield_count(iid) == facts_before:
            status, note = "exhausted", "no fact or finding was written back"

        self.store.set_state(iid, status, note or None)
        if status == "done":
            self.store.mark_tested(task_id, self.store.anchors(iid))
        with self.lock:
            self.inboxes.pop(iid, None)
            self.kill_flags.pop(iid, None)
        self.live_drop(lk)
        self.emit(f"  [w{iid}] {status}: {summary[:100]}")

    def _yield_count(self, node_id: int) -> int:
        r = self.store.one("SELECT COUNT(*) c FROM exploration_edges WHERE src_id=? AND rel='yields'",
                           (node_id,))
        return int(r["c"]) if r else 0

    # ------------------------------------------------------------------ main loop
    def run_task(self, task_id: int, rounds: int | None = None, workers: int | None = None) -> dict:
        task = self.store.get_task(task_id)
        if not task:
            raise SystemExit(f"no task {task_id}")
        rounds = rounds or self.settings.max_rounds
        workers = max(1, workers or self.settings.max_workers)
        deadline = (time.time() + self.settings.task_deadline_s) if self.settings.task_deadline_s else 0
        self.clear_stop(task_id)
        self.apply_runtime_settings()
        self.reload_llm()
        self.emit(f"Titan task #{task_id}: {task['goal']}")

        for rnd in range(max(1, rounds)):
            if self.stop_requested(task_id):
                self.emit("[engine] stop requested; finishing current work")
                self.store.set_task_status(task_id, "stopped")
                break
            if self.store.goal_met(task_id):
                self.store.set_task_status(task_id, "achieved")
                break
            if deadline and time.time() > deadline:
                self.emit("[engine] task deadline reached; stopping")
                self.store.set_task_status(task_id, "stopped")
                break

            n = self.store.bump_round(task_id)
            self.emit(f"[round {n}] planning")
            try:
                final, added = self.plan_round(task_id)
            except Exception as e:  # noqa: BLE001 - a dead endpoint must not traceback
                self.emit(f"[engine] planner failed: {type(e).__name__}: {e}")
                self.emit("[engine] check TITAN_LLM_BASE_URL / TITAN_LLM_MODEL / "
                          "TITAN_LLM_API_KEY with: titan doctor")
                self.store.log(task_id, "engine", "error", f"planner: {e}"[:2000])
                self.store.set_task_status(task_id, "stopped")
                break
            if final:
                self.emit("  planner: " + final.strip().replace("\n", " ")[:400])
            if self.store.goal_met(task_id):
                break

            claimed = []
            for _ in range(workers):
                token = uuid.uuid4().hex
                row = self.store.claim_intent(task_id, token, self.settings.intent_lease_s)
                if not row:
                    break
                claimed.append((row, token))

            if not claimed:
                if added == 0:
                    self.stalls += 1
                    self.emit(f"[engine] stall {self.stalls}: no open intent")
                    if self.stalls >= 3:
                        self.store.set_task_status(task_id, "failed")
                        break
                    self.store.add_intent(task_id, f"Advance the task goal with untested surface: "
                                                   f"{task['goal']}", priority=-1)
                continue
            self.stalls = 0

            threads = []
            for row, token in claimed:
                t = threading.Thread(target=self._worker, args=(task_id, row, token, None),
                                     daemon=True)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()

        # Budget ended: give the planner one judgement-only pass so evidence it already
        # holds can close the goals (and only that).
        current = self.store.get_task(task_id)
        if (current and current["status"] == "open" and not self.store.goal_met(task_id)
                and not self.stop_requested(task_id)):
            self.emit("[engine] final judgement pass")
            try:
                verdict = self.final_judgement(task_id)
                if verdict:
                    self.emit("  planner: " + verdict.strip().replace("\n", " ")[:300])
            except Exception as e:  # noqa: BLE001
                self.emit(f"[engine] judgement pass failed: {type(e).__name__}: {e}")
            if self.store.goal_met(task_id):
                self.store.set_task_status(task_id, "achieved")

        status = self.store.get_task(task_id)["status"]
        ov = self.store.graph_overview(task_id)
        return {
            "task_id": task_id,
            "status": status,
            "rounds": ov["round"],
            "coverage": ov["coverage"],
            "findings": ov["findings_total"],
            "facts": ov["facts_total"],
            "usage": self.store.usage_totals(task_id),
            "goals": ov["goals"],
        }

    # ------------------------------------------------------------------ chat
    def chat(self, task_id: int, message: str) -> str:
        scope = Scope(self.store.scope(task_id))
        wd = self.run_workdir(task_id)
        guard = Guard(self.store, self.settings, task_id, "main", scope, wd)
        ctx = Ctx(self.store, self.settings, task_id, "main", "main",
                  wd, guard, self.pacer, self)
        ctx.skills = self.skills
        system = ("You are the operator interface of Dewaguard Titan. You do not run the engagement "
                  "yourself: read the graph, answer, and queue hints with add_hint or steer_work. "
                  "Never invent results; answer only from tool output.\n\n"
                  + self.skills.index() + "\n\nLIVE GRAPH:\n"
                  + json.dumps(self.store.graph_overview(task_id), ensure_ascii=False, indent=1))
        return run_loop(self.llm, self.registry, "main", system, message, ctx, guard, 12)
