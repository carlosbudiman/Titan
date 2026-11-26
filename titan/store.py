"""SQLite store: the two graphs.

Graph 1 (assets)      : global, shared by every task. Tables: assets, task_scope.
Graph 2 (exploration) : per task. explorations, exploration_nodes,
                        exploration_edges, exploration_anchors, task_constraints.

Node kinds: begin | goal | intent | fact | finding | hint | digest
Edge rels : spawns | derived_from | yields | proves | covers
"""
from __future__ import annotations

from datetime import datetime, timezone

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Iterable

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS assets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    type          TEXT NOT NULL,
    ukey          TEXT NOT NULL,
    domain        TEXT,
    root_domain   TEXT,
    ip            TEXT,
    port          INTEGER,
    url           TEXT,
    service_type  TEXT,
    service_name  TEXT,
    status_code   INTEGER,
    content_length INTEGER,
    page_title    TEXT,
    technologies  TEXT NOT NULL DEFAULT '[]',
    params        TEXT NOT NULL DEFAULT '[]',
    auth          TEXT NOT NULL DEFAULT '[]',
    extra         TEXT NOT NULL DEFAULT '{}',
    task_ids      TEXT NOT NULL DEFAULT '[]',
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_asset      ON assets(type, ukey);
CREATE INDEX IF NOT EXISTS idx_asset_domain     ON assets(domain);
CREATE INDEX IF NOT EXISTS idx_asset_root       ON assets(root_domain);
CREATE INDEX IF NOT EXISTS idx_asset_ip         ON assets(ip);

CREATE TABLE IF NOT EXISTS task_scope (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id    INTEGER NOT NULL REFERENCES explorations(id) ON DELETE CASCADE,
    kind       TEXT NOT NULL,          -- domain | ip | cidr | url | keyword
    value      TEXT NOT NULL,
    reason     TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(task_id, kind, value)
);

CREATE TABLE IF NOT EXISTS task_coverage (
    task_id   INTEGER NOT NULL,
    asset_id  INTEGER NOT NULL,
    tested_at TEXT NOT NULL,
    PRIMARY KEY (task_id, asset_id)
);

CREATE TABLE IF NOT EXISTS explorations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT,
    goal        TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'open',   -- open | achieved | failed | stopped
    round_no    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS exploration_nodes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    exploration_id INTEGER NOT NULL REFERENCES explorations(id) ON DELETE CASCADE,
    kind           TEXT NOT NULL,
    payload        TEXT NOT NULL DEFAULT '{}',
    priority       INTEGER NOT NULL DEFAULT 0,
    state          TEXT NOT NULL,
    origin         TEXT,
    owner          TEXT,
    blocked_reason TEXT,
    content_version INTEGER NOT NULL DEFAULT 0,
    claim_token    TEXT,
    heartbeat_at   TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    completed_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_node_task ON exploration_nodes(exploration_id, kind, state);
CREATE INDEX IF NOT EXISTS idx_node_frontier ON exploration_nodes(exploration_id, priority DESC)
    WHERE kind='intent' AND state='open';

CREATE TABLE IF NOT EXISTS exploration_edges (
    exploration_id INTEGER NOT NULL,
    src_id         INTEGER NOT NULL,
    dst_id         INTEGER NOT NULL,
    rel            TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    PRIMARY KEY (exploration_id, src_id, rel, dst_id),
    CHECK (src_id <> dst_id)
);

CREATE TABLE IF NOT EXISTS exploration_anchors (
    node_id  INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    PRIMARY KEY (node_id, asset_id)
);

