"""Local web console for Dewaguard Titan.

Serves the single-page UI (titan/gui.py) plus a JSON API. Binds 127.0.0.1 by
default: the mutating endpoints are operator controls, not a service. Binding it
anywhere else requires TITAN_CONSOLE_TOKEN, and then every request must carry the
matching X-Titan-Token header.
"""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .config import key_source, load_api_key, mask, save_api_key
from .engine import Engine
from .gui import GUI
from .llm import LLM, LLMError, list_models
from .skills import SkillIndex
from .store import Store

LOOPBACK_BINDS = {"127.0.0.1", "::1", "localhost"}


def _json_bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode()


def _settings_payload(settings, store: Store) -> dict:
    s = store.settings()
    key = load_api_key(settings)
    return {
        "llm": {
            "base_url": s.get("llm.base_url") or settings.base_url,
            "model": s.get("llm.model") or settings.model,
            "timeout": int(s.get("llm.timeout") or settings.request_timeout),
            "max_tokens": int(s.get("llm.max_tokens") or settings.max_tokens),
            "temperature": float(s.get("llm.temperature") or settings.temperature),
            "key_masked": mask(key),
            "key_source": key_source(settings),
        },
        "run": {
            "rps": s.get("run.rps") or str(settings.rps),
            "max_workers": s.get("run.max_workers") or str(settings.max_workers),
            "noise_profile": s.get("run.noise_profile") or settings.noise_profile,
        },
    }


