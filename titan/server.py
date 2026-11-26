"""Local web console for Dewaguard Titan.

Serves a single-page UI plus a small JSON API. Binds 127.0.0.1 by default: the
mutating endpoints (create task, run, stop, steer, kill) are operator controls, not
a service. If you bind it anywhere else you must set TITAN_CONSOLE_TOKEN, and every
request then needs the matching X-Titan-Token header.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .engine import Engine
from .store import Store

LOOPBACK_BINDS = {"127.0.0.1", "::1", "localhost"}

GUI = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>Dewaguard Titan</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0e1013;--panel:#161a20;--line:#262c36;--fg:#d8dee9;--dim:#7d8798;
      --accent:#59a6ff;--ok:#4cc38a;--warn:#e2b93b;--bad:#e05561}
*{box-sizing:border-box}
body{margin:0;font:13px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
     background:var(--bg);color:var(--fg)}
header{display:flex;align-items:center;gap:1rem;padding:.6rem 1rem;border-bottom:1px solid var(--line);
       background:var(--panel);position:sticky;top:0;z-index:5;flex-wrap:wrap}
header h1{font-size:.85rem;letter-spacing:.18em;margin:0;font-weight:600}
header .stat{color:var(--dim)} header .stat b{color:var(--fg)}
main{display:grid;grid-template-columns:270px 1fr;min-height:calc(100vh - 49px)}
nav{border-right:1px solid var(--line);padding:.6rem;overflow:auto}
nav .task{padding:.45rem .55rem;border:1px solid transparent;border-radius:4px;cursor:pointer;
          margin-bottom:.25rem}
nav .task:hover{background:#1b2028}
nav .task.on{background:#1d2634;border-color:#2f4a6d}
nav .task .t{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
nav .task .m{color:var(--dim);font-size:11px}
section{padding:1rem 1.2rem;overflow:auto}
h2{font-size:.95rem;margin:.2rem 0 .1rem}
h3{font-size:.78rem;letter-spacing:.09em;color:var(--dim);text-transform:uppercase;margin:1.2rem 0 .4rem}
button{background:#1f2731;color:var(--fg);border:1px solid var(--line);border-radius:4px;
       padding:.28rem .6rem;cursor:pointer;font:inherit}
button:hover{border-color:#3d4a5c}
button.pri{background:#1d3a5c;border-color:#2f5b8f}
button.danger{background:#3a1f23;border-color:#5e2b31}
button:disabled{opacity:.45;cursor:default}
input,textarea,select{background:#10141a;color:var(--fg);border:1px solid var(--line);
       border-radius:4px;padding:.3rem .45rem;font:inherit;width:100%}
textarea{resize:vertical;min-height:4.2rem}
table{border-collapse:collapse;width:100%}
th,td{text-align:left;padding:.28rem .4rem;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--dim);font-weight:500;font-size:11px;letter-spacing:.06em;text-transform:uppercase}
tr:hover td{background:#141920}
.row{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
.card{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:.7rem .8rem}
.tag{display:inline-block;padding:0 .35rem;border-radius:3px;font-size:11px;border:1px solid var(--line)}
.s-open{color:var(--accent)} .s-running{color:var(--warn)}
.s-done,.s-confirmed,.s-met,.s-achieved{color:var(--ok)}
.s-exhausted,.s-blocked,.s-stopped,.s-failed,.s-abandoned{color:var(--bad)}
.muted{color:var(--dim)}
pre{white-space:pre-wrap;word-break:break-word;background:#10141a;border:1px solid var(--line);
    border-radius:4px;padding:.5rem;max-height:22rem;overflow:auto;margin:.3rem 0}
.tabs{display:flex;gap:.3rem;margin:.9rem 0 .2rem}
.tabs button{border-radius:4px 4px 0 0;border-bottom-color:transparent}
.tabs button.on{background:#1d2634;border-color:#2f4a6d;color:#fff}
.hint{color:var(--dim);font-size:11px}
@media(max-width:820px){main{grid-template-columns:1fr}nav{border-right:0;border-bottom:1px solid var(--line)}}
</style></head>
<body>
<header>
  <h1>DEWAGUARD TITAN</h1>
  <span class="stat">task <b id="hTask">-</b></span>
  <span class="stat">status <b id="hStatus">-</b></span>
  <span class="stat">round <b id="hRound">0</b></span>
  <span class="stat">coverage <b id="hCov">0%</b></span>
  <span class="stat">findings <b id="hFind">0</b></span>
  <span id="hLive" class="muted"></span>
</header>
<main>
  <nav>
    <div class="row" style="margin-bottom:.5rem">
      <button class="pri" onclick="showNew()">+ task</button>
      <button onclick="loadTasks()">refresh</button>
    </div>
    <div id="tasks"></div>
  </nav>
  <section id="main"><p class="muted">Select or create a task.</p></section>
</main>
<script>
const $ = s => document.querySelector(s);
const esc = s => String(s === null || s === undefined ? '' : s)
  .replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let S = {tasks: [], task: 0, data: null, tab: 'overview', timer: null, view: 'task'};

async function api(path, body) {
  const opts = body === undefined ? {} : {method:'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)};
  const r = await fetch(path, opts);
  const txt = await r.text();
  let j; try { j = JSON.parse(txt); } catch (e) { j = {error: txt}; }
  if (!r.ok && !j.error) j.error = 'HTTP ' + r.status;
  return j;
}

async function loadTasks() {
  const j = await api('/api/tasks');
  S.tasks = j.tasks || [];
  const el = $('#tasks');
  if (!el) return;
  el.innerHTML = S.tasks.map(t => `
    <div class="task ${t.id === S.task ? 'on' : ''}" onclick="selectTask(${t.id})">
      <span class="t">#${t.id} ${esc(t.title || t.goal)}</span>
      <span class="m">${esc(t.status)} &middot; ${t.round_no}r</span>
    </div>`).join('') || '<p class="muted" style="padding:.4rem">no tasks</p>';
}

async function selectTask(id) {
  S.task = id; S.view = 'task';
  await loadTasks();
  await refresh(true);
  clearInterval(S.timer);
  S.timer = setInterval(() => refresh(false), 2000);
}

async function refresh(force) {
  if (!S.task || S.view !== 'task') return;
  const j = await api('/api/state?task=' + S.task);
  if (j.error) { $('#main').innerHTML = '<p class="s-failed">' + esc(j.error) + '</p>'; return; }
  S.data = j;
  $('#hTask').textContent = '#' + j.task.id;
  $('#hStatus').textContent = j.task.status;
  $('#hStatus').className = 's-' + j.task.status;
  $('#hRound').textContent = j.overview.round;
  $('#hCov').textContent = j.overview.coverage.pct + '%';
  $('#hFind').textContent = j.overview.findings_total;
  $('#hLive').textContent = j.running ? 'running' : '';
  $('#hLive').className = j.running ? 's-running' : 'muted';
  render();
}

function render() {
  if (S.view === 'new') return;
  const d = S.data; if (!d) return;
  const ov = d.overview;
  const tabs = ['overview','intents','facts','findings','assets','activity','graph'];
  const head = `
    <h2>#${d.task.id} ${esc(d.task.title)}</h2>
    <div class="muted">${esc(d.task.goal)}</div>
    <div class="row" style="margin:.7rem 0">
      <label class="hint">rounds <input id="rRounds" style="width:5rem" value="${Math.max(5, d.task.round_no || 10)}"></label>
      <label class="hint">workers <input id="rWorkers" style="width:4rem" value="2"></label>
      <button class="pri" onclick="runTask()" ${d.running ? 'disabled' : ''}>${d.running ? 'running...' : 'run'}</button>
      <button class="danger" onclick="stopTask()" ${d.running ? '' : 'disabled'}>stop</button>
      <button onclick="exportMd()">export .md</button>
      <span class="muted">${ov.facts_total} facts &middot; ${ov.findings_total} findings &middot;
      coverage ${ov.coverage.pct}% (${ov.coverage.tested}/${ov.coverage.assets})</span>
    </div>
    <div class="tabs">${tabs.map(t => `<button class="${t===S.tab?'on':''}" onclick="setTab('${t}')">${t}</button>`).join('')}</div>
    <div id="pane"></div>`;
  $('#main').innerHTML = head;
  const pane = $('#pane');
  if (S.tab === 'overview') pane.innerHTML = tabOverview(d);
  if (S.tab === 'intents') pane.innerHTML = tabIntents(d);
  if (S.tab === 'facts') pane.innerHTML = tabFacts(d);
  if (S.tab === 'findings') pane.innerHTML = tabFindings(d);
  if (S.tab === 'assets') pane.innerHTML = tabAssets(d);
  if (S.tab === 'activity') pane.innerHTML = tabActivity(d);
  if (S.tab === 'graph') pane.innerHTML = tabGraph(d);
}

function setTab(t) { S.tab = t; render(); }

function intentRow(i) {
  return `<div class="row" style="align-items:flex-start;margin-bottom:.25rem">
    <span class="tag s-${esc(i.state)}">${esc(i.state)}</span>
    <span style="flex:1">#${i.id} ${esc(i.summary)}</span>
    ${i.state === 'running'
      ? `<button onclick="steer(${i.id})">steer</button><button class="danger" onclick="kill(${i.id})">kill</button>`
      : ''}
  </div>`;
}

function tabOverview(d) {
  const ov = d.overview;
  const queue = [...ov.running_intents, ...ov.open_intents];
  return `
  <div class="grid2">
    <div class="card"><h3 style="margin-top:0">goals</h3>
      ${ov.goals.map(g => `<div class="row"><span class="tag s-${esc(g.state)}">${esc(g.state)}</span>
        <span>${esc(g.text)}</span></div>`).join('') || '<span class="muted">none</span>'}
      <h3>constraints</h3>
      ${ov.constraints.map(c => `<div><span class="tag">${esc(c.kind)}</span> ${esc(c.text)}</div>`).join('') || '<span class="muted">none</span>'}
    </div>
    <div class="card"><h3 style="margin-top:0">queue</h3>
      ${queue.map(intentRow).join('') || '<span class="muted">idle</span>'}
      <h3>hint</h3>
      <textarea id="hintText" placeholder="operator hint for the next planning rounds"></textarea>
      <div class="row" style="margin-top:.35rem"><button onclick="addHint()">queue hint</button></div>
    </div>
  </div>`;
}

function tabIntents(d) {
  const ov = d.overview;
  const all = [...ov.running_intents, ...ov.open_intents, ...ov.recent_done];
  if (!all.length) return '<p class="muted">no intents yet</p>';
  return `<table><tr><th>state</th><th>id</th><th>summary</th><th>assets</th><th></th></tr>
    ${all.map(i => `<tr><td class="s-${esc(i.state)}">${esc(i.state)}</td><td>${i.id}</td>
      <td>${esc(i.summary)}<div class="hint">${esc(i.blocked_reason || '')}</div></td>
      <td>${(i.asset_ids || []).join(', ')}</td>
      <td>${i.state === 'running' ? `<button onclick="steer(${i.id})">steer</button>
        <button class="danger" onclick="kill(${i.id})">kill</button>` : ''}</td></tr>`).join('')}
    </table>`;
}

function tabFacts(d) {
  const f = d.overview.recent_facts;
  if (!f.length) return '<p class="muted">no facts yet</p>';
  return `<table><tr><th>id</th><th>summary</th><th>source</th><th>confidence</th><th>from</th></tr>
    ${f.map(x => `<tr><td>${x.id}</td><td>${esc(x.summary)}</td>
      <td class="muted">${esc(x.source || '')}</td><td class="muted">${esc(x.confidence || '')}</td>
      <td class="muted">${esc(x.from_intent || '')}</td></tr>`).join('')}</table>
    <p class="hint">newest ${f.length}</p>`;
}

function tabFindings(d) {
  if (!d.findings.length) return '<p class="muted">no findings</p>';
  return d.findings.map(f => `<div class="card" style="margin-bottom:.6rem">
    <div class="row"><span class="tag">${esc(f.severity)}</span>
      <b>${esc(f.vulnclass)}</b> <span class="muted">#${f.id} &middot; ${esc(f.proof_basis)} &middot; ${esc(f.status)}</span></div>
    <div>${esc(f.summary)}</div>
    <div class="hint">endpoint ${esc(f.endpoint || '-')} &middot; param ${esc(f.parameter || '-')} &middot; traffic ${esc(JSON.stringify(f.traffic_refs))}</div>
    ${f.evidence ? `<pre>${esc(f.evidence)}</pre>` : ''}
    ${f.poc ? `<pre>${esc(f.poc)}</pre>` : ''}</div>`).join('');
}

function tabAssets(d) {
  if (!d.assets.length) return '<p class="muted">no assets yet</p>';
  return `<table><tr><th>id</th><th>type</th><th>key</th><th>status</th><th>tech</th></tr>
    ${d.assets.map(a => `<tr><td>${a.id}</td><td>${esc(a.type)}</td>
      <td>${esc(a.url || a.domain || a.ip || a.app_name || '')}</td>
      <td>${a.status_code || ''}</td><td class="muted">${esc((a.technologies || []).join(' '))}</td></tr>`).join('')}
    </table>`;
}

function tabActivity(d) {
  if (!d.activity.length) return '<p class="muted">no activity yet</p>';
  return `<table><tr><th>id</th><th>worker</th><th>kind</th><th>summary</th></tr>
    ${d.activity.map(a => `<tr><td>${a.id}</td><td class="muted">${esc(a.worker || '')}</td>
      <td class="muted">${esc(a.kind || '')}</td><td>${esc(a.summary || '')}</td></tr>`).join('')}</table>`;
}

function tabGraph(d) { return `<pre>${esc(JSON.stringify(d.overview, null, 1))}</pre>`; }

function showNew() {
  S.view = 'new'; S.task = 0; clearInterval(S.timer);
  $('#main').innerHTML = `
    <h2>New engagement</h2>
    <div class="card" style="max-width:52rem">
      <div class="hint">goal - the end state you must prove, not a task list</div>
      <textarea id="nGoal" placeholder="Find and prove the highest-impact unauthenticated entry point on app.example.com"></textarea>
      <div class="hint" style="margin-top:.5rem">scope - one per line, kind=value (domain, url, ip, cidr, keyword)</div>
      <textarea id="nScope" placeholder="domain=example.com"></textarea>
      <div class="row" style="margin-top:.5rem">
        <input id="nTitle" placeholder="title (optional)" style="flex:1">
        <button class="pri" onclick="createTask()">create</button>
        <button onclick="cancelNew()">cancel</button>
      </div>
      <div id="nMsg" class="hint" style="margin-top:.5rem"></div>
    </div>`;
}

function cancelNew() {
  S.view = 'task';
  if (S.tasks.length) selectTask(S.tasks[0].id); else location.reload();
}

async function createTask() {
  const goal = $('#nGoal').value.trim();
  if (!goal) { $('#nMsg').textContent = 'goal is required'; return; }
  const scope = $('#nScope').value.split('\n').map(l => l.trim()).filter(Boolean).map(l => {
    const i = l.indexOf('=');
    return i < 0 ? {kind:'domain', value:l} : {kind:l.slice(0,i).trim(), value:l.slice(i+1).trim()};
  });
  const j = await api('/api/task', {goal: goal, title: $('#nTitle').value.trim(), scope: scope});
  if (j.error) { $('#nMsg').textContent = j.error; return; }
  await loadTasks(); selectTask(j.task);
}

async function runTask() {
  const rounds = parseInt($('#rRounds').value || '10', 10);
  const workers = parseInt($('#rWorkers').value || '2', 10);
  const j = await api('/api/run', {task: S.task, rounds: rounds, workers: workers});
  if (j.error) alert(j.error);
  setTimeout(() => refresh(true), 300);
}

async function stopTask() {
  const j = await api('/api/stop', {task: S.task});
  if (j.error) alert(j.error);
  await refresh(true);
}

async function addHint() {
  const text = $('#hintText').value.trim(); if (!text) return;
  const j = await api('/api/hint', {task: S.task, text: text});
  if (j.error) alert(j.error); else { $('#hintText').value = ''; refresh(true); }
}

async function steer(id) {
  const msg = prompt('course correction for intent #' + id); if (!msg) return;
  const j = await api('/api/steer', {task: S.task, intent: id, message: msg});
  if (j.error) alert(j.error);
}

async function kill(id) {
  if (!confirm('stop intent #' + id + '?')) return;
  const j = await api('/api/kill', {task: S.task, intent: id, reason: 'operator'});
  if (j.error) alert(j.error);
}

function exportMd() { window.location = '/api/export?task=' + S.task; }

loadTasks().then(() => { if (S.tasks.length) selectTask(S.tasks[0].id); });
</script></body></html>
"""