CREATE TABLE IF NOT EXISTS task_constraints (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id    INTEGER NOT NULL REFERENCES explorations(id) ON DELETE CASCADE,
    kind       TEXT NOT NULL,        -- allow | deny
    text       TEXT NOT NULL,
    origin     TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS findings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id        INTEGER NOT NULL,
    node_id        INTEGER NOT NULL,
    vulnclass      TEXT NOT NULL,
    severity       TEXT NOT NULL,
    asset_id       INTEGER,
    endpoint       TEXT,
    parameter      TEXT,
    summary        TEXT NOT NULL,
    evidence       TEXT,
    poc            TEXT,
    counterevidence TEXT,
    confidence     TEXT,
    proof_basis    TEXT,
    traffic_refs   TEXT NOT NULL DEFAULT '[]',
    status         TEXT NOT NULL DEFAULT 'open',   -- open | confirmed | false_positive | duplicate | ignored
    created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_findings_task ON findings(task_id, status);

CREATE TABLE IF NOT EXISTS traffic (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id        INTEGER NOT NULL,
    method         TEXT NOT NULL,
    url            TEXT NOT NULL,
    status         INTEGER,
    req_headers    TEXT NOT NULL DEFAULT '{}',
    req_body       TEXT,
    resp_headers   TEXT NOT NULL DEFAULT '{}',
    resp_body      TEXT,
    created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_traffic_task ON traffic(task_id, id);

CREATE TABLE IF NOT EXISTS activity (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id        INTEGER NOT NULL,
    node_id        INTEGER,
    worker         TEXT,
    kind           TEXT,
    tool           TEXT,
    summary        TEXT,
    detail         TEXT,
    metadata       TEXT NOT NULL DEFAULT '{}',
    tokens_in      INTEGER,
    tokens_out     INTEGER,
    created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_activity_task ON activity(task_id, id);

CREATE TABLE IF NOT EXISTS skills (
    name        TEXT PRIMARY KEY,
    description TEXT,
    path        TEXT,
    frontmatter TEXT NOT NULL DEFAULT '{}',
    enabled     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS approvals (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id    INTEGER NOT NULL,
    round_no   INTEGER NOT NULL,
    status     TEXT NOT NULL DEFAULT 'pending',   -- pending | approved | denied | timeout
    note       TEXT,
    created_at TEXT NOT NULL,
    decided_at TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_state (
    key        TEXT PRIMARY KEY,
    task_id    INTEGER NOT NULL,
    role       TEXT,
    intent     INTEGER,
    state      TEXT,
    tool       TEXT,
    note       TEXT,
    model      TEXT,
    turns      INTEGER NOT NULL DEFAULT 0,
    tokens_in  INTEGER NOT NULL DEFAULT 0,
    tokens_out INTEGER NOT NULL DEFAULT 0,
    started    REAL NOT NULL,
    updated    REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_usage (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id    INTEGER,
    agent      TEXT,
    model      TEXT,
    tokens_in  INTEGER,
    tokens_out INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id    INTEGER,
    worker     TEXT,
    tool       TEXT,
    action     TEXT,
    reason     TEXT,
    command    TEXT,
    created_at TEXT NOT NULL
);
"""

NODE_STATES = {
    "begin": ("open",),
    "goal": ("open", "met", "abandoned"),
    "intent": ("open", "running", "paused", "done", "blocked", "exhausted", "stopped", "deleted"),
    "fact": ("confirmed", "dismissed", "origin"),
    "finding": ("confirmed", "dismissed"),
    "hint": ("active", "consumed"),
    "digest": ("active", "superseded"),
}


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def parse_utc(iso: str | None):
    if not iso:
        return None
    try:
        return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def local_hms(iso: str | None, with_date: bool = False) -> str:
    """Render a stored UTC timestamp in this machine's local time."""
    dt = parse_utc(iso)
    if not dt:
        return ""
    loc = dt.astimezone()
    return loc.strftime("%Y-%m-%d %H:%M:%S" if with_date else "%H:%M:%S")


def seconds_between(a: str | None, b: str | None) -> int | None:
    da, db = parse_utc(a), parse_utc(b)
    if not da or not db:
        return None
    return max(0, int((db - da).total_seconds()))


def jloads(s: str | None, default: Any) -> Any:
    if not s:
        return default
    try:
        return json.loads(s)
    except (ValueError, TypeError):
        return default


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.db = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        with self.lock:
            self.db.executescript(SCHEMA)
            for stmt in ("ALTER TABLE explorations ADD COLUMN workdir TEXT",
                         "ALTER TABLE explorations ADD COLUMN mode TEXT"):
                try:
                    self.db.execute(stmt)
                except sqlite3.OperationalError:
                    pass
            self.db.commit()

    # ---------------------------------------------------------------- helpers
    def q(self, sql: str, args: Iterable = ()) -> list[sqlite3.Row]:
        with self.lock:
            return list(self.db.execute(sql, tuple(args)))

    def one(self, sql: str, args: Iterable = ()) -> sqlite3.Row | None:
        with self.lock:
            return self.db.execute(sql, tuple(args)).fetchone()

    def x(self, sql: str, args: Iterable = ()) -> int:
        with self.lock:
            cur = self.db.execute(sql, tuple(args))
            self.db.commit()
            return cur.lastrowid or 0

    # ---------------------------------------------------------------- tasks
    def create_task(self, goal: str, title: str = "", description: str = "",
                    scope: list[dict] | None = None, workdir: str = "",
                    mode: str = "autonomous") -> int:
        ts = now()
        tid = self.x(
            "INSERT INTO explorations(title, goal, description, status, workdir, mode,"
            " created_at, updated_at) VALUES(?,?,?,'open',?,?,?,?)",
            (title or goal[:80], goal, description, workdir or "",
             "approval" if mode == "approval" else "autonomous", ts, ts))
        self.add_node(tid, "begin", {"goal": goal, "scope": scope or []}, state="open", origin="operator")
        self.add_node(tid, "goal", {"text": goal}, state="open", origin="operator")
        for s in scope or []:
            self.add_scope(tid, s.get("kind", ""), s.get("value", ""), s.get("reason", "operator"))
        return tid

    def get_task(self, task_id: int) -> sqlite3.Row | None:
        return self.one("SELECT * FROM explorations WHERE id=?", (task_id,))

    def list_tasks(self, limit: int = 50) -> list[sqlite3.Row]:
        return self.q(
            "SELECT e.*,"
            " (SELECT COUNT(*) FROM findings f WHERE f.task_id=e.id"
            "   AND f.status NOT IN ('false_positive','duplicate','ignored')) AS findings_total,"
            " (SELECT COUNT(*) FROM exploration_nodes n WHERE n.exploration_id=e.id"
            "   AND n.kind='fact' AND n.state<>'dismissed') AS facts_total"
            " FROM explorations e ORDER BY e.id DESC LIMIT ?", (limit,))

    def set_task_status(self, task_id: int, status: str) -> None:
        self.x("UPDATE explorations SET status=?, updated_at=? WHERE id=?", (status, now(), task_id))

    # ---------------------------------------------------------------- approvals
    def set_task_mode(self, task_id: int, mode: str) -> None:
        m = "approval" if mode == "approval" else "autonomous"
        self.x("UPDATE explorations SET mode=?, updated_at=? WHERE id=?", (m, now(), task_id))

    def request_approval(self, task_id: int, round_no: int, note: str = "") -> int:
        ts = now()
        with self.lock:
            self.db.execute("UPDATE approvals SET status='timeout', decided_at=?"
                            " WHERE task_id=? AND status='pending'", (ts, task_id))
            self.db.commit()
        return self.x("INSERT INTO approvals(task_id,round_no,status,note,created_at)"
                      " VALUES(?,?,'pending',?,?)", (task_id, round_no, note[:1000], ts))

    def decide_approval(self, task_id: int, decision: str, note: str = "") -> bool:
        status = "approved" if decision == "approve" else "denied"
        with self.lock:
            cur = self.db.execute(
                "UPDATE approvals SET status=?, note=COALESCE(NULLIF(?,''), note), decided_at=?"
                " WHERE task_id=? AND status='pending'", (status, note[:500], now(), task_id))
            self.db.commit()
            return cur.rowcount > 0

    def pending_approval(self, task_id: int) -> dict | None:
        r = self.one("SELECT * FROM approvals WHERE task_id=? AND status='pending'"
                     " ORDER BY id DESC LIMIT 1", (task_id,))
        return dict(r) if r else None

    def rename_task(self, task_id: int, title: str) -> bool:
        with self.lock:
            cur = self.db.execute("UPDATE explorations SET title=?, updated_at=? WHERE id=?",
                                  (title.strip()[:200] or f"task {task_id}", now(), task_id))
            self.db.commit()
            return cur.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """Remove one engagement and everything derived from it. Assets are shared and
        only lose this task id."""
        if not self.get_task(task_id):
            return False
        with self.lock:
            node_ids = [r["id"] for r in self.db.execute(
                "SELECT id FROM exploration_nodes WHERE exploration_id=?", (task_id,))]
            for nid in node_ids:
                self.db.execute("DELETE FROM exploration_anchors WHERE node_id=?", (nid,))
            self.db.execute("DELETE FROM exploration_edges WHERE exploration_id=?", (task_id,))
            self.db.execute("DELETE FROM exploration_nodes WHERE exploration_id=?", (task_id,))
            self.db.execute("DELETE FROM findings WHERE task_id=?", (task_id,))
            self.db.execute("DELETE FROM traffic WHERE task_id=?", (task_id,))
            self.db.execute("DELETE FROM activity WHERE task_id=?", (task_id,))
            self.db.execute("DELETE FROM task_constraints WHERE task_id=?", (task_id,))
            self.db.execute("DELETE FROM task_coverage WHERE task_id=?", (task_id,))
            self.db.execute("DELETE FROM task_scope WHERE task_id=?", (task_id,))
            self.db.execute("DELETE FROM llm_usage WHERE task_id=?", (task_id,))
            self.db.execute("DELETE FROM audit_log WHERE task_id=?", (task_id,))
            self.db.execute("DELETE FROM agent_state WHERE task_id=?", (task_id,))
            self.db.execute("DELETE FROM explorations WHERE id=?", (task_id,))
            for row in self.db.execute("SELECT id, task_ids FROM assets").fetchall():
                ids = jloads(row["task_ids"], [])
                if task_id in ids:
                    ids = [i for i in ids if i != task_id]
                    self.db.execute("UPDATE assets SET task_ids=? WHERE id=?",
                                    (json.dumps(ids), row["id"]))
            self.db.commit()
        return True

    def bump_round(self, task_id: int) -> int:
        self.x("UPDATE explorations SET round_no=round_no+1, updated_at=? WHERE id=?", (now(), task_id))
        row = self.one("SELECT round_no FROM explorations WHERE id=?", (task_id,))
        return int(row["round_no"]) if row else 0

    SCOPE_KINDS = ("domain", "ip", "cidr", "url", "keyword")

    @classmethod
    def normalise_scope(cls, kind: str, value: str) -> tuple[str, str]:
        """Accept 'ip:1.2.3.4', 'kind=value' leftovers and bare values.

        The guard matches on (kind, value), so a value stored with its prefix still
        attached ("ip:192.168.168.98" under kind=domain) silently refuses everything.
        """
        import ipaddress

        kind = (kind or "").strip().lower()
        value = (value or "").strip()
        if ":" in value:
            pre, rest = value.split(":", 1)
            pre = pre.strip().lower()
            if pre in cls.SCOPE_KINDS and rest.strip():
                kind, value = pre, rest.strip()
        if kind not in cls.SCOPE_KINDS or kind == "domain":
            # "domain" is the form default; a bare IP/CIDR/URL is not a domain name.
            low = value.lower()
            if low.startswith("http://") or low.startswith("https://"):
                kind = "url"
            else:
                try:
                    if "/" in low:
                        ipaddress.ip_network(low, strict=False)
                        kind = "cidr"
                    else:
                        ipaddress.ip_address(low)
                        kind = "ip"
                except ValueError:
                    kind = "domain"
        return kind, value

    def add_scope(self, task_id: int, kind: str, value: str, reason: str = "") -> None:
        kind, value = self.normalise_scope(kind, value)
        if not (task_id and kind and value):
            return
        with self.lock:
            self.db.execute(
                "INSERT OR IGNORE INTO task_scope(task_id,kind,value,reason,created_at) VALUES(?,?,?,?,?)",
                (task_id, kind, value.strip().lower(), reason, now()))
            self.db.commit()

    def scope(self, task_id: int) -> list[dict]:
        out = []
        for r in self.q("SELECT kind,value,reason FROM task_scope WHERE task_id=?", (task_id,)):
            kind, value = self.normalise_scope(r["kind"], r["value"])
            out.append({"kind": kind, "value": value, "reason": r["reason"]})
        return out

    def add_constraint(self, task_id: int, kind: str, text: str, origin: str = "planner") -> None:
        self.x("INSERT INTO task_constraints(task_id,kind,text,origin,created_at) VALUES(?,?,?,?,?)",
               (task_id, kind, text, origin, now()))

    def constraints(self, task_id: int) -> list[dict]:
        return [dict(r) for r in self.q("SELECT kind,text FROM task_constraints WHERE task_id=? ORDER BY id", (task_id,))]

    # ---------------------------------------------------------------- nodes
    def add_node(self, task_id: int, kind: str, payload: dict, state: str | None = None,
                 origin: str | None = None, owner: str | None = None,
                 priority: int = 0, asset_ids: list[int] | None = None) -> int:
        if state is None:
            state = {"begin": "open", "goal": "open", "intent": "open", "fact": "confirmed",
                     "finding": "confirmed", "hint": "active", "digest": "active"}[kind]
        ts = now()
        nid = self.x(
            "INSERT INTO exploration_nodes(exploration_id,kind,payload,priority,state,origin,owner,"
            "created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (task_id, kind, json.dumps(payload, ensure_ascii=False), priority, state, origin, owner, ts, ts))
        for aid in asset_ids or []:
            with self.lock:
                self.db.execute("INSERT OR IGNORE INTO exploration_anchors(node_id,asset_id) VALUES(?,?)",
                                (nid, int(aid)))
                self.db.commit()
        return nid

    def node(self, node_id: int) -> sqlite3.Row | None:
        return self.one("SELECT * FROM exploration_nodes WHERE id=?", (node_id,))

    def node_payload(self, node_id: int) -> dict:
        r = self.node(node_id)
        return jloads(r["payload"], {}) if r else {}

    def anchors(self, node_id: int) -> list[int]:
        return [r["asset_id"] for r in self.q("SELECT asset_id FROM exploration_anchors WHERE node_id=?", (node_id,))]

    def anchor(self, node_id: int, asset_id: int) -> None:
        with self.lock:
            self.db.execute("INSERT OR IGNORE INTO exploration_anchors(node_id,asset_id) VALUES(?,?)",
                            (int(node_id), int(asset_id)))
            self.db.commit()

    def add_edge(self, task_id: int, src: int, dst: int, rel: str) -> None:
        if not src or not dst or src == dst:
            return
        with self.lock:
            self.db.execute(
                "INSERT OR IGNORE INTO exploration_edges(exploration_id,src_id,dst_id,rel,created_at)"
                " VALUES(?,?,?,?,?)", (task_id, src, dst, rel, now()))
            self.db.commit()

    def edges_of(self, node_id: int) -> dict:
        up = self.q("SELECT src_id, rel FROM exploration_edges WHERE dst_id=?", (node_id,))
        down = self.q("SELECT dst_id, rel FROM exploration_edges WHERE src_id=?", (node_id,))
        return {"parents": [r["src_id"] for r in up], "children": [r["dst_id"] for r in down]}

    def set_state(self, node_id: int, state: str, reason: str | None = None) -> None:
        ts = now()
        if state in ("done", "blocked", "exhausted", "stopped", "met", "abandoned"):
            self.x("UPDATE exploration_nodes SET state=?, blocked_reason=?, updated_at=?, completed_at=?,"
                   " claim_token=NULL WHERE id=?", (state, reason, ts, ts, node_id))
        else:
            self.x("UPDATE exploration_nodes SET state=?, updated_at=? WHERE id=?",
                   (state, ts, node_id))

    # ---------------------------------------------------------------- intents
    def add_intent(self, task_id: int, summary: str, asset_ids: list[int] | None = None,
                   parent_ids: list[int] | None = None, priority: int = 0) -> int:
        nid = self.add_node(task_id, "intent", {"summary": summary, "asset_ids": asset_ids or []},
                            priority=priority, origin="planner", asset_ids=asset_ids)
        for pid in parent_ids or []:
            self.add_edge(task_id, pid, nid, "spawns")
        return nid

    def claim_intent(self, task_id: int, token: str, lease_s: int) -> sqlite3.Row | None:
        """Atomically claim one open intent (or steal an expired one)."""
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                cutoff = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - lease_s))
                row = self.db.execute(
                    "SELECT * FROM exploration_nodes WHERE exploration_id=? AND kind='intent'"
                    " AND (state='open' OR (state='running' AND (heartbeat_at IS NULL OR heartbeat_at < ?)))"
                    " ORDER BY priority DESC, id ASC LIMIT 1", (task_id, cutoff)).fetchone()
                if row is None:
                    self.db.execute("COMMIT")
                    return None
                self.db.execute(
                    "UPDATE exploration_nodes SET state='running', claim_token=?, heartbeat_at=?,"
                    " owner=?, updated_at=? WHERE id=?",
                    (token, now(), token[:8], now(), row["id"]))
                self.db.execute("COMMIT")
                return self.node(row["id"])
            except Exception:
                self.db.execute("ROLLBACK")
                raise

    def heartbeat(self, node_id: int, token: str) -> None:
        self.x("UPDATE exploration_nodes SET heartbeat_at=? WHERE id=? AND claim_token=?",
               (now(), node_id, token))

    def pending_intents(self, task_id: int) -> int:
        r = self.one("SELECT COUNT(*) c FROM exploration_nodes WHERE exploration_id=? AND kind='intent'"
                     " AND state IN ('open','running','paused')", (task_id,))
        return int(r["c"]) if r else 0

    def open_intents(self, task_id: int, limit: int = 20) -> list[dict]:
        rows = self.q("SELECT * FROM exploration_nodes WHERE exploration_id=? AND kind='intent'"
                      " AND state IN ('open','running','paused') ORDER BY priority DESC, id LIMIT ?",
                      (task_id, limit))
        return [self._node_view(r) for r in rows]

    def recent_done(self, task_id: int, limit: int = 12) -> list[dict]:
        rows = self.q("SELECT * FROM exploration_nodes WHERE exploration_id=? AND kind='intent'"
                      " AND state IN ('done','blocked','exhausted','stopped') ORDER BY id DESC LIMIT ?",
                      (task_id, limit))
        return [self._node_view(r) for r in rows]

    def _node_view(self, r: sqlite3.Row) -> dict:
        p = jloads(r["payload"], {})
        created, completed = r["created_at"], r["completed_at"]
        took = seconds_between(created, completed) if completed else \
            seconds_between(created, now())
        return {"id": r["id"], "kind": r["kind"], "state": r["state"],
                "summary": p.get("summary") or p.get("text") or p.get("goal") or "",
                "asset_ids": self.anchors(r["id"]), "priority": r["priority"],
                "created_at": created, "started": local_hms(created),
                "completed_at": completed, "finished": local_hms(completed),
                "took_s": took, "running": completed is None and r["state"] == "running",
                "blocked_reason": r["blocked_reason"]}

    # ---------------------------------------------------------------- goals
    def goals(self, task_id: int) -> list[dict]:
        rows = self.q("SELECT * FROM exploration_nodes WHERE exploration_id=? AND kind='goal' ORDER BY id",
                      (task_id,))
        out = []
        for r in rows:
            p = jloads(r["payload"], {})
            out.append({"id": r["id"], "state": r["state"], "text": p.get("text", ""),
                        "reason": p.get("reason"), "evidence_id": p.get("evidence_id")})
        return out

    def goal_met(self, task_id: int) -> bool:
        gs = self.goals(task_id)
        return bool(gs) and all(g["state"] == "met" for g in gs)

    # ---------------------------------------------------------------- facts / findings
    def add_fact(self, task_id: int, summary: str, detail: str = "", source: str = "inference",
                 confidence: str = "inferred", intent_id: int | None = None,
                 evidence: str = "", asset_ids: list[int] | None = None) -> int:
        nid = self.add_node(task_id, "fact",
                            {"summary": summary, "detail": detail, "source": source,
                             "confidence": confidence, "evidence": evidence},
                            origin=str(intent_id or ""), asset_ids=asset_ids)
        if intent_id:
            self.add_edge(task_id, intent_id, nid, "yields")
        return nid

    def add_finding(self, task_id: int, vulnclass: str, severity: str, summary: str,
                    evidence: str, poc: str = "", asset_id: int | None = None,
                    endpoint: str = "", parameter: str = "", confidence: str = "observed",
                    proof_basis: str = "executed-live", counterevidence: str = "",
                    traffic_refs: list[int] | None = None, intent_id: int | None = None) -> tuple[int, int]:
        nid = self.add_node(task_id, "finding",
                            {"summary": summary, "vulnclass": vulnclass, "severity": severity,
                             "evidence": evidence, "poc": poc, "confidence": confidence,
                             "proof_basis": proof_basis, "traffic_refs": traffic_refs or []},
                            origin=str(intent_id or ""), asset_ids=[asset_id] if asset_id else None)
        if intent_id:
            self.add_edge(task_id, intent_id, nid, "yields")
        fid = self.x(
            "INSERT INTO findings(task_id,node_id,vulnclass,severity,asset_id,endpoint,parameter,summary,"
            "evidence,poc,counterevidence,confidence,proof_basis,traffic_refs,status,created_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,'open',?)",
            (task_id, nid, vulnclass, severity, asset_id, endpoint, parameter, summary, evidence, poc,
             counterevidence, confidence, proof_basis, json.dumps(traffic_refs or []), now()))
        return nid, fid

    def duplicate_finding(self, task_id: int, vulnclass: str, endpoint: str, parameter: str) -> sqlite3.Row | None:
        return self.one(
            "SELECT * FROM findings WHERE task_id=? AND lower(vulnclass)=lower(?) AND endpoint=? AND parameter=?"
            " AND status NOT IN ('false_positive','duplicate','ignored')",
            (task_id, vulnclass, endpoint or "", parameter or ""))

    def findings(self, task_id: int, only_active: bool = True) -> list[dict]:
        sql = "SELECT * FROM findings WHERE task_id=?"
        if only_active:
            sql += " AND status NOT IN ('false_positive','duplicate','ignored')"
        sql += " ORDER BY id DESC"
        out = []
        for r in self.q(sql, (task_id,)):
            d = dict(r)
            d["traffic_refs"] = jloads(d.get("traffic_refs"), [])
            d["at_local"] = local_hms(d.get("created_at"))
            out.append(d)
        return out

    def list_facts(self, task_id: int, limit: int = 20, q: str = "") -> list[dict]:
        args: list[Any] = [task_id]
        sql = ("SELECT * FROM exploration_nodes WHERE exploration_id=? AND kind='fact'"
               " AND state<>'dismissed'")
        if q:
            sql += " AND payload LIKE ?"
            args.append(f"%{q}%")
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        out = []
        for r in self.q(sql, args):
            p = jloads(r["payload"], {})
            out.append({"id": r["id"], "summary": p.get("summary", ""), "source": p.get("source"),
                        "confidence": p.get("confidence"), "from_intent": p.get("from_intent") or r["origin"],
                        "created_at": r["created_at"],
                        "at_local": local_hms(r["created_at"])})
        return out

    # ---------------------------------------------------------------- assets
    @staticmethod
    def _ukey(a: dict) -> str:
        t = a.get("type", "")
        if t in ("root_domain",):
            return (a.get("domain") or "").lower()
        if t == "ip":
            return (a.get("ip") or "")
        if t == "subdomain":
            return f"{a.get('domain','').lower()}|{a.get('record_type') or ''}"
        if t == "app":
            return (a.get("bundle_id") or a.get("app_name") or "").lower()
        if t == "service":
            if (a.get("service_type") or "http") == "http":
                return (a.get("url") or "").rstrip("/")
            return f"{a.get('domain') or ''}|{a.get('ip') or ''}|{a.get('port') or 0}|{a.get('service_name') or ''}"
        if t == "endpoint":
            return f"{(a.get('url') or '').rstrip('/')}|{(a.get('method') or 'GET').upper()}"
        return (a.get("url") or a.get("domain") or a.get("ip") or "").lower()

    def add_asset(self, task_id: int, a: dict) -> int:
        t = a.get("type") or "service"
        ukey = self._ukey({**a, "type": t})
        if not ukey.strip("|"):
            return 0
        ts = now()
        with self.lock:
            row = self.db.execute("SELECT * FROM assets WHERE type=? AND ukey=?", (t, ukey)).fetchone()
            techs = list(a.get("technologies") or [])
            params = list(a.get("params") or [])
            if row is None:
                aid = self.x(
                    "INSERT INTO assets(type,ukey,domain,root_domain,ip,port,url,service_type,service_name,"
                    "status_code,content_length,page_title,technologies,params,auth,extra,task_ids,"
                    "first_seen,last_seen) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (t, ukey, a.get("domain"), a.get("root_domain"), a.get("ip"), a.get("port"),
                     a.get("url"), a.get("service_type"), a.get("service_name"), a.get("status_code"),
                     a.get("content_length"), a.get("page_title"), json.dumps(techs),
                     json.dumps(params), json.dumps(a.get("auth") or []),
                     json.dumps(a.get("extra") or {}), json.dumps([task_id]), ts, ts))
                return aid
            aid = int(row["id"])
            merged_techs = list(dict.fromkeys(jloads(row["technologies"], []) + techs))
            merged_params = list(dict.fromkeys(jloads(row["params"], []) + params))
            task_ids = list(dict.fromkeys(jloads(row["task_ids"], []) + [task_id]))
            self.db.execute(
                "UPDATE assets SET domain=COALESCE(?,domain), root_domain=COALESCE(?,root_domain),"
                " ip=COALESCE(?,ip), port=COALESCE(?,port), url=COALESCE(?,url),"
                " service_type=COALESCE(?,service_type), service_name=COALESCE(?,service_name),"
                " status_code=COALESCE(?,status_code), content_length=COALESCE(?,content_length),"
                " page_title=COALESCE(?,page_title), technologies=?, params=?, extra=?, task_ids=?, last_seen=?"
                " WHERE id=?",
                (a.get("domain"), a.get("root_domain"), a.get("ip"), a.get("port"), a.get("url"),
                 a.get("service_type"), a.get("service_name"), a.get("status_code"),
                 a.get("content_length"), a.get("page_title"), json.dumps(merged_techs),
                 json.dumps(merged_params), json.dumps({**jloads(row["extra"], {}), **(a.get("extra") or {})}),
                 json.dumps(task_ids), ts, aid))
            self.db.commit()
            return aid

    def assets(self, task_id: int | None = None, type: str = "", q: str = "", limit: int = 100) -> list[dict]:
        sql = "SELECT * FROM assets WHERE 1=1"
        args: list[Any] = []
        if task_id is not None:
            sql += " AND task_ids LIKE ?"
            args.append(f"%{task_id}%")
        if type:
            sql += " AND type=?"
            args.append(type)
        if q:
            sql += " AND (id=? OR domain LIKE ? OR url LIKE ? OR ip LIKE ? OR technologies LIKE ? OR page_title LIKE ?)"
            args += [int(q) if q.isdigit() else -1, f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"]
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        out = []
        for r in self.q(sql, args):
            d = dict(r)
            for k in ("technologies", "params", "auth", "task_ids"):
                d[k] = jloads(d.get(k), [])
            d["extra"] = jloads(d.get("extra"), {})
            out.append(d)
        return out

    def asset(self, asset_id: int) -> dict | None:
        r = self.one("SELECT * FROM assets WHERE id=?", (asset_id,))
        if not r:
            return None
        d = dict(r)
        for k in ("technologies", "params", "auth", "task_ids"):
            d[k] = jloads(d.get(k), [])
        d["extra"] = jloads(d.get("extra"), {})
        return d

    def asset_counts(self, task_id: int | None = None) -> dict:
        sql = "SELECT type, COUNT(*) c FROM assets"
        args: list[Any] = []
        if task_id is not None:
            sql += " WHERE task_ids LIKE ?"
            args.append(f"%{task_id}%")
        sql += " GROUP BY type"
        return {r["type"]: int(r["c"]) for r in self.q(sql, args)}

    def mark_tested(self, task_id: int, asset_ids: Iterable[int]) -> None:
        ts = now()
        with self.lock:
            for aid in asset_ids:
                self.db.execute("INSERT OR IGNORE INTO task_coverage(task_id,asset_id,tested_at)"
                                " VALUES(?,?,?)", (task_id, int(aid), ts))
            self.db.commit()

    def coverage(self, task_id: int) -> dict:
        total = self.one("SELECT COUNT(*) c FROM assets WHERE task_ids LIKE ?", (f"%{task_id}%",))
        tested = self.one("SELECT COUNT(*) c FROM task_coverage WHERE task_id=?", (task_id,))
        t = int(total["c"]) if total else 0
        d = int(tested["c"]) if tested else 0
        return {"assets": t, "tested": d, "pct": round(100.0 * d / t, 1) if t else 0.0}

    # ---------------------------------------------------------------- traffic
    def add_traffic(self, task_id: int, method: str, url: str, status: int,
                    req_headers: dict, req_body: str, resp_headers: dict, resp_body: str) -> int:
        return self.x("INSERT INTO traffic(task_id,method,url,status,req_headers,req_body,resp_headers,"
                      "resp_body,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                      (task_id, method, url, status, json.dumps(req_headers), (req_body or "")[:200000],
                       json.dumps(resp_headers), (resp_body or "")[:200000], now()))

    def traffic(self, traffic_id: int) -> dict | None:
        r = self.one("SELECT * FROM traffic WHERE id=?", (traffic_id,))
        return dict(r) if r else None

    def traffic_search(self, task_id: int, host: str = "", limit: int = 10) -> list[dict]:
        if host:
            return [dict(r) for r in self.q(
                "SELECT id,method,url,status,length(resp_body) rlen FROM traffic WHERE task_id=? AND url LIKE ?"
                " ORDER BY id DESC LIMIT ?", (task_id, f"%{host}%", limit))]
        return [dict(r) for r in self.q(
            "SELECT id,method,url,status,length(resp_body) rlen FROM traffic WHERE task_id=?"
            " ORDER BY id DESC LIMIT ?", (task_id, limit))]

    # ---------------------------------------------------------------- activity / audit
    def log(self, task_id: int, worker: str, kind: str, summary: str, tool: str = "",
            node_id: int | None = None, detail: str = "", metadata: dict | None = None,
            tokens_in: int = 0, tokens_out: int = 0) -> int:
        return self.x("INSERT INTO activity(task_id,node_id,worker,kind,tool,summary,detail,metadata,"
                      "tokens_in,tokens_out,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                      (task_id, node_id, worker, kind, tool, summary[:4000], detail[:20000],
                       json.dumps(metadata or {}), tokens_in, tokens_out, now()))

    def activity(self, task_id: int, limit: int = 50) -> list[dict]:
        """Oldest -> newest, each row carrying local wall-clock time and the seconds
        since the previous row (so a trace reads like a timeline)."""
        rows = list(reversed(self.q(
            "SELECT * FROM activity WHERE task_id=? ORDER BY id DESC LIMIT ?", (task_id, limit))))
        out, prev = [], None
        for r in rows:
            d = dict(r)
            d["at"] = d["created_at"]
            d["at_local"] = local_hms(d["created_at"])
            d["date_local"] = local_hms(d["created_at"], with_date=True)
            d["delta_s"] = seconds_between(prev, d["created_at"]) if prev else None
            prev = d["created_at"]
            out.append(d)
        return out

    def audit(self, task_id: int, worker: str, tool: str, action: str, reason: str = "",
              command: str = "") -> None:
        self.x("INSERT INTO audit_log(task_id,worker,tool,action,reason,command,created_at)"
               " VALUES(?,?,?,?,?,?,?)", (task_id, worker, tool, action, reason[:2000], command[:4000], now()))

    def usage(self, task_id: int, agent: str, model: str, tokens_in: int, tokens_out: int) -> None:
        self.x("INSERT INTO llm_usage(task_id,agent,model,tokens_in,tokens_out,created_at)"
               " VALUES(?,?,?,?,?,?)", (task_id, agent, model, tokens_in, tokens_out, now()))

    def usage_totals(self, task_id: int) -> dict:
        r = self.one("SELECT COALESCE(SUM(tokens_in),0) ti, COALESCE(SUM(tokens_out),0) to_"
                     " FROM llm_usage WHERE task_id=?", (task_id,))
        return {"tokens_in": int(r["ti"]) if r else 0, "tokens_out": int(r["to_"]) if r else 0}

    # ---------------------------------------------------------------- skills
    def upsert_skill(self, name: str, description: str, path: str, frontmatter: dict) -> None:
        with self.lock:
            self.db.execute(
                "INSERT INTO skills(name,description,path,frontmatter,enabled) VALUES(?,?,?,?,1)"
                " ON CONFLICT(name) DO UPDATE SET description=excluded.description,"
                " path=excluded.path, frontmatter=excluded.frontmatter",
                (name, description, path, json.dumps(frontmatter)))
            self.db.commit()

    def skill_list(self) -> list[dict]:
        return [dict(r) for r in self.q("SELECT * FROM skills WHERE enabled=1 ORDER BY name")]

    # ---------------------------------------------------------------- overview
    def graph_overview(self, task_id: int) -> dict:
        t = self.get_task(task_id)
        goals = self.goals(task_id)
        open_i = self.open_intents(task_id)
        running = [i for i in open_i if i["state"] == "running"]
        done = self.recent_done(task_id)
        facts_total = self.one("SELECT COUNT(*) c FROM exploration_nodes WHERE exploration_id=?"
                               " AND kind='fact' AND state<>'dismissed'", (task_id,))
        recent_facts = self.list_facts(task_id, limit=12)
        for f in recent_facts:
            f.pop("created_at", None)
        findings_total = len(self.findings(task_id))
        cov = self.coverage(task_id)
        hints = [{"id": r["id"], "text": jloads(r["payload"], {}).get("text", "")} for r in
                 self.q("SELECT * FROM exploration_nodes WHERE exploration_id=? AND kind='hint'"
                        " AND state='active' ORDER BY id", (task_id,))]
        return {
            "task_id": task_id,
            "title": t["title"] if t else "",
            "goal": t["goal"] if t else "",
            "status": t["status"] if t else "",
            "round": t["round_no"] if t else 0,
            "assets": self.asset_counts(task_id),
            "goals": goals,
            "open_intents": [i for i in open_i if i["state"] != "running"],
            "running_intents": running,
            "recent_done": done,
            "frontier_open": len([i for i in open_i if i["state"] == "open"]),
            "facts_total": int(facts_total["c"]) if facts_total else 0,
            "recent_facts": recent_facts,
            "findings_total": findings_total,
            "coverage": cov,
            "hints": hints,
            "constraints": self.constraints(task_id),
            "scope": self.scope(task_id),
            "workdir": (t["workdir"] if t else "") or "",
        }

    def node_detail(self, node_id: int) -> dict | None:
        r = self.node(node_id)
        if not r:
            return None
        d = dict(r)
        d["payload"] = jloads(d["payload"], {})
        d["anchors"] = self.anchors(node_id)
        d["edges"] = self.edges_of(node_id)
        return d

    def close(self) -> None:
        with self.lock:
            self.db.close()

    # ---------------------------------------------------------------- enumeration view
    def enumeration(self, task_id: int) -> dict:
        """Human-readable enumeration record: hosts -> services -> endpoints, with the
        observations (facts) attached to each host, newest last."""
        from urllib.parse import urlparse

        def host_of(url: str) -> str:
            try:
                return (urlparse(url).hostname or "").lower()
            except ValueError:
                return ""

        assets = self.assets(task_id, limit=1000)
        facts = [dict(r) for r in self.q(
            "SELECT * FROM exploration_nodes WHERE exploration_id=? AND kind='fact'"
            " AND state<>'dismissed' ORDER BY id", (task_id,))]
        fact_anchor = {}
        for f in facts:
            ids = self.anchors(f["id"])
            fact_anchor[f["id"]] = ids

        hosts: dict[str, dict] = {}

        def host(key: str) -> dict:
            key = key or "(unattached)"
            return hosts.setdefault(key, {"key": key, "ip": "", "domain": "",
                                          "services": [], "endpoints": [],
                                          "observations": []})

        for a in assets:
            h = ""
            if a["type"] == "ip":
                h = a["ip"] or ""
            elif a["type"] in ("root_domain", "subdomain"):
                h = a["domain"] or ""
            elif a["type"] in ("service", "endpoint"):
                h = host_of(a.get("url") or "") or a.get("ip") or a.get("domain") or ""
            elif a["type"] == "app":
                h = a.get("domain") or ""
            if not h:
                continue
            rec = host(h)
            rec["ip"] = rec["ip"] or (a.get("ip") or "")
            rec["domain"] = rec["domain"] or (a.get("domain") or "")
            if a["type"] == "service":
                rec["services"].append({
                    "id": a["id"], "url": a.get("url") or "", "status": a.get("status_code"),
                    "title": a.get("page_title") or "", "service": a.get("service_name") or "",
                    "tech": a.get("technologies") or [], "port": a.get("port"),
                })
            elif a["type"] == "endpoint":
                rec["endpoints"].append({
                    "id": a["id"], "url": a.get("url") or "", "status": a.get("status_code"),
                    "params": a.get("params") or [], "method": a.get("extra", {}).get("method", ""),
                })

        for f in facts:
            payload = jloads(f["payload"], {})
            entry = {"id": f["id"], "summary": payload.get("summary", ""),
                     "detail": payload.get("detail", ""), "source": payload.get("source", ""),
                     "confidence": payload.get("confidence", ""),
                     "evidence": payload.get("evidence", ""),
                     "at": f["created_at"], "intent": f["origin"] or ""}
            placed = False
            for aid in fact_anchor.get(f["id"], []):
                a = self.asset(int(aid))
                if not a:
                    continue
                h = ""
                if a["type"] in ("service", "endpoint"):
                    h = host_of(a.get("url") or "") or a.get("ip") or ""
                elif a["type"] == "ip":
                    h = a["ip"] or ""
                else:
                    h = a.get("domain") or ""
                if h:
                    host(h)["observations"].append(entry)
                    placed = True
                    break
            if not placed:
                hosts.setdefault("(unattached)", {"key": "(unattached)", "ip": "",
                                                 "domain": "", "services": [],
                                                 "endpoints": [], "observations": []}
                              )["observations"].append(entry)

        out = []
        for key, h in hosts.items():
            if not (h["services"] or h["endpoints"] or h["observations"]):
                continue
            h["services"].sort(key=lambda s: (s["url"] or ""))
            h["endpoints"].sort(key=lambda e: (e["url"] or ""))
            for svc in h["services"]:
                base = svc["url"].rstrip("/")
                svc["endpoints"] = [e for e in h["endpoints"]
                                    if e["url"].rstrip("/").startswith(base)]
            attached = {id(e) for s in h["services"] for e in s["endpoints"]}
            h["loose_endpoints"] = [e for e in h["endpoints"] if id(e) not in attached]
            out.append(h)
        out.sort(key=lambda h: (h["key"] == "(unattached)", h["key"]))
        return {
            "hosts": out,
            "counts": {
                "hosts": len([h for h in out if h["key"] != "(unattached)"]),
                "services": sum(len(h["services"]) for h in out),
                "endpoints": sum(len(h["endpoints"]) for h in out),
                "observations": len(facts),
            },
            "facts": [{"id": f["id"], "summary": jloads(f["payload"], {}).get("summary", ""),
                       "source": jloads(f["payload"], {}).get("source", ""),
                       "confidence": jloads(f["payload"], {}).get("confidence", ""),
                       "at": f["created_at"]} for f in facts],
        }

    # ---------------------------------------------------------------- views
    def timeline(self, task_id: int, limit: int = 400) -> list[dict]:
        """Every intent with start/finish/duration, for the Gantt strip."""
        out = []
        for r in self.q("SELECT id,state,payload,created_at,completed_at,owner,priority"
                        " FROM exploration_nodes WHERE exploration_id=? AND kind='intent'"
                        " ORDER BY id LIMIT ?", (task_id, limit)):
            p = jloads(r["payload"], {})
            finished = r["completed_at"]
            out.append({
                "id": r["id"], "state": r["state"], "summary": p.get("summary", ""),
                "started_at": r["created_at"], "finished_at": finished,
                "started": local_hms(r["created_at"]), "finished": local_hms(finished),
                "took_s": seconds_between(r["created_at"], finished or now()),
                "worker": r["owner"] or "",
            })
        return out

    def coverage_detail(self, task_id: int) -> dict:
        total = self.q("SELECT id,type,url,domain,ip FROM assets WHERE task_ids LIKE ?",
                       (f"%{task_id}%",))
        tested = {r["asset_id"] for r in self.q(
            "SELECT asset_id FROM task_coverage WHERE task_id=?", (task_id,))}
        untested = [dict(r) for r in total if r["id"] not in tested]
        return {"assets": len(total), "tested": len(tested),
                "pct": round(100.0 * len(tested) / len(total), 1) if total else 0.0,
                "untested": untested[:80]}

    # ---------------------------------------------------------------- settings
    def get_setting(self, key: str, default: str = "") -> str:
        r = self.one("SELECT value FROM settings WHERE key=?", (key,))
        return r["value"] if r and r["value"] is not None else default

    def set_setting(self, key: str, value: str) -> None:
        with self.lock:
            self.db.execute(
                "INSERT INTO settings(key,value,updated_at) VALUES(?,?,?)"
                " ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (key, str(value), now()))
            self.db.commit()

    def settings(self) -> dict:
        return {r["key"]: r["value"] for r in self.q("SELECT key,value FROM settings")}

    # ---------------------------------------------------------------- graph / traffic views
    def graph_data(self, task_id: int) -> dict:
        nodes = []
        for r in self.q("SELECT id,kind,payload,state,priority,created_at,completed_at"
                        " FROM exploration_nodes WHERE exploration_id=? ORDER BY id", (task_id,)):
            p = jloads(r["payload"], {})
            nodes.append({"id": r["id"], "kind": r["kind"], "state": r["state"],
                          "label": (p.get("summary") or p.get("text") or p.get("goal") or "")[:120],
                          "priority": r["priority"], "created_at": r["created_at"]})
        edges = [dict(r) for r in self.q(
            "SELECT src_id AS src, dst_id AS dst, rel FROM exploration_edges"
            " WHERE exploration_id=?", (task_id,))]
        return {"nodes": nodes, "edges": edges}

    def traffic_list(self, task_id: int, q: str = "", limit: int = 50) -> list[dict]:
        sql = ("SELECT id,method,url,status,length(resp_body) AS rlen,created_at"
               " FROM traffic WHERE task_id=?")
        args: list[Any] = [task_id]
        if q:
            sql += " AND (url LIKE ? OR resp_body LIKE ?)"
            args += [f"%{q}%", f"%{q}%"]
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(max(1, min(int(limit), 200)))
        return [dict(r) for r in self.q(sql, args)]

    def set_finding_status(self, finding_id: int, status: str) -> bool:
        allowed = {"open", "confirmed", "false_positive", "duplicate", "ignored"}
        if status not in allowed:
            return False
        with self.lock:
            cur = self.db.execute("UPDATE findings SET status=? WHERE id=?", (status, finding_id))
            self.db.commit()
            return cur.rowcount > 0

    def agent_usage(self, task_id: int) -> list[dict]:
        return [dict(r) for r in self.q(
            "SELECT agent, COUNT(*) calls, SUM(tokens_in) tin, SUM(tokens_out) tout"
            " FROM llm_usage WHERE task_id=? GROUP BY agent ORDER BY agent", (task_id,))]

    # ---------------------------------------------------------------- live agents
    def agent_upsert(self, key: str, task_id: int, **f) -> None:
        t = time.time()
        with self.lock:
            row = self.db.execute("SELECT started, turns, tokens_in, tokens_out"
                                  " FROM agent_state WHERE key=?", (key,)).fetchone()
            if row is None:
                self.db.execute(
                    "INSERT INTO agent_state(key,task_id,role,intent,state,tool,note,model,"
                    "turns,tokens_in,tokens_out,started,updated)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (key, task_id, f.get("role"), f.get("intent"), f.get("state"),
                     f.get("tool"), (f.get("note") or "")[:400], f.get("model"),
                     int(f.get("turns") or 0), int(f.get("tokens_in") or 0),
                     int(f.get("tokens_out") or 0), t, t))
            else:
                self.db.execute(
                    "UPDATE agent_state SET state=COALESCE(?,state), tool=COALESCE(?,tool),"
                    " note=COALESCE(?,note), intent=COALESCE(?,intent),"
                    " turns=turns+?, tokens_in=tokens_in+?, tokens_out=tokens_out+?,"
                    " model=COALESCE(?,model), updated=? WHERE key=?",
                    (f.get("state"), f.get("tool"), (f.get("note") or None),
                     f.get("intent"), int(f.get("turn") or 0) if f.get("turn") else
                     int(f.get("turns") or 0),
                     int(f.get("tokens_in") or 0), int(f.get("tokens_out") or 0),
                     f.get("model"), t, key))
            self.db.commit()

    def agent_drop(self, key: str) -> None:
        with self.lock:
            self.db.execute("DELETE FROM agent_state WHERE key=?", (key,))
            self.db.commit()

    def agents(self, task_id: int = 0) -> list[dict]:
        sql = "SELECT * FROM agent_state"
        args: tuple = ()
        if task_id:
            sql += " WHERE task_id=?"
            args = (task_id,)
        now = time.time()
        out = []
        for r in self.q(sql, args):
            d = dict(r)
            d["elapsed_s"] = int(now - (d.get("started") or now))
            d["idle_s"] = int(now - (d.get("updated") or now))
            if d["idle_s"] > 120 and d.get("state") not in ("idle", "stale"):
                d["state"] = "stale"
            out.append(d)
        return sorted(out, key=lambda x: (x.get("role") != "planner", x.get("key", "")))