def serve(settings, task_id: int = 0) -> int:
    store = Store(settings.db_path)
    engine = Engine(settings, store=store)
    skills = SkillIndex(settings.skill_dir)
    running: dict[int, threading.Thread] = {}
    lock = threading.Lock()
    token = settings.console_token
    external = settings.console_bind not in LOOPBACK_BINDS
    if external and not token:
        raise SystemExit("refusing to bind the console off-localhost without "
                         "TITAN_CONSOLE_TOKEN set")

    class H(BaseHTTPRequestHandler):
        server_version = "TitanConsole"

        def log_message(self, *a):
            pass

        # ---------------------------------------------------------------- plumbing
        def _auth_ok(self) -> bool:
            return not token or self.headers.get("X-Titan-Token", "") == token

        def _send(self, code: int, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _html(self, body: str):
            self._send(200, body.encode(), "text/html; charset=utf-8")

        def _json(self, obj, code: int = 200):
            self._send(code, _json_bytes(obj), "application/json")

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if not n:
                return {}
            try:
                data = json.loads(self.rfile.read(n).decode() or "{}")
                return data if isinstance(data, dict) else {}
            except ValueError:
                return {}

        def _tid(self, q) -> int:
            return int((q.get("task") or [task_id or 0])[0] or 0)

        # ---------------------------------------------------------------- GET
        def do_GET(self):  # noqa: N802
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if not self._auth_ok():
                return self._json({"error": "unauthorised"}, 401)
            try:
                return self._get(u.path, q)
            except Exception as e:  # noqa: BLE001 - never 500 without a message
                return self._json({"error": f"{type(e).__name__}: {e}"}, 500)

        def _get(self, path: str, q):
            if path == "/":
                return self._html(GUI)

            if path == "/api/tasks":
                return self._json({"tasks": [dict(r) for r in store.list_tasks(50)]})

            if path == "/api/state":
                tid = self._tid(q)
                if not store.get_task(tid):
                    return self._json({"error": f"no task {tid}"}, 404)
                with lock:
                    is_running = tid in running and running[tid].is_alive()
                return self._json({
                    "task": dict(store.get_task(tid)),
                    "mode": (store.get_task(tid)["mode"] or "autonomous"),
                    "approval": store.pending_approval(tid),
                    "overview": store.graph_overview(tid),
                    "enumeration": store.enumeration(tid),
                    "findings": store.findings(tid),
                    "assets": store.assets(tid, limit=200),
                    "activity": store.activity(tid, 60),
                    "running": is_running,
                })

            if path == "/api/agents":
                tid = self._tid(q)
                return self._json({
                    "live": engine.live_snapshot(tid),
                    "usage": store.agent_usage(tid),
                    "activity": store.activity(tid, 40),
                })

            if path == "/api/graph":
                tid = self._tid(q)
                if not store.get_task(tid):
                    return self._json({"error": f"no task {tid}"}, 404)
                return self._json(store.graph_data(tid))

            if path == "/api/node":
                nid = int((q.get("id") or [0])[0] or 0)
                d = store.node_detail(nid)
                return self._json(d or {"error": f"no node {nid}"}, 200 if d else 404)

            if path == "/api/skills":
                return self._json({"skills": [
                    {"name": k, "description": v.description, "path": str(v.path)}
                    for k, v in sorted(skills.skills.items())]})

            if path == "/api/skill":
                name = (q.get("name") or [""])[0]
                return self._json({"name": name, "body": skills.read(name)})

            if path == "/api/traffic":
                tid = self._tid(q)
                return self._json({"traffic": store.traffic_list(
                    tid, (q.get("q") or [""])[0], 100)})

            if path == "/api/traffic_one":
                t = store.traffic(int((q.get("id") or [0])[0] or 0))
                if not t:
                    return self._json({"error": "no such record"}, 404)
                t["resp_body"] = (t.get("resp_body") or "")[:40000]
                t["req_body"] = (t.get("req_body") or "")[:4000]
                return self._json(t)

            if path == "/api/settings":
                return self._json(_settings_payload(settings, store))

            if path == "/api/models":
                url = (q.get("url") or [settings.base_url])[0]
                key = (q.get("key") or [load_api_key(settings)])[0]
                try:
                    return self._json({"models": list_models(url, key)})
                except LLMError as e:
                    return self._json({"error": str(e)}, 400)

            if path == "/api/export":
                tid = int((q.get("task") or [0])[0] or 0)
                if not store.get_task(tid):
                    return self._json({"error": "no task"}, 404)
                md = _report(store, tid).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_header("Content-Disposition",
                                 f'attachment; filename="titan-task-{tid}.md"')
                self.send_header("Content-Length", str(len(md)))
                self.end_headers()
                self.wfile.write(md)
                return

            return self._json({"error": "not found"}, 404)

        # ---------------------------------------------------------------- POST
        def do_POST(self):  # noqa: N802
            u = urlparse(self.path)
            if not self._auth_ok():
                return self._json({"error": "unauthorised"}, 401)
            body = self._body()
            try:
                return self._post(u.path, body)
            except Exception as e:  # noqa: BLE001
                return self._json({"error": f"{type(e).__name__}: {e}"}, 500)

        def _post(self, path: str, body: dict):
            if path == "/api/settings":
                llm = body.get("llm") or {}
                run = body.get("run") or {}
                pairs = {
                    "llm.base_url": llm.get("base_url"),
                    "llm.model": llm.get("model"),
                    "llm.timeout": llm.get("timeout"),
                    "llm.max_tokens": llm.get("max_tokens"),
                    "llm.temperature": llm.get("temperature"),
                    "run.rps": run.get("rps"),
                    "run.max_workers": run.get("max_workers"),
                    "run.noise_profile": run.get("noise_profile"),
                }
                for k, v in pairs.items():
                    if v is not None and str(v) != "":
                        store.set_setting(k, str(v))
                new_key = str(body.get("api_key") or "").strip()
                if new_key:
                    save_api_key(settings, new_key)
                engine.reload_llm()
                engine.apply_runtime_settings()
                return self._json(_settings_payload(settings, store))

            if path == "/api/settings/test":
                base = str(body.get("base_url") or "").strip() or settings.base_url
                model = str(body.get("model") or "").strip() or settings.model
                key = str(body.get("api_key") or "").strip() or load_api_key(settings)
                if not model:
                    return self._json({"error": "model is required"}, 400)
                t0 = time.time()
                try:
                    reply = LLM(base, model, key, 60, 32).chat(
                        [{"role": "user", "content": "Say exactly: ok"}])
                except LLMError as e:
                    return self._json({"error": str(e)}, 400)
                return self._json({
                    "ok": True,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "reply": (reply.content or "").strip()[:120],
                    "tokens_in": reply.tokens_in, "tokens_out": reply.tokens_out,
                })

            if path == "/api/task":
                goal = str(body.get("goal") or "").strip()
                if not goal:
                    return self._json({"error": "goal is required"}, 400)
                if not engine.llm_config()["model"]:
                    return self._json({"error": "no model configured: open Settings and "
                                                "set the endpoint + model"}, 400)
                scope = [s for s in (body.get("scope") or [])
                         if isinstance(s, dict) and s.get("value")]
                tid = engine.new_task(goal, str(body.get("title") or ""),
                                      str(body.get("desc") or ""), scope,
                                      str(body.get("workdir") or "").strip(),
                                      str(body.get("mode") or "autonomous"))
                return self._json({"task": tid})

            if path == "/api/task/delete":
                tid = int(body.get("task") or 0)
                if not store.delete_task(tid):
                    return self._json({"error": f"no task {tid}"}, 404)
                engine.live_drop("planner")
                return self._json({"deleted": tid})

            if path == "/api/task/rename":
                tid = int(body.get("task") or 0)
                title = str(body.get("title") or "").strip()
                if not title:
                    return self._json({"error": "title is required"}, 400)
                if not store.rename_task(tid, title):
                    return self._json({"error": f"no task {tid}"}, 404)
                return self._json({"task": tid, "title": title})

            if path == "/api/run":
                tid = int(body.get("task") or 0)
                if not store.get_task(tid):
                    return self._json({"error": f"no task {tid}"}, 404)
                with lock:
                    if tid in running and running[tid].is_alive():
                        return self._json({"error": "already running"}, 409)
                    raw_rounds = body.get("rounds")
                    rounds = int(raw_rounds) if raw_rounds not in (None, "", 0) else None
                    workers = max(1, min(int(body.get("workers") or settings.max_workers), 8))
                    mode = str(body.get("mode") or store.get_task(tid)["mode"] or "autonomous")

                    def job():
                        try:
                            engine.run_task(tid, rounds=rounds, workers=workers, mode=mode)
                        except Exception as e:  # noqa: BLE001
                            store.log(tid, "engine", "error", f"run failed: {e}")

                    t = threading.Thread(target=job, daemon=True)
                    running[tid] = t
                    t.start()
                return self._json({"started": tid})

            if path == "/api/stop":
                tid = int(body.get("task") or 0)
                if not store.get_task(tid):
                    return self._json({"error": "no task"}, 404)
                engine.request_stop(tid)
                return self._json({"stopping": tid})

            if path == "/api/approve":
                tid = int(body.get("task") or 0)
                decision = str(body.get("decision") or "approve")
                if not store.get_task(tid):
                    return self._json({"error": f"no task {tid}"}, 404)
                ok = engine.approve(tid, decision)
                store.log(tid, "operator", "approval", decision)
                return self._json({"approval": decision, "applied": bool(ok)})

            if path == "/api/hint":
                tid = int(body.get("task") or 0)
                text = str(body.get("text") or "").strip()
                if not (store.get_task(tid) and text):
                    return self._json({"error": "task and text required"}, 400)
                nid = store.add_node(tid, "hint", {"text": text}, origin="operator")
                return self._json({"hint": nid})

            if path == "/api/steer":
                tid = int(body.get("task") or 0)
                iid = int(body.get("intent") or 0)
                msg = str(body.get("message") or "").strip()
                if not msg:
                    return self._json({"error": "message required"}, 400)
                ok = engine.steer(iid, msg)
                store.log(tid, "operator", "steer", f"intent {iid}: {msg}")
                return self._json({"steered": bool(ok), "intent": iid})

            if path == "/api/kill":
                tid = int(body.get("task") or 0)
                iid = int(body.get("intent") or 0)
                ok = engine.kill(iid, str(body.get("reason") or "operator"))
                store.log(tid, "operator", "kill", f"intent {iid}")
                return self._json({"stopping": bool(ok), "intent": iid})

            if path == "/api/finding":
                fid = int(body.get("id") or 0)
                status = str(body.get("status") or "")
                if not store.set_finding_status(fid, status):
                    return self._json({"error": f"cannot set finding {fid} to {status!r}"}, 400)
                return self._json({"finding": fid, "status": status})

            if path == "/api/scope":
                tid = int(body.get("task") or 0)
                kind = str(body.get("kind") or "").strip()
                value = str(body.get("value") or "").strip()
                if not (store.get_task(tid) and kind and value):
                    return self._json({"error": "task, kind and value required"}, 400)
                store.add_scope(tid, kind, value, "operator")
                return self._json({"scope": store.scope(tid)})

            return self._json({"error": "not found"}, 404)

    try:
        srv = ThreadingHTTPServer((settings.console_bind, settings.console_port), H)
    except OSError as e:
        raise SystemExit(f"cannot bind {settings.console_bind}:{settings.console_port} "
                         f"({e}). Another 'titan serve' may still be running: "
                         f"check with: ss -ltnp | grep {settings.console_port}") from e
    url = f"http://{settings.console_bind}:{settings.console_port}"
    print(f"Dewaguard Titan console: {url}  (Ctrl-C to stop)")
    if external:
        print("  note: exposed off-localhost; X-Titan-Token required on every request")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


def _report(store: Store, task_id: int) -> str:
    t = store.get_task(task_id)
    ov = store.graph_overview(task_id)
    lines = [f"# Engagement report - task #{task_id}", "", f"**Goal:** {t['goal']}", "",
             f"**Status:** {t['status']} | **Coverage:** {ov['coverage']['pct']}% "
             f"({ov['coverage']['tested']}/{ov['coverage']['assets']}) | "
             f"**Findings:** {ov['findings_total']}", "", "## Goals", ""]
    lines += [f"- [{g['state']}] {g['text']}" for g in ov["goals"]]
    lines += ["", "## Findings", ""]
    for f in store.findings(task_id):
        lines += [f"### {f['vulnclass']} - {f['severity'].upper()}", "",
                  f"- Endpoint: `{f['endpoint'] or '-'}`  Parameter: `{f['parameter'] or '-'}`",
                  f"- Proof basis: {f['proof_basis']} - Confidence: {f['confidence']} - "
                  f"Status: {f['status']}", "", f["summary"], "", "**Evidence**", "", "```",
                  (f["evidence"] or "").strip(), "```", ""]
        if f.get("poc"):
            lines += ["**PoC**", "", "```", f["poc"].strip(), "```", ""]
    lines += ["", "## Exploration facts", ""]
    for f in store.list_facts(task_id, limit=200):
        lines.append(f"- {f['summary']} *({f.get('confidence')}/{f.get('source')})*")
    return "\n".join(lines) + "\n"
