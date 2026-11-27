"""The console page: one HTML document, no framework, no build step."""

GUI = r"""<!doctype html>
<html lang="en" data-theme="dark" data-density="comfortable"><head><meta charset="utf-8">
<title>Dewaguard Titan</title>
<link rel="icon" type="image/png" href="data:image/png;base64,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">
<meta name="viewport" content="width=device-width,initial-scale=1">
<script>
  (function () {
    var t = localStorage.getItem('titan-theme');
    if (!t) t = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', t);
    var d = localStorage.getItem('titan-density');
    if (d) document.documentElement.setAttribute('data-density', d);
  })();
</script>
<style>
:root{
  --fs-11:11px; --fs-12:12px; --fs-13:13px; --fs-15:15px; --fs-20:20px;
  --r:8px; --sev-critical:#7f1d1d; --sev-high:#a5342f; --sev-medium:#9a7412;
  --sev-low:#3f6b52; --sev-info:#5b5f66;
}
:root, [data-theme="light"]{
  --bg:#f7f5f4; --surface:#ffffff; --surface-2:#faf8f8; --line:#e6dedd;
  --fg:#221a1c; --dim:#5c4b4e; --brand:#7d2030; --brand-2:#9c2b3c; --on-brand:#ffffff;
  --ok:#1c7a4d; --warn:#8a6a10; --bad:#b3261e; --chip:#f4eaec; --shadow:none;
  --sel:#f0e2e4;
}
[data-theme="dark"]{
  --bg:#121011; --surface:#1a1517; --surface-2:#201a1c; --line:#312628;
  --fg:#efe8e9; --dim:#ac9da0; --brand:#c04a5c; --brand-2:#a53648; --on-brand:#ffffff;
  --ok:#4fbe8a; --warn:#d9b04a; --bad:#ef6a63; --chip:#2a1f22; --shadow:none;
  --sel:#2b1f23;
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--fg);font-size:var(--fs-13);line-height:1.55;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Inter,
    "Noto Sans",Arial,sans-serif;-webkit-font-smoothing:antialiased}
code,pre,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:var(--fs-12)}
h1,h2,h3{font-weight:600;letter-spacing:-.01em}

/* ---------- chrome ---------- */
header{display:flex;align-items:center;gap:.9rem;padding:.55rem 1.1rem;background:var(--surface);
  border-bottom:1px solid var(--line);position:sticky;top:0;z-index:30;flex-wrap:wrap}
.brand{display:flex;align-items:center}
.brand .lg{height:27px;width:auto;display:block}
[data-theme="light"] .lg-dark{display:none}
[data-theme="dark"] .lg-light{display:none}
.crumbs{color:var(--dim);font-size:var(--fs-12);display:flex;gap:.35rem;align-items:center;
  min-width:0}
.crumbs b{color:var(--fg);font-weight:600;max-width:26rem;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap}
.live{display:flex;gap:.35rem;align-items:center;font-size:var(--fs-11);color:var(--dim)}
.live .pill{display:inline-flex;gap:.3rem;align-items:center;border:1px solid var(--line);
  border-radius:999px;padding:0 .45rem;background:var(--surface-2)}
header .spacer{flex:1}
.iconbtn{border:1px solid transparent;background:none;color:var(--dim);border-radius:var(--r);
  width:30px;height:30px;display:grid;place-items:center;cursor:pointer;font-size:14px}
.iconbtn:hover{color:var(--fg);background:var(--surface-2)}
.menu{position:absolute;right:1rem;top:3rem;background:var(--surface);border:1px solid var(--line);
  border-radius:10px;padding:.35rem;z-index:70;min-width:13rem;box-shadow:0 8px 24px rgba(0,0,0,.12)}
.menu button{display:block;width:100%;text-align:left;border:0;background:none;padding:.4rem .6rem;
  border-radius:6px;color:var(--fg);font:inherit;font-size:var(--fs-13);cursor:pointer}
.menu button:hover{background:var(--surface-2)}
.menu .sep{height:1px;background:var(--line);margin:.3rem .2rem}
.menu .muted{padding:.2rem .6rem}

main{display:grid;grid-template-columns:246px 1fr;min-height:calc(100vh - 44px)}
aside{background:var(--surface);border-right:1px solid var(--line);padding:.7rem;overflow:auto}
aside .head{display:flex;align-items:center;justify-content:space-between;margin-bottom:.5rem}
aside .head span{font-size:var(--fs-11);text-transform:uppercase;letter-spacing:.06em;color:var(--dim)}
aside .task{padding:.45rem .5rem;border:1px solid transparent;border-radius:var(--r);cursor:pointer;
  position:relative;margin-bottom:.15rem}
aside .task:hover{background:var(--surface-2)}
aside .task.on{background:var(--sel);border-color:var(--brand)}
aside .task .t{display:block;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
  padding-right:1.1rem}
aside .task .m{color:var(--dim);font-size:var(--fs-11);display:flex;gap:.35rem;align-items:center}
aside .task .kill{position:absolute;right:.25rem;top:.3rem;opacity:0;border:0;background:none;
  color:var(--dim);cursor:pointer;font-size:14px;line-height:1;padding:0 .2rem}
aside .task:hover .kill{opacity:1}
aside .task .kill:hover{color:var(--bad)}
section{padding:1.1rem 1.3rem;overflow:auto}

/* ---------- primitives ---------- */
button{background:var(--surface);color:var(--fg);border:1px solid var(--line);border-radius:var(--r);
  padding:.34rem .7rem;cursor:pointer;font:inherit;font-size:var(--fs-13)}
button:hover{background:var(--surface-2)}
button.pri{background:var(--brand);border-color:var(--brand);color:var(--on-brand);font-weight:500}
button.pri:hover{background:var(--brand-2)}
button.ghost{background:none;border-color:transparent;color:var(--dim)}
button.ghost:hover{color:var(--fg);background:var(--surface-2)}
button.danger{color:var(--bad)}
button:disabled{opacity:.45;cursor:not-allowed}
button.sm{padding:.15rem .45rem;font-size:var(--fs-12)}
input,textarea,select{background:var(--surface);color:var(--fg);border:1px solid var(--line);
  border-radius:var(--r);padding:.34rem .55rem;font:inherit;font-size:var(--fs-13);width:100%}
input:focus,textarea:focus,select:focus,button:focus-visible{outline:2px solid var(--brand);
  outline-offset:-1px}
textarea{resize:vertical;min-height:4rem}
a{color:var(--brand)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:.85rem .95rem}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:.9rem}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:.9rem}
.row{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}
.muted{color:var(--dim)}
.hint{color:var(--dim);font-size:var(--fs-12)}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
hr{border:0;border-top:1px solid var(--line);margin:1rem 0}

table{border-collapse:separate;border-spacing:0;width:100%;background:var(--surface);
  border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:var(--fs-13)}
th,td{text-align:left;padding:.55rem .65rem;border-bottom:1px solid var(--line);vertical-align:top;
  overflow-wrap:anywhere}
th{position:sticky;top:0;background:var(--surface-2);color:var(--dim);font-weight:600;
  font-size:var(--fs-11);text-transform:uppercase;letter-spacing:.05em;z-index:1}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:0}
tbody tr:hover td,table tr:hover td{background:var(--surface-2)}
[data-density="compact"] th,[data-density="compact"] td{padding:.32rem .55rem}

.chip{display:inline-flex;align-items:center;gap:.25rem;padding:.05rem .45rem;border-radius:999px;
  font-size:var(--fs-11);background:var(--chip);border:1px solid var(--line)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--dim);flex:0 0 auto}
.dot.live{background:var(--ok)}
.dot.tool{background:var(--warn)}
.dot.idle{background:var(--dim)}
.sev{display:inline-block;padding:.05rem .45rem;border-radius:999px;font-size:var(--fs-11);
  color:#fff;text-transform:uppercase;letter-spacing:.05em;font-weight:600}
.sev-critical{background:var(--sev-critical)} .sev-high{background:var(--sev-high)}
.sev-medium{background:var(--sev-medium)} .sev-low{background:var(--sev-low)}
.sev-info{background:var(--sev-info)}
.s-open{color:var(--brand)} .s-running,.s-thinking,.s-judging,.s-waiting_approval{color:var(--warn)}
.s-done,.s-confirmed,.s-met,.s-achieved{color:var(--ok)}
.s-exhausted,.s-blocked,.s-stopped,.s-failed,.s-abandoned,.s-stale{color:var(--bad)}
pre{white-space:pre-wrap;word-break:break-word;background:var(--surface-2);border:1px solid var(--line);
  border-radius:var(--r);padding:.6rem;max-height:24rem;overflow:auto;margin:.35rem 0}
.empty{color:var(--dim);padding:1.4rem;text-align:center;border:1px dashed var(--line);
  border-radius:10px;background:var(--surface)}
.empty b{color:var(--fg);display:block;margin-bottom:.2rem}
label.f{display:block;margin:.6rem 0}
label.f>span{display:block;color:var(--dim);font-size:var(--fs-12);margin-bottom:.2rem}
.skel{height:1rem;border-radius:6px;background:linear-gradient(90deg,var(--surface-2),var(--chip),
  var(--surface-2));background-size:200% 100%;animation:sh 1.1s infinite;margin:.4rem 0}
@keyframes sh{from{background-position:0 0}to{background-position:-200% 0}}

/* ---------- page ---------- */
.pagehead{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;
  padding-bottom:.8rem;border-bottom:1px solid var(--line);margin-bottom:.9rem}
.pagehead h2{font-size:var(--fs-20);margin:0 0 .15rem}
.pagehead .goal{color:var(--dim);max-width:52rem}
.pagehead .actions{display:flex;gap:.4rem;align-items:center;flex-wrap:wrap}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:var(--r);overflow:hidden}
.seg button{border:0;border-radius:0;background:var(--surface);color:var(--dim);padding:.3rem .6rem;
  font-size:var(--fs-12)}
.seg button.on{background:var(--sel);color:var(--brand);font-weight:600;
  box-shadow:inset 0 -2px 0 var(--brand)}
.stepper{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:var(--r);
  overflow:hidden;background:var(--surface)}
.stepper button{border:0;border-radius:0;padding:.2rem .45rem;background:none;color:var(--dim)}
.stepper input{width:2.2rem;border:0;text-align:center;padding:.2rem 0;background:none}
.statline{display:flex;gap:.7rem;align-items:center;flex-wrap:wrap;font-size:var(--fs-12);
  color:var(--dim);margin-bottom:.9rem}
.meter{width:110px;height:6px;border-radius:3px;background:var(--chip);
  border:1px solid var(--line);overflow:hidden}
.meter i{display:block;height:100%;background:var(--brand);border-radius:3px}
.statline .sep{color:var(--line)}
.tabs{display:flex;gap:.1rem;margin:0 0 1rem;border-bottom:1px solid var(--line);flex-wrap:wrap}
.tabs button{border:0;border-bottom:2px solid transparent;border-radius:0;background:none;
  color:var(--dim);padding:.45rem .7rem;font-size:var(--fs-13)}
.tabs button.on{color:var(--brand);border-bottom-color:var(--brand);font-weight:600}
.banner{border:1px solid var(--brand);background:var(--sel);border-radius:10px;padding:.6rem .8rem;
  margin-bottom:.9rem}
.filters{display:flex;gap:.3rem;align-items:center;flex-wrap:wrap;margin-bottom:.8rem}
.filters .chip{cursor:pointer}
.filters .chip.on{background:var(--brand);color:var(--on-brand);border-color:var(--brand)}

/* gantt */
.gantt{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:.7rem .8rem}
.lane{display:grid;grid-template-columns:5.5rem 1fr;gap:.5rem;align-items:center;margin-bottom:.3rem}
.lane .who{font-size:var(--fs-11);color:var(--dim);text-align:right;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.track{position:relative;height:16px;background:var(--surface-2);border-radius:4px}
.bar{position:absolute;top:2px;height:12px;border-radius:3px;background:var(--brand);opacity:.9;
  min-width:2px}
.bar.done{background:var(--ok)} .bar.stopped,.bar.blocked,.bar.failed{background:var(--bad)}
.bar.open{background:var(--line)}
.axis{display:flex;justify-content:space-between;font-size:var(--fs-11);color:var(--dim);
  margin-left:6rem;margin-top:.2rem}

/* ---------- toasts / modal ---------- */
#toasts{position:fixed;right:.8rem;top:3.3rem;display:flex;flex-direction:column;gap:.4rem;
  z-index:60;width:19rem;max-width:calc(100vw - 2rem)}
.toast{position:relative;background:var(--surface);border:1px solid var(--line);
  border-left:3px solid var(--brand);border-radius:var(--r);padding:.5rem 1.4rem .5rem .65rem;
  font-size:var(--fs-12);animation:slide .16s ease-out}
.toast.click{cursor:pointer}
.toast.click:hover{background:var(--surface-2)}
.toast .tt{font-weight:600;display:block;line-height:1.35}
.toast .tb{color:var(--dim);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
  overflow:hidden;overflow-wrap:anywhere}
.toast .tx{position:absolute;right:.25rem;top:.2rem;border:0;background:none;color:var(--dim);
  cursor:pointer;font-size:13px;line-height:1;padding:.2rem}
.toast .tx:hover{color:var(--fg)}
.toast.err{border-left-color:var(--bad)} .toast.ok{border-left-color:var(--ok)}
.toast.finding{border-left-color:var(--sev-critical)} .toast.fact{border-left-color:var(--brand)}
@keyframes slide{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
.overlay{position:fixed;inset:0;background:rgba(18,10,12,.42);display:grid;place-items:center;
  z-index:80;padding:1rem}
.modal{width:min(34rem,100%);animation:pop .14s ease-out}
@keyframes pop{from{opacity:0;transform:scale(.985)}to{opacity:1;transform:none}}
kbd{font-family:inherit;border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;
  padding:0 .3rem;font-size:var(--fs-11);background:var(--surface-2)}
/* notifications panel */
#bellBadge{position:absolute;top:-2px;right:-2px;background:var(--brand);color:#fff;
  font-size:9px;min-width:13px;height:13px;border-radius:7px;line-height:13px;text-align:center;
  padding:0 3px;font-weight:600}
#bell{position:relative}
.panel{position:absolute;right:.9rem;top:3.2rem;width:24rem;max-width:calc(100vw - 2rem);
  background:var(--surface);border:1px solid var(--line);border-radius:10px;z-index:70;
  box-shadow:0 12px 30px rgba(0,0,0,.14);overflow:hidden}
.panel .ph{display:flex;align-items:center;justify-content:space-between;padding:.55rem .7rem;
  border-bottom:1px solid var(--line);font-weight:600;font-size:var(--fs-12)}
.panel .pl{max-height:22rem;overflow:auto}
.nitem{padding:.5rem .7rem;border-bottom:1px solid var(--line);cursor:pointer;position:relative}
.nitem:hover{background:var(--surface-2)}
.nitem .nt{font-weight:600;font-size:var(--fs-12)}
.nitem .nb{color:var(--dim);font-size:var(--fs-11);display:-webkit-box;-webkit-line-clamp:2;
  -webkit-box-orient:vertical;overflow:hidden}
.nitem .nm{color:var(--dim);font-size:10.5px;margin-top:.1rem}
.nitem.unread{background:var(--sel)}
.nitem.unread:before{content:'';position:absolute;left:.28rem;top:.75rem;width:5px;height:5px;
  border-radius:50%;background:var(--brand)}
/* chat: overview card + dock */
.chatmini{flex:1;min-height:10rem;max-height:20rem;overflow:auto;display:flex;flex-direction:column;
  gap:.35rem;padding-right:.2rem}
.chatmini .bubble{font-size:var(--fs-12)}
.cactions{display:flex;gap:.3rem;flex-wrap:wrap;margin:-.15rem 0 .35rem}
.cactions button{opacity:.85}
.qstrip{border-top:1px solid var(--line);margin-top:.5rem;max-height:11rem;overflow:auto}
.ctabs{display:flex;gap:.2rem;padding:.35rem .5rem 0;overflow:auto;border-bottom:1px solid var(--line)}
.ctab{border:0;background:none;color:var(--dim);font-size:var(--fs-11);padding:.25rem .45rem;
  border-radius:6px 6px 0 0;position:relative;white-space:nowrap}
.ctab:hover{background:var(--surface-2)}
.ctab.on{background:var(--sel);color:var(--brand);font-weight:600}
.cdot{display:inline-block;width:5px;height:5px;border-radius:50%;background:var(--brand);
  margin-left:.25rem;vertical-align:middle}
/* chat dock */
.chat{position:fixed;right:.9rem;bottom:.9rem;width:26rem;max-width:calc(100vw - 1.6rem);
  height:30rem;background:var(--surface);border:1px solid var(--line);border-radius:12px;
  z-index:75;display:flex;flex-direction:column;box-shadow:0 16px 40px rgba(0,0,0,.18)}
.chat .ch{padding:.5rem .7rem;border-bottom:1px solid var(--line);display:flex;
  justify-content:space-between;align-items:center;font-weight:600;font-size:var(--fs-12)}
.chat .body{flex:1;overflow:auto;padding:.6rem .7rem;display:flex;flex-direction:column;gap:.5rem}
.bubble{max-width:88%;padding:.45rem .6rem;border-radius:10px;font-size:var(--fs-12);
  white-space:pre-wrap;overflow-wrap:anywhere}
.bubble.me{align-self:flex-end;background:var(--brand);color:var(--on-brand)}
.bubble.you{align-self:flex-start;background:var(--surface-2);border:1px solid var(--line)}
.bubble.sys{align-self:center;color:var(--dim);font-size:var(--fs-11)}
.chat .cf{border-top:1px solid var(--line);padding:.5rem;display:flex;gap:.4rem}

/* artifacts tree */
.tnode{padding:.2rem .35rem;border-radius:5px;font-size:var(--fs-12);cursor:pointer;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:flex;gap:.4rem;
  justify-content:space-between}
.tnode:hover{background:var(--surface-2)}
.tnode.on{background:var(--sel);color:var(--brand);font-weight:600}
.tnode.dir{color:var(--dim);cursor:default;font-weight:600;margin-top:.35rem}
.tnode.dir:hover{background:none}
.tnode .sz{color:var(--dim);font-size:var(--fs-11)}
pre.code{max-height:32rem}
.md{line-height:1.6}
.md code{background:var(--surface-2);border:1px solid var(--line);border-radius:4px;padding:0 .2rem}

/* live graph */
@keyframes nodepulse{0%,100%{opacity:.35}50%{opacity:1}}
@keyframes dashmove{to{stroke-dashoffset:-10}}
.live-node{animation:nodepulse 1.7s ease-in-out infinite}
.live-edge{stroke-dasharray:5 5;animation:dashmove .9s linear infinite}

@media(max-width:960px){main{grid-template-columns:1fr}aside{border-right:0;
  border-bottom:1px solid var(--line)}section{padding:.9rem}.grid2,.grid3{grid-template-columns:1fr}}
</style></head>
<body>
<header>
  <div class="brand">
    <img class="lg lg-light" alt="Dewaguard Titan" src="data:image/webp;base64,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">
    <img class="lg lg-dark" alt="Dewaguard Titan" src="data:image/webp;base64,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">
  </div>
  <div class="crumbs" id="crumbs"></div>
  <span class="live" id="live"></span>
  <span class="spacer"></span>
  <button class="iconbtn" id="bell" title="Notifications" onclick="toggleNotifs()">◔
    <span id="bellBadge" style="display:none"></span></button>
  <button class="iconbtn" id="chatbtn" title="Ask the planner" onclick="toggleChat()">✦</button>
  <button class="iconbtn" id="theme" title="Light / dark" onclick="toggleTheme()">◐</button>
  <button class="iconbtn" id="gear" title="Menu" onclick="toggleMenu()">⋯</button>
</header>
<main>
  <aside>
    <div class="head"><span>Engagements</span><button class="pri sm" onclick="showNew()">New</button></div>
    <div id="tasks"></div>
  </aside>
  <section id="main"><div class="empty"><b>No engagement selected</b>Create one, or pick one from the list.</div></section>
</main>
<div id="notifHost"></div>
<div id="chatHost"></div>
<div id="toasts"></div>
<div id="menuHost"></div>
<div id="modalHost"></div>
<script>
const $ = s => document.querySelector(s);
const esc = s => String(s === null || s === undefined ? '' : s)
  .replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let S = {tasks: [], task: 0, data: null, tab: 'overview', view: 'task',
         settings: null, skills: null, traffic: null, trafficId: 0, trafficQ: '',
         graph: null, nodeSel: 0, models: [], lastSig: '', findSev: '', findStatus: '',
         findQ: '', actWorker: '', actKind: '', graphKind: '', expanded: {},
         lastResult: {}, scopeInfo: null, commands: null, artifacts: null, artPath: '', artText: '',
         artMode: 'files'};
let SEEN = null;
const TABS = [['overview','Overview'],['scope','Scope'],['commands','Commands'],
              ['enumeration','Enumeration'],['findings','Findings'],['artifacts','Artifacts'],
              ['activity','Activity'],['graph','Graph']];

let SEENKEYS = new Set(JSON.parse(localStorage.getItem('titan-seen') || '[]'));
let NOTIFS = JSON.parse(localStorage.getItem('titan-notifs') || '[]');
let CHAT = {};        // taskId -> [{role, text}]

function saveSeen() { localStorage.setItem('titan-seen', JSON.stringify([...SEENKEYS].slice(-500))); }
function saveNotifs() { localStorage.setItem('titan-notifs', JSON.stringify(NOTIFS.slice(0, 60))); }

function notify(title, body, kind, onClick, key, taskId) {
  const k = key || (kind + '|' + title + '|' + String(body || '').slice(0, 60));
  if (SEENKEYS.has(k)) return;
  SEENKEYS.add(k); saveSeen();
  NOTIFS.unshift({k, title, body: body || '', kind: kind || '', ts: Date.now(),
                  task: taskId || S.task, read: false});
  NOTIFS = NOTIFS.slice(0, 60); saveNotifs();
  renderBell();
  transientToast(title, body, kind, onClick);
}

function transientToast(title, body, kind, onClick) {
  const box = $('#toasts');
  const el = document.createElement('div');
  el.className = 'toast ' + (kind || '') + (onClick ? ' click' : '');
  el.innerHTML = `<span class="tt">${esc(title)}</span>${body ? `<span class="tb">${esc(body)}</span>` : ''}` +
    '<button class="tx" aria-label="Dismiss">×</button>';
  el.querySelector('.tx').onclick = ev => { ev.stopPropagation(); el.remove(); };
  if (onClick) el.onclick = () => { el.remove(); onClick(); };
  box.prepend(el);
  while (box.children.length > 3) box.lastChild.remove();
  setTimeout(() => el.remove(), onClick ? 9000 : 5000);
}

function toast(msg, kind) { transientToast(msg, '', kind || 'ok'); }

function renderBell() {
  const unread = NOTIFS.filter(n => !n.read).length;
  const b = $('#bellBadge');
  if (!b) return;
  b.style.display = unread ? 'block' : 'none';
  b.textContent = unread > 9 ? '9+' : String(unread);
}

function toggleNotifs() {
  const host = $('#notifHost');
  if (host.innerHTML) { host.innerHTML = ''; return; }
  const rows = NOTIFS.length ? NOTIFS.map((n, i) => `
    <div class="nitem ${n.read ? '' : 'unread'}" onclick="openNotif(${i})">
      <div class="nt">${esc(n.title)}</div>
      ${n.body ? `<div class="nb">${esc(n.body)}</div>` : ''}
      <div class="nm">${timeAgo(new Date(n.ts).toISOString())}${n.task ? ' · engagement #' + n.task : ''}
        ${n.read ? ' · viewed' : ' · new'}</div>
    </div>`).join('')
    : '<div class="empty" style="margin:.6rem"><b>Nothing yet</b>Findings, observations and scope requests land here.</div>';
  host.innerHTML = `<div class="panel">
      <div class="ph"><span>Notifications</span>
        <span class="row" style="gap:.4rem">
          <button class="sm ghost" onclick="markAllRead()">Mark all read</button>
          <button class="sm ghost" onclick="clearNotifs()">Clear</button></span></div>
      <div class="pl">${rows}</div></div>`;
  setTimeout(() => document.addEventListener('click', closePanelsOnce, {once: true}), 0);
}

function closePanelsOnce(e) {
  if (!e.target.closest('.panel') && !e.target.closest('#bell')) $('#notifHost').innerHTML = '';
}

function markAllRead() { NOTIFS.forEach(n => n.read = true); saveNotifs(); renderBell(); toggleNotifs(); toggleNotifs(); }
function clearNotifs() { NOTIFS = []; saveNotifs(); renderBell(); toggleNotifs(); }

async function openNotif(i) {
  const n = NOTIFS[i];
  if (!n) return;
  n.read = true; saveNotifs(); renderBell();
  $('#notifHost').innerHTML = '';
  if (n.task && n.task !== S.task) await selectTask(n.task);
  if (n.kind === 'finding') setTab('findings');
  else if (n.kind === 'fact') setTab('enumeration');
  else if (n.kind === 'scope') setTab('scope');
  else if (n.kind === 'command') setTab('commands');
  toggleNotifs();
}

/* ---------- planner chat (overview card + dock, per-engagement) ---------- */
function thread(taskId) {
  const id = taskId || S.task;
  if (!CHAT[id]) CHAT[id] = {msgs: [], busy: false, seen: 0};
  return CHAT[id];
}

function pushMsg(taskId, role, text) {
  const th = thread(taskId);
  th.msgs.push({role: role, text: text, ts: Date.now()});
  if (th.msgs.length > 80) th.msgs = th.msgs.slice(-80);
}

function chatBubbles(taskId) {
  const th = thread(taskId);
  if (!th.msgs.length) {
    return `<div class="bubble sys">Ask about progress or say what to do next.
      It can queue intents, hint the planner and steer a running worker.</div>`;
  }
  return th.msgs.map((m, i) => {
    if (m.role === 'me') {
      return `<div class="bubble me">${esc(m.text)}</div>
        <div class="cactions"><button class="sm ghost" title="Send this instruction to the planner"
          onclick="hintFrom(${taskId}, ${i})">Send as hint</button></div>`;
    }
    const ids = [...new Set((m.text.match(/#(\d+)/g) || []).map(x => x.slice(1)))].slice(0, 3);
    return `<div class="bubble you">${esc(m.text)}</div>
      <div class="cactions">
        <button class="sm ghost" onclick="hintFrom(${taskId}, ${i})">Queue as hint</button>
        ${ids.map(id => `<button class="sm" onclick="steer(${id})">Steer #${id}</button>`).join('')}
      </div>`;
  }).join('');
}

async function hintFrom(taskId, idx) {
  const th = thread(taskId);
  const m = th.msgs[idx];
  if (!m) return;
  const text = (m.text || '').slice(0, 800).trim();
  if (!text) return;
  const j = await api('/api/hint', {task: taskId, text: text});
  if (j.error) { toast(j.error, 'err'); return; }
  toast('Queued as a hint on engagement #' + taskId);
}

function toggleChat() {
  const host = $('#chatHost');
  if (host.innerHTML) { host.innerHTML = ''; return; }
  S.chatTask = S.chatTask || S.task;
  renderChat();
  setTimeout(() => { const el = $('#chatText'); if (el) el.focus(); }, 50);
}

function chatTabs() {
  const ids = [...new Set([...Object.keys(CHAT).map(Number), S.task, S.chatTask].filter(Boolean))]
    .sort((a, b) => a - b);
  return `<div class="ctabs">${ids.map(id => {
    const th = thread(id);
    const t = (S.tasks || []).find(x => x.id === id) || {};
    const unread = th.msgs.filter(m => m.ts > th.seen).length && id !== S.chatTask;
    return `<button class="ctab ${id === S.chatTask ? 'on' : ''}" onclick="switchChat(${id})"
      title="${esc(t.title || t.goal || '')}">#${id}${unread ? '<i class="cdot"></i>' : ''}</button>`;
  }).join('')}</div>`;
}

function switchChat(id) { S.chatTask = id; thread(id).seen = Date.now(); renderChat(); }

function renderChat() {
  const host = $('#chatHost');
  if (!host) return;
  const id = S.chatTask || S.task;
  const th = thread(id);
  host.innerHTML = `<div class="chat">
    <div class="ch"><span>Planner · <b>#${id}</b></span>
      <button class="iconbtn" onclick="toggleChat()">×</button></div>
    ${chatTabs()}
    <div class="body" id="chatBody">${chatBubbles(id)}
      ${th.busy ? '<div class="bubble sys">thinking…</div>' : ''}</div>
    <div class="cf">
      <input id="chatText" placeholder="ask about #${id}, or say what to do next"
        onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChat('dock')}">
      <button class="pri" onclick="sendChat('dock')" ${th.busy ? 'disabled' : ''}>Send</button>
    </div></div>`;
  const body = $('#chatBody');
  if (body) body.scrollTop = body.scrollHeight;
}

function renderChatCard() {
  const el = $('#ovChat');
  if (!el) return;
  const k = el.scrollTop;
  el.innerHTML = chatBubbles(S.task) + (thread(S.task).busy ? '<div class="bubble sys">thinking…</div>' : '');
  el.scrollTop = el.scrollHeight || k;
}

async function sendChat(source) {
  const id = source === 'dock' ? (S.chatTask || S.task) : S.task;
  const input = source === 'dock' ? $('#chatText') : $('#ovChatText');
  const text = (input && input.value || '').trim();
  if (!text || !id) return;
  pushMsg(id, 'me', text);
  if (input) input.value = '';
  const th = thread(id);
  th.busy = true;
  if (source === 'dock') renderChat(); else renderChatCard();
  if (source !== 'dock') renderChatCard();
  const j = await api('/api/chat', {task: id, message: text});
  th.busy = false;
  pushMsg(id, 'you', j.error ? 'Error: ' + j.error : (j.reply || '(no reply)'));
  if (source === 'dock') renderChat(); else renderChatCard();
  if ($('#ovChat')) renderChatCard();
  if (id === S.task) refresh(true);
}

function modal(opts) {
  return new Promise(resolve => {
    const host = $('#modalHost');
    const fields = (opts.fields || []).map(f => `
      <label class="f"><span>${esc(f.label)}</span>
        ${f.type === 'textarea'
          ? `<textarea id="m_${f.id}" rows="3">${esc(f.value || '')}</textarea>`
          : `<input id="m_${f.id}" value="${esc(f.value || '')}" placeholder="${esc(f.placeholder || '')}">`}
      </label>`).join('');
    const body = opts.html || fields;
    host.innerHTML = `<div class="overlay" data-overlay>
      <div class="modal card" role="dialog" aria-modal="true">
        <h2 style="margin:0 0 .3rem;font-size:var(--fs-15)">${esc(opts.title)}</h2>
        ${opts.message ? `<div class="muted" style="margin-bottom:.7rem">${opts.message}</div>` : ''}
        ${body}
        <div class="row" style="justify-content:flex-end;margin-top:1rem">
          <button class="ghost" id="mCancel">${esc(opts.cancel || 'Cancel')}</button>
          <button class="${opts.danger ? 'danger' : 'pri'}" id="mOk">${esc(opts.ok || 'Save')}</button>
        </div></div></div>`;
    const close = v => { host.innerHTML = ''; document.removeEventListener('keydown', key); resolve(v); };
    const submit = () => {
      const vals = {};
      (opts.fields || []).forEach(f => { const el = $('#m_' + f.id); vals[f.id] = el ? el.value.trim() : ''; });
      close(opts.fields && opts.fields.length ? vals : true);
    };
    const key = e => {
      if (e.key === 'Escape') close(null);
      if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') { e.preventDefault(); submit(); }
    };
    host.querySelector('[data-overlay]').addEventListener('mousedown', e => {
      if (e.target.dataset.overlay !== undefined) close(null);
    });
    $('#mOk').onclick = submit;
    $('#mCancel').onclick = () => close(null);
    document.addEventListener('keydown', key);
    const first = host.querySelector('input, textarea');
    if (first) { first.focus(); first.select && first.select(); }
  });
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

/* ---------- chrome ---------- */
function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('titan-theme', next);
  if (S.tab === 'graph' && S.graph && $('#pane')) $('#pane').innerHTML = graphHtml(S.graph);
}

function toggleMenu() {
  const host = $('#menuHost');
  if (host.innerHTML) { host.innerHTML = ''; return; }
  const dense = document.documentElement.getAttribute('data-density') === 'compact';
  host.innerHTML = `<div class="menu">
    <button onclick="goGlobal('settings')">Settings</button>
    <button onclick="goGlobal('skills')">Skills</button>
    <div class="sep"></div>
    <button onclick="toggleDensity()">${dense ? 'Comfortable density' : 'Compact density'}</button>
    <button onclick="shortcuts()">Keyboard shortcuts</button>
    <div class="sep"></div>
    <div class="muted">api: localhost only</div>
  </div>`;
  setTimeout(() => document.addEventListener('click', closeMenuOnce, {once: true}), 0);
}
function closeMenuOnce(e) { if (!e.target.closest('.menu') && !e.target.closest('#gear')) $('#menuHost').innerHTML = ''; }
function toggleDensity() {
  const cur = document.documentElement.getAttribute('data-density');
  const next = cur === 'compact' ? 'comfortable' : 'compact';
  document.documentElement.setAttribute('data-density', next);
  localStorage.setItem('titan-density', next);
  $('#menuHost').innerHTML = '';
}

function shortcuts() {
  modal({title: 'Keyboard shortcuts', ok: 'Close', html: `
    <table style="border:0">
      <tr><td><kbd>g</kbd> then <kbd>o</kbd></td><td>Overview</td></tr>
      <tr><td><kbd>g</kbd> then <kbd>f</kbd></td><td>Findings</td></tr>
      <tr><td><kbd>g</kbd> then <kbd>e</kbd></td><td>Enumeration</td></tr>
      <tr><td><kbd>g</kbd> then <kbd>s</kbd></td><td>Scope</td></tr>
      <tr><td><kbd>g</kbd> then <kbd>c</kbd></td><td>Commands</td></tr>
      <tr><td><kbd>g</kbd> then <kbd>v</kbd></td><td>Artifacts</td></tr>
      <tr><td><kbd>g</kbd> then <kbd>a</kbd></td><td>Activity</td></tr>
      <tr><td><kbd>g</kbd> then <kbd>r</kbd></td><td>Graph</td></tr>
      <tr><td><kbd>/</kbd></td><td>Focus the filter box</td></tr>
      <tr><td><kbd>?</kbd></td><td>This list</td></tr>
      <tr><td><kbd>esc</kbd></td><td>Close dialog / menu</td></tr>
    </table>`});
}

document.addEventListener('keydown', e => {
  if (e.target.matches('input,textarea,select')) {
    if (e.key === 'Escape') e.target.blur();
    return;
  }
  if (e.key === 'g') { S.pendingG = Date.now(); return; }
  if (S.pendingG && Date.now() - S.pendingG < 900) {
    const map = {o: 'overview', s: 'scope', c: 'commands', e: 'enumeration', f: 'findings',
                 v: 'artifacts', a: 'activity', r: 'graph'};
    if (map[e.key]) { S.pendingG = 0; if (S.view !== 'task') goGlobal('task'); else setTab(map[e.key]); return; }
  }
  if (e.key === '/') {
    const el = document.querySelector('#findQ') || document.querySelector('#trafficQ')
      || document.querySelector('#hintText');
    if (el) { e.preventDefault(); el.focus(); }
  }
  if (e.key === '?') shortcuts();
  if (e.key === 'Escape') { $('#menuHost').innerHTML = ''; }
});

function drawTabs() {
  if (S.view !== 'task' || !S.data) return '';
  return `<div class="tabs">${TABS.map(([k, label]) =>
    `<button class="${S.tab === k ? 'on' : ''}" onclick="setTab('${k}')">${label}</button>`).join('')}</div>`;
}

async function goGlobal(view) {
  S.view = view; $('#menuHost').innerHTML = '';
  if (view === 'task') { if (S.task) await refresh(true); else showEmpty(); }
  if (view === 'settings') await loadSettings();
  if (view === 'skills') await loadSkills();
}

async function loadTasks() {
  const j = await api('/api/tasks');
  if (j.error) return;
  S.tasks = j.tasks || [];
  diffTaskCounts();
  renderSidebar();
  renderCrumbs();
}

function renderSidebar() {
  const el = $('#tasks'); if (!el) return;
  el.innerHTML = S.tasks.map(t => `
    <div class="task ${t.id === S.task ? 'on' : ''}" onclick="selectTask(${t.id})">
      <button class="kill" title="Delete" onclick="event.stopPropagation(); delTask(${t.id})">×</button>
      <span class="t">${esc(t.title || t.goal)}</span>
      <span class="m"><span class="s-${esc(t.status)}">${esc(t.status)}</span>
        · ${t.round_no} round${t.round_no === 1 ? '' : 's'}
        ${t.findings_total ? '· <span class="sev sev-high" title="' + t.findings_total + ' finding(s)">'
          + t.findings_total + 'F</span>' : ''}
        ${t.facts_total ? '· ' + t.facts_total + ' obs' : ''}</span>
    </div>`).join('') || '<div class="empty">No engagements yet</div>';
}

function renderCrumbs() {
  if (S.view !== 'task' || !S.data) { $('#crumbs').innerHTML = ''; return; }
  const d = S.data;
  $('#crumbs').innerHTML = `<span>Engagement</span><span>/</span>
    <b>#${d.task.id}</b>
    <span class="chip s-${esc(d.task.status)}">${esc(d.task.status)}</span>`;
}

function diffTaskCounts() {
  const counts = t => [t.facts_total || 0, t.findings_total || 0];
  if (!SEEN) { SEEN = {}; S.tasks.forEach(t => { SEEN[t.id] = counts(t); }); return; }
  S.tasks.forEach(t => {
    const [fa, fi] = counts(t);
    const prev = SEEN[t.id];
    if (prev && t.id !== S.task) {
      const title = (t.title || t.goal || '').slice(0, 80);
      if (fi > prev[1]) notify('New finding — #' + t.id, title, 'finding', () => selectTask(t.id));
      else if (fa > prev[0]) notify('New observations — #' + t.id, (fa - prev[0]) + ' added · ' + title,
                                    'fact', () => selectTask(t.id));
    }
    SEEN[t.id] = [fa, fi];
  });
}

async function selectTask(id) {
  S.task = id; S.view = 'task'; S.nodeSel = 0; S.expanded = {}; S.trafficId = 0;
  S.chatTask = id; thread(id).seen = Date.now();
  await loadTasks();
  await refresh(true);
  await loadLive();
}

function showEmpty() {
  $('#main').innerHTML = '<div class="empty"><b>No engagement selected</b>Create one, or pick one from the list.</div>';
}

/* ---------- state ---------- */
async function refresh(force) {
  if (!S.task || S.view !== 'task') return;
  const j = await api('/api/state?task=' + S.task);
  if (j.error) {
    if (force) toast(j.error, 'err');
    S.task = 0; S.data = null; showEmpty(); $('#crumbs').innerHTML = ''; $('#live').innerHTML = '';
    return;
  }
  const prev = S.data;
  S.data = j;
  if (prev) {
    const nf = j.overview.findings_total - prev.overview.findings_total;
    const no = j.overview.facts_total - prev.overview.facts_total;
    if (nf > 0) {
      const f = (j.findings || [])[0];
      notify(nf === 1 ? 'New finding' : nf + ' new findings',
             f ? (f.vulnclass + ' — ' + f.summary) : '', 'finding',
             () => { setTab('findings'); }, 'finding:' + S.task + ':' + (f ? f.id : nf));
    }
    if (no > 0) {
      const f = (j.overview.recent_facts || [])[0];
      notify(no === 1 ? 'New observation' : no + ' new observations',
             f ? f.summary : '', 'fact', () => { setTab('enumeration'); },
             'fact:' + S.task + ':' + no);
    }
    const cmds = ((j.commands || {}).pending || []).length;
    const prevCmds = ((prev.commands || {}).pending || []).length;
    if (cmds > prevCmds) {
      const c = ((j.commands || {}).pending || [])[0];
      notify('Command waiting for approval', c ? (c.rule + ' — ' + (c.command || '').slice(0, 80)) : '',
             'command', () => { setTab('commands'); }, 'cmd:' + S.task + ':' + (c ? c.id : cmds));
    }
    const pend = ((j.scope || {}).pending || []).length;
    const prevPend = ((prev.scope || {}).pending || []).length;
    if (pend > prevPend) {
      const c = ((j.scope || {}).pending || [])[0];
      notify('Outside scope — approval needed', c ? c.host + ' was found by the run' : '',
             'scope', () => { setTab('scope'); }, 'scope:' + S.task + ':' + (c ? c.id : pend));
    }
  }
  const sig = [j.task.status, j.overview.round, j.overview.facts_total, j.overview.findings_total,
               j.overview.open_intents.length, j.overview.running_intents.length,
               j.running ? 1 : 0, j.approval ? 1 : 0, S.tab,
               j.enumeration && j.enumeration.counts ? j.enumeration.counts.services : 0,
               (j.findings || []).map(f => f.id + f.status).join(','),
               (j.timeline || []).length,
               ((j.scope || {}).pending || []).length,
               ((j.commands || {}).pending || []).length].join('|');
  renderCrumbs();
  if (!force && sig === S.lastSig && prev) { renderLiveFromData(); return; }
  S.lastSig = sig;
  const ae = document.activeElement;
  const typing = ae && ae.closest('#main') && /INPUT|TEXTAREA|SELECT/.test(ae.tagName);
  if (typing && !force) return;
  const scroller = $('#main');
  const st = scroller ? scroller.scrollTop : 0;
  render();
  if (scroller) scroller.scrollTop = st;
}

function render() {
  if (S.view !== 'task' || !S.data) return;
  const d = S.data, ov = d.overview;
  const sc = $('#main');
  const keepMain = sc ? sc.scrollTop : 0;
  const keepTree = ($('#artTree') || {}).scrollTop || 0;
  const keepChat = ($('#ovChat') || {}).scrollTop || 0;
  const keepGraph = ($('#graphwrap') || {}).scrollLeft || 0;
  const dense = document.documentElement.getAttribute('data-density') === 'compact';
  const cov = ov.coverage;
  $('#main').innerHTML = `
    <div class="pagehead">
      <div>
        <h2>${esc(d.task.title || ('Engagement #' + d.task.id))}</h2>
        <div class="goal">${esc(d.task.goal)}</div>
      </div>
      <div class="actions">
        <div class="seg" title="Autonomy for this engagement">
          <button class="${(d.mode || 'autonomous') === 'autonomous' ? 'on' : ''}"
            onclick="setMode('autonomous')">Autonomous</button>
          <button class="${d.mode === 'approval' ? 'on' : ''}"
            onclick="setMode('approval')">Approval</button>
        </div>
        <span class="hint" style="margin-left:.2rem">workers</span>
        <div class="stepper" title="Parallel workers — applies live">
          <button onclick="bumpWorkers(-1)">−</button>
          <input id="rWorkers" value="${d.workers || 2}" onchange="applyWorkers()">
          <button onclick="bumpWorkers(1)">+</button>
        </div>
        <button class="pri" onclick="runTask()" ${d.running ? 'disabled' : ''}>${d.running ? 'Running…' : 'Start'}</button>
        <button onclick="stopTask()" ${(d.running || d.approval) ? '' : 'disabled'}>Stop</button>
        <button onclick="reportPreview()" title="Client-facing report">Report</button>
        <button class="ghost" onclick="taskMenu(${d.task.id})" title="More">⋯</button>
      </div>
    </div>
    <div class="statline">
      <span class="row" style="gap:.4rem">coverage
        <span class="meter"><i style="width:${cov.pct}%"></i></span>
        <b>${cov.pct}%</b> <span class="muted">${cov.tested} of ${cov.assets} asset${cov.assets === 1 ? '' : 's'}</span></span>
      <span class="chip">${ov.findings_total} finding${ov.findings_total === 1 ? '' : 's'}</span>
      <span class="chip">${ov.facts_total} observation${ov.facts_total === 1 ? '' : 's'}</span>
      <span class="chip">round ${ov.round}</span>
      ${(d.scope && (d.scope.pending || []).length) ? `<span class="chip s-running"
        style="cursor:pointer" onclick="setTab('scope')">${d.scope.pending.length} host(s) need scope</span>` : ''}
      ${(d.commands && (d.commands.pending || []).length) ? `<span class="chip s-running"
        style="cursor:pointer" onclick="setTab('commands')">${d.commands.pending.length} command(s) need approval</span>` : ''}
      <span style="flex:1"></span>
      <span class="mono muted" style="font-size:var(--fs-11)" title="artifacts: ${esc(d.workdir || '')}">${esc(d.workdir || '~/.titan/runs/tasks/' + d.task.id)}</span>
      ${d.running ? '<span class="chip s-running">● running</span>' : ''}
    </div>
    ${(!d.running && !d.approval && (ov.open_intents.length + ov.running_intents.length) > 0) ? `
      <div class="banner" style="border-color:var(--warn)"><div class="row">
        <b>No worker is running.</b>
        <span class="muted">${ov.open_intents.length + ov.running_intents.length} intent(s) are queued
          from the last round — press Start to resume them.</span></div></div>` : ''}
    ${d.approval ? `<div class="banner"><div class="row">
        <b>Waiting for your approval</b><span class="chip">round ${d.approval.round_no}</span>
        <span style="flex:1"></span>
        <button class="pri" onclick="decide('approve')">Approve &amp; continue</button>
        <button class="danger" onclick="decide('deny')">Stop here</button></div>
        <div class="muted" style="margin-top:.25rem">${esc(d.approval.note || '')}</div></div>` : ''}
    ${drawTabs()}
    <div id="pane"></div>`;
  const pane = $('#pane');
  if (S.tab === 'overview') pane.innerHTML = tabOverview(d);
  if (S.tab === 'scope') pane.innerHTML = tabScope(d, S.scopeInfo);
  if (S.tab === 'commands') pane.innerHTML = tabCommands(d, S.commands);
  if (S.tab === 'findings') pane.innerHTML = tabFindings(d);
  if (S.tab === 'enumeration') pane.innerHTML = tabEnumeration(d);
  if (S.tab === 'artifacts') { pane.innerHTML = tabArtifacts(d); loadArtifacts(); }
  if (S.tab === 'activity') pane.innerHTML = tabActivity(d);
  if (S.tab === 'graph') { pane.innerHTML = '<div class="skel" style="height:8rem"></div>'; loadGraph(); }
  if (sc) sc.scrollTop = keepMain;
  const tree = $('#artTree'); if (tree) tree.scrollTop = keepTree;
  const oc = $('#ovChat'); if (oc) oc.scrollTop = keepChat;
  const gw = $('#graphwrap'); if (gw) gw.scrollLeft = keepGraph;
  renderLiveFromData();
  renderBell();
  if (S.tab === 'overview') thread(S.task).seen = Date.now();
  renderChatCard();
}

function typingGuard() { return false; }

function setTab(t) {
  S.tab = t;
  const sc = $('#main'); const st = sc ? sc.scrollTop : 0;
  render();
  if (sc) sc.scrollTop = st;
  if (t === 'scope' && S.task) loadScope();
  if (t === 'commands' && S.task) loadCommands();
  if (t === 'artifacts' && S.task) loadArtifacts();
}

/* ---------- overview ---------- */
function tabOverview(d) {
  const ov = d.overview;
  const queue = [...ov.running_intents, ...ov.open_intents];
  const cov = d.coverage || {untested: []};
  return `
  <div class="card" style="margin-bottom:.9rem">
    <div class="row" style="justify-content:space-between;margin-bottom:.4rem">
      <h3 style="margin:0;font-size:var(--fs-15)">Intent timeline</h3>
      <span class="hint">${(d.timeline || []).length} intents · bar length is wall-clock duration · click a bar to open it</span>
    </div>
    ${gantt(d.timeline || [])}
  </div>

  <div class="grid2">
    <div class="card"><h3 style="margin:0 0 .5rem;font-size:var(--fs-15)">Goals</h3>
      ${ov.goals.map(g => `<div class="row" style="margin-bottom:.3rem;align-items:flex-start">
        <span class="chip s-${esc(g.state)}">${esc(g.state)}</span><span>${esc(g.text)}</span></div>`).join('')
        || '<span class="muted">none</span>'}
      <hr>
      <h3 style="margin:0 0 .4rem;font-size:var(--fs-12);color:var(--dim)">Constraints</h3>
      ${ov.constraints.map(c => `<div><span class="chip">${esc(c.kind)}</span> ${esc(c.text)}</div>`).join('')
        || '<span class="muted">none stated</span>'}
    </div>
    <div class="card" style="display:flex;flex-direction:column">
      <div class="row" style="justify-content:space-between;margin-bottom:.4rem">
        <h3 style="margin:0;font-size:var(--fs-15)">Planner</h3>
        <span class="hint">top funnel — ask, or tell it what to do</span>
      </div>
      <div id="ovChat" class="chatmini">${chatBubbles(d.task.id)}</div>
      <div class="cf" style="margin-top:.45rem">
        <input id="ovChatText" placeholder="ask about progress, or say what to do next"
          onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChat('ov')}">
        <button class="pri" onclick="sendChat('ov')">Send</button>
      </div>
      <div class="qstrip">
        <div class="hint" style="margin:.5rem 0 .25rem;text-transform:uppercase;letter-spacing:.05em">
          Queue · ${queue.filter(i => i.state === 'running').length} running ·
          ${queue.filter(i => i.state !== 'running').length} open</div>
        ${queue.map(intentRow).join('') || '<div class="muted">idle — nothing dispatched</div>'}
      </div>
    </div>
  </div>

  ${ov.hints.length ? `<div class="card" style="margin-top:.9rem">
    <div class="row" style="justify-content:space-between;margin-bottom:.4rem">
      <h3 style="margin:0;font-size:var(--fs-15)">Operator notes</h3>
      <span class="hint">${ov.hints.length} hint(s) fed to the planner, newest last</span></div>
    ${ov.hints.map((h, i) => `<div style="margin-bottom:.45rem">
      <span class="chip">note ${i + 1}</span> <span>${esc(h.text)}</span></div>`).join('')}
  </div>` : ''}

  <div class="card" style="margin-top:.9rem">
    <div class="row" style="justify-content:space-between;margin-bottom:.4rem">
      <h3 style="margin:0;font-size:var(--fs-15)">Scope</h3>
      <span class="hint">hosts and ranges the guard will allow</span>
    </div>
    <div class="row" style="margin-bottom:.5rem">
      ${ov.scope.map(s => `<span class="chip"><code>${esc(s.value)}</code>
        <span class="muted">${esc(s.kind)}</span></span>`).join('')
        || '<span class="s-failed">No scope — every targeted command is refused.</span>'}
    </div>
    <div class="row">
      <select id="scopeKind" style="width:7rem">
        <option>domain</option><option>ip</option><option>cidr</option><option>url</option><option>keyword</option>
      </select>
      <input id="scopeValue" placeholder="value" style="flex:1">
      <button onclick="addScope()">Add target</button>
    </div>
  </div>

  <div class="grid2" style="margin-top:.9rem">
    <div class="card"><h3 style="margin:0 0 .4rem;font-size:var(--fs-15)">Live agents</h3>
      <div id="liveCards"><div class="skel"></div></div></div>
    <div class="card"><h3 style="margin:0 0 .4rem;font-size:var(--fs-15)">Untested assets</h3>
      ${(cov.untested || []).length
        ? cov.untested.slice(0, 12).map(a => `<div class="mono hint">${esc(a.url || a.domain || a.ip || '')}</div>`).join('')
          + (cov.untested.length > 12 ? `<div class="hint">+ ${cov.untested.length - 12} more</div>` : '')
        : '<div class="muted">None — everything seen is covered by a finished intent.</div>'}
    </div>
  </div>`;
}

function intentRow(i) {
  const timing = i.state === 'running'
    ? `started ${esc(i.started || '')} · running ${fmtDur(i.took_s)}`
    : `${esc(i.started || '')} → ${esc(i.finished || '')} · ${fmtDur(i.took_s)}`;
  return `<div style="margin-bottom:.55rem">
    <div class="row" style="align-items:flex-start">
      <span class="chip s-${esc(i.state)}">${esc(i.state)}</span>
      <span style="flex:1">#${i.id} ${esc(i.summary)}</span>
      ${i.state === 'running' ? `<button class="sm" onclick="steer(${i.id})">Steer</button>
        <button class="sm danger" onclick="kill(${i.id})">Stop</button>` : ''}
    </div>
    <div class="hint">${timing}</div></div>`;
}

function gantt(items) {
  if (!items.length) return '<div class="muted">No intents yet.</div>';
  const times = [];
  items.forEach(i => {
    if (i.started_at) times.push(Date.parse(i.started_at));
    if (i.finished_at) times.push(Date.parse(i.finished_at));
  });
  const t0 = Math.min(...times), t1 = Math.max(...times, Date.now());
  const span = Math.max(1000, t1 - t0);
  const lanes = {};
  items.forEach(i => {
    const w = i.worker && i.worker.startsWith('w') ? i.worker : 'unassigned';
    (lanes[w] = lanes[w] || []).push(i);
  });
  const rows = Object.keys(lanes).sort().map(w => {
    const bars = lanes[w].map(i => {
      const s = Date.parse(i.started_at || new Date().toISOString());
      const e = i.finished_at ? Date.parse(i.finished_at) : Date.now();
      const left = ((s - t0) / span) * 100;
      const width = Math.max(0.6, ((e - s) / span) * 100);
      const cls = ['done', 'stopped', 'blocked', 'failed', 'open', 'running', 'exhausted']
        .includes(i.state) ? i.state : 'running';
      return `<div class="bar ${cls}" style="left:${left.toFixed(2)}%;width:${width.toFixed(2)}%"
        title="#${i.id} ${esc(i.summary).slice(0, 90)} — ${fmtDur(i.took_s)} (${esc(i.state)})"
        onclick="openIntent(${i.id})"></div>`;
    }).join('');
    return `<div class="lane"><div class="who" title="${esc(w)}">${esc(w)}</div>
      <div class="track">${bars}</div></div>`;
  }).join('');
  const fmt = ts => new Date(ts).toLocaleTimeString('en-GB', {hour: '2-digit', minute: '2-digit'});
  return `<div class="gantt">${rows}<div class="axis"><span>${fmt(t0)}</span>
    <span>${fmt((t0 + t1) / 2)}</span><span>${fmt(t1)}</span></div></div>`;
}

function openIntent(id) { S.tab = 'activity'; S.actQ = '#' + id; setTab('activity'); }

/* ---------- live agents ---------- */
async function loadLive() {
  if (!S.task) return;
  const j = await api('/api/agents?task=' + S.task);
  S.lastResult = j;
  renderLive(j);
}

function renderLiveFromData() {
  const d = S.data;
  if (!d) return;
  const strip = (d.overview.running_intents || []).map(i =>
    `<span class="pill"><span class="dot live"></span>w? · #${i.id}</span>`).join('');
  $('#live').innerHTML = d.running
    ? (strip || '<span class="pill"><span class="dot live"></span>planner</span>')
    : (d.approval ? '<span class="pill"><span class="dot tool"></span>awaiting approval</span>' : '');
}

function renderLive(a) {
  const el = $('#liveCards'); if (!el) return;
  const live = (a && a.live) || [];
  el.innerHTML = live.length ? live.map(x => {
    const cls = x.state === 'tool' ? 'tool' : (x.idle_s > 20 ? 'idle' : 'live');
    return `<div class="row" style="align-items:flex-start;margin-bottom:.45rem;flex-wrap:nowrap">
      <span class="dot ${cls}" style="margin-top:.45rem"></span>
      <div style="flex:1"><div class="row"><b>${esc(x.key)}</b>
        <span class="chip s-${esc(x.state)}">${esc(x.state)}</span>
        ${x.intent ? `<span class="muted">#${x.intent}</span>` : ''}
        <span class="hint">${x.elapsed_s}s · ${x.turns} turns · ${(x.tokens_in || 0) + (x.tokens_out || 0)} tok</span>
        ${x.state === 'tool' && x.intent ? `<button class="sm" onclick="steer(${x.intent})">Steer</button>` : ''}</div>
      <div class="hint mono">${esc(x.tool ? x.tool + ' — ' : '')}${esc((x.note || '').slice(0, 160))}</div>
      </div></div>`;
  }).join('') : '<div class="muted">No agent running.</div>';
}

/* ---------- scope ---------- */
async function loadScope() {
  if (!S.task) return;
  S.scopeInfo = await api('/api/scope?task=' + S.task);
  if (S.tab !== 'scope') return;
  const pane = $('#pane'); if (!pane) return;
  pane.innerHTML = tabScope(S.data, S.scopeInfo);
}

function scopeCovers(entries, host) {
  if (!host) return true;
  const h = host.toLowerCase();
  return (entries || []).some(e => {
    if (e.kind === 'exclude') return false;
    const v = (e.value || '').toLowerCase().split('://').pop().split('/')[0].split(':')[0];
    if (e.kind === 'ip' || e.kind === 'cidr') return h === v;
    if (e.kind === 'subdomain') return h === v;
    return h === v || h.endsWith('.' + v);
  });
}

function tabScope(d, info) {
  info = info || S.scopeInfo || {entries: (d.scope || {}).entries || [],
    candidates: (d.scope || {}).pending || [], policy: (d.scope || {}).policy || {},
    resolved: {}, matches: {}};
  const entries = info.entries || [];
  const pending = (info.candidates || []).filter(c => c.state === 'pending');
  const decided = (info.candidates || []).filter(c => c.state !== 'pending').slice(0, 8);
  const policy = info.policy || {};
  const kindLabel = {domain: 'domain + subdomains', subdomain: 'exact host', ip: 'address',
    cidr: 'range', url: 'url', keyword: 'keyword', exclude: 'exclude'};
  const row = e => {
    const res = (info.resolved || {})[e.value];
    return `<tr>
      <td><span class="chip">${esc(kindLabel[e.kind] || e.kind)}</span></td>
      <td class="mono">${esc(e.value)}</td>
      <td class="hint">${res && res.length ? esc(res.join(', ')) : '—'}</td>
      <td class="muted">${esc(e.reason || '')}</td>
      <td class="num"><button class="sm ghost" title="Remove"
        onclick="removeScope('${esc(e.kind)}','${esc(e.value).replace(/'/g, '&#39;')}')">×</button></td></tr>`;
  };
  const approved = entries.filter(e => e.kind !== 'exclude');
  const excludes = entries.filter(e => e.kind === 'exclude');
  return `
  <div class="grid2">
    <div class="card">
      <div class="row" style="justify-content:space-between;margin-bottom:.4rem">
        <h3 style="margin:0;font-size:var(--fs-15)">Approved targets</h3>
        <span class="chip">${approved.length}</span></div>
      <table><tr><th>Matches</th><th>Value</th><th>Resolves to</th><th>Source</th><th></th></tr>
        ${approved.map(row).join('') || '<tr><td colspan="5" class="muted">No scope — every target is refused.</td></tr>'}
      </table>
      <div class="row" style="margin-top:.6rem">
        <select id="scopeKind" style="width:11rem">
          <option value="domain">domain + subdomains</option>
          <option value="subdomain">exact host</option>
          <option value="ip">address</option>
          <option value="cidr">range (cidr)</option>
          <option value="url">url (host:port)</option>
          <option value="keyword">keyword</option>
        </select>
        <input id="scopeValue" placeholder="example.com, 10.0.0.0/24, https://app:8443" style="flex:1">
        <button class="pri" onclick="addScopeEntry()">Add</button>
      </div>
      <div class="hint" style="margin-top:.3rem">A domain entry allows its subdomains and any
        address those names resolve to, so scans against the IP are not refused. Pasted commands
        are reduced to their targets — a command is never stored as scope.</div>
    </div>

    <div class="card">
      <div class="row" style="justify-content:space-between;margin-bottom:.4rem">
        <h3 style="margin:0;font-size:var(--fs-15)">Discovered — pending approval</h3>
        <span class="chip ${pending.length ? 's-running' : ''}">${pending.length}</span></div>
      ${pending.length ? pending.map(c => `
        <div style="border-top:1px solid var(--line);padding:.45rem 0">
          <div class="row" style="align-items:flex-start">
            <code style="flex:1">${esc(c.host)}</code>
            <button class="pri sm" onclick="decideScope(${c.id}, true)">Approve</button>
            <button class="sm" onclick="decideScope(${c.id}, false)">Reject</button>
          </div>
          <div class="hint">${esc(c.source || '')} · ${esc(timeAgo(c.created_at))}
            ${c.evidence ? ' · ' + esc((c.evidence || '').slice(0, 140)) : ''}</div>
        </div>`).join('') : '<div class="muted">Nothing waiting. Hosts the guard refuses appear here.</div>'}
      ${decided.length ? `<div class="hint" style="margin-top:.5rem">recently decided:
        ${decided.map(c => `<span class="chip">${esc(c.host)} ${esc(c.state)}</span>`).join(' ')}</div>` : ''}

      <hr>
      <h3 style="margin:0 0 .4rem;font-size:var(--fs-15)">Automatic approval</h3>
      <label class="row" style="gap:.4rem;margin-bottom:.3rem">
        <input type="checkbox" style="width:auto" ${policy.auto_subdomains ? 'checked' : ''}
          onchange="setScopePolicy({auto_subdomains: this.checked})">
        <span>Subdomains of an approved domain <span class="hint">(recommended)</span></span></label>
      <label class="row" style="gap:.4rem;margin-bottom:.3rem">
        <input type="checkbox" style="width:auto" ${policy.auto_same_ip ? 'checked' : ''}
          onchange="setScopePolicy({auto_same_ip: this.checked})">
        <span>Hosts sharing an address with an approved target</span></label>
      <label class="row" style="gap:.4rem">
        <input type="checkbox" style="width:auto" ${policy.auto_any ? 'checked' : ''}
          onchange="setScopePolicy({auto_any: this.checked})">
        <span>Any host the run discovers <span class="hint">(hands-off; still logged)</span></span></label>
      <div class="hint" style="margin-top:.3rem">Everything not covered waits for you here.
        Auto-approvals are tagged in the audit log.</div>

      <hr>
      <h3 style="margin:0 0 .4rem;font-size:var(--fs-15)">Excluded</h3>
      ${excludes.map(row).join('') || '<div class="muted">No exclusions.</div>'}
      <div class="row" style="margin-top:.4rem">
        <input id="excludeValue" placeholder="staging.example.com" style="flex:1">
        <button onclick="addExclude()">Exclude</button></div>
    </div>
  </div>`;
}

async function addScopeEntry() {
  const kind = $('#scopeKind').value, value = ($('#scopeValue').value || '').trim();
  if (!value) return;
  const j = await api('/api/scope/add', {task: S.task, kind: kind, value: value});
  if (j.error) { toast(j.error, 'err'); return; }
  $('#scopeValue').value = '';
  toast('Scope updated'); await refresh(true); await loadScope();
}

async function addExclude() {
  const value = ($('#excludeValue').value || '').trim();
  if (!value) return;
  const j = await api('/api/scope/add', {task: S.task, kind: 'exclude', value: value});
  if (j.error) { toast(j.error, 'err'); return; }
  $('#excludeValue').value = '';
  toast('Excluded ' + value); await refresh(true); await loadScope();
}

async function removeScope(kind, value) {
  const j = await api('/api/scope/remove', {task: S.task, kind: kind, value: value});
  if (j.error) { toast(j.error, 'err'); return; }
  toast('Removed ' + value); await refresh(true); await loadScope();
}

async function decideScope(id, approve) {
  const j = await api('/api/scope/decide', {id: id, approve: approve});
  if (j.error) { toast(j.error, 'err'); return; }
  toast((approve ? 'Approved ' : 'Rejected ') + j.host + (approve ? ' — the run can use it now' : ''));
  await refresh(true); await loadScope();
}

async function setScopePolicy(patch) {
  const j = await api('/api/scope/policy', {task: S.task, ...patch});
  if (j.error) { toast(j.error, 'err'); return; }
  toast('Scope policy updated'); await refresh(true); await loadScope();
}

/* ---------- command approvals ---------- */
async function loadCommands() {
  if (!S.task) return;
  S.commands = await api('/api/commands?task=' + S.task);
  if (S.tab !== 'commands') return;
  const pane = $('#pane');
  if (pane) pane.innerHTML = tabCommands(S.data, S.commands);
}

function tabCommands(d, info) {
  info = info || S.commands || {pending: (d.commands || {}).pending || [],
    decided: [], policy: (d.commands || {}).policy || {}};
  const pending = info.pending || [];
  const decided = (info.decided || []).filter(c => c.state !== 'pending').slice(0, 12);
  const policy = info.policy || {};
  return `<div class="card" style="margin-bottom:.8rem">
      <div class="row" style="justify-content:space-between">
        <div><h3 style="margin:0;font-size:var(--fs-15)">Command approval</h3>
          <div class="hint">Commands the guard holds for a human decision — state-changing requests,
            privileged actions, exploitation tooling, installs and writes outside the folder.
            Scope is separate: an approved host does not approve a risky command.</div></div>
        <label class="row" style="gap:.4rem;white-space:nowrap">
          <input type="checkbox" style="width:auto" ${policy.auto_commands ? 'checked' : ''}
            onchange="setCommandPolicy(this.checked)">
          <span>Auto-approve commands</span></label>
      </div></div>
    ${pending.length ? pending.map(c => `
      <div class="card" style="margin-bottom:.6rem">
        <div class="row" style="align-items:flex-start">
          <span class="chip s-running">pending</span>
          <div style="flex:1;min-width:12rem">
            <div class="hint">${esc(c.rule || '')} · ${esc(c.worker || '')} · ${esc(timeAgo(c.created_at))}</div>
            <pre style="margin:.25rem 0">${esc(c.command)}</pre>
          </div>
          <div class="row">
            <button class="pri sm" onclick="decideCommand(${c.id}, true)">Approve</button>
            <button class="sm" onclick="decideCommand(${c.id}, false)">Reject</button></div>
        </div></div>`).join('')
      : `<div class="empty"><b>Nothing waiting</b>Commands that need a decision appear here;
          with auto-approval on, they run and are recorded instead.</div>`}
    ${decided.length ? `<div class="card"><div class="hint" style="text-transform:uppercase;
        letter-spacing:.05em;margin-bottom:.3rem">Recently decided</div>
      <table><tr><th>State</th><th>Command</th><th>Rule</th><th>When</th></tr>
        ${decided.map(c => `<tr><td><span class="chip s-${c.state === 'rejected' ? 'failed' : 'done'}">${esc(c.state)}</span></td>
          <td class="mono">${esc((c.command || '').slice(0, 120))}</td>
          <td class="muted">${esc(c.rule || '')}</td>
          <td class="mono muted">${esc(c.decided_at ? c.decided_at.slice(11, 19) : '')}</td></tr>`).join('')}
      </table></div>` : ''}`;
}

async function decideCommand(id, approve) {
  const j = await api('/api/commands/decide', {id: id, approve: approve});
  if (j.error) { toast(j.error, 'err'); return; }
  toast((approve ? 'Approved — the worker can repeat the command' : 'Rejected') );
  await refresh(true); await loadCommands();
}

async function setCommandPolicy(on) {
  const j = await api('/api/scope/policy', {task: S.task, auto_commands: on});
  if (j.error) { toast(j.error, 'err'); return; }
  toast(on ? 'Commands are auto-approved (still recorded)' : 'Commands now wait for you');
  await refresh(true); await loadCommands();
}

/* ---------- findings ---------- */
function sevRank(s) { return ({critical: 0, high: 1, medium: 2, low: 3, info: 4})[s] ?? 9; }

function tabFindings(d) {
  let fs = (d.findings || []).slice().sort((a, b) => sevRank(a.severity) - sevRank(b.severity));
  const total = fs.length;
  if (S.findSev) fs = fs.filter(f => f.severity === S.findSev);
  if (S.findStatus) fs = fs.filter(f => f.status === S.findStatus);
  if (S.findQ) {
    const q = S.findQ.toLowerCase();
    fs = fs.filter(f => (f.vulnclass + f.summary + (f.endpoint || '')).toLowerCase().includes(q));
  }
  const sevs = ['critical', 'high', 'medium', 'low', 'info'];
  const toolbar = `<div class="filters">
      <input id="findQ" placeholder="Filter findings" value="${esc(S.findQ)}" style="width:16rem"
        oninput="S.findQ=this.value; clearTimeout(window._ft); window._ft=setTimeout(()=>setTab('findings'),200)">
      ${sevs.map(s => `<span class="chip ${S.findSev === s ? 'on' : ''}"
        onclick="S.findSev='${S.findSev === s ? '' : s}'; setTab('findings')">${s}</span>`).join('')}
      <span class="chip ${S.findStatus === 'open' ? 'on' : ''}"
        onclick="S.findStatus='${S.findStatus === 'open' ? '' : 'open'}'; setTab('findings')">open only</span>
      <span style="flex:1"></span>
      <button class="sm" onclick="copyAllFindings()">Copy all (markdown)</button>
      <button class="sm" onclick="reportPreview()">Report preview</button>
    </div>`;
  if (!total) {
    return toolbar + `<div class="empty"><b>No findings yet</b>
      The agent records a finding only with reproducible evidence — version matches are observations, not findings.</div>`;
  }
  if (!fs.length) return toolbar + '<div class="empty">No findings match the current filter.</div>';
  return toolbar + fs.map(f => findingCard(f)).join('');
}

function findingCard(f) {
  const open = !!S.expanded['f' + f.id];
  const states = ['open', 'confirmed', 'false_positive', 'duplicate', 'ignored'];
  return `<div class="card" style="margin-bottom:.6rem">
    <div class="row" style="align-items:flex-start">
      <span class="sev sev-${esc(f.severity)}">${esc(f.severity)}</span>
      <div style="flex:1;min-width:12rem">
        <div style="font-weight:600">${esc(f.vulnclass)}</div>
        <div class="hint">${esc(f.endpoint || '—')}${f.parameter ? ' · ' + esc(f.parameter) : ''}
          · #${f.id} · ${esc(f.at_local || '')} · ${esc(f.proof_basis)}</div>
      </div>
      <div class="seg">${states.map(s => `<button class="${f.status === s ? 'on' : ''}"
        onclick="setFinding(${f.id},'${s}')" title="${s}">${shortStatus(s)}</button>`).join('')}</div>
      <button class="sm ghost" onclick="toggleFinding(${f.id})">${open ? 'Hide' : 'Details'}</button>
    </div>
    <div style="margin:.35rem 0">${esc(f.summary)}</div>
    ${open ? findingDetail(f) : ''}
  </div>`;
}

function shortStatus(s) {
  return ({open: 'Open', confirmed: 'Confirmed', false_positive: 'FP',
           duplicate: 'Dup', ignored: 'Ignored'})[s] || s;
}

function findingDetail(f) {
  return `<div class="grid2" style="margin-top:.5rem">
      <div><h3 style="margin:0 0 .3rem;font-size:var(--fs-12);color:var(--dim)">Evidence</h3>
        <pre>${esc(deesc(f.evidence))}</pre></div>
      <div><h3 style="margin:0 0 .3rem;font-size:var(--fs-12);color:var(--dim)">Reproduction</h3>
        <pre>${esc(deesc(f.poc || '—'))}</pre>
        ${f.counterevidence ? `<h3 style="margin:.4rem 0 .3rem;font-size:var(--fs-12);color:var(--dim)">Considered and excluded</h3>
          <div class="hint">${esc(f.counterevidence)}</div>` : ''}
        <div class="row" style="margin-top:.4rem">
          <button class="sm" onclick="copyFinding(${f.id})">Copy as markdown</button>
          <span class="hint">traffic ${esc(JSON.stringify(f.traffic_refs))}</span></div>
      </div></div>`;
}

function toggleFinding(id) { S.expanded['f' + id] = !S.expanded['f' + id]; setTab('findings'); }

function findingMd(f) {
  return `### ${f.vulnclass} — ${f.severity}\n\n` +
    `**Asset:** ${f.endpoint || '—'}  \n` +
    `**Parameter:** ${f.parameter || '—'}  \n` +
    `**Status:** ${f.status} · **Confidence:** ${f.confidence} (${f.proof_basis})  \n` +
    `**Evidence refs:** ${(f.traffic_refs || []).join(', ') || '—'}\n\n` +
    `${f.summary}\n\n**Evidence**\n\n\`\`\`\n${(f.evidence || '').trim()}\n\`\`\`\n` +
    (f.poc ? `\n**Reproduction**\n\n\`\`\`\n${f.poc.trim()}\n\`\`\`\n` : '') +
    (f.counterevidence ? `\n**Considered and excluded:** ${f.counterevidence}\n` : '');
}

async function copyFinding(id) {
  const f = (S.data.findings || []).find(x => x.id === id);
  if (!f) return;
  try { await navigator.clipboard.writeText(findingMd(f)); toast('Finding #' + id + ' copied'); }
  catch (e) { toast('Clipboard blocked by the browser', 'err'); }
}

async function copyAllFindings() {
  const fs = S.data.findings || [];
  if (!fs.length) return;
  const md = fs.map(findingMd).join('\n---\n\n');
  try { await navigator.clipboard.writeText(md); toast(fs.length + ' findings copied'); }
  catch (e) { toast('Clipboard blocked by the browser', 'err'); }
}

function reportPreview() { window.open('/api/report?task=' + S.task, '_blank'); }

/* ---------- enumeration ---------- */
function tabEnumeration(d) {
  const e = d.enumeration || {hosts: [], counts: {}};
  const c = e.counts || {};
  const scopeEntries = ((d.scope || {}).entries) || [];
  const head = `<div class="filters">
      <span class="chip">${c.hosts || 0} hosts</span><span class="chip">${c.services || 0} services</span>
      <span class="chip">${c.endpoints || 0} paths</span><span class="chip">${c.observations || 0} observations</span>
      <span style="flex:1"></span>
      <button class="sm ghost" onclick="refresh(true)">Refresh</button></div>`;
  const body = (e.hosts && e.hosts.length)
    ? e.hosts.map(h => hostBlock(h, scopeEntries)).join('')
    : `<div class="empty"><b>Nothing enumerated yet</b>Hosts, services, paths and observations
        appear here as the workers write them back, and are mirrored under
        <code>enumeration/</code> in the engagement folder.</div>`;
  const raw = (d.overview.recent_facts || []).length ? `
    <details style="margin-top:.8rem"><summary class="hint" style="cursor:pointer">
      Raw observations (${d.overview.recent_facts.length})</summary>
      <table style="margin-top:.4rem"><tr><th>#</th><th>Fact</th><th>Source</th><th>Confidence</th><th>When</th></tr>
      ${d.overview.recent_facts.map(x => `<tr><td class="muted">${x.id}</td><td>${esc(x.summary)}</td>
        <td class="muted">${esc(x.source || '')}</td><td class="muted">${esc(x.confidence || '')}</td>
        <td class="mono muted">${esc(x.at_local || '')}</td></tr>`).join('')}</table></details>` : '';
  return head + body + raw;
}

function confidenceChip(o) {
  const live = o.confidence === 'observed';
  return `<span class="chip" style="border-color:${live ? 'var(--ok)' : 'var(--line)'};
    color:${live ? 'var(--ok)' : 'var(--dim)'}">${esc(o.confidence || 'inferred')}</span>`;
}

function hostBlock(h, scopeEntries) {
  const key = h.key || '';
  const title = key === '(unattached)' ? 'General observations' : key;
  const inScope = scopeCovers(scopeEntries, h.ip || key);
  const svc = (h.services || []);
  const ports = svc.map(s => s.port).filter(Boolean);
  const tech = [...new Set(svc.flatMap(s => s.tech || []))];

  const svcRows = svc.map(s => `<tr>
      <td class="mono">${esc(s.port || '')}</td>
      <td class="mono">${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noreferrer">${esc(s.url)}</a>` : '—'}</td>
      <td>${s.status ? `<span class="chip">${esc(String(s.status))}</span>` : ''}
          ${esc(s.title || '')}</td>
      <td class="hint">${esc((s.tech || []).join(', '))}</td>
      <td class="num hint">${(s.endpoints || []).length || ''}</td></tr>`).join('');

  const paths = svc.flatMap(s => (s.endpoints || []).map(e => ({...e, base: s.url})));
  const pathRows = paths.slice(0, 80).map(e => `<tr>
      <td class="mono">${esc(e.url)}</td>
      <td class="num">${e.status_code ? `<span class="chip">${esc(String(e.status_code))}</span>` : ''}</td>
      <td class="hint">${esc(e.label || '')}</td></tr>`).join('');

  const loose = (h.loose_endpoints || []).slice(0, 40);
  const obs = (h.observations || []).map(o => `<div style="border-top:1px solid var(--line);padding:.45rem 0">
      <div class="row" style="gap:.4rem;align-items:baseline">
        ${confidenceChip(o)}
        <span style="flex:1">${esc(o.summary)}</span>
        <span class="hint mono">${esc(o.source || '')}${o.at_local ? ' · ' + esc(o.at_local) : ''}</span>
      </div>
      ${o.detail ? `<div class="muted" style="font-size:var(--fs-12);margin-top:.15rem">${esc(o.detail)}</div>` : ''}
    </div>`).join('');

  return `<div class="card" style="margin-bottom:.9rem">
    <div class="row" style="justify-content:space-between;align-items:baseline;flex-wrap:wrap">
      <div>
        <div style="font-weight:600;font-size:var(--fs-15)">${esc(title)}</div>
        <div class="hint">${h.ip && h.ip !== key ? 'address ' + esc(h.ip) + ' · ' : ''}
          ${ports.length ? 'ports ' + esc([...new Set(ports)].join(', ')) + ' · ' : ''}
          ${tech.length ? esc(tech.slice(0, 4).join(', ')) + ' · ' : ''}
          ${(h.observations || []).length} observation(s)</div>
      </div>
      <div class="row">
        ${inScope
          ? '<span class="chip" style="color:var(--ok);border-color:var(--ok)">in scope</span>'
          : `<span class="chip" style="color:var(--warn);border-color:var(--warn)">not in scope</span>
             <button class="sm pri" onclick="approveHost('${esc(h.ip || key).replace(/'/g, "&#39;")}')">Add to scope</button>`}
        <button class="sm ghost" onclick="S.artPath='enumeration/${esc(key)}/summary.md'; setTab('artifacts')">Files</button>
      </div>
    </div>

    ${svc.length ? `<div style="margin-top:.6rem">
      <div class="hint" style="text-transform:uppercase;letter-spacing:.05em;margin-bottom:.25rem">Services</div>
      <table><tr><th class="num">Port</th><th>URL</th><th>Status / title</th><th>Technologies</th><th class="num">Paths</th></tr>
        ${svcRows}</table></div>` : ''}

    ${pathRows ? `<div style="margin-top:.6rem">
      <div class="hint" style="text-transform:uppercase;letter-spacing:.05em;margin-bottom:.25rem">Paths</div>
      <table><tr><th>Path</th><th class="num">Status</th><th>Note</th></tr>${pathRows}</table></div>` : ''}

    ${loose.length ? `<div style="margin-top:.5rem"><div class="hint">other paths:
      ${loose.map(e => `<code>${esc(e.url)}</code>`).join(' ')}</div></div>` : ''}

    ${obs ? `<div style="margin-top:.6rem">
      <div class="hint" style="text-transform:uppercase;letter-spacing:.05em;margin-bottom:.25rem">Observations</div>
      ${obs}</div>` : ''}
  </div>`;
}

async function approveHost(host) {
  const j = await api('/api/scope/add', {task: S.task, kind: 'domain', value: host});
  if (j.error) { toast(j.error, 'err'); return; }
  toast('Added ' + host + ' to scope'); await refresh(true);
}

/* ---------- evidence ---------- */
function tabArtifacts(d) {
  const mode = S.artMode || 'files';
  const toolbar = `<div class="filters">
      <span class="chip ${mode === 'files' ? 'on' : ''}" style="cursor:pointer"
        onclick="S.artMode='files'; setTab('artifacts')">Files</span>
      <span class="chip ${mode === 'traffic' ? 'on' : ''}" style="cursor:pointer"
        onclick="S.artMode='traffic'; setTab('artifacts')">Traffic</span>
      <span style="flex:1"></span>
      <span class="hint mono" id="artRoot">${esc((S.artifacts || {}).root || (d.workdir || ''))}</span>
      <button class="sm ghost" onclick="loadArtifacts()">Refresh</button></div>`;
  if (mode === 'traffic') {
    return toolbar + `<div class="grid2">
      <div><h3 style="margin:0 0 .4rem;font-size:var(--fs-15)">Assets</h3>
        ${assetTable(d)}</div>
      <div><h3 style="margin:0 0 .4rem;font-size:var(--fs-15)">Recorded traffic</h3>
        <div class="row" style="margin-bottom:.4rem">
          <input id="trafficQ" placeholder="Search URL or body" value="${esc(S.trafficQ)}" style="flex:1"
            onkeydown="if(event.key==='Enter'){S.trafficQ=this.value;loadTraffic()}">
          <button class="sm" onclick="S.trafficQ=$('#trafficQ').value; loadTraffic()">Search</button>
        </div>
        <div id="trafficList"><div class="skel"></div></div>
        <div id="trafficDetail"></div></div></div>`;
  }
  const files = (S.artifacts || {}).tree || [];
  const tree = files.length ? files.map(f => {
    const depth = (f.path.split('/').length - 1);
    const name = f.path.split('/').pop();
    const sel = f.path === S.artPath;
    if (f.type === 'dir') {
      return `<div class="tnode dir" style="padding-left:${depth * 12}px">${esc(name)}/</div>`;
    }
    return `<div class="tnode ${sel ? 'on' : ''}" style="padding-left:${depth * 12}px"
      onclick="openArtifact('${esc(f.path).replace(/'/g, "&#39;")}')" title="${esc(f.path)}">
      ${esc(name)}<span class="sz">${fmtSize(f.size)}</span></div>`;
  }).join('') : `<div class="empty" style="margin:.5rem"><b>No files yet</b>
      They are written at the end of each round — start the engagement, or press Refresh.</div>`;
  return toolbar + `<div style="display:grid;grid-template-columns:330px 1fr;gap:.8rem;align-items:start">
    <div class="card" style="padding:.4rem;max-height:34rem;overflow:auto" id="artTree">${tree}</div>
    <div class="card" id="artView">${artifactViewer()}</div></div>`;
}

function assetTable(d) {
  const assets = (d.assets || []).filter(a => a.type === 'service' || a.type === 'endpoint');
  if (!assets.length) return '<div class="empty">No services or endpoints recorded.</div>';
  return `<table><tr><th>Type</th><th>Target</th><th class="num">Status</th></tr>
    ${assets.slice(0, 200).map(a => `<tr><td class="muted">${esc(a.type)}</td>
      <td class="mono">${esc(a.url || a.domain || a.ip || '')}</td>
      <td class="num">${a.status_code || ''}</td></tr>`).join('')}</table>`;
}

function artifactViewer() {
  if (!S.artPath) {
    return `<div class="empty"><b>Pick a file</b>The engagement folder is the source of truth:
      <code>enumeration/</code>, <code>findings/</code>, <code>poc/</code>, <code>evidence/</code>,
      <code>report/report.md</code>.</div>`;
  }
  const name = S.artPath.split('/').pop();
  const isMd = /\.md$/i.test(name);
  const isImg = /\.(png|jpe?g|gif|webp|svg)$/i.test(name);
  const body = isImg
    ? `<img src="/api/artifact?task=${S.task}&raw=1&path=${encodeURIComponent(S.artPath)}"
        style="max-width:100%;border-radius:8px" alt="${esc(name)}">`
    : isMd ? mdToHtml(S.artText || '') : `<pre class="code">${esc(S.artText || '')}</pre>`;
  return `<div class="row" style="justify-content:space-between;margin-bottom:.4rem">
      <div><b>${esc(name)}</b> <span class="hint mono">${esc(S.artPath)}</span></div>
      <div class="row"><span class="hint">${fmtSize((S.artText || '').length)}</span>
      <button class="sm ghost" onclick="copyArtifact()">Copy</button></div></div>
    ${body}`;
}

async function loadArtifacts() {
  if (!S.task) return;
  S.artifacts = await api('/api/artifacts?task=' + S.task);
  if (S.artMode && S.artMode !== 'files') { if (S.tab === 'artifacts') loadTraffic(); return; }
  if (S.tab !== 'artifacts') return;
  const pane = $('#pane'); if (!pane) return;
  pane.innerHTML = tabArtifacts(S.data);
  if (S.artPath) openArtifact(S.artPath, true);
}

async function openArtifact(path, quiet) {
  S.artPath = path;
  if (!quiet) { const pane = $('#pane'); if (pane) pane.innerHTML = tabArtifacts(S.data); }
  const j = await api('/api/artifact?task=' + S.task + '&path=' + encodeURIComponent(path));
  if (j.error) { toast(j.error, 'err'); return; }
  S.artText = j.binary ? '(binary file — open it from disk)' : (j.text || '');
  const view = $('#artView'); if (view) view.innerHTML = artifactViewer();
  document.querySelectorAll('#artTree .tnode').forEach(n => n.classList.remove('on'));
  const sel = [...document.querySelectorAll('#artTree .tnode')]
    .find(n => n.getAttribute('title') === path);
  if (sel) sel.classList.add('on');
}

async function copyArtifact() {
  try { await navigator.clipboard.writeText(S.artText || ''); toast('Copied'); }
  catch (e) { toast('Clipboard blocked by the browser', 'err'); }
}

function mdToHtml(src) {
  const codes = [];
  let out = esc(deesc(src || '')).replace(/```[a-z]*\n([\s\S]*?)```/g, (m, code) => {
    codes.push(`<pre class="code">${code}</pre>`);
    return `\u0001${codes.length - 1}\u0001`;
  });
  out = out
    .replace(/^### (.*)$/gm, '<div style="font-weight:600;margin:.7rem 0 .2rem">$1</div>')
    .replace(/^## (.*)$/gm, '<div style="font-weight:600;font-size:var(--fs-15);margin:.9rem 0 .25rem">$1</div>')
    .replace(/^# (.*)$/gm, '<div style="font-weight:600;font-size:var(--fs-15);margin:.2rem 0 .4rem">$1</div>')
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^- (.*)$/gm, '<div>• $1</div>')
    .replace(/^(\d+)\. (.*)$/gm, '<div>$1. $2</div>')
    .replace(/\n{2,}/g, '<div style="height:.5rem"></div>')
    .replace(/\n/g, '<br>');
  out = out.replace(/\u0001(\d+)\u0001/g, (m, i) => codes[+i] || '');
  return `<div class="md">${out}</div>`;
}

function fmtSize(n) {
  if (!n) return '';
  if (n < 1024) return n + ' B';
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
  return (n / 1048576).toFixed(1) + ' MB';
}

async function loadTraffic() {
  if (!S.task) return;
  const q = S.trafficQ || '';
  const j = await api('/api/traffic?task=' + S.task + (q ? '&q=' + encodeURIComponent(q) : ''));
  const rows = j.traffic || [];
  const el = $('#trafficList'); if (!el) return;
  el.innerHTML = rows.length ? `<table><tr><th class="num">#</th><th>Method</th><th>URL</th><th class="num">Status</th></tr>
      ${rows.slice(0, 80).map(t => `<tr style="cursor:pointer" onclick="readTraffic(${t.id})">
        <td class="num muted">${t.id}</td><td>${esc(t.method)}</td><td class="mono">${esc(t.url)}</td>
        <td class="num s-${t.status >= 400 ? 'failed' : 'done'}">${t.status}</td></tr>`).join('')}</table>
      <div class="hint">${rows.length} record(s)</div>`
    : '<div class="empty">No traffic recorded for this engagement.</div>';
  if (S.trafficId) readTraffic(S.trafficId);
}

async function readTraffic(id) {
  S.trafficId = id;
  const j = await api('/api/traffic_one?id=' + id);
  const el = $('#trafficDetail'); if (!el) return;
  if (j.error) { el.innerHTML = `<div class="empty">${esc(j.error)}</div>`; return; }
  el.innerHTML = `<div class="card" style="margin-top:.6rem">
    <div class="row"><b>${esc(j.method)}</b> <code>${esc(j.url)}</code>
      <span class="chip">${j.status}</span><span style="flex:1"></span>
      <button class="sm ghost" onclick="copyTraffic(${id})">Copy</button></div>
    <div class="grid2" style="margin-top:.5rem">
      <div><div class="hint">request headers</div><pre>${esc(hdr(j.req_headers))}</pre></div>
      <div><div class="hint">response headers</div><pre>${esc(hdr(j.resp_headers))}</pre></div>
    </div>
    <div class="hint">response body</div><pre>${esc((j.resp_body || '').slice(0, 20000))}</pre></div>`;
}

async function copyTraffic(id) {
  const j = await api('/api/traffic_one?id=' + id);
  const text = `${j.method} ${j.url}\n\n${JSON.stringify(j.req_headers || {}, null, 1)}\n\n` +
    `${j.status}\n${JSON.stringify(j.resp_headers || {}, null, 1)}\n\n${j.resp_body || ''}`;
  try { await navigator.clipboard.writeText(text); toast('Traffic #' + id + ' copied'); }
  catch (e) { toast('Clipboard blocked by the browser', 'err'); }
}

/* ---------- activity ---------- */
function tabActivity(d) {
  const all = d.activity || [];
  const workers = [...new Set(all.map(a => a.worker || ''))].filter(Boolean).sort();
  const kinds = [...new Set(all.map(a => a.kind || ''))].filter(Boolean).sort();
  let rows = all.slice();
  if (S.actWorker) rows = rows.filter(a => a.worker === S.actWorker);
  if (S.actKind) rows = rows.filter(a => a.kind === S.actKind);
  rows.reverse();
  return `<div class="filters">
      <select style="width:9rem" onchange="S.actWorker=this.value; setTab('activity')">
        <option value="">all workers</option>
        ${workers.map(w => `<option ${S.actWorker === w ? 'selected' : ''}>${esc(w)}</option>`).join('')}
      </select>
      <select style="width:9rem" onchange="S.actKind=this.value; setTab('activity')">
        <option value="">all kinds</option>
        ${kinds.map(k => `<option ${S.actKind === k ? 'selected' : ''}>${esc(k)}</option>`).join('')}
      </select>
      <span class="hint">${rows.length} events · local time (${esc(localZone())}) · Δ since previous event</span>
      <span style="flex:1"></span><button class="sm ghost" onclick="refresh(true)">Refresh</button></div>
    <table style="table-layout:fixed">
    <colgroup><col style="width:3.2rem"><col style="width:6.4rem"><col style="width:4.4rem">
      <col style="width:5rem"><col style="width:8rem"><col></colgroup>
    <tr><th class="num">#</th><th>Time</th><th>Δ</th><th>Worker</th><th>Kind</th><th>Detail</th></tr>
    ${rows.map(a => `<tr><td class="num muted">${a.id}</td>
      <td class="mono">${esc(a.at_local || '')}</td>
      <td class="mono muted">${a.delta_s == null ? '—' : fmtDur(a.delta_s)}</td>
      <td class="muted">${esc(a.worker || '')}</td><td class="muted">${esc(a.kind || '')}</td>
      <td title="${esc((a.summary || '').slice(0, 4000))}">${esc((a.summary || '').slice(0, 320))}
        ${(a.summary || '').length > 320 ? '…' : ''}</td></tr>`).join('')}</table>`;
}

/* ---------- graph ---------- */
async function loadGraph() {
  if (!S.task) return;
  S.graph = await api('/api/graph?task=' + S.task);
  if (S.tab !== 'graph') return;
  $('#pane').innerHTML = graphHtml(S.graph);
  graphApply();
}

function graphHtml(g) {
  if (!g || g.error) return `<div class="empty">${esc((g && g.error) || 'no data')}</div>`;
  const kinds = ['begin', 'goal', 'intent', 'fact', 'finding', 'hint'];
  let nodes = g.nodes || [];
  const allNodes = nodes.slice();
  if (S.graphKind) nodes = nodes.filter(n => n.kind === S.graphKind);
  const keep = new Set(nodes.map(n => n.id));
  const edges = (g.edges || []).filter(e => keep.has(e.src) && keep.has(e.dst));
  const level = {}; const kids = {};
  edges.forEach(e => (kids[e.src] = kids[e.src] || []).push(e.dst));
  const roots = nodes.filter(n => n.kind === 'begin' || !edges.some(e => e.dst === n.id));
  const q = roots.map(n => [n.id, 0]); roots.forEach(n => level[n.id] = 0);
  while (q.length) {
    const [id, lv] = q.shift();
    (kids[id] || []).forEach(k => { if (level[k] === undefined) { level[k] = lv + 1; q.push([k, lv + 1]); } });
  }
  nodes.forEach(n => { if (level[n.id] === undefined) level[n.id] = 0; });
  const cols = {}; nodes.forEach(n => (cols[level[n.id]] = cols[level[n.id]] || []).push(n));
  const W = 290, H = 78, GX = 76, GY = 16, PAD = 20;
  const maxLevel = Math.max(0, ...Object.keys(cols).map(Number));
  const height = PAD * 2 + Math.max(...Object.values(cols).map(c => c.length), 1) * (H + GY);
  const width = PAD * 2 + (maxLevel + 1) * (W + GX);
  const pos = {};
  Object.keys(cols).forEach(lv => cols[lv].forEach((n, i) => {
    pos[n.id] = {x: PAD + Number(lv) * (W + GX), y: PAD + i * (H + GY)};
  }));

  const css = getComputedStyle(document.documentElement);
  const v = (n, f) => (css.getPropertyValue(n) || f).trim();
  const surface = v('--surface', '#fff'), line = v('--line', '#ddd'), fg = v('--fg', '#222');
  const dim = v('--dim', '#777'), brand = v('--brand', '#7d2030');
  const ok = v('--ok', '#1c7a4d'), bad = v('--bad', '#b3261e'), warn = v('--warn', '#8a6a10');
  const active = !!(S.data && (S.data.running || S.data.approval));

  const stateColour = n => {
    if (n.kind === 'hint') return line;
    if (n.state === 'running') return active ? brand : dim;
    if (['done', 'met', 'achieved', 'confirmed'].includes(n.state)) return ok;
    if (['exhausted', 'stale'].includes(n.state)) return warn;
    if (['blocked', 'stopped', 'failed', 'abandoned'].includes(n.state)) return bad;
    return line;
  };
  const liveSet = new Set(nodes.filter(n => n.state === 'running' && active).map(n => n.id));

  let svg = `<svg viewBox="0 0 ${width} ${height}" id="gsvg" preserveAspectRatio="xMinYMin meet"
      style="width:100%;height:34rem;display:block;cursor:grab;touch-action:none"
      onwheel="graphWheel(event)" onmousedown="graphDown(event)"
      font-family="-apple-system,Segoe UI,Roboto,sans-serif">`;
  edges.forEach(e => {
    const a = pos[e.src], b = pos[e.dst]; if (!a || !b) return;
    const x1 = a.x + W, y1 = a.y + H / 2, x2 = b.x, y2 = b.y + H / 2, mx = (x1 + x2) / 2;
    const hot = liveSet.has(e.src) || liveSet.has(e.dst);
    svg += `<path class="${hot ? 'live-edge' : ''}" d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}"
      fill="none" stroke="${hot ? brand : line}" stroke-opacity="${hot ? 1 : .85}" stroke-width="${hot ? 1.9 : 1.4}"/>`;
  });
  nodes.forEach(n => {
    const p = pos[n.id];
    const border = stateColour(n);
    const sel = n.id === S.nodeSel;
    const live = liveSet.has(n.id);
    const label = (n.label || '').replace(/\s+/g, ' ').trim() || ('(' + n.kind + ')');
    const lines = [];
    let rest = label;
    const max = 42;
    while (rest && lines.length < 3) {
      if (rest.length <= max) { lines.push(rest); rest = ''; break; }
      let cut = rest.lastIndexOf(' ', max);
      if (cut < max * 0.55) cut = max;
      lines.push(rest.slice(0, cut).trim());
      rest = rest.slice(cut).trim();
    }
    if (rest && lines.length) {
      lines[lines.length - 1] = lines[lines.length - 1].replace(/\s*\S*$/, '') + '…';
    }
    const stateText = live ? 'running'
      : (n.state === 'running' ? 'stale' : (n.state && n.state !== 'open' ? n.state : ''));
    svg += `<g class="${live ? 'live-node' : ''}" style="cursor:pointer" onclick="showNode(${n.id})">
      <title>${esc(n.kind)} #${n.id} · ${esc(n.state || '')} — ${esc(label)}</title>
      <rect x="${p.x}" y="${p.y}" width="${W}" height="${H}" rx="7" fill="${surface}"
        stroke="${sel ? brand : border}" stroke-width="${sel ? 2.6 : (live ? 2.2 : 1.3)}"/>
      <rect x="${p.x}" y="${p.y}" width="4" height="${H}" rx="2" fill="${border}"/>
      <text x="${p.x + 12}" y="${p.y + 15}" fill="${dim}" font-size="11">${esc(n.kind)} #${n.id}${
        stateText ? ' · ' + esc(stateText) : ''}</text>
      <text x="${p.x + 12}" y="${p.y + 36}" fill="${fg}" font-size="12.5">${esc(lines[0] || '')}</text>
      <text x="${p.x + 12}" y="${p.y + 53}" fill="${fg}" font-size="12.5">${esc(lines[1] || '')}</text>
      <text x="${p.x + 12}" y="${p.y + 70}" fill="${fg}" font-size="12.5">${esc(lines[2] || '')}</text>
      ${live ? `<circle cx="${p.x + W - 12}" cy="${p.y + 12}" r="4" fill="${brand}">
        <animate attributeName="opacity" values="1;0.2;1" dur="1.4s" repeatCount="indefinite"/></circle>` : ''}
      </g>`;
  });
  svg += '</svg>';

  return `<div class="filters">
      ${kinds.map(k => `<span class="chip ${S.graphKind === k ? 'on' : ''}"
        onclick="S.graphKind='${S.graphKind === k ? '' : k}'; setTab('graph')">${k}</span>`).join('')}
      <span class="hint">${nodes.length}/${allNodes.length} nodes · ${edges.length} edges${
        liveSet.size ? ` · <b style="color:var(--brand)">${liveSet.size} running</b>` : ''}${
        active ? ' · live' : ''}</span>
      <span style="flex:1"></span>
      <button class="sm" onclick="graphZoom(-1)">−</button>
      <button class="sm" onclick="graphZoom(1)">+</button>
      <button class="sm" onclick="graphFit()">Fit</button>
      <button class="sm ghost" onclick="loadGraph()">Refresh</button></div>
    <div class="hint" style="margin:-.2rem 0 .5rem">legend:
      <span class="chip" style="border-color:var(--brand)">running</span>
      <span class="chip" style="border-color:var(--ok)">done / met</span>
      <span class="chip" style="border-color:var(--warn)">exhausted / stale</span>
      <span class="chip" style="border-color:var(--bad)">blocked / failed</span>
      <span class="chip">queued</span>
      · drag to pan, scroll to zoom${active ? '' : ' · nothing is running right now'}</div>
    <div id="graphwrap" style="overflow:hidden;border:1px solid var(--line);border-radius:10px;
      background:var(--surface)" data-w="${width}" data-h="${height}">${svg}</div>
    <div id="nodedetail" style="margin-top:.6rem">${S.nodeSel ? '' : '<p class="hint">Select a node for its payload.</p>'}</div>`;
}

let GDRAG = null;
function graphView() {
  if (!S.graphView) S.graphView = {k: 1, x: 0, y: 0};
  return S.graphView;
}
function graphApply() {
  const svg = $('#gsvg'); if (!svg) return;
  const wrap = $('#graphwrap');
  const W = Number(wrap.dataset.w), H = Number(wrap.dataset.h);
  const v = graphView();
  svg.setAttribute('viewBox', `${v.x} ${v.y} ${W / v.k} ${H / v.k}`);
}
function graphZoom(dir) {
  const v = graphView();
  v.k = Math.max(0.3, Math.min(4, v.k * (dir > 0 ? 1.25 : 0.8)));
  graphApply();
}
function graphFit() { S.graphView = {k: 1, x: 0, y: 0}; graphApply(); }
function graphWheel(ev) {
  ev.preventDefault();
  const v = graphView();
  const wrap = $('#graphwrap');
  const W = Number(wrap.dataset.w), H = Number(wrap.dataset.h);
  const rect = $('#gsvg').getBoundingClientRect();
  const fx = (ev.clientX - rect.left) / rect.width, fy = (ev.clientY - rect.top) / rect.height;
  const wx = v.x + fx * (W / v.k), wy = v.y + fy * (H / v.k);
  v.k = Math.max(0.3, Math.min(6, v.k * (ev.deltaY < 0 ? 1.15 : 0.87)));
  v.x = wx - fx * (W / v.k);
  v.y = wy - fy * (H / v.k);
  graphApply();
}
function graphDown(ev) {
  const v = graphView();
  GDRAG = {x: ev.clientX, y: ev.clientY, vx: v.x, vy: v.y};
  const svg = $('#gsvg'); svg.style.cursor = 'grabbing';
  const move = e => {
    if (!GDRAG) return;
    if (Math.abs(e.clientX - GDRAG.x) + Math.abs(e.clientY - GDRAG.y) > 4) window.__graphDragged = true;
    const wrap = $('#graphwrap');
    const W = Number(wrap.dataset.w);
    const rect = svg.getBoundingClientRect();
    const dvx = (e.clientX - GDRAG.x) * (W / v.k) / rect.width;
    const dvy = (e.clientY - GDRAG.y) * (W / v.k) / rect.width;
    v.x = GDRAG.vx - dvx; v.y = GDRAG.vy - dvy;
    graphApply();
  };
  const up = () => {
    GDRAG = null; svg.style.cursor = 'grab';
    window.removeEventListener('mousemove', move);
    window.removeEventListener('mouseup', up);
  };
  window.addEventListener('mousemove', move);
  window.addEventListener('mouseup', up);
}

async function showNode(id) {
  if (window.__graphDragged) { window.__graphDragged = false; return; }
  S.nodeSel = id;
  if (S.graph) $('#pane').innerHTML = graphHtml(S.graph);
  const j = await api('/api/node?id=' + id);
  const el = $('#nodedetail');
  if (el) el.innerHTML = j.error ? `<div class="empty">${esc(j.error)}</div>`
    : `<pre>${esc(JSON.stringify(j, null, 1))}</pre>`;
}

/* ---------- settings / skills ---------- */
async function loadSettings() {
  S.settings = await api('/api/settings');
  renderSettings();
}

function renderSettings() {
  const s = S.settings || {};
  const llm = s.llm || {}, run = s.run || {};
  $('#crumbs').innerHTML = '<span>Settings</span>';
  $('#main').innerHTML = `
    <div class="pagehead"><div><h2>Settings</h2>
      <div class="goal">Model endpoint, run defaults and pacing. Applies to every engagement.</div></div></div>
    <div class="grid2">
      <div class="card">
        <h3 style="margin:0 0 .3rem;font-size:var(--fs-15)">Model</h3>
        <label class="f"><span>Endpoint (OpenAI-compatible)</span><input id="sUrl" value="${esc(llm.base_url || '')}"></label>
        <label class="f"><span>Model</span><input id="sModel" value="${esc(llm.model || '')}"></label>
        <div class="row"><button class="sm" onclick="listModels()">List models</button>
          <span class="hint" id="sModelsHint"></span></div>
        <div id="sModels" class="hint" style="max-height:9rem;overflow:auto;margin-top:.3rem"></div>
        <label class="f"><span>API key — ${esc(llm.key_masked || 'unset')} via ${esc(llm.key_source || '—')}</span>
          <input id="sKey" type="password" placeholder="leave blank to keep the current key" autocomplete="off"></label>
        <div class="grid2">
          <label class="f"><span>Timeout (s)</span><input id="sTimeout" value="${esc(llm.timeout || 600)}"></label>
          <label class="f"><span>Max tokens (0 = default)</span><input id="sMaxTokens" value="${esc(llm.max_tokens || 0)}"></label>
        </div>
        <label class="f"><span>Temperature</span><input id="sTemp" value="${esc(llm.temperature || 0.2)}"></label>
      </div>
      <div class="card">
        <h3 style="margin:0 0 .3rem;font-size:var(--fs-15)">Run defaults</h3>
        <label class="f"><span>Requests per second per host</span><input id="sRps" value="${esc(run.rps || '2')}"></label>
        <label class="f"><span>Parallel workers</span><input id="sWorkers" value="${esc(run.max_workers || '2')}"></label>
        <label class="f"><span>Noise profile</span>
          <select id="sNoise">${['quiet', 'balanced', 'aggressive', 'off'].map(o =>
            `<option ${o === (run.noise_profile || 'balanced') ? 'selected' : ''}>${o}</option>`).join('')}</select></label>
        <div class="row" style="margin-top:.8rem">
          <button class="pri" onclick="saveSettings()">Save</button>
          <button onclick="testSettings()">Test connection</button></div>
        <div id="sMsg" class="hint" style="margin-top:.4rem"></div>
        <hr><div class="hint">The API key is stored in <code>~/.titan/secrets.json</code> (0600), never in the
          database. <code>TITAN_LLM_API_KEY</code> overrides it.</div>
      </div>
    </div>`;
}

async function listModels() {
  const url = $('#sUrl').value.trim(), key = $('#sKey').value.trim();
  $('#sModelsHint').textContent = 'probing…';
  const j = await api('/api/models?url=' + encodeURIComponent(url) + (key ? '&key=' + encodeURIComponent(key) : ''));
  if (j.error) { $('#sModelsHint').textContent = j.error; return; }
  S.models = j.models || [];
  $('#sModelsHint').textContent = S.models.length + ' available';
  $('#sModels').innerHTML = S.models.map(m =>
    `<div style="cursor:pointer" onclick="pickModel('${esc(m).replace(/'/g, "\\'")}')">${esc(m)}</div>`).join('');
}
function pickModel(m) { $('#sModel').value = m; }

async function saveSettings() {
  const body = {llm: {base_url: $('#sUrl').value.trim(), model: $('#sModel').value.trim(),
                      timeout: parseInt($('#sTimeout').value || '600', 10),
                      max_tokens: parseInt($('#sMaxTokens').value || '0', 10),
                      temperature: parseFloat($('#sTemp').value || '0.2')},
                run: {rps: $('#sRps').value.trim(), max_workers: $('#sWorkers').value.trim(),
                      noise_profile: $('#sNoise').value},
                api_key: $('#sKey').value.trim() || undefined};
  const j = await api('/api/settings', body);
  $('#sKey').value = '';
  if (j.error) { toast(j.error, 'err'); return; }
  S.settings = j; renderSettings(); toast('Settings saved');
}

async function testSettings() {
  $('#sMsg').textContent = 'Testing…';
  const j = await api('/api/settings/test', {base_url: $('#sUrl').value.trim(),
    model: $('#sModel').value.trim(), api_key: $('#sKey').value.trim() || undefined});
  $('#sMsg').innerHTML = j.error ? `<span class="s-failed">${esc(j.error)}</span>`
    : `<span class="s-done">Connected in ${j.latency_ms} ms — ${esc((j.reply || '').slice(0, 60))}</span>`;
}

async function loadSkills() {
  const j = await api('/api/skills');
  S.skills = j.skills || [];
  $('#crumbs').innerHTML = '<span>Skills</span>';
  $('#main').innerHTML = `<div class="pagehead"><div><h2>Skills</h2>
      <div class="goal">Procedural knowledge available to the workers. Loaded on demand by name.</div></div></div>
    <div class="grid2">
      <div class="card">${S.skills.map(s => `<div style="cursor:pointer;margin-bottom:.45rem"
          onclick="readSkill('${esc(s.name).replace(/'/g, "\\'")}')">
          <b>${esc(s.name)}</b><div class="hint">${esc(s.description || '')}</div></div>`).join('')}</div>
      <div class="card"><pre id="skillBody" class="hint">Select a skill.</pre></div>
    </div>`;
}

async function readSkill(name) {
  const j = await api('/api/skill?name=' + encodeURIComponent(name));
  $('#skillBody').textContent = j.body || j.error || '';
}

/* ---------- new engagement ---------- */
function showNew() {
  S.view = 'new'; S.task = 0; $('#menuHost').innerHTML = '';
  $('#crumbs').innerHTML = '<span>New engagement</span>'; $('#live').innerHTML = '';
  renderSidebar();
  $('#main').innerHTML = `
    <div class="pagehead"><div><h2>New engagement</h2>
      <div class="goal">One objective, an authorized scope and a directory for its artifacts.</div></div></div>
    <div class="card" style="max-width:56rem">
      <label class="f"><span>Goal — the end state you must prove</span>
        <textarea id="nGoal" placeholder="Find and prove the highest-impact unauthenticated entry point on app.example.com"></textarea></label>
      <label class="f"><span>Authorized targets — one per line, kind=value (domain, url, ip, cidr, keyword)</span>
        <textarea id="nScope" placeholder="domain=example.com"></textarea></label>
      <div class="grid2">
        <label class="f"><span>Title (optional)</span>
          <input id="nTitle" placeholder="Acme — external web assessment"></label>
        <label class="f"><span>Artifact directory (optional)</span>
          <input id="nWorkdir" placeholder="blank = ~/.titan/runs/tasks/&lt;id&gt;"></label>
      </div>
      <label class="f"><span>Autonomy</span>
        <select id="nMode">
          <option value="autonomous">Autonomous — until the goal is met or you stop it</option>
          <option value="approval">Approval — confirm before every round</option>
        </select></label>
      <div class="row" style="margin-top:.7rem">
        <button class="pri" onclick="createTask()" id="nCreate">Create engagement</button>
        <button class="ghost" onclick="cancelNew()">Cancel</button>
        <span id="nMsg" class="hint"></span></div>
    </div>`;
  $('#nGoal').focus();
}

function cancelNew() { if (S.tasks.length) selectTask(S.tasks[0].id); else goGlobal('settings'); }

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
  const j = await api('/api/task', {goal: goal, title: $('#nTitle').value.trim(), scope: scope,
                                    workdir: ($('#nWorkdir').value || '').trim(),
                                    mode: $('#nMode').value});
  if (j.error) {
    btn.disabled = false; btn.textContent = 'Create engagement';
    $('#nMsg').textContent = j.error; toast(j.error, 'err'); return;
  }
  await loadTasks(); toast('Engagement #' + j.task + ' created');
  await selectTask(j.task);
}

/* ---------- actions ---------- */
function taskMenu(id) {
  const host = $('#menuHost');
  host.innerHTML = `<div class="menu">
    <button onclick="renameTask()">Rename</button>
    <button onclick="reportPreview(); $('#menuHost').innerHTML=''">Report preview</button>
    <button onclick="exportMd(); $('#menuHost').innerHTML=''">Download markdown</button>
    <div class="sep"></div>
    <button class="danger" onclick="delTask(${id})">Delete engagement</button>
  </div>`;
  setTimeout(() => document.addEventListener('click', closeMenuOnce, {once: true}), 0);
}

async function setMode(mode) {
  const j = await api('/api/task/settings', {task: S.task, mode: mode});
  if (j.error) { toast(j.error, 'err'); return; }
  toast(mode === 'approval' ? 'Approval mode — confirm each round' : 'Autonomous mode');
  await refresh(true);
}

function bumpWorkers(delta) {
  const el = $('#rWorkers'); if (!el) return;
  el.value = Math.max(1, Math.min(8, (parseInt(el.value || '2', 10) || 2) + delta));
  applyWorkers();
}

async function applyWorkers() {
  const el = $('#rWorkers'); if (!el) return;
  const workers = Math.max(1, Math.min(8, parseInt(el.value || '2', 10) || 2));
  el.value = workers;
  const j = await api('/api/task/settings', {task: S.task, workers: workers});
  if (j.error) { toast(j.error, 'err'); return; }
  toast(workers + ' worker(s)' + (S.data && S.data.running ? ' — applied to the running engagement' : ''));
}

async function runTask() {
  const j = await api('/api/run', {task: S.task, workers: parseInt($('#rWorkers').value || '2', 10)});
  if (j.error) { toast(j.error, 'err'); return; }
  toast(S.data && S.data.mode === 'approval' ? 'Started — you will confirm each round' : 'Running');
  await refresh(true);
}

async function stopTask() {
  const j = await api('/api/stop', {task: S.task});
  if (j.error) { toast(j.error, 'err'); return; }
  toast('Stopping after the current step'); await refresh(true);
}

async function decide(decision) {
  const j = await api('/api/approve', {task: S.task, decision: decision});
  if (j.error) { toast(j.error, 'err'); return; }
  toast(decision === 'approve' ? 'Approved — continuing' : 'Denied — stopping');
  await refresh(true);
}

async function delTask(id) {
  const v = await modal({title: 'Delete engagement #' + id + '?',
    message: 'Removes goals, intents, facts, findings and recorded traffic. Artifacts on disk are left alone.',
    ok: 'Delete permanently', danger: true});
  $('#menuHost').innerHTML = '';
  if (!v) return;
  const j = await api('/api/task/delete', {task: id});
  if (j.error) { toast(j.error, 'err'); return; }
  toast('Engagement #' + id + ' deleted');
  if (SEEN) delete SEEN[id];
  if (S.task === id) { S.task = 0; S.data = null; }
  await loadTasks();
  if (S.tasks.length) await selectTask(S.tasks[0].id); else showEmpty();
}

async function renameTask() {
  $('#menuHost').innerHTML = '';
  const cur = S.data ? (S.data.task.title || '') : '';
  const v = await modal({title: 'Rename engagement', ok: 'Save',
    fields: [{id: 'title', label: 'Title', value: cur}]});
  if (!v) return;
  const j = await api('/api/task/rename', {task: S.task, title: v.title});
  if (j.error) { toast(j.error, 'err'); return; }
  toast('Renamed'); await loadTasks(); await refresh(true);
}

async function addScope() {
  const kind = $('#scopeKind').value, value = ($('#scopeValue').value || '').trim();
  if (!value) return;
  const j = await api('/api/scope', {task: S.task, kind: kind, value: value});
  if (j.error) { toast(j.error, 'err'); return; }
  $('#scopeValue').value = '';
  toast('Scope added'); await refresh(true);
}

async function addHint() {
  const text = $('#hintText').value.trim(); if (!text) return;
  const j = await api('/api/hint', {task: S.task, text: text});
  if (j.error) { toast(j.error, 'err'); return; }
  $('#hintText').value = ''; toast('Hint queued'); await refresh(true);
}

async function steer(id) {
  const v = await modal({title: 'Steer intent #' + id,
    message: 'The worker reads this before its next step; it keeps its intent.',
    fields: [{id: 'msg', label: 'Course correction', type: 'textarea',
              placeholder: 'e.g. stop path brute force, go deeper on /exhibitor/v1/state'}],
    ok: 'Send to worker'});
  if (!v || !v.msg) return;
  const j = await api('/api/steer', {task: S.task, intent: id, message: v.msg});
  if (j.error) toast(j.error, 'err'); else toast('Sent to worker #' + id);
}

async function kill(id) {
  const v = await modal({title: 'Stop intent #' + id + '?',
    message: 'The worker finishes the current step, writes back what it has, then stops.',
    ok: 'Stop intent', danger: true});
  if (!v) return;
  const j = await api('/api/kill', {task: S.task, intent: id, reason: 'operator'});
  if (j.error) toast(j.error, 'err'); else toast('Intent #' + id + ' stopping');
}

async function setFinding(id, status) {
  if (S.data) {
    const f = (S.data.findings || []).find(x => x.id === id);
    if (f) f.status = status;              // optimistic
  }
  setTab('findings');
  const j = await api('/api/finding', {id: id, status: status});
  if (j.error) { toast(j.error, 'err'); await refresh(true); return; }
  toast('Finding #' + id + ' → ' + shortStatus(status)); await refresh(true);
}

function exportMd() { window.location = '/api/export?task=' + S.task; }

/* ---------- helpers ---------- */
function deesc(s) {
  const str = String(s || '');
  if (str.includes('\n')) return str;          // real newlines already
  return str.replace(/\\n/g, '\n').replace(/\\t/g, '\t');
}

function hdr(v) {
  if (v === null || v === undefined) return '';
  if (typeof v === 'string') {
    try { return JSON.stringify(JSON.parse(v), null, 1); } catch (e) { return v; }
  }
  return JSON.stringify(v, null, 1);
}

function fmtDur(sec) {
  if (sec === null || sec === undefined) return '';
  if (sec < 60) return sec + 's';
  if (sec < 3600) return Math.floor(sec / 60) + 'm ' + String(sec % 60).padStart(2, '0') + 's';
  return Math.floor(sec / 3600) + 'h ' + String(Math.floor((sec % 3600) / 60)).padStart(2, '0') + 'm';
}
function pathOf(url) {
  try { return new URL(url, location.origin).pathname || '/'; } catch (e) { return url; }
}
function timeAgo(iso) {
  if (!iso) return '';
  const t = Date.parse(iso); if (isNaN(t)) return iso;
  const s = Math.max(0, Math.round((Date.now() - t) / 1000));
  if (s < 60) return s + 's ago';
  if (s < 3600) return Math.round(s / 60) + 'm ago';
  if (s < 86400) return Math.round(s / 3600) + 'h ago';
  return Math.round(s / 86400) + 'd ago';
}
function localZone() {
  try { return Intl.DateTimeFormat().resolvedOptions().timeZone + ' ' +
    new Date().toLocaleTimeString('en-GB', {timeZoneName: 'short'}).split(' ').pop(); }
  catch (e) { return 'local'; }
}

/* ---------- boot ---------- */
async function tick() {
  if (document.hidden) return;
  await loadTasks();
  if (S.view === 'task' && S.task) { await refresh(false); await loadLive(); }
}
setInterval(tick, 3000);

loadTasks().then(() => { if (S.tasks.length) selectTask(S.tasks[0].id); else goGlobal('settings'); });
</script></body></html>
"""
