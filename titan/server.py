"""Read-only local console. Binds 127.0.0.1 by default; no mutating endpoints."""
from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .store import Store


def _page(store: Store, task_id: int) -> str:
    tasks = store.list_tasks(20)
    if not task_id and tasks:
        task_id = tasks[0]["id"]
    t = store.get_task(task_id) if task_id else None
    if not t:
        body = "<p>No tasks yet. Run <code>titan new \"goal\" --scope domain=example.com</code>.</p>"
    else:
        ov = store.graph_overview(task_id)
        rows = "".join(
            f"<tr><td>{html.escape(i['state'])}</td><td>{i['id']}</td>"
            f"<td>{html.escape(i['summary'])}</td></tr>"
            for i in ov["open_intents"] + ov["running_intents"])
        facts = "".join(f"<li><b>{f['id']}</b> {html.escape(f['summary'])} "
                        f"<i>({html.escape(str(f.get('confidence')))}/{html.escape(str(f.get('source')))})</i></li>"
                        for f in ov["recent_facts"])
        finds = "".join(
            f"<li><b>[{html.escape(f['severity'])}] {html.escape(f['vulnclass'])}</b> "
            f"{html.escape(f['summary'])}<br><code>{html.escape(f['endpoint'] or '-')}</code></li>"
            for f in store.findings(task_id))
        goals = "".join(f"<li>[{html.escape(g['state'])}] {html.escape(g['text'])}</li>"
                        for g in ov["goals"])
        body = f"""
        <h2>Task #{task_id} — {html.escape(t['title'])}</h2>
        <p class="muted">{html.escape(t['goal'])}</p>
        <p>status <b>{html.escape(t['status'])}</b> · round {ov['round']} ·
           coverage <b>{ov['coverage']['pct']}%</b> ({ov['coverage']['tested']}/{ov['coverage']['assets']}) ·
           findings <b>{ov['findings_total']}</b> · facts {ov['facts_total']}</p>
        <h3>Goals</h3><ul>{goals or '<li>none</li>'}</ul>
        <h3>Open / running intents</h3>
        <table><tr><th>state</th><th>id</th><th>summary</th></tr>{rows or '<tr><td colspan=3>none</td></tr>'}</table>
        <h3>Findings</h3><ul>{finds or '<li>none</li>'}</ul>
        <h3>Recent facts</h3><ul>{facts or '<li>none</li>'}</ul>"""
    nav = "".join(f"<a href='/?task={r['id']}'>#{r['id']} {html.escape(r['title'][:40])}</a> "
                  for r in tasks)
    return f"""<!doctype html><meta charset="utf-8"><title>Titan console</title>
<style>
 body{{font:14px/1.5 ui-monospace,Menlo,monospace;background:#111;color:#ddd;margin:2rem;max-width:64rem}}
 a{{color:#7cc7ff;text-decoration:none}} h1{{font-size:1.1rem;letter-spacing:.08em}}
 table{{border-collapse:collapse;width:100%}} td,th{{border-bottom:1px solid #2a2a2a;padding:.3rem;
 text-align:left;vertical-align:top}} .muted{{color:#888}} nav{{margin:1rem 0}}
</style>
<h1>DEWAGUARD TITAN</h1><nav>{nav}</nav>{body}
<p class="muted">read-only · {len(tasks)} task(s)</p>"""


def serve(settings, task_id: int = 0) -> int:
    store = Store(settings.db_path)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def do_GET(self):  # noqa: N802
            u = urlparse(self.path)
            if u.path == "/api/overview":
                q = parse_qs(u.query)
                tid = int((q.get("task") or [task_id or 0])[0] or 0)
                data = store.graph_overview(tid) if tid else {}
                return self._json(data)
            if u.path == "/api/findings":
                q = parse_qs(u.query)
                tid = int((q.get("task") or [task_id or 0])[0] or 0)
                return self._json({"findings": store.findings(tid)})
            if u.path != "/":
                self.send_error(404)
                return
            q = parse_qs(u.query)
            tid = int((q.get("task") or [task_id or 0])[0] or 0)
            page = _page(store, tid).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

        def _json(self, data):
            raw = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    srv = ThreadingHTTPServer((settings.console_bind, settings.console_port), H)
    print(f"console: http://{settings.console_bind}:{settings.console_port}  (Ctrl-C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0
