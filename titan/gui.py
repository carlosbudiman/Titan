"""The console page: one HTML document, no framework, no build step."""

GUI = r"""<!doctype html>
<html lang="en" data-theme="dark"><head><meta charset="utf-8">
<title>Dewaguard Titan</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script>
  (function () {
    var t = localStorage.getItem('titan-theme');
    if (!t) t = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', t);
  })();
</script>
<style>
:root, [data-theme="light"]{
  --bg:#f5f2f1; --surface:#ffffff; --surface-2:#faf7f7; --line:#e7dedd;
  --fg:#241a1d; --dim:#665558; --brand:#7d2030; --brand-2:#9c2b3c; --on-brand:#ffffff;
  --ok:#1c7a4d; --warn:#8a6a10; --bad:#b3261e; --chip:#f4eaec;
  --shadow:0 1px 2px rgba(60,20,30,.06), 0 6px 18px rgba(60,20,30,.05);
}
[data-theme="dark"]{
  --bg:#120f10; --surface:#1b1517; --surface-2:#221a1d; --line:#332629;
  --fg:#f0e9ea; --dim:#a29194; --brand:#c04a5c; --brand-2:#a53648; --on-brand:#ffffff;
  --ok:#4fbe8a; --warn:#d9b04a; --bad:#ef6a63; --chip:#2b1f23;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 22px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--fg);
  font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",
       "Inter","Noto Sans",Arial,sans-serif;-webkit-font-smoothing:antialiased}
code,pre,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px}
h1,h2,h3{font-weight:600;letter-spacing:-.01em}
header{display:flex;align-items:center;gap:1.4rem;padding:.8rem 1.4rem;
  background:var(--surface);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20;
  box-shadow:var(--shadow);flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:.6rem}
.brand .mark{width:22px;height:22px;border-radius:6px;background:var(--brand);
  display:grid;place-items:center;color:var(--on-brand);font-weight:700;font-size:12px}
.brand h1{font-size:.95rem;margin:0;letter-spacing:.04em;text-transform:uppercase;color:var(--brand)}
nav.top{display:flex;gap:.15rem;background:var(--surface-2);padding:.2rem;border-radius:9px;
  border:1px solid var(--line)}
nav.top button{border:0;background:none;color:var(--dim);padding:.35rem .75rem;border-radius:7px;
  font:inherit;font-size:13px;cursor:pointer}
nav.top button:hover{color:var(--fg)}
nav.top button.on{background:var(--surface);color:var(--brand);font-weight:600;box-shadow:var(--shadow)}
header .spacer{flex:1}
.stat{color:var(--dim);font-size:12.5px}
.stat b{color:var(--fg);font-weight:600}
main{display:grid;grid-template-columns:264px 1fr;min-height:calc(100vh - 57px)}
aside{background:var(--surface);border-right:1px solid var(--line);padding:.9rem;overflow:auto}
aside .head{display:flex;align-items:center;justify-content:space-between;margin-bottom:.6rem}
aside .task{padding:.55rem .6rem;border:1px solid transparent;border-radius:8px;cursor:pointer;
  margin-bottom:.3rem;position:relative}
aside .task:hover{background:var(--surface-2)}
aside .task.on{background:var(--chip);border-color:var(--brand)}
aside .task .t{display:block;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
  padding-right:1rem}
aside .task .m{color:var(--dim);font-size:11.5px;display:block;margin-top:.1rem}
aside .task .kill{position:absolute;right:.3rem;top:.3rem;opacity:0;border:0;background:none;
  color:var(--dim);cursor:pointer;font-size:15px;line-height:1;padding:0 .2rem}
aside .task:hover .kill{opacity:1}
aside .task .kill:hover{color:var(--bad)}
section{padding:1.4rem 1.6rem;overflow:auto}
h2{font-size:1.15rem;margin:.1rem 0 .35rem}
h3{font-size:.76rem;letter-spacing:.05em;color:var(--dim);text-transform:uppercase;margin:1.3rem 0 .5rem}
button{background:var(--surface);color:var(--fg);border:1px solid var(--line);border-radius:8px;
  padding:.4rem .8rem;cursor:pointer;font:inherit;font-size:13px;transition:background .12s}
button:hover{background:var(--surface-2)}
button.pri{background:var(--brand);border-color:var(--brand);color:var(--on-brand);font-weight:500}
button.pri:hover{background:var(--brand-2)}
button.ghost{background:none;border-color:transparent;color:var(--dim)}
button.ghost:hover{color:var(--fg);background:var(--surface-2)}
button.danger{color:var(--bad);border-color:var(--line)}
button.danger:hover{background:var(--chip)}
button:disabled{opacity:.45;cursor:not-allowed}
input,textarea,select{background:var(--surface);color:var(--fg);border:1px solid var(--line);
  border-radius:8px;padding:.45rem .6rem;font:inherit;font-size:13px;width:100%}
input:focus,textarea:focus,select:focus{outline:2px solid var(--brand);outline-offset:-1px}
textarea{resize:vertical;min-height:4.2rem}
table{border-collapse:separate;border-spacing:0;width:100%;background:var(--surface);
  border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:.5rem .65rem;border-bottom:1px solid var(--line);vertical-align:top;
  overflow-wrap:anywhere}
th{color:var(--dim);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;
  background:var(--surface-2)}
tr:last-child td{border-bottom:0}
tr:hover td{background:var(--surface-2)}
.row{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:1.1rem}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:1rem 1.1rem;
  box-shadow:var(--shadow)}
.chip{display:inline-block;padding:.1rem .5rem;border-radius:999px;font-size:11.5px;
  background:var(--chip);color:var(--fg);border:1px solid var(--line)}
.s-open{color:var(--brand)} .s-running,.s-thinking,.s-judging{color:var(--warn)}
.s-done,.s-confirmed,.s-met,.s-achieved,.s-tool{color:var(--ok)}
.s-exhausted,.s-blocked,.s-stopped,.s-failed,.s-abandoned,.s-stale{color:var(--bad)}
.s-idle{color:var(--dim)}
.muted{color:var(--dim)}
pre{white-space:pre-wrap;word-break:break-word;background:var(--surface-2);border:1px solid var(--line);
  border-radius:10px;padding:.7rem;max-height:26rem;overflow:auto;margin:.4rem 0}
.tabs{display:flex;gap:.3rem;margin:1rem 0 .9rem;flex-wrap:wrap;border-bottom:1px solid var(--line)}
.tabs button{border:0;border-bottom:2px solid transparent;border-radius:0;background:none;
  color:var(--dim);padding:.45rem .7rem}
.tabs button:hover{color:var(--fg);background:none}
.tabs button.on{color:var(--brand);border-bottom-color:var(--brand);font-weight:600}
.hint{color:var(--dim);font-size:12px}
.empty{color:var(--dim);padding:1.2rem;text-align:center;border:1px dashed var(--line);
  border-radius:12px;background:var(--surface)}
label.f{display:block;margin:.7rem 0}
label.f span{display:block;color:var(--dim);font-size:12px;margin-bottom:.2rem}
.dot{width:9px;height:9px;border-radius:50%;background:var(--dim);flex:0 0 auto}
.dot.live{background:var(--ok);box-shadow:0 0 0 4px rgba(28,122,77,.14)}
.dot.tool{background:var(--warn);box-shadow:0 0 0 4px rgba(154,116,18,.14)}
.dot.idle{background:var(--dim)}
#graphwrap{overflow:auto;border:1px solid var(--line);border-radius:12px;background:var(--surface)}
#graphwrap svg{display:block}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-thumb{background:var(--line);border-radius:8px}
::-webkit-scrollbar-track{background:transparent}
#toasts{position:fixed;right:1.1rem;bottom:1.1rem;display:flex;flex-direction:column;gap:.5rem;
  z-index:50;max-width:26rem}
.toast{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--brand);
  border-radius:8px;padding:.6rem .8rem;box-shadow:var(--shadow);font-size:13px}
.toast.err{border-left-color:var(--bad)}
.toast.ok{border-left-color:var(--ok)}
@media(max-width:900px){main{grid-template-columns:1fr}aside{border-right:0;
  border-bottom:1px solid var(--line)}section{padding:1rem}.grid2{grid-template-columns:1fr}}
</style></head>
<body>
<header>
  <div class="brand"><span class="mark">T</span><h1>Dewaguard Titan</h1></div>
  <nav class="top" id="topnav"></nav>
  <span class="spacer"></span>
  <span class="stat" id="hstats"></span>
  <button class="ghost" id="themeBtn" title="Toggle light / dark" onclick="toggleTheme()">◐</button>
</header>
<main>
  <aside>
    <div class="head"><h3 style="margin:0">Engagements</h3>
      <button class="pri" onclick="showNew()">+ New</button></div>
    <div id="tasks"></div>
  </aside>
  <section id="main"><div class="empty">Select an engagement, or create one.</div></section>
</main>
<div id="toasts"></div>
<script>
const $ = s => document.querySelector(s);
const esc = s => String(s === null || s === undefined ? '' : s)
  .replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let S = {tasks: [], task: 0, data: null, tab: 'overview', view: 'task',
         agents: null, settings: null, skills: null, traffic: null,
         graph: null, nodeSel: 0, models: [], trafficQ: '', lastSig: ''};

const VIEWS = [['task','Engagement'],['agents','Agents'],['settings','Settings'],
               ['skills','Skills'],['traffic','Traffic']];

function toast(msg, kind) {
  const el = document.createElement('div');
  el.className = 'toast ' + (kind || '');
  el.textContent = msg;
  $('#toasts').appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

async function api(path, body) {
  const opts = body === undefined ? {} : {method: 'POST',
    headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)};
  const r = await fetch(path, opts);
  const txt = await r.text();
  let j; try { j = JSON.parse(txt); } catch (e) { j = {error: txt}; }
  if (!r.ok && !j.error) j.error = 'HTTP ' + r.status;
  return j;
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('titan-theme', next);
  if (S.view === 'task' && S.tab === 'graph' && S.graph) $('#pane').innerHTML = graphHtml(S.graph);
}

function drawNav() {
  $('#topnav').innerHTML = VIEWS.map(([v, label]) =>
    `<button class="${S.view === v ? 'on' : ''}" onclick="go('${v}')">${label}</button>`).join('');
}

async function go(view) {
  S.view = view; drawNav();
  if (view === 'task' && S.task) await refresh(true);
  if (view === 'agents') await loadAgents();
  if (view === 'settings') await loadSettings();
  if (view === 'skills') await loadSkills();
  if (view === 'traffic') await loadTraffic();
}

async function loadTasks() {
  const j = await api('/api/tasks');
  if (j.error) return;
  S.tasks = j.tasks || [];
  const el = $('#tasks');
  if (!el) return;
  el.innerHTML = S.tasks.map(t => `
    <div class="task ${t.id === S.task ? 'on' : ''}" onclick="selectTask(${t.id})">
      <button class="kill" title="Delete engagement"
        onclick="event.stopPropagation(); delTask(${t.id})">&times;</button>
      <span class="t">${esc(t.title || t.goal)}</span>
      <span class="m">#${t.id} · <span class="s-${esc(t.status)}">${esc(t.status)}</span> · ${t.round_no} round${t.round_no === 1 ? '' : 's'}</span>
    </div>`).join('') || '<div class="empty">No engagements yet</div>';
}

async function selectTask(id) {
  S.task = id; S.view = 'task'; S.nodeSel = 0; drawNav();
  await loadTasks();
  await refresh(true);
}

async function refresh(force) {
  if (!S.task || S.view !== 'task') return;
  const j = await api('/api/state?task=' + S.task);
  if (j.error) {
    if (force) toast(j.error, 'err');
    S.task = 0; S.data = null;
    $('#main').innerHTML = '<div class="empty">' + esc(j.error) + '</div>';
    $('#hstats').innerHTML = '';
    return;
  }
  const prev = S.data;
  S.data = j;
  const sig = [j.task.status, j.overview.round, j.overview.facts_total,
               j.overview.findings_total, j.overview.open_intents.length,
               j.overview.running_intents.length, j.running ? 1 : 0,
               j.approval ? 1 : 0, S.tab].join('|');
  $('#hstats').innerHTML = `<b>#${j.task.id}</b> · <b class="s-${esc(j.task.status)}">${esc(j.task.status)}</b>
    · round <b>${j.overview.round}</b> · coverage <b>${j.overview.coverage.pct}%</b>
    · findings <b>${j.overview.findings_total}</b>
    ${j.running ? '· <span class="s-running">running</span>' : ''}`;
  if (!force && sig === S.lastSig && prev) return;   // nothing changed: leave the DOM alone
  S.lastSig = sig;
  const scroller = $('#main');
  const sy = window.scrollY, st = scroller ? scroller.scrollTop : 0;
  render();
  window.scrollTo(0, sy);
  if (scroller) scroller.scrollTop = st;
}

function render() {
  if (S.view !== 'task' || !S.data) return;
  const ae = document.activeElement;
  if (ae && ae.closest && ae.closest('#main') &&
      (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA' || ae.tagName === 'SELECT')) return;
  const draftHint = (document.querySelector('#hintText') || {}).value || '';
  const draftScope = (document.querySelector('#scopeValue') || {}).value || '';
  const d = S.data, ov = d.overview;
  const tabs = ['overview','agents','intents','facts','findings','assets','traffic','activity','graph'];
  $('#main').innerHTML = `
    <div class="row" style="justify-content:space-between;align-items:flex-start">
      <div>
        <h2>${esc(d.task.title || ('Engagement #' + d.task.id))}</h2>
        <div class="muted" style="max-width:60rem">${esc(d.task.goal)}</div>
        <div class="hint mono" style="margin-top:.25rem">artifacts: ${esc(ov.workdir || '(default ~/.titan/runs/tasks/' + d.task.id + ')')}</div>
      </div>
      <div class="row">
        <button class="ghost" onclick="renameTask()">Rename</button>
        <button class="danger" onclick="delTask(${d.task.id})">Delete</button>
      </div>
    </div>
    <div class="row" style="margin:1rem 0">
      <label class="hint">Mode
        <select id="rMode" style="width:auto">
          <option value="autonomous" ${(d.mode || 'autonomous') === 'autonomous' ? 'selected' : ''}>Autonomous — run until the goal is met or you stop it</option>
          <option value="approval" ${d.mode === 'approval' ? 'selected' : ''}>Approval — confirm before each round</option>
        </select></label>
      <label class="hint">Workers <input id="rWorkers" style="width:4.5rem" value="2"></label>
      <button class="pri" onclick="runTask()" ${d.running ? 'disabled' : ''}>${d.running ? 'Running…' : 'Start'}</button>
      <button onclick="stopTask()" ${(d.running || d.approval) ? '' : 'disabled'}>Stop</button>
      <button onclick="exportMd()">Export report</button>
      <span class="muted" style="margin-left:.4rem">${ov.facts_total} facts · ${ov.findings_total} findings ·
        coverage ${ov.coverage.pct}% (${ov.coverage.tested}/${ov.coverage.assets})</span>
    </div>
    ${d.approval ? `<div class="card" style="border-color:var(--brand);margin-bottom:1rem">
      <div class="row"><b>Waiting for your approval</b>
        <span class="chip">round ${d.approval.round_no}</span>
        <span style="flex:1"></span>
        <button class="pri" onclick="decide('approve')">Approve &amp; continue</button>
        <button class="danger" onclick="decide('deny')">Stop here</button></div>
      <div class="muted" style="margin-top:.35rem">${esc(d.approval.note || '')}</div></div>` : ''}
    <div class="tabs">${tabs.map(t => `<button class="${t === S.tab ? 'on' : ''}" onclick="setTab('${t}')">${t}</button>`).join('')}</div>
    <div id="pane"></div>`;
  const pane = $('#pane');
  if (S.tab === 'overview') pane.innerHTML = tabOverview(d);
  if (S.tab === 'agents') { pane.innerHTML = '<div class="empty">Loading agents…</div>'; loadAgents(); }
  if (S.tab === 'intents') pane.innerHTML = tabIntents(d);
  if (S.tab === 'facts') pane.innerHTML = tabFacts(d);
  if (S.tab === 'findings') pane.innerHTML = tabFindings(d);
  if (S.tab === 'assets') pane.innerHTML = tabAssets(d);
  if (S.tab === 'traffic') { pane.innerHTML = '<div class="empty">Loading traffic…</div>'; loadTraffic(); }
  if (S.tab === 'activity') pane.innerHTML = tabActivity(d);
  if (S.tab === 'graph') { pane.innerHTML = '<div class="empty">Loading graph…</div>'; loadGraph(); }
  if (draftHint && $('#hintText')) $('#hintText').value = draftHint;
  if (draftScope && $('#scopeValue')) $('#scopeValue').value = draftScope;
}

function setTab(t) { S.tab = t; render(); }

function intentRow(i) {
  return `<div class="row" style="align-items:flex-start;margin-bottom:.35rem">
    <span class="chip s-${esc(i.state)}">${esc(i.state)}</span>
    <span style="flex:1">#${i.id} ${esc(i.summary)}</span>
    ${i.state === 'running'
      ? `<button onclick="steer(${i.id})">Steer</button><button class="danger" onclick="kill(${i.id})">Stop</button>`
      : ''}</div>`;
}

function tabOverview(d) {
  const ov = d.overview;
  const queue = [...ov.running_intents, ...ov.open_intents];
  return `<div class="grid2">
    <div class="card"><h3 style="margin-top:0">Goals</h3>
      ${ov.goals.map(g => `<div class="row" style="margin-bottom:.3rem">
        <span class="chip s-${esc(g.state)}">${esc(g.state)}</span>
        <span>${esc(g.text)}</span></div>`).join('') || '<span class="muted">none</span>'}
      <h3>Constraints</h3>
      ${ov.constraints.map(c => `<div><span class="chip">${esc(c.kind)}</span> ${esc(c.text)}</div>`).join('') || '<span class="muted">none</span>'}
      ${ov.hints.length ? '<h3>Hints</h3>' + ov.hints.map(h => `<div>· ${esc(h.text)}</div>`).join('') : ''}
      <h3>Authorized scope</h3>
      ${ov.scope.map(s => `<div><span class="chip">${esc(s.kind)}</span> <code>${esc(s.value)}</code></div>`).join('')
        || '<div class="s-failed">No scope — every targeted command is refused.</div>'}
      <div class="row" style="margin-top:.5rem">
        <select id="scopeKind" style="width:7rem">
          <option>domain</option><option>ip</option><option>cidr</option>
          <option>url</option><option>keyword</option>
        </select>
        <input id="scopeValue" placeholder="value" style="flex:1">
        <button onclick="addScope()">Add</button>
      </div>
    </div>
    <div class="card"><h3 style="margin-top:0">Queue</h3>
      ${queue.map(intentRow).join('') || '<span class="muted">idle — nothing dispatched</span>'}
      <h3>Add a hint</h3>
      <textarea id="hintText" placeholder="Instructions for the next planning rounds"></textarea>
      <div class="row" style="margin-top:.5rem"><button class="pri" onclick="addHint()">Queue hint</button></div>
    </div></div>`;
}

async function loadAgents() {
  if (!S.task) return;
  S.agents = await api('/api/agents?task=' + S.task);
  if (S.tab !== 'agents' && S.view !== 'agents') return;
  const html = agentsHtml(S.agents);
  if (S.view === 'agents') $('#main').innerHTML = html;
  else if ($('#pane')) $('#pane').innerHTML = html;
}

function agentsHtml(a) {
  if (!a || a.error) return '<div class="empty">' + esc((a && a.error) || 'no data') + '</div>';
  const live = a.live || [];
  const cards = live.length ? live.map(x => {
    const cls = x.state === 'tool' ? 'tool' : (x.idle_s > 20 ? 'idle' : 'live');
    return `<div class="card" style="margin-bottom:.6rem">
      <div class="row" style="align-items:flex-start;flex-wrap:nowrap">
        <span class="dot ${cls}" style="margin-top:.5rem"></span>
        <div style="flex:1">
          <div class="row"><b>${esc(x.key)}</b>
            <span class="chip s-${esc(x.state)}">${esc(x.state)}</span>
            ${x.intent ? `<span class="muted">intent #${x.intent}</span>` : ''}
            <span class="muted">${x.elapsed_s}s · ${x.turns} turns · ${(x.tokens_in || 0) + (x.tokens_out || 0)} tokens</span>
            ${x.state === 'tool' && x.intent
              ? `<button onclick="steer(${x.intent})">Steer</button>
                 <button class="danger" onclick="kill(${x.intent})">Stop</button>` : ''}
          </div>
          <div class="muted mono" style="margin-top:.2rem">${esc(x.tool ? x.tool + ' — ' : '')}${esc((x.note || '').slice(0, 200))}</div>
        </div></div></div>`;
  }).join('') : '<div class="empty">No agent is running. Start a run to see the planner and workers here.</div>';

  const usage = (a.usage || []).map(u => `<tr><td>${esc(u.agent)}</td><td>${u.calls}</td>
      <td>${u.tin || 0}</td><td>${u.tout || 0}</td></tr>`).join('');
  const act = (a.activity || []).slice(0, 40).map(x => `<tr><td class="muted">${esc(x.worker || '')}</td>
      <td class="muted">${esc(x.kind || '')}</td><td>${esc((x.summary || '').slice(0, 240))}</td></tr>`).join('');

  return `<h3 style="margin-top:0">Live agents</h3>${cards}
    <h3>Token usage</h3>
    <table><tr><th>Agent</th><th>Calls</th><th>In</th><th>Out</th></tr>
      ${usage || '<tr><td colspan=4 class="muted">none yet</td></tr>'}</table>
    <h3>Recent steps</h3>
    <table><tr><th>Worker</th><th>Kind</th><th>Detail</th></tr>
      ${act || '<tr><td colspan=3 class="muted">none yet</td></tr>'}</table>`;
}

function tabIntents(d) {
  const ov = d.overview;
  const all = [...ov.running_intents, ...ov.open_intents, ...ov.recent_done];
  if (!all.length) return '<div class="empty">No intents dispatched yet.</div>';
  return `<table><tr><th>State</th><th>#</th><th>Direction</th><th>Assets</th><th></th></tr>
    ${all.map(i => `<tr><td class="s-${esc(i.state)}">${esc(i.state)}</td><td>${i.id}</td>
      <td>${esc(i.summary)}<div class="hint">${esc(i.blocked_reason || '')}</div></td>
      <td>${(i.asset_ids || []).join(', ')}</td>
      <td>${i.state === 'running' ? `<button onclick="steer(${i.id})">Steer</button>
        <button class="danger" onclick="kill(${i.id})">Stop</button>` : ''}</td></tr>`).join('')}
    </table>`;
}

function tabFacts(d) {
  const f = d.overview.recent_facts;
  if (!f.length) return '<div class="empty">No facts recorded yet.</div>';
  return `<table><tr><th>#</th><th>Fact</th><th>Source</th><th>Confidence</th><th>From intent</th></tr>
    ${f.map(x => `<tr><td>${x.id}</td><td>${esc(x.summary)}</td>
      <td class="muted">${esc(x.source || '')}</td><td class="muted">${esc(x.confidence || '')}</td>
      <td class="muted">${esc(x.from_intent || '')}</td></tr>`).join('')}</table>
    <p class="hint">Showing the newest ${f.length}.</p>`;
}

function tabFindings(d) {
  if (!d.findings.length) return '<div class="empty">No findings recorded.</div>';
  const opts = ['open', 'confirmed', 'false_positive', 'duplicate', 'ignored'];
  return d.findings.map(f => `<div class="card" style="margin-bottom:.7rem">
    <div class="row"><span class="chip">${esc(f.severity)}</span>
      <b>${esc(f.vulnclass)}</b> <span class="muted">#${f.id} · ${esc(f.proof_basis)}</span>
      <span style="flex:1"></span>
      <select style="width:auto" onchange="setFinding(${f.id}, this.value)">
        ${opts.map(o => `<option ${o === f.status ? 'selected' : ''}>${o}</option>`).join('')}
      </select></div>
    <div style="margin:.4rem 0">${esc(f.summary)}</div>
    <div class="hint">Endpoint ${esc(f.endpoint || '—')} · parameter ${esc(f.parameter || '—')} ·
      traffic ${esc(JSON.stringify(f.traffic_refs))}</div>
    ${f.evidence ? `<pre>${esc(f.evidence)}</pre>` : ''}
    ${f.poc ? `<pre>${esc(f.poc)}</pre>` : ''}</div>`).join('');
}

function tabAssets(d) {
  if (!d.assets.length) return '<div class="empty">No assets discovered yet.</div>';
  return `<table><tr><th>#</th><th>Type</th><th>Target</th><th>Status</th><th>Technologies</th></tr>
    ${d.assets.map(a => `<tr><td>${a.id}</td><td>${esc(a.type)}</td>
      <td>${esc(a.url || a.domain || a.ip || a.app_name || '')}</td>
      <td>${a.status_code || ''}</td><td class="muted">${esc((a.technologies || []).join(' '))}</td></tr>`).join('')}
    </table>`;
}

function tabActivity(d) {
  if (!d.activity.length) return '<div class="empty">No activity yet.</div>';
  return `<table><tr><th>#</th><th>Worker</th><th>Kind</th><th>Summary</th></tr>
    ${d.activity.map(a => `<tr><td>${a.id}</td><td class="muted">${esc(a.worker || '')}</td>
      <td class="muted">${esc(a.kind || '')}</td><td>${esc(a.summary || '')}</td></tr>`).join('')}</table>`;
}

async function loadGraph() {
  if (!S.task) return;
  S.graph = await api('/api/graph?task=' + S.task);
  if (S.tab !== 'graph') return;
  $('#pane').innerHTML = graphHtml(S.graph);
}

function graphHtml(g) {
  if (!g || g.error) return '<div class="empty">' + esc((g && g.error) || 'no data') + '</div>';
  const nodes = g.nodes || [], edges = g.edges || [];
  const level = {}; const kids = {};
  edges.forEach(e => (kids[e.src] = kids[e.src] || []).push(e.dst));
  const roots = nodes.filter(n => n.kind === 'begin' || !edges.some(e => e.dst === n.id));
  const queue = roots.map(n => [n.id, 0]); roots.forEach(n => level[n.id] = 0);
  while (queue.length) {
    const [id, lv] = queue.shift();
    (kids[id] || []).forEach(k => {
      if (level[k] === undefined) { level[k] = lv + 1; queue.push([k, lv + 1]); }
    });
  }
  nodes.forEach(n => { if (level[n.id] === undefined) level[n.id] = 0; });
  const cols = {}; nodes.forEach(n => (cols[level[n.id]] = cols[level[n.id]] || []).push(n));
  const W = 200, H = 36, GX = 64, GY = 16, PAD = 22;
  const maxLevel = Math.max(0, ...Object.keys(cols).map(Number));
  const height = PAD * 2 + Math.max(...Object.values(cols).map(c => c.length), 1) * (H + GY);
  const width = PAD * 2 + (maxLevel + 1) * (W + GX);
  const pos = {};
  Object.keys(cols).forEach(lv => cols[lv].forEach((n, i) => {
    pos[n.id] = {x: PAD + Number(lv) * (W + GX), y: PAD + i * (H + GY)};
  }));
  const css = getComputedStyle(document.documentElement);
  const v = (name, fallback) => (css.getPropertyValue(name) || fallback).trim();
  const surface = v('--surface', '#fff'), line = v('--line', '#ddd'), fg = v('--fg', '#222');
  const dim = v('--dim', '#777'), brand = v('--brand', '#7d2030');
  const palette = {begin: line, goal: '#2f6b4f', intent: brand, fact: '#4b6b8a',
                   finding: '#8a2f3f', hint: '#8a6b2f', digest: line};
  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg"
      font-family="-apple-system,Segoe UI,Roboto,sans-serif">`;
  edges.forEach(e => {
    const a = pos[e.src], b = pos[e.dst]; if (!a || !b) return;
    const x1 = a.x + W, y1 = a.y + H / 2, x2 = b.x, y2 = b.y + H / 2, mx = (x1 + x2) / 2;
    svg += `<path d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}" fill="none"
      stroke="${line}" stroke-width="1.2"/>`;
    svg += `<text x="${mx - 10}" y="${(y1 + y2) / 2 - 4}" fill="${dim}" font-size="9">${esc(e.rel)}</text>`;
  });
  nodes.forEach(n => {
    const p = pos[n.id];
    const tint = palette[n.kind] || line;
    const sel = n.id === S.nodeSel;
    svg += `<g style="cursor:pointer" onclick="showNode(${n.id})">
      <title>${esc(n.kind)} #${n.id}: ${esc(n.label || '')}</title>
      <rect x="${p.x}" y="${p.y}" width="${W}" height="${H}" rx="7" fill="${surface}"
        stroke="${sel ? brand : tint}" stroke-width="${sel ? 2.4 : 1.3}"/>
      <rect x="${p.x}" y="${p.y + 6}" width="3.5" height="${H - 12}" rx="2" fill="${tint}"/>
      <text x="${p.x + 12}" y="${p.y + 15}" fill="${dim}" font-size="9.5">${esc(n.kind)} #${n.id}</text>
      <text x="${p.x + 12}" y="${p.y + 28}" fill="${fg}" font-size="10.5">${esc((n.label || '').slice(0, 32))}</text>
      </g>`;
  });
  svg += '</svg>';
  return `<div class="row" style="margin-bottom:.5rem">
      <span class="hint">${nodes.length} nodes · ${edges.length} edges — click a node for its payload</span>
      <button onclick="loadGraph()">Refresh</button></div>
    <div id="graphwrap">${svg}</div>
    <div id="nodedetail" style="margin-top:.6rem">${S.nodeSel ? '' : '<p class="hint">Select a node to see its payload.</p>'}</div>`;
}

async function showNode(id) {
  S.nodeSel = id;
  if (S.graph) $('#pane').innerHTML = graphHtml(S.graph);
  const j = await api('/api/node?id=' + id);
  const el = $('#nodedetail');
  if (el) el.innerHTML = j.error ? `<div class="empty">${esc(j.error)}</div>`
    : `<pre>${esc(JSON.stringify(j, null, 1))}</pre>`;
}

async function loadSettings() {
  S.settings = await api('/api/settings');
  renderSettings();
}

function renderSettings() {
  const s = S.settings || {};
  const llm = s.llm || {}, run = s.run || {};
  $('#main').innerHTML = `
    <h2>Settings</h2>
    <div class="grid2">
      <div class="card">
        <h3 style="margin-top:0">Model</h3>
        <label class="f"><span>Endpoint (OpenAI-compatible)</span>
          <input id="sUrl" value="${esc(llm.base_url || '')}"></label>
        <label class="f"><span>Model</span>
          <input id="sModel" value="${esc(llm.model || '')}"></label>
        <div class="row"><button onclick="listModels()">List models</button>
          <span class="hint" id="sModelsHint"></span></div>
        <div id="sModels" class="hint" style="max-height:9rem;overflow:auto;margin-top:.4rem"></div>
        <label class="f"><span>API key — ${esc(llm.key_masked || 'unset')} via ${esc(llm.key_source || '—')}</span>
          <input id="sKey" type="password" placeholder="leave blank to keep the current key" autocomplete="off"></label>
        <div class="grid2">
          <label class="f"><span>Timeout (s)</span><input id="sTimeout" value="${esc(llm.timeout || 600)}"></label>
          <label class="f"><span>Max tokens (0 = default)</span><input id="sMaxTokens" value="${esc(llm.max_tokens || 0)}"></label>
        </div>
        <label class="f"><span>Temperature</span><input id="sTemp" value="${esc(llm.temperature || 0.2)}"></label>
      </div>
      <div class="card">
        <h3 style="margin-top:0">Run defaults</h3>
        <label class="f"><span>Requests per second per host</span><input id="sRps" value="${esc(run.rps || '2')}"></label>
        <label class="f"><span>Parallel workers</span><input id="sWorkers" value="${esc(run.max_workers || '2')}"></label>
        <label class="f"><span>Noise profile</span>
          <select id="sNoise">${['quiet', 'balanced', 'aggressive', 'off'].map(o =>
            `<option ${o === (run.noise_profile || 'balanced') ? 'selected' : ''}>${o}</option>`).join('')}</select></label>
        <div class="row" style="margin-top:.9rem">
          <button class="pri" onclick="saveSettings()">Save</button>
          <button onclick="testSettings()">Test connection</button>
        </div>
        <div id="sMsg" class="hint" style="margin-top:.5rem"></div>
        <h3>Storage</h3>
        <div class="hint">The API key is written to <code>~/.titan/secrets.json</code> with mode 0600 and is
          never stored in the database or returned to this page. Values here override the
          <code>TITAN_*</code> environment variables, except <code>TITAN_LLM_API_KEY</code>, which
          takes precedence over the saved key.</div>
      </div>
    </div>`;
}

async function listModels() {
  const url = $('#sUrl').value.trim(), key = $('#sKey').value.trim();
  $('#sModelsHint').textContent = 'probing…';
  const j = await api('/api/models?url=' + encodeURIComponent(url) +
                      (key ? '&key=' + encodeURIComponent(key) : ''));
  if (j.error) { $('#sModelsHint').textContent = j.error; return; }
  S.models = j.models || [];
  $('#sModelsHint').textContent = S.models.length + ' available';
  $('#sModels').innerHTML = S.models.map(m =>
    `<div style="cursor:pointer;padding:.15rem 0" onclick="pickModel('${esc(m).replace(/'/g, "\\'")}')">${esc(m)}</div>`).join('');
}

function pickModel(m) { $('#sModel').value = m; }

async function saveSettings() {
  const body = {
    llm: {base_url: $('#sUrl').value.trim(), model: $('#sModel').value.trim(),
          timeout: parseInt($('#sTimeout').value || '600', 10),
          max_tokens: parseInt($('#sMaxTokens').value || '0', 10),
          temperature: parseFloat($('#sTemp').value || '0.2')},
    run: {rps: $('#sRps').value.trim(), max_workers: $('#sWorkers').value.trim(),
          noise_profile: $('#sNoise').value},
    api_key: $('#sKey').value.trim() || undefined};
  const j = await api('/api/settings', body);
  $('#sKey').value = '';
  if (j.error) { toast(j.error, 'err'); return; }
  S.settings = j; renderSettings(); toast('Settings saved', 'ok');
}

async function testSettings() {
  $('#sMsg').textContent = 'Testing…';
  const j = await api('/api/settings/test', {
    base_url: $('#sUrl').value.trim(), model: $('#sModel').value.trim(),
    api_key: $('#sKey').value.trim() || undefined});
  if (j.error) { $('#sMsg').innerHTML = '<span class="s-failed">' + esc(j.error) + '</span>'; return; }
  $('#sMsg').innerHTML = `<span class="s-done">Connected in ${j.latency_ms} ms — ${esc((j.reply || '').slice(0, 60))}</span>`;
}

async function loadSkills() {
  const j = await api('/api/skills');
  S.skills = j.skills || [];
  $('#main').innerHTML = `<h2>Skills</h2>
    <div class="grid2">
      <div class="card"><h3 style="margin-top:0">Installed (${S.skills.length})</h3>
        ${S.skills.map(s => `<div style="cursor:pointer;margin-bottom:.5rem"
          onclick="readSkill('${esc(s.name).replace(/'/g, "\\'")}')">
          <b>${esc(s.name)}</b><div class="hint">${esc(s.description || '')}</div></div>`).join('')}
      </div>
      <div class="card"><h3 style="margin-top:0">SKILL.md</h3>
        <pre id="skillBody" class="hint">Select a skill.</pre></div>
    </div>`;
}

async function readSkill(name) {
  const j = await api('/api/skill?name=' + encodeURIComponent(name));
  $('#skillBody').textContent = j.body || j.error || '';
}

async function loadTraffic() {
  if (!S.task) { $('#main').innerHTML = '<div class="empty">Select an engagement first.</div>'; return; }
  const q = (S.trafficQ || '');
  const j = await api('/api/traffic?task=' + S.task + (q ? '&q=' + encodeURIComponent(q) : ''));
  const rows = j.traffic || [];
  const html = `<h2>Recorded traffic</h2>
    <div class="row" style="margin-bottom:.7rem">
      <input id="tq" placeholder="Search URL or response body" value="${esc(q)}" style="width:22rem">
      <button onclick="S.trafficQ=$('#tq').value; loadTraffic()">Search</button>
      <span class="hint">${rows.length} record(s)</span>
    </div>
    ${rows.length ? `<table><tr><th>#</th><th>Method</th><th>URL</th><th>Status</th><th>Bytes</th></tr>
      ${rows.map(t => `<tr style="cursor:pointer" onclick="readTraffic(${t.id})">
        <td>${t.id}</td><td>${esc(t.method)}</td><td>${esc(t.url)}</td>
        <td class="s-${t.status >= 400 ? 'failed' : 'done'}">${t.status}</td><td>${t.rlen}</td></tr>`).join('')}
      </table>` : '<div class="empty">No traffic recorded for this engagement.</div>'}
    <div id="tdetail"></div>`;
  if (S.view === 'traffic') $('#main').innerHTML = html;
  else if ($('#pane')) $('#pane').innerHTML = html;
}

async function readTraffic(id) {
  const j = await api('/api/traffic_one?id=' + id);
  const el = $('#tdetail'); if (!el) return;
  el.innerHTML = `<h3>Request ${id}</h3><pre>${esc(JSON.stringify(
    {method: j.method, url: j.url, status: j.status, req_headers: j.req_headers}, null, 1))}</pre>
    <h3>Response headers</h3><pre>${esc(JSON.stringify(j.resp_headers || {}, null, 1))}</pre>
    <h3>Response body</h3><pre>${esc((j.resp_body || '').slice(0, 20000))}</pre>`;
}

function showNew() {
  S.view = 'new'; S.task = 0; drawNav(); $('#hstats').innerHTML = '';
  $('#main').innerHTML = `
    <h2>New engagement</h2>
    <div class="card" style="max-width:56rem">
      <label class="f"><span>Goal — the end state you must prove, not a task list</span>
        <textarea id="nGoal" placeholder="Find and prove the highest-impact unauthenticated entry point on app.example.com"></textarea></label>
      <label class="f"><span>Authorized targets — one per line, kind=value (domain, url, ip, cidr, keyword)</span>
        <textarea id="nScope" placeholder="domain=example.com"></textarea></label>
      <label class="f"><span>Title (optional)</span>
        <input id="nTitle" placeholder="Acme — external web assessment"></label>
      <label class="f"><span>Run mode</span>
        <select id="nMode">
          <option value="autonomous">Autonomous — keep going until the goal is met or you stop it</option>
          <option value="approval">Approval — confirm before every round</option>
        </select></label>
      <label class="f"><span>Artifact directory — notes, loot and captures for this engagement (optional)</span>
        <input id="nWorkdir" placeholder="blank = ~/.titan/runs/tasks/&lt;id&gt;"></label>
      <div class="row" style="margin-top:.8rem">
        <button class="pri" onclick="createTask()" id="nCreate">Create engagement</button>
        <button class="ghost" onclick="cancelNew()">Cancel</button>
        <span id="nMsg" class="hint"></span>
      </div>
    </div>`;
  $('#nGoal').focus();
}

function cancelNew() { if (S.tasks.length) selectTask(S.tasks[0].id); else go('settings'); }

async function createTask() {
  const goal = $('#nGoal').value.trim();
  if (!goal) { $('#nMsg').textContent = 'A goal is required.'; return; }
  const scope = $('#nScope').value.split('\n').map(l => l.trim()).filter(Boolean).map(l => {
    const i = l.indexOf('=');
    return i < 0 ? {kind: 'domain', value: l} : {kind: l.slice(0, i).trim(), value: l.slice(i + 1).trim()};
  });
  const btn = $('#nCreate');
  btn.disabled = true; btn.textContent = 'Creating…';
  $('#nMsg').textContent = 'Decomposing the goal into measurable targets…';
  const workdir = ($('#nWorkdir').value || '').trim();
  const j = await api('/api/task', {goal: goal, title: $('#nTitle').value.trim(),
                                    scope: scope, workdir: workdir,
                                    mode: $('#nMode').value});
  if (j.error) {
    btn.disabled = false; btn.textContent = 'Create engagement';
    $('#nMsg').textContent = j.error; toast(j.error, 'err'); return;
  }
  await loadTasks();
  toast('Engagement #' + j.task + ' created', 'ok');
  await selectTask(j.task);
}

async function delTask(id) {
  if (!confirm('Delete engagement #' + id + '?\n\n' +
               'This removes its goals, intents, facts, findings and recorded traffic. ' +
               'It cannot be undone.')) return;
  const j = await api('/api/task/delete', {task: id});
  if (j.error) { toast(j.error, 'err'); return; }
  toast('Engagement #' + id + ' deleted', 'ok');
  if (S.task === id) { S.task = 0; S.data = null; }
  await loadTasks();
  if (S.tasks.length) await selectTask(S.tasks[0].id);
  else {
    $('#hstats').innerHTML = '';
    $('#main').innerHTML = '<div class="empty">Select an engagement, or create one.</div>';
  }
}

async function renameTask() {
  const cur = S.data ? (S.data.task.title || '') : '';
  const title = prompt('Engagement title', cur);
  if (title === null) return;
  const j = await api('/api/task/rename', {task: S.task, title: title.trim()});
  if (j.error) { toast(j.error, 'err'); return; }
  toast('Renamed', 'ok');
  await loadTasks(); await refresh(true);
}

async function runTask() {
  const workers = parseInt($('#rWorkers').value || '2', 10);
  const mode = $('#rMode').value;
  const j = await api('/api/run', {task: S.task, workers: workers, mode: mode});
  if (j.error) { toast(j.error, 'err'); return; }
  toast(mode === 'approval' ? 'Started in approval mode — you will be asked each round'
                            : 'Running autonomously — press Stop to end it', 'ok');
  await refresh(true);
}

async function decide(decision) {
  const j = await api('/api/approve', {task: S.task, decision: decision});
  if (j.error) { toast(j.error, 'err'); return; }
  toast(decision === 'approve' ? 'Approved — continuing' : 'Denied — stopping', 'ok');
  await refresh(true);
}

async function stopTask() {
  const j = await api('/api/stop', {task: S.task});
  if (j.error) { toast(j.error, 'err'); return; }
  toast('Stopping after the current step', 'ok');
  await refresh(true);
}

async function addScope() {
  const kind = $('#scopeKind').value, value = ($('#scopeValue').value || '').trim();
  if (!value) return;
  const j = await api('/api/scope', {task: S.task, kind: kind, value: value});
  if (j.error) { toast(j.error, 'err'); return; }
  toast('Scope added — ' + kind + '=' + value, 'ok');
  $('#scopeValue').value = '';
  await refresh(true);
}

async function addHint() {
  const text = $('#hintText').value.trim(); if (!text) return;
  const j = await api('/api/hint', {task: S.task, text: text});
  if (j.error) { toast(j.error, 'err'); return; }
  $('#hintText').value = '';
  toast('Hint queued', 'ok');
  await refresh(true);
}

async function steer(id) {
  const msg = prompt('Course correction for intent #' + id); if (!msg) return;
  const j = await api('/api/steer', {task: S.task, intent: id, message: msg});
  if (j.error) toast(j.error, 'err'); else toast('Sent to worker ' + id, 'ok');
}

async function kill(id) {
  if (!confirm('Stop intent #' + id + '?')) return;
  const j = await api('/api/kill', {task: S.task, intent: id, reason: 'operator'});
  if (j.error) toast(j.error, 'err'); else toast('Intent ' + id + ' stopping', 'ok');
}

async function setFinding(id, status) {
  const j = await api('/api/finding', {id: id, status: status});
  if (j.error) toast(j.error, 'err');
  else { toast('Finding #' + id + ' → ' + status, 'ok'); refresh(true); }
}

function exportMd() { window.location = '/api/export?task=' + S.task; }

// Background sync: sidebar and the open engagement stay current with no manual refresh.
async function tick() {
  if (document.hidden) return;
  await loadTasks();
  if (S.view === 'task' && S.task) await refresh(false);
  else if (S.view === 'agents') await loadAgents();
}
setInterval(tick, 3000);

drawNav();
loadTasks().then(() => { if (S.tasks.length) selectTask(S.tasks[0].id); else go('settings'); });
</script></body></html>
"""