def _json_bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode()


def serve(settings, task_id: int = 0) -> int:
    store = Store(settings.db_path)
    engine = Engine(settings, store=store)
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

        def _auth_ok(self) -> bool:
            if not token:
                return True
            return self.headers.get("X-Titan-Token", "") == token

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

        # ---------------------------------------------------------------- GET
        def do_GET(self):  # noqa: N802
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if not self._auth_ok():
                return self._json({"error": "unauthorised"}, 401)

            if u.path == "/":
                return self._html(GUI)

            if u.path == "/api/tasks":
                return self._json({"tasks": [dict(r) for r in store.list_tasks(50)]})

            if u.path == "/api/state":
                tid = int((q.get("task") or [task_id or 0])[0] or 0)
                if not store.get_task(tid):
                    return self._json({"error": f"no task {tid}"}, 404)
                with lock:
                    is_running = tid in running and running[tid].is_alive()
                return self._json({
                    "task": dict(store.get_task(tid)),
                    "overview": store.graph_overview(tid),
                    "findings": store.findings(tid),
                    "assets": store.assets(tid, limit=200),
                    "activity": list(reversed(store.activity(tid, 60))),
                    "running": is_running,
                })

            if u.path == "/api/export":
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

            if u.path == "/api/task":
                goal = str(body.get("goal") or "").strip()
                if not goal:
                    return self._json({"error": "goal is required"}, 400)
                scope = [s for s in (body.get("scope") or [])
                         if isinstance(s, dict) and s.get("value")]
                if not settings.model:
                    return self._json({"error": "no model configured: set TITAN_LLM_MODEL and "
                                                "TITAN_LLM_BASE_URL (see titan doctor)"}, 400)
                try:
                    tid = engine.new_task(goal, str(body.get("title") or ""),
                                          str(body.get("desc") or ""), scope)
                except Exception as e:  # noqa: BLE001
                    return self._json({"error": f"{type(e).__name__}: {e}"}, 500)
                return self._json({"task": tid})

            if u.path == "/api/run":
                tid = int(body.get("task") or 0)
                if not store.get_task(tid):
                    return self._json({"error": f"no task {tid}"}, 404)
                with lock:
                    if tid in running and running[tid].is_alive():
                        return self._json({"error": "already running"}, 409)
                    rounds = max(1, int(body.get("rounds") or settings.max_rounds))
                    workers = max(1, min(int(body.get("workers") or settings.max_workers), 8))

                    def job():
                        try:
                            engine.run_task(tid, rounds=rounds, workers=workers)
                        except Exception as e:  # noqa: BLE001
                            store.log(tid, "engine", "error", f"run failed: {e}")

                    t = threading.Thread(target=job, daemon=True)
                    running[tid] = t
                    t.start()
                return self._json({"started": tid})

            if u.path == "/api/stop":
                tid = int(body.get("task") or 0)
                if not store.get_task(tid):
                    return self._json({"error": "no task"}, 404)
                engine.request_stop(tid)
                return self._json({"stopping": tid})

            if u.path == "/api/hint":
                tid = int(body.get("task") or 0)
                text = str(body.get("text") or "").strip()
                if not (store.get_task(tid) and text):
                    return self._json({"error": "task and text required"}, 400)
                nid = store.add_node(tid, "hint", {"text": text}, origin="operator")
                return self._json({"hint": nid})

            if u.path == "/api/steer":
                tid = int(body.get("task") or 0)
                iid = int(body.get("intent") or 0)
                msg = str(body.get("message") or "").strip()
                if not msg:
                    return self._json({"error": "message required"}, 400)
                ok = engine.steer(iid, msg)
                store.log(tid, "operator", "steer", f"intent {iid}: {msg}")
                return self._json({"steered": bool(ok), "intent": iid})

            if u.path == "/api/kill":
                tid = int(body.get("task") or 0)
                iid = int(body.get("intent") or 0)
                ok = engine.kill(iid, str(body.get("reason") or "operator"))
                store.log(tid, "operator", "kill", f"intent {iid}")
                return self._json({"stopping": bool(ok), "intent": iid})

            return self._json({"error": "not found"}, 404)

    srv = ThreadingHTTPServer((settings.console_bind, settings.console_port), H)
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
