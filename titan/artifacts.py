"""Deterministic artifact tree under an engagement's work directory.

The database is the queryable index; these files are the durable, human-readable
output. Each round rewrites them from the evidence so a consultant can open the
folder and finish the report without the console — and so nothing only ever exists
inside SQLite.

Layout
------
    00-meta.json              goal, scope, policy, counts, timings
    enumeration/hosts.json    machine index (what the GUI reads)
    enumeration/<host>/summary.md | paths.txt | http.txt
    findings/index.json       and findings/F-01-<slug>.md
    poc/F-01-<slug>/request.http | response.http | poc.sh | README.md
    evidence/traffic.jsonl    every recorded request/response
    evidence/observations.jsonl
    report/report.md
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def slug(text: str, limit: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:limit].rstrip("-")) or "item"


def _text(value: str) -> str:
    """Some evidence was captured with literal \\n; make files readable on disk."""
    s = str(value or "")
    if "\n" in s and "\\n" in s:
        s = s.replace("\\n", "\n").replace("\\t", "\t")
    return s


def _safe(host: str) -> str:
    h = (host or "unattached").strip().lower()
    h = re.sub(r"[^a-z0-9.\-]+", "_", h)
    return h.strip("._") or "unattached"


class Artifacts:
    def __init__(self, workdir: str | Path):
        self.root = Path(workdir).expanduser()

    # ---------------------------------------------------------------- helpers
    def _write(self, rel: str, text: str) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
        return p

    def _json(self, rel: str, obj) -> Path:
        return self._write(rel, json.dumps(obj, indent=1, ensure_ascii=False, default=str))

    # ---------------------------------------------------------------- public
    def write_all(self, store, task_id: int) -> dict:
        row = store.get_task(task_id)
        if not row:
            return {"files": 0}
        task = dict(row)
        ov = store.graph_overview(task_id)
        enum = store.enumeration(task_id)
        findings = store.findings(task_id, only_active=False)
        scope = store.scope(task_id)
        policy = store.scope_policy(task_id)
        traffic = store.traffic_list(task_id, "", 2000)
        self.root.mkdir(parents=True, exist_ok=True)

        written = 0
        written += bool(self._json("00-meta.json", {
            "task": task_id,
            "title": task["title"] or "",
            "goal": task["goal"],
            "status": task["status"],
            "round": ov["round"],
            "mode": task.get("mode") or "autonomous",
            "workdir": str(self.root),
            "scope": scope,
            "scope_policy": policy,
            "counts": {"assets": ov["assets"], "facts": ov["facts_total"],
                       "findings": ov["findings_total"], "traffic": len(traffic)},
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }))

        # ---- enumeration
        written += bool(self._json("enumeration/hosts.json", {
            "task": task_id, "counts": enum.get("counts", {}),
            "hosts": [{k: v for k, v in h.items() if k != "observations"} for h in enum["hosts"]],
        }))
        for h in enum["hosts"]:
            folder = f"enumeration/{_safe(h['key'])}"
            written += bool(self._write(f"{folder}/summary.md", self._host_md(h)))
            paths = []
            for s in h.get("services", []):
                paths.append(f"# {s.get('url', '')} [{s.get('status') or ''}] {s.get('title') or ''}")
                for e in s.get("endpoints", []):
                    paths.append(f"{e.get('url', '')}\t{e.get('status_code') or ''}\t{e.get('label') or ''}")
            for e in h.get("loose_endpoints", []):
                paths.append(f"{e.get('url', '')}\t{e.get('status_code') or ''}")
            if paths:
                written += bool(self._write(f"{folder}/paths.txt", "\n".join(paths)))
            http = self._host_http(store, task_id, h)
            if http:
                written += bool(self._write(f"{folder}/http.txt", http))

        # ---- findings + poc
        index = []
        for i, f in enumerate(sorted(findings, key=lambda x: x["id"]), 1):
            name = f"F-{i:02d}-{slug(f['vulnclass'])}"
            index.append({"ref": name, "id": f["id"], "severity": f["severity"],
                          "vulnclass": f["vulnclass"], "endpoint": f.get("endpoint"),
                          "status": f.get("status"), "file": f"findings/{name}.md",
                          "poc": f"poc/{name}/"})
            written += bool(self._write(f"findings/{name}.md", self._finding_md(f, name)))
            if f.get("traffic_refs"):
                written += bool(self._write(f"poc/{name}/README.md", self._poc_md(f, name)))
                req = resp = ""
                for tid in f["traffic_refs"][:3]:
                    t = store.traffic(int(tid))
                    if not t:
                        continue
                    req += self._http_request(t) + "\n\n"
                    resp += self._http_response(t) + "\n\n"
                if req:
                    written += bool(self._write(f"poc/{name}/request.http", req.strip()))
                if resp:
                    written += bool(self._write(f"poc/{name}/response.http", resp.strip()))
                if f.get("poc"):
                    script = _text(f["poc"]).strip()
                    if not script.startswith("#!"):
                        script = "#!/usr/bin/env bash\nset -euo pipefail\n" + script
                    p = self._write(f"poc/{name}/poc.sh", script)
                    try:
                        p.chmod(0o755)
                    except OSError:
                        pass
                    written += 1
        written += bool(self._json("findings/index.json", index))

        # ---- evidence
        if traffic:
            lines = []
            for t in traffic:
                full = store.traffic(int(t["id"])) or {}
                lines.append(json.dumps({
                    "id": full.get("id"), "method": full.get("method"), "url": full.get("url"),
                    "status": full.get("status"), "req_headers": full.get("req_headers"),
                    "req_body": (full.get("req_body") or "")[:4000],
                    "resp_headers": full.get("resp_headers"),
                    "resp_body": (full.get("resp_body") or "")[:8000],
                    "at": full.get("created_at"),
                }, ensure_ascii=False))
            written += bool(self._write("evidence/traffic.jsonl", "\n".join(lines)))
        facts = store.list_facts(task_id, limit=2000)
        if facts:
            written += bool(self._write("evidence/observations.jsonl", "\n".join(
                json.dumps(f, ensure_ascii=False) for f in facts)))

        # ---- report
        written += bool(self._write("report/report.md", self._report_md(store, task_id)))
        return {"files": written, "root": str(self.root)}

    # ---------------------------------------------------------------- markdown
    def _host_md(self, h: dict) -> str:
        out = [f"# {h['key']}", ""]
        if h.get("domain") and h["domain"] != h["key"]:
            out.append(f"Domain: `{h['domain']}`")
        if h.get("ip") and h["ip"] != h["key"]:
            out.append(f"Address: `{h['ip']}`")
        out.append("")
        if h.get("services"):
            out += ["## Services", ""]
            for s in h["services"]:
                out.append(f"### {s.get('url', '')}")
                meta = []
                if s.get("status"):
                    meta.append(f"status {s['status']}")
                if s.get("title"):
                    meta.append(f"title {s['title']}")
                if s.get("tech"):
                    meta.append("tech " + ", ".join(s["tech"]))
                if meta:
                    out.append(" · ".join(meta))
                for e in s.get("endpoints", [])[:200]:
                    out.append(f"- `{e.get('url', '')}` {e.get('status_code') or ''}")
                out.append("")
        if h.get("observations"):
            out += ["## Observations", ""]
            for o in h["observations"]:
                out.append(f"- **{o.get('confidence')}** {o.get('summary')}")
                if o.get("detail"):
                    out.append(f"  {o['detail']}")
                src = " · ".join(x for x in [o.get("source"), o.get("at_local")] if x)
                if src:
                    out.append(f"  `{src}`")
            out.append("")
        return "\n".join(out)

    def _host_http(self, store, task_id: int, h: dict) -> str:
        rows = []
        for t in store.traffic_list(task_id, h["key"], 40):
            full = store.traffic(int(t["id"]))
            if not full:
                continue
            rows.append(self._http_request(full))
            rows.append(self._http_response(full))
            rows.append("")
        return "\n".join(rows)

    @staticmethod
    def _http_request(t: dict) -> str:
        headers = t.get("req_headers") or "{}"
        if isinstance(headers, str):
            try:
                headers = json.loads(headers)
            except ValueError:
                pass
        if isinstance(headers, dict):
            headers = "\n".join(f"{k}: {v}" for k, v in headers.items())
        body = (t.get("req_body") or "").strip()
        return f"{t.get('method', 'GET')} {t.get('url', '')} HTTP/1.1\n{headers}" + (
            f"\n\n{body}" if body else "")

    @staticmethod
    def _http_response(t: dict) -> str:
        headers = t.get("resp_headers") or "{}"
        if isinstance(headers, str):
            try:
                headers = json.loads(headers)
            except ValueError:
                pass
        if isinstance(headers, dict):
            headers = "\n".join(f"{k}: {v}" for k, v in headers.items())
        body = (t.get("resp_body") or "").strip()
        if len(body) > 4000:
            body = body[:4000] + "\n… truncated"
        return f"HTTP/1.1 {t.get('status', '')}\n{headers}" + (f"\n\n{body}" if body else "")

    @staticmethod
    def _finding_md(f: dict, name: str) -> str:
        lines = [f"# {name} — {f['vulnclass']}", "",
                 f"**Severity:** {f['severity']}  ",
                 f"**Status:** {f.get('status')}  ",
                 f"**Asset:** `{f.get('endpoint') or '—'}`  ",
                 f"**Parameter:** {f.get('parameter') or '—'}  ",
                 f"**Confidence:** {f.get('confidence')} ({f.get('proof_basis')})  ",
                 f"**Evidence refs:** {', '.join(str(x) for x in (f.get('traffic_refs') or [])) or '—'}",
                 "", "## Summary", "", f.get("summary") or "", "",
                 "## Evidence", "", "```", _text(f.get("evidence")).strip(), "```"]
        if f.get("poc"):
            lines += ["", "## Reproduction", "", "```", _text(f["poc"]).strip(), "```"]
        if f.get("counterevidence"):
            lines += ["", "## Considered and excluded", "", f["counterevidence"]]
        return "\n".join(lines)

    @staticmethod
    def _poc_md(f: dict, name: str) -> str:
        return (f"# {name}\n\n`request.http` and `response.http` hold the captured exchange; "
                f"`poc.sh` reproduces it.\n\nEndpoint: `{f.get('endpoint')}`\n\n"
                f"{f.get('summary') or ''}\n")

    def _report_md(self, store, task_id: int) -> str:
        task = store.get_task(task_id)
        ov = store.graph_overview(task_id)
        enum = store.enumeration(task_id)
        findings = store.findings(task_id, only_active=False)

        out = [f"# {task['title'] or 'Engagement report'}", "",
               f"Engagement #{task_id} · status {task['status']} · round {ov['round']}", "",
               "## Objective", "", task["goal"], "", "## Scope", ""]
        for s in store.scope(task_id):
            out.append(f"- `{s['kind']}={s['value']}`")
        out += ["", f"## Findings ({len(findings)})", ""]
        if not findings:
            out.append("No confirmed findings.")
        for i, f in enumerate(sorted(findings, key=lambda x: x["id"]), 1):
            out += [f"### {i}. {f['vulnclass']} ({f['severity']})", "",
                    f"- Asset: `{f.get('endpoint') or '—'}`",
                    f"- Status: {f.get('status')}",
                    f"- Evidence refs: {', '.join(str(x) for x in (f.get('traffic_refs') or [])) or '—'}",
                    "", f.get("summary") or "", ""]
            if f.get("evidence"):
                out += ["```", f["evidence"].strip(), "```", ""]
        out += ["## What was enumerated", ""]
        for h in enum["hosts"]:
            if not (h.get("services") or h.get("observations")):
                continue
            out.append(f"### {h['key']}")
            for s in h.get("services", []):
                out.append(f"- `{s.get('url', '')}` {s.get('status') or ''} {s.get('title') or ''}")
            for o in h.get("observations", []):
                if o.get("confidence") == "observed":
                    out.append(f"- {o.get('summary')}")
            out.append("")
        return "\n".join(out)
