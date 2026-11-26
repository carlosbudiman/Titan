"""The console page: one HTML document, no framework, no build step."""

GUI = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>Dewaguard Titan</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0e1013;--panel:#161a20;--line:#262c36;--fg:#d8dee9;--dim:#7d8798;
      --accent:#59a6ff;--ok:#4cc38a;--warn:#e2b93b;--bad:#e05561;--plan:#c58af9}
*{box-sizing:border-box}
body{margin:0;font:13px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
     background:var(--bg);color:var(--fg)}
header{display:flex;align-items:center;gap:1.2rem;padding:.55rem 1rem;border-bottom:1px solid var(--line);
       background:var(--panel);position:sticky;top:0;z-index:5;flex-wrap:wrap}
header h1{font-size:.82rem;letter-spacing:.18em;margin:0;font-weight:600;color:#fff}
nav.top{display:flex;gap:.15rem}
nav.top button{border:1px solid transparent;background:none;color:var(--dim);padding:.22rem .55rem}
nav.top button:hover{color:var(--fg)}
nav.top button.on{color:#fff;background:#1d2634;border-color:#2f4a6d;border-radius:4px}
header .stat{color:var(--dim);font-size:12px} header .stat b{color:var(--fg)}
header .spacer{flex:1}
main{display:grid;grid-template-columns:250px 1fr;min-height:calc(100vh - 44px)}
aside{border-right:1px solid var(--line);padding:.6rem;overflow:auto}
aside .task{padding:.42rem .5rem;border:1px solid transparent;border-radius:4px;cursor:pointer;margin-bottom:.22rem}
aside .task:hover{background:#1b2028}
aside .task.on{background:#1d2634;border-color:#2f4a6d}
aside .task .t{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
aside .task .m{color:var(--dim);font-size:11px}
section{padding:1rem 1.2rem;overflow:auto}
h2{font-size:.95rem;margin:.2rem 0 .2rem}
h3{font-size:.74rem;letter-spacing:.09em;color:var(--dim);text-transform:uppercase;margin:1.1rem 0 .4rem}
button{background:#1f2731;color:var(--fg);border:1px solid var(--line);border-radius:4px;
       padding:.26rem .6rem;cursor:pointer;font:inherit}
button:hover{border-color:#3d4a5c}
button.pri{background:#1d3a5c;border-color:#2f5b8f}
button.danger{background:#3a1f23;border-color:#5e2b31}
button:disabled{opacity:.45;cursor:default}
input,textarea,select{background:#10141a;color:var(--fg);border:1px solid var(--line);
       border-radius:4px;padding:.3rem .45rem;font:inherit;width:100%}
textarea{resize:vertical;min-height:4rem}
label.f{display:block;margin:.55rem 0}
label.f span{display:block;color:var(--dim);font-size:11px;margin-bottom:.15rem}
table{border-collapse:collapse;width:100%}
th,td{text-align:left;padding:.26rem .4rem;border-bottom:1px solid var(--line);vertical-align:top;
       overflow-wrap:anywhere}
th{color:var(--dim);font-weight:500;font-size:11px;letter-spacing:.06em;text-transform:uppercase}
tr:hover td{background:#141920}
.row{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
.card{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:.7rem .8rem}
.tag{display:inline-block;padding:0 .35rem;border-radius:3px;font-size:11px;border:1px solid var(--line)}
.s-open{color:var(--accent)} .s-running,.s-thinking{color:var(--warn)}
.s-done,.s-confirmed,.s-met,.s-achieved,.s-tool{color:var(--ok)}
.s-exhausted,.s-blocked,.s-stopped,.s-failed,.s-abandoned{color:var(--bad)}
.s-idle{color:var(--dim)}
.muted{color:var(--dim)}
pre{white-space:pre-wrap;word-break:break-word;background:#10141a;border:1px solid var(--line);
    border-radius:4px;padding:.5rem;max-height:26rem;overflow:auto;margin:.3rem 0}
.tabs{display:flex;gap:.25rem;margin:.8rem 0 .2rem;flex-wrap:wrap}
.tabs button{border-radius:4px 4px 0 0;border-bottom-color:transparent;color:var(--dim)}
.tabs button.on{background:#1d2634;border-color:#2f4a6d;color:#fff}
.hint{color:var(--dim);font-size:11px}
.agent{display:flex;gap:.7rem;align-items:flex-start}
.dot{width:8px;height:8px;border-radius:50%;background:var(--dim);margin-top:.45rem;flex:0 0 auto}
.dot.live{background:var(--ok);box-shadow:0 0 0 3px rgba(76,195,138,.15)}
.dot.tool{background:var(--warn);box-shadow:0 0 0 3px rgba(226,185,59,.15)}
.dot.idle{background:#4a5361}
#graphwrap{overflow:auto;border:1px solid var(--line);border-radius:6px;background:#0b0e12}
#graphwrap svg{display:block}
@media(max-width:860px){main{grid-template-columns:1fr}aside{border-right:0;border-bottom:1px solid var(--line)}}
</style></head>
<body>
<header>
  <h1>DEWAGUARD TITAN</h1>
  <nav class="top" id="topnav"></nav>
  <span class="spacer"></span>
  <span class="stat" id="hstats"></span>
</header>
<main>
  <aside>
    <div class="row" style="margin-bottom:.5rem">
      <button class="pri" onclick="showNew()">+ task</button>
      <button onclick="loadTasks()">refresh</button>
    </div>
    <div id="tasks"></div>
  </aside>
  <section id="main"><p class="muted">Select or create a task.</p></section>
</main>
<script>
const $ = s => document.querySelector(s);
const esc = s => String(s === null || s === undefined ? '' : s)
  .replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let S = {tasks: [], task: 0, data: null, tab: 'overview', timer: null, view: 'task',
         agents: null, settings: null, skills: null, skillBody: '', traffic: null,
         graph: null, nodeSel: 0, models: [], test: null};

const VIEWS = [['task','task'],['agents','agents'],['settings','settings'],
               ['skills','skills'],['traffic','traffic']];

async function api(path, body) {
  const opts = body === undefined ? {} : {method:'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)};
  const r = await fetch(path, opts);
  const txt = await r.text();
  let j; try { j = JSON.parse(txt); } catch (e) { j = {error: txt}; }
  if (!r.ok && !j.error) j.error = 'HTTP ' + r.status;
  return j;
}

function drawNav() {
  $('#topnav').innerHTML = VIEWS.map(([v,label]) =>
    `<button class="${S.view===v?'on':''}" onclick="go('${v}')">${label}</button>`).join('');
}

async function go(view) {
  S.view = view; drawNav();
  clearInterval(S.timer); S.timer = null;
  if (view === 'task') { await refresh(true); S.timer = setInterval(() => refresh(false), 2000); }
  if (view === 'agents') { await loadAgents(); S.timer = setInterval(loadAgents, 1500); }
  if (view === 'settings') await loadSettings();
  if (view === 'skills') await loadSkills();
  if (view === 'traffic') await loadTraffic();
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
  S.task = id; S.view = 'task'; drawNav();
  await loadTasks();
  clearInterval(S.timer);
  await refresh(true);
  S.timer = setInterval(() => refresh(false), 2000);
}

async function refresh(force) {
  if (!S.task || S.view !== 'task') return;
  const j = await api('/api/state?task=' + S.task);
  if (j.error) { $('#main').innerHTML = '<p class="s-failed">' + esc(j.error) + '</p>'; return; }
  S.data = j;
  $('#hstats').innerHTML = `task <b>#${j.task.id}</b> &middot; <b class="s-${esc(j.task.status)}">${esc(j.task.status)}</b>
    &middot; round <b>${j.overview.round}</b> &middot; coverage <b>${j.overview.coverage.pct}%</b>
    &middot; findings <b>${j.overview.findings_total}</b>
    ${j.running ? '&middot; <span class="s-running">running</span>' : ''}`;
  render();
}

function render() {
  if (S.view !== 'task' || !S.data) return;
  const d = S.data, ov = d.overview;
  const tabs = ['overview','agents','intents','facts','findings','assets','traffic','activity','graph'];
  $('#main').innerHTML = `
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
  const pane = $('#pane');
  if (S.tab === 'overview') pane.innerHTML = tabOverview(d);
  if (S.tab === 'agents') { pane.innerHTML = '<p class="muted">loading agents...</p>'; loadAgents(); }
  if (S.tab === 'intents') pane.innerHTML = tabIntents(d);
  if (S.tab === 'facts') pane.innerHTML = tabFacts(d);
  if (S.tab === 'findings') pane.innerHTML = tabFindings(d);
  if (S.tab === 'assets') pane.innerHTML = tabAssets(d);
  if (S.tab === 'traffic') { pane.innerHTML = '<p class="muted">loading traffic...</p>'; loadTraffic(); }
  if (S.tab === 'activity') pane.innerHTML = tabActivity(d);
  if (S.tab === 'graph') { pane.innerHTML = '<p class="muted">loading graph...</p>'; loadGraph(); }
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
  return `<div class="grid2">
    <div class="card"><h3 style="margin-top:0">goals</h3>
      ${ov.goals.map(g => `<div class="row"><span class="tag s-${esc(g.state)}">${esc(g.state)}</span>
        <span>${esc(g.text)}</span></div>`).join('') || '<span class="muted">none</span>'}
      <h3>constraints</h3>
      ${ov.constraints.map(c => `<div><span class="tag">${esc(c.kind)}</span> ${esc(c.text)}</div>`).join('') || '<span class="muted">none</span>'}
      ${ov.hints.length ? '<h3>hints</h3>' + ov.hints.map(h => `<div>&middot; ${esc(h.text)}</div>`).join('') : ''}
    </div>
    <div class="card"><h3 style="margin-top:0">queue</h3>
      ${queue.map(intentRow).join('') || '<span class="muted">idle</span>'}
      <h3>hint</h3>
      <textarea id="hintText" placeholder="operator hint for the next planning rounds"></textarea>
      <div class="row" style="margin-top:.35rem"><button onclick="addHint()">queue hint</button></div>
    </div></div>`;
}

// ------------------------------------------------------------------ agents
async function loadAgents() {
  if (!S.task) return;
  S.agents = await api('/api/agents?task=' + S.task);
  if (S.tab !== 'agents' && S.view !== 'agents') return;
  const html = agentsHtml(S.agents);
  if (S.view === 'agents') $('#main').innerHTML = html;
  else if ($('#pane')) $('#pane').innerHTML = html;
}

function agentsHtml(a) {
  if (!a || a.error) return '<p class="s-failed">' + esc((a && a.error) || 'no data') + '</p>';
  const live = a.live || [];
  const cards = live.length ? live.map(x => {
    const cls = x.state === 'tool' ? 'tool' : (x.idle_s > 20 ? 'idle' : 'live');
    return `<div class="card" style="margin-bottom:.5rem">
      <div class="agent"><span class="dot ${cls}"></span><div style="flex:1">
        <div class="row"><b>${esc(x.key)}</b>
          <span class="tag s-${esc(x.state)}">${esc(x.state)}</span>
          ${x.intent ? `<span class="muted">intent #${x.intent}</span>` : ''}
          <span class="muted">${x.elapsed_s}s &middot; ${x.turns} turns &middot;
            ${(x.tokens_in||0)+(x.tokens_out||0)} tok</span>
          ${x.state === 'tool' ? `<button onclick="steer(${x.intent})">steer</button>
            <button class="danger" onclick="kill(${x.intent})">kill</button>` : ''}
        </div>
        <div class="muted">${esc(x.tool ? x.tool + ' :: ' : '')}${esc((x.note||'').slice(0,180))}</div>
      </div></div></div>`;
  }).join('') : '<p class="muted">no agent running (start a run)</p>';

  const usage = (a.usage || []).map(u => `<tr><td>${esc(u.agent)}</td><td>${u.calls}</td>
      <td>${u.tin||0}</td><td>${u.tout||0}</td></tr>`).join('');
  const act = (a.activity || []).slice(0, 40).map(x => `<tr><td class="muted">${esc(x.worker||'')}</td>
      <td class="muted">${esc(x.kind||'')}</td><td>${esc((x.summary||'').slice(0,200))}</td></tr>`).join('');

  return `<h3 style="margin-top:0">live agents</h3>${cards}
    <h3>token usage</h3>
    <table><tr><th>agent</th><th>calls</th><th>in</th><th>out</th></tr>
      ${usage || '<tr><td colspan=4 class="muted">none</td></tr>'}</table>
    <h3>recent steps</h3>
    <table><tr><th>worker</th><th>kind</th><th>summary</th></tr>
      ${act || '<tr><td colspan=3 class="muted">none</td></tr>'}</table>`;
}

// ------------------------------------------------------------------ task tabs
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
  const opts = ['open','confirmed','false_positive','duplicate','ignored'];
  return d.findings.map(f => `<div class="card" style="margin-bottom:.6rem">
    <div class="row"><span class="tag">${esc(f.severity)}</span>
      <b>${esc(f.vulnclass)}</b> <span class="muted">#${f.id} &middot; ${esc(f.proof_basis)}</span>
      <select style="width:auto" onchange="setFinding(${f.id}, this.value)">
        ${opts.map(o => `<option ${o===f.status?'selected':''}>${o}</option>`).join('')}
      </select></div>
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

// ------------------------------------------------------------------ graph
async function loadGraph() {
  if (!S.task) return;
  S.graph = await api('/api/graph?task=' + S.task);
  if (S.tab !== 'graph') return;
  $('#pane').innerHTML = graphHtml(S.graph);
}

function graphHtml(g) {
  if (!g || g.error) return '<p class="s-failed">' + esc((g && g.error) || 'no data') + '</p>';
  const nodes = g.nodes || [], edges = g.edges || [];
  const byId = {}; nodes.forEach(n => byId[n.id] = n);
  const level = {}; const kids = {}; edges.forEach(e => (kids[e.src] = kids[e.src] || []).push(e.dst));
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
  const W = 170, H = 32, GX = 70, GY = 18, PAD = 24;
  const maxLevel = Math.max(0, ...Object.keys(cols).map(Number));
  const height = PAD * 2 + Math.max(...Object.values(cols).map(c => c.length), 1) * (H + GY);
  const width = PAD * 2 + (maxLevel + 1) * (W + GX);
  const pos = {};
  Object.keys(cols).forEach(lv => cols[lv].forEach((n, i) => {
    pos[n.id] = {x: PAD + Number(lv) * (W + GX), y: PAD + i * (H + GY)};
  }));
  const kinds = {begin:'#2a3442',goal:'#243b2c',intent:'#22303f',fact:'#2a2a3d',finding:'#3a2430',hint:'#33301f',digest:'#2b2b2b'};
  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace,monospace">`;
  edges.forEach(e => {
    const a = pos[e.src], b = pos[e.dst]; if (!a || !b) return;
    const x1 = a.x + W, y1 = a.y + H / 2, x2 = b.x, y2 = b.y + H / 2;
    const mx = (x1 + x2) / 2;
    svg += `<path d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}" fill="none"
      stroke="#33404f" stroke-width="1"/>`;
    svg += `<text x="${mx - 8}" y="${(y1 + y2) / 2 - 3}" fill="#5a6576" font-size="9">${esc(e.rel)}</text>`;
  });
  nodes.forEach(n => {
    const p = pos[n.id]; const fill = kinds[n.kind] || '#262c36';
    const stroke = n.id === S.nodeSel ? '#59a6ff' : '#394452';
    svg += `<g style="cursor:pointer" onclick="showNode(${n.id})">
      <title>${esc(n.kind)} #${n.id}: ${esc(n.label || '')}</title>
      <rect x="${p.x}" y="${p.y}" width="${W}" height="${H}" rx="4" fill="${fill}" stroke="${stroke}"/>
      <text x="${p.x + 7}" y="${p.y + 13}" fill="#7d8798" font-size="9">${esc(n.kind)} #${n.id}</text>
      <text x="${p.x + 7}" y="${p.y + 25}" fill="#d8dee9" font-size="10">${esc((n.label || '').slice(0, 27))}</text>
      </g>`;
  });
  svg += '</svg>';
  return `<div class="row" style="margin-bottom:.4rem">
      <span class="hint">${nodes.length} nodes, ${edges.length} edges - click a node</span>
      <button onclick="loadGraph()">refresh</button></div>
    <div id="graphwrap">${svg}</div>
    <div id="nodedetail">${S.nodeSel ? '' : '<p class="hint">select a node for its payload</p>'}</div>`;
}

async function showNode(id) {
  S.nodeSel = id;
  const j = await api('/api/node?id=' + id);
  const el = $('#nodedetail');
  if (el) el.innerHTML = j.error ? `<p class="s-failed">${esc(j.error)}</p>`
    : `<pre>${esc(JSON.stringify(j, null, 1))}</pre>`;
}

// ------------------------------------------------------------------ settings
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
        <h3 style="margin-top:0">model endpoint</h3>
        <label class="f"><span>base URL (OpenAI-compatible)</span>
          <input id="sUrl" value="${esc(llm.base_url || '')}"></label>
        <label class="f"><span>model id</span>
          <input id="sModel" value="${esc(llm.model || '')}"></label>
        <div class="row">
          <button onclick="listModels()">list models</button>
          <span class="hint" id="sModelsHint"></span>
        </div>
        <div id="sModels" class="hint" style="max-height:9rem;overflow:auto"></div>
        <label class="f"><span>API key (${esc(llm.key_masked || 'unset')} via ${esc(llm.key_source || '-')})</span>
          <input id="sKey" type="password" placeholder="blank = keep existing" autocomplete="off"></label>
        <label class="f"><span>request timeout (s)</span>
          <input id="sTimeout" value="${esc(llm.timeout || 600)}"></label>
        <label class="f"><span>max tokens (0 = endpoint default)</span>
          <input id="sMaxTokens" value="${esc(llm.max_tokens || 0)}"></label>
        <label class="f"><span>temperature</span>
          <input id="sTemp" value="${esc(llm.temperature || 0.2)}"></label>
      </div>
      <div class="card">
        <h3 style="margin-top:0">run defaults</h3>
        <label class="f"><span>requests per second per host</span>
          <input id="sRps" value="${esc(run.rps || '2')}"></label>
        <label class="f"><span>parallel workers</span>
          <input id="sWorkers" value="${esc(run.max_workers || '2')}"></label>
        <label class="f"><span>noise profile</span>
          <select id="sNoise">
            ${['quiet','balanced','aggressive','off'].map(o =>
              `<option ${o===(run.noise_profile||'balanced')?'selected':''}>${o}</option>`).join('')}
          </select></label>
        <div class="row" style="margin-top:.8rem">
          <button class="pri" onclick="saveSettings()">save</button>
          <button onclick="testSettings()">test connection</button>
        </div>
        <div id="sMsg" class="hint" style="margin-top:.5rem"></div>
        <h3>notes</h3>
        <div class="hint">
          The key is written to ~/.titan/secrets.json with mode 0600, never to the
          database and never echoed back. Values here override the TITAN_* environment,
          except TITAN_LLM_API_KEY, which wins over the saved key.
        </div>
      </div>
    </div>`;
}

async function listModels() {
  const url = $('#sUrl').value.trim(), key = $('#sKey').value.trim();
  $('#sModelsHint').textContent = 'probing...';
  const j = await api('/api/models?url=' + encodeURIComponent(url) +
                      (key ? '&key=' + encodeURIComponent(key) : ''));
  if (j.error) { $('#sModelsHint').textContent = j.error; return; }
  S.models = j.models || [];
  $('#sModelsHint').textContent = S.models.length + ' model(s)';
  $('#sModels').innerHTML = S.models.map(m =>
    `<div style="cursor:pointer" onclick="pickModel('${esc(m).replace(/'/g, "\\'")}')">${esc(m)}</div>`).join('');
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
    api_key: $('#sKey').value.trim() || undefined
  };
  const j = await api('/api/settings', body);
  $('#sKey').value = '';
  if (j.error) { $('#sMsg').innerHTML = '<span class="s-failed">' + esc(j.error) + '</span>'; return; }
  S.settings = j;
  renderSettings();
  $('#sMsg').innerHTML = '<span class="s-ok">saved</span>';
}

async function testSettings() {
  $('#sMsg').textContent = 'testing...';
  const j = await api('/api/settings/test', {
    base_url: $('#sUrl').value.trim(), model: $('#sModel').value.trim(),
    api_key: $('#sKey').value.trim() || undefined});
  if (j.error) $('#sMsg').innerHTML = '<span class="s-failed">' + esc(j.error) + '</span>';
  else $('#sMsg').innerHTML = `<span class="s-done">ok in ${j.latency_ms} ms: ${esc((j.reply||'').slice(0,80))}</span>`;
}

// ------------------------------------------------------------------ skills
async function loadSkills() {
  const j = await api('/api/skills');
  S.skills = j.skills || [];
  $('#main').innerHTML = `<h2>Skills</h2>
    <div class="grid2">
      <div class="card"><h3 style="margin-top:0">installed (${S.skills.length})</h3>
        ${S.skills.map(s => `<div style="cursor:pointer;margin-bottom:.35rem"
          onclick="readSkill('${esc(s.name).replace(/'/g, "\\'")}')">
          <b>${esc(s.name)}</b><div class="hint">${esc(s.description || '')}</div></div>`).join('')}
      </div>
      <div class="card"><h3 style="margin-top:0">skill.md</h3>
        <pre id="skillBody" class="hint">select a skill</pre></div>
    </div>`;
}

async function readSkill(name) {
  const j = await api('/api/skill?name=' + encodeURIComponent(name));
  $('#skillBody').textContent = j.body || j.error || '';
}

// ------------------------------------------------------------------ traffic
async function loadTraffic() {
  if (!S.task) { $('#main').innerHTML = '<p class="muted">select a task first</p>'; return; }
  const q = (S.trafficQ || '').trim();
  const j = await api('/api/traffic?task=' + S.task + (q ? '&q=' + encodeURIComponent(q) : ''));
  const rows = j.traffic || [];
  const html = `<h2>Traffic - task #${S.task}</h2>
    <div class="row" style="margin-bottom:.6rem">
      <input id="tq" placeholder="search url or body" value="${esc(q)}" style="width:20rem">
      <button onclick="S.trafficQ=$('#tq').value; loadTraffic()">search</button>
      <span class="hint">${rows.length} record(s)</span>
    </div>
    <table><tr><th>id</th><th>method</th><th>url</th><th>status</th><th>bytes</th></tr>
      ${rows.map(t => `<tr style="cursor:pointer" onclick="readTraffic(${t.id})">
        <td>${t.id}</td><td>${esc(t.method)}</td><td>${esc(t.url)}</td>
        <td class="s-${t.status >= 400 ? 'failed' : 'done'}">${t.status}</td><td>${t.rlen}</td></tr>`).join('')}
    </table>
    <div id="tdetail"></div>`;
  if (S.view === 'traffic') $('#main').innerHTML = html;
  else if ($('#pane')) $('#pane').innerHTML = html;
}

async function readTraffic(id) {
  const j = await api('/api/traffic_one?id=' + id);
  const el = $('#tdetail'); if (!el) return;
  el.innerHTML = `<h3>request ${id}</h3><pre>${esc(JSON.stringify(
    {method: j.method, url: j.url, status: j.status, req_headers: j.req_headers}, null, 1))}</pre>
    <h3>response headers</h3><pre>${esc(JSON.stringify(j.resp_headers || {}, null, 1))}</pre>
    <h3>response body</h3><pre>${esc((j.resp_body || '').slice(0, 20000))}</pre>`;
}

// ------------------------------------------------------------------ actions
function showNew() {
  S.view = 'new'; S.task = 0; clearInterval(S.timer); drawNav();
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

function cancelNew() { if (S.tasks.length) selectTask(S.tasks[0].id); else go('settings'); }

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

async function setFinding(id, status) {
  const j = await api('/api/finding', {id: id, status: status});
  if (j.error) alert(j.error); else refresh(true);
}

function exportMd() { window.location = '/api/export?task=' + S.task; }

drawNav();
loadTasks().then(() => { if (S.tasks.length) selectTask(S.tasks[0].id); else go('settings'); });
</script></body></html>
"""
