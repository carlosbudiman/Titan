"""Tool catalog: specs (OpenAI function schema) + handlers.

Handlers receive a Ctx and return a string. The engine runs Guard.check() before
any handler, so handlers can assume the call was authorised.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MAX_OUT = 20000


def _trunc(s: str, n: int = MAX_OUT) -> str:
    s = s or ""
    if len(s) <= n:
        return s
    return s[: n // 2] + f"\n…[{len(s) - n} chars truncated]…\n" + s[-n // 2:]


def _j(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1)


@dataclass
class Ctx:
    store: object
    settings: object
    task_id: int
    agent: str
    worker: str
    workdir: Path
    guard: object
    pacer: object
    runtime: object = None
    skills: object = None
    node_id: int = 0


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable

    def spec(self) -> dict:
        return {"type": "function", "function": {"name": self.name,
                                                 "description": self.description,
                                                 "parameters": self.parameters}}


def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required or []}


S = {"type": "string"}
I = {"type": "integer"}
B = {"type": "boolean"}
A = {"type": "array", "items": S}


class Registry:
    def __init__(self, skills):
        self.skills = skills
        self.tools: dict[str, Tool] = {}
        self._build()

    # ------------------------------------------------------------------ setup
    def add(self, name: str, desc: str, params: dict, fn: Callable) -> None:
        self.tools[name] = Tool(name, desc, params, fn)

    def _build(self) -> None:
        add = self.add

        # ---- shell / files
        add("bash",
            "Run a shell command inside the task working directory. Use for scanners "
            "(nmap, httpx, nuclei, ffuf), curl and one-off probes. Commands are rate "
            "limited by platform policy; destructive or out-of-scope commands are blocked.",
            _obj({"command": S, "timeout": I}, ["command"]), t_bash)
        add("webfetch",
            "Fetch one HTTP(S) URL. Response is stored as traffic evidence and can be "
            "cited by report_finding(traffic_refs). Paced per host.",
            _obj({"url": S, "method": S, "headers": {"type": "object"},
                  "body": S, "timeout": I}, ["url"]), t_webfetch)
        add("read_file", "Read a text file from the task work directory.",
            _obj({"path": S, "offset": I, "limit": I}, ["path"]), t_read_file)
        add("write_file", "Write a text file inside the task work directory (overwrites).",
            _obj({"path": S, "content": S}, ["path", "content"]), t_write_file)
        add("edit_file", "Replace one exact substring in a file inside the work directory.",
            _obj({"path": S, "old": S, "new": S}, ["path", "old", "new"]), t_edit_file)
        add("ls", "List a directory inside the work directory.",
            _obj({"path": S}), t_ls)
        add("grep", "Regex search across files under the work directory.",
            _obj({"pattern": S, "path": S, "limit": I}, ["pattern"]), t_grep)

        # ---- asset graph
        add("insert_assets",
            "Register assets in the global asset graph (graph 1). Assets are things that "
            "exist: root_domain, ip, subdomain, app, service, endpoint. Not conclusions.",
            _obj({"items": {"type": "array", "items": {"type": "object"}}}, ["items"]),
            t_insert_assets)
        add("list_assets",
            "Query the asset graph (search by id/domain/url/ip/technology, filter by type).",
            _obj({"q": S, "type": S, "limit": I, "task_only": B}), t_list_assets)
        add("list_untested_assets",
            "List in-scope assets of this task that have no completed intent yet.",
            _obj({"type": S, "limit": I}), t_list_untested)
        add("add_task_scope",
            "Add an authorized target (domain/ip/cidr/url/keyword) to this task's scope.",
            _obj({"kind": S, "value": S, "reason": S}, ["kind", "value"]), t_add_scope)

        # ---- exploration graph
        add("graph_overview", "Read the whole task graph summary (goals, intents, facts, "
                              "findings, coverage). Usually already attached to your prompt.",
            _obj({}), lambda c: _j(c.store.graph_overview(c.task_id)))
        add("list_facts", "List exploration facts (newest first), optional substring filter.",
            _obj({"limit": I, "q": S}), t_list_facts)
        add("list_findings", "List findings recorded in this task.",
            _obj({}), t_list_findings)
        add("node_detail", "Full payload, anchors and edges of one exploration node.",
            _obj({"id": I}, ["id"]), t_node_detail)
        add("record_fact",
            "Record one exploration conclusion/fact in graph 2. Merge related observations "
            "into ONE fact (summary + detail). Declare the source of the content.",
            _obj({
                "summary": S,
                "detail": S,
                "source": {"type": "string", "enum": ["target_response", "tool_output",
                                                      "third_party_intel", "operator_input",
                                                      "inference"]},
                "confidence": {"type": "string", "enum": ["observed", "inferred"]},
                "evidence": S,
                "intent_id": I,
                "asset_ids": {"type": "array", "items": I},
            }, ["summary"]), t_record_fact)
        add("report_finding",
            "Report a CONFIRMED vulnerability with reproducible evidence. Requires evidence "
            "from an actual trigger in this run; version/CVE matching is not a finding. "
            "Duplicates of the same class+endpoint+parameter are refused.",
            _obj({
                "vulnclass": S, "severity": {"type": "string",
                                             "enum": ["critical", "high", "medium", "low", "info"]},
                "summary": S, "evidence": S, "poc": S,
                "asset_id": I, "endpoint": S, "parameter": S,
                "confidence": {"type": "string", "enum": ["observed", "inferred"]},
                "proof_basis": {"type": "string", "enum": ["executed-live", "executed-lab",
                                                           "static-analysis-unexecuted"]},
                "counterevidence": S,
                "traffic_refs": {"type": "array", "items": I},
                "intent_id": I,
            }, ["vulnclass", "severity", "summary", "evidence"]), t_report_finding)

        # ---- planner-only control
        add("add_intent",
            "Dispatch exploration intents (max 4 per call). One sentence each: full target + "
            "what to do + why. Do not duplicate open/running intents.",
            _obj({"intents": {"type": "array", "maxItems": 4, "items": {
                "type": "object",
                "properties": {"summary": S, "asset_ids": {"type": "array", "items": I},
                               "parent_ids": {"type": "array", "items": I},
                               "priority": I},
                "required": ["summary"]}}}, ["intents"]), t_add_intent)
        add("prove_goal", "Mark one goal met, citing a fact/finding id as evidence.",
            _obj({"goal_id": I, "evidence_id": I, "reason": S},
                 ["goal_id", "evidence_id", "reason"]), t_prove_goal)
        add("list_goals", "List goals with state.", _obj({}),
            lambda c: _j(c.store.goals(c.task_id)))
        add("steer_work", "Send a course correction to a running worker (does not stop it).",
            _obj({"intent_id": I, "message": S}, ["intent_id", "message"]), t_steer_work)
        add("kill_work", "Stop a running worker whose whole direction is wrong.",
            _obj({"intent_id": I, "reason": S}, ["intent_id", "reason"]), t_kill_work)
        add("get_worker_trace", "The activity trail of one intent (tool calls + results).",
            _obj({"intent_id": I, "limit": I}, ["intent_id"]), t_worker_trace)
        add("add_hint", "Queue an operator hint for the next planning rounds.",
            _obj({"text": S}, ["text"]), t_add_hint)

        # ---- traffic + skills + operator
        add("traffic_search", "Search recorded HTTP traffic of this task by host substring.",
            _obj({"host": S, "limit": I}), t_traffic_search)
        add("traffic_get", "Read one recorded request/response by id.",
            _obj({"id": I}, ["id"]), t_traffic_get)
        add("read_skill", "Load a skill's full instructions by name (see skill index).",
            _obj({"name": S}, ["name"]), t_read_skill)
        add("ask_operator", "Ask the human operator for the exact command to run when the "
                            "environment (not the target) blocks you.",
            _obj({"question": S, "command": S}, ["question"]), t_ask_operator)

    # ------------------------------------------------------------------ api
    AGENT_TOOLS = {
        "planner": ["graph_overview", "list_facts", "list_findings", "node_detail", "list_goals",
                    "add_intent", "prove_goal", "steer_work", "kill_work", "get_worker_trace",
                    "list_assets", "insert_assets", "add_hint", "add_task_scope",
                    "list_untested_assets", "read_skill", "bash", "webfetch"],
        "worker": ["bash", "webfetch", "read_file", "write_file", "edit_file", "ls", "grep",
                   "insert_assets", "list_assets", "record_fact", "report_finding",
                   "list_findings", "node_detail", "traffic_search", "traffic_get",
                   "read_skill", "ask_operator"],
        "main": ["graph_overview", "list_facts", "list_findings", "node_detail", "list_assets",
                 "add_hint", "read_skill", "bash", "webfetch"],
    }

    def specs(self, agent: str) -> list[dict]:
        return [self.tools[n].spec() for n in self.AGENT_TOOLS.get(agent, []) if n in self.tools]

    def call(self, name: str, args: dict, ctx: Ctx) -> tuple[str, bool]:
        tool = self.tools.get(name)
        if not tool:
            return f"ERROR: unknown tool {name}", True
        try:
            return tool.handler(ctx, **(args or {})), False
        except TypeError as e:
            return f"ERROR: bad arguments for {name}: {e}", True
        except Exception as e:  # noqa: BLE001 - tool errors must not kill the loop
            return f"ERROR: {type(e).__name__}: {e}", True


# ====================================================================== shell / files
def t_bash(c: Ctx, command: str, timeout: int = 180) -> str:
    timeout = max(1, min(int(timeout or 180), 900))
    env = dict(os.environ)
    env.update({"TITAN_TASK": str(c.task_id), "TITAN_AGENT": c.agent,
                "TITAN_UA": c.settings.user_agent})
    try:
        p = subprocess.run(command, shell=True, cwd=str(c.workdir), capture_output=True,
                           text=True, timeout=timeout, env=env)
        out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr else "")
        c.store.log(c.task_id, c.worker, "tool_result", f"bash exit={p.returncode}",
                    tool="bash", detail=out[:4000], node_id=None)
        return _trunc(f"exit={p.returncode}\n{out}")
    except subprocess.TimeoutExpired:
        return f"ERROR: command timed out after {timeout}s"


def _safe_path(c: Ctx, path: str) -> Path:
    base = c.workdir.resolve()
    p = Path(path).expanduser()
    p = (base / p) if not p.is_absolute() else p
    p = p.resolve()
    if not p.is_relative_to(base):
        raise ValueError(f"path {path} escapes the task work directory")
    return p


def t_read_file(c: Ctx, path: str, offset: int = 1, limit: int = 400) -> str:
    p = _safe_path(c, path)
    if not p.is_file():
        return f"ERROR: no such file {path}"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    offset = max(1, int(offset or 1))
    limit = max(1, min(int(limit or 400), 2000))
    chunk = lines[offset - 1: offset - 1 + limit]
    return _trunc(f"{p} ({len(lines)} lines)\n" + "\n".join(f"{i + offset}|{l}"
                                                           for i, l in enumerate(chunk)))


def t_write_file(c: Ctx, path: str, content: str) -> str:
    p = _safe_path(c, path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"wrote {len(content)} bytes to {p}"


def t_edit_file(c: Ctx, path: str, old: str, new: str) -> str:
    p = _safe_path(c, path)
    txt = p.read_text(encoding="utf-8", errors="replace")
    if old not in txt:
        return "ERROR: old string not found"
    p.write_text(txt.replace(old, new, 1), encoding="utf-8")
    return f"edited {p}"


def t_ls(c: Ctx, path: str = ".") -> str:
    p = _safe_path(c, path)
    if not p.is_dir():
        return f"ERROR: not a directory: {path}"
    return "\n".join(sorted(x.name + ("/" if x.is_dir() else "") for x in p.iterdir())[:500])


def t_grep(c: Ctx, pattern: str, path: str = ".", limit: int = 60) -> str:
    p = _safe_path(c, path)
    rx = re.compile(pattern)
    hits = []
    files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file() and f.stat().st_size < 4_000_000]
    for f in files:
        try:
            for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{f}:{i}:{line[:300]}")
                    if len(hits) >= limit:
                        raise StopIteration
        except (OSError, StopIteration):
            break
    return "\n".join(hits) or "(no matches)"


def t_webfetch(c: Ctx, url: str, method: str = "GET", headers: dict | None = None,
               body: str = "", timeout: int = 30) -> str:
    if not re.match(r"^https?://", url or ""):
        return "ERROR: url must be http(s)"
    host = re.sub(r"^https?://", "", url).split("/")[0]
    slept = c.pacer.wait(host.split(":")[0]) if c.pacer else 0.0
    hdrs = {"User-Agent": c.settings.user_agent, "Accept": "*/*"}
    hdrs.update({str(k): str(v) for k, v in (headers or {}).items()})
    data = body.encode() if body else None
    req = urllib.request.Request(url, data=data, headers=hdrs, method=(method or "GET").upper())
    try:
        with urllib.request.urlopen(req, timeout=max(5, min(int(timeout or 30), 120))) as r:
            raw = r.read(400000).decode("utf-8", "replace")
            status, rh = r.status, dict(r.headers)
    except urllib.error.HTTPError as e:
        raw = e.read(400000).decode("utf-8", "replace")
        status, rh = e.code, dict(e.headers or {})
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return f"ERROR: fetch failed: {e}"
    tid = c.store.add_traffic(c.task_id, (method or "GET").upper(), url, status, hdrs, body or "",
                              rh, raw)
    return _trunc(f"traffic_id={tid} status={status} (paced {slept:.2f}s)\n"
                  f"headers: {_j(rh)}\n\n{raw}")


# ====================================================================== graphs
ASSET_TYPES = ("root_domain", "ip", "subdomain", "app", "service", "endpoint")


def _norm_asset(a: dict) -> dict:
    """Accept the shortcuts models actually write (value/host/target) and fill the
    derived fields (root_domain, service_type) the graph queries rely on."""
    out = dict(a)
    v = out.get("value") or out.get("target") or out.get("host") or out.get("key")
    t = out.get("type")
    if v:
        v = str(v).strip()
        if t == "ip" and not out.get("ip"):
            out["ip"] = v
        elif t in ("domain", "root_domain", "subdomain") and not out.get("domain"):
            out["domain"] = v
        elif t == "app" and not out.get("app_name"):
            out["app_name"] = v
        elif t in ("service", "endpoint") and not out.get("url"):
            out["url"] = v if "://" in v else "http://" + v
    url = out.get("url")
    if url and "://" not in str(url):
        out["url"] = "http://" + str(url)
    if out.get("url"):
        from urllib.parse import urlparse
        try:
            host = urlparse(out["url"]).hostname or ""
        except ValueError:
            host = ""
        if host and not out.get("domain"):
            out["domain"] = host
        if t == "service" and not out.get("service_type"):
            out["service_type"] = "http"
    dom = out.get("domain")
    if dom and not out.get("root_domain"):
        parts = str(dom).split(".")
        out["root_domain"] = ".".join(parts[-2:]) if len(parts) >= 2 else str(dom)
    return out


def t_insert_assets(c: Ctx, items: list[dict]) -> str:
    if not isinstance(items, list):
        return "ERROR: items must be a list"
    out = []
    for a in items[:60]:
        if not isinstance(a, dict):
            continue
        a = _norm_asset(a)
        if a.get("type") not in ASSET_TYPES:
            out.append({"error": f"invalid type {a.get('type')!r} (expected one of "
                                 f"{', '.join(ASSET_TYPES)})", "item": a})
            continue
        aid = c.store.add_asset(c.task_id, a)
        if not aid:
            out.append({"error": "missing identifier for type " + str(a.get("type")),
                        "item": a})
            continue
        if c.node_id:
            c.store.anchor(c.node_id, aid)
        out.append({"id": aid, "type": a.get("type"),
                    "key": a.get("url") or a.get("domain") or a.get("ip") or a.get("app_name")})
    c.store.log(c.task_id, c.worker, "assets", f"insert_assets {len(out)}", tool="insert_assets")
    return _j({"inserted": out})


def t_list_assets(c: Ctx, q: str = "", type: str = "", limit: int = 50, task_only: bool = False) -> str:
    rows = c.store.assets(c.task_id if task_only else None, type=type, q=q,
                          limit=max(1, min(int(limit or 50), 300)))
    slim = [{k: r[k] for k in ("id", "type", "domain", "ip", "port", "url", "service_name",
                               "status_code", "page_title", "technologies")} for r in rows]
    return _j({"count": len(slim), "assets": slim})


def t_list_untested(c: Ctx, type: str = "", limit: int = 40) -> str:
    rows = c.store.q(
        "SELECT a.id,a.type,a.domain,a.ip,a.port,a.url,a.page_title FROM assets a"
        " LEFT JOIN task_coverage tc ON tc.asset_id=a.id AND tc.task_id=?"
        " WHERE a.task_ids LIKE ? AND tc.asset_id IS NULL" + (" AND a.type=?" if type else "") +
        " ORDER BY a.id DESC LIMIT ?",
        (c.task_id, f"%{c.task_id}%", *([type] if type else []), max(1, min(int(limit or 40), 200))))
    return _j({"count": len(rows), "untested": [dict(r) for r in rows]})


def t_add_scope(c: Ctx, kind: str, value: str, reason: str = "") -> str:
    c.store.add_scope(c.task_id, kind, value, reason or f"set by {c.agent}")
    return f"scope += {kind}:{value}"


def t_add_intent(c: Ctx, intents: list[dict]) -> str:
    if c.agent != "planner":
        return "ERROR: only the planner dispatches intents"
    out = []
    existing = [i["summary"].strip().lower() for i in
                c.store.open_intents(c.task_id) + c.store.recent_done(c.task_id, 30)]
    goal_nodes = c.store.goals(c.task_id)
    default_parent = [goal_nodes[0]["id"]] if goal_nodes else []
    for it in (intents or [])[:4]:
        summary = (it.get("summary") or "").strip()
        if not summary:
            continue
        if summary.lower() in existing:
            out.append({"skipped": "duplicate", "summary": summary})
            continue
        nid = c.store.add_intent(c.task_id, summary,
                                 asset_ids=[int(x) for x in it.get("asset_ids") or []],
                                 parent_ids=[int(x) for x in it.get("parent_ids") or []] or default_parent,
                                 priority=int(it.get("priority") or 0))
        out.append({"id": nid, "summary": summary})
    c.store.log(c.task_id, c.worker, "intents", f"dispatched {len(out)}", tool="add_intent")
    return _j({"dispatched": out})


def t_record_fact(c: Ctx, summary: str, detail: str = "", source: str = "inference",
                  confidence: str = "inferred", evidence: str = "", intent_id: int = 0,
                  asset_ids: list[int] | None = None) -> str:
    source = source if source in ("target_response", "tool_output", "third_party_intel",
                                  "operator_input", "inference") else "inference"
    iid = int(intent_id or 0) or (c.node_id if c.agent == "worker" else 0)
    nid = c.store.add_fact(c.task_id, summary, detail, source, confidence,
                           intent_id=iid or None, evidence=evidence,
                           asset_ids=[int(x) for x in (asset_ids or [])])
    return f"fact recorded: {nid}"


def t_report_finding(c: Ctx, vulnclass: str, severity: str, summary: str, evidence: str,
                     poc: str = "", asset_id: int = 0, endpoint: str = "", parameter: str = "",
                     confidence: str = "observed", proof_basis: str = "executed-live",
                     counterevidence: str = "", traffic_refs: list[int] | None = None,
                     intent_id: int = 0) -> str:
    if not (evidence or "").strip():
        return "ERROR: a finding needs evidence from an actual trigger"
    if (confidence == "inferred") and proof_basis != "static-analysis-unexecuted":
        return ("ERROR: an inferred candidate is not a confirmed finding. Record it with "
                "record_fact(confidence=inferred) instead.")
    dup = c.store.duplicate_finding(c.task_id, vulnclass, endpoint, parameter)
    if dup:
        return (f"REFUSED: finding {dup['id']} already covers {vulnclass} at {endpoint} "
                f"param={parameter!r}. Extend that finding's evidence instead of duplicating.")
    refs = [int(x) for x in (traffic_refs or [])]
    for r in refs:
        if not c.store.traffic(r):
            return f"ERROR: traffic ref {r} does not exist"
    nid, fid = c.store.add_finding(
        c.task_id, vulnclass, severity, summary, evidence, poc,
        asset_id=int(asset_id or 0) or None, endpoint=endpoint, parameter=parameter,
        confidence=confidence, proof_basis=proof_basis, counterevidence=counterevidence,
        traffic_refs=refs, intent_id=int(intent_id or 0) or (c.node_id or None))
    c.store.log(c.task_id, c.worker, "finding", f"{severity} {vulnclass}: {summary}",
                tool="report_finding", node_id=nid, detail=evidence[:2000])
    return _j({"finding_node": nid, "finding_id": fid,
               "note": "recorded; report writer can expand it later"})


def t_list_findings(c: Ctx) -> str:
    fs = c.store.findings(c.task_id)
    slim = [{k: f[k] for k in ("id", "node_id", "vulnclass", "severity", "endpoint",
                               "parameter", "summary", "status", "proof_basis")} for f in fs]
    return _j({"count": len(slim), "findings": slim})


def t_list_facts(c: Ctx, limit: int = 20, q: str = "") -> str:
    return _j(c.store.list_facts(c.task_id, limit=max(1, min(int(limit or 20), 100)), q=q))


def t_node_detail(c: Ctx, id: int) -> str:
    d = c.store.node_detail(int(id))
    if not d:
        return f"ERROR: no node {id}"
    return _trunc(_j(d), 12000)


def t_prove_goal(c: Ctx, goal_id: int, evidence_id: int, reason: str) -> str:
    g = c.store.node(int(goal_id))
    if not g or g["kind"] != "goal":
        return f"ERROR: {goal_id} is not a goal"
    ev = c.store.node(int(evidence_id))
    if not ev:
        return f"ERROR: evidence node {evidence_id} does not exist"
    if ev["kind"] == "fact":
        p = json.loads(ev["payload"])
        if p.get("source") == "target_response":
            return ("REFUSED: a target_response fact cannot prove a goal (the target can plant "
                    "it). Cite a tool_output fact or a finding with bound traffic.")
    if ev["kind"] == "finding":
        f = c.store.one("SELECT * FROM findings WHERE node_id=?", (int(evidence_id),))
        if f and f["status"] in ("false_positive", "duplicate", "ignored"):
            return f"REFUSED: finding {f['id']} is labelled {f['status']}."
        if f and not json.loads(f["traffic_refs"] or "[]"):
            return ("REFUSED: an unbound finding does not close a goal. Bind traffic_refs or use "
                    "an observed tool_output fact.")
    if ev["kind"] not in ("fact", "finding"):
        return "ERROR: evidence must be a fact or a finding"
    payload = json.loads(g["payload"])
    payload.update({"reason": reason, "evidence_id": int(evidence_id)})
    c.store.x("UPDATE exploration_nodes SET payload=?, state='met', completed_at=?, updated_at=?"
              " WHERE id=?", (json.dumps(payload), _now(), _now(), int(goal_id)))
    c.store.add_edge(c.task_id, int(evidence_id), int(goal_id), "proves")
    met = c.store.goal_met(c.task_id)
    if met:
        c.store.set_task_status(c.task_id, "achieved")
    return _j({"goal": int(goal_id), "state": "met", "task_achieved": met})


def t_steer_work(c: Ctx, intent_id: int, message: str) -> str:
    if not c.runtime:
        return "ERROR: no runtime"
    ok = c.runtime.steer(int(intent_id), message)
    return "steered" if ok else f"ERROR: no live worker on intent {intent_id}"


def t_kill_work(c: Ctx, intent_id: int, reason: str = "") -> str:
    if not c.runtime:
        return "ERROR: no runtime"
    ok = c.runtime.kill(int(intent_id), reason)
    return "stopping" if ok else f"ERROR: no live worker on intent {intent_id}"


def t_worker_trace(c: Ctx, intent_id: int, limit: int = 40) -> str:
    rows = c.store.q("SELECT kind,tool,summary,detail,created_at FROM activity WHERE task_id=?"
                     " AND node_id=? ORDER BY id LIMIT ?",
                     (c.task_id, int(intent_id), max(1, min(int(limit or 40), 200))))
    return _trunc(_j([dict(r) for r in rows]), 12000)


def t_add_hint(c: Ctx, text: str) -> str:
    nid = c.store.add_node(c.task_id, "hint", {"text": text}, origin=c.agent)
    return f"hint queued: {nid}"


def t_traffic_search(c: Ctx, host: str = "", limit: int = 10) -> str:
    return _j(c.store.traffic_search(c.task_id, host, max(1, min(int(limit or 10), 50))))


def t_traffic_get(c: Ctx, id: int) -> str:
    t = c.store.traffic(int(id))
    if not t or t["task_id"] != c.task_id:
        return f"ERROR: no traffic {id} in this task"
    return _trunc(_j({**t, "resp_body": t["resp_body"][:8000],
                      "req_body": (t["req_body"] or "")[:2000]}), 12000)


def t_read_skill(c: Ctx, name: str) -> str:
    if c.skills is None:
        return "ERROR: skills are not loaded in this run"
    return _trunc(c.skills.read(name), 30000)


def t_ask_operator(c: Ctx, question: str, command: str = "") -> str:
    c.store.log(c.task_id, c.worker, "operator", question, tool="ask_operator",
                detail=command or "")
    if c.runtime and getattr(c.runtime, "ask", None):
        ans = c.runtime.ask(question, command)
        if ans:
            return ans
    return ("No operator attached (headless run). Do not retry with different flags: record the "
            "blocker as a fact (source=operator_input is wrong here — use tool_output) and continue "
            "with another direction.")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
