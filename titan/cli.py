"""Dewaguard Titan command line."""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from .agents import GOALS_PROMPT
from .config import VERSION, Settings, key_source, load_api_key, mask, save_api_key
from .engine import Engine
from .llm import LLM, MockLLM, Reply, list_models
from .skills import SkillIndex
from .store import Store, jloads


def _settings(args) -> Settings:
    s = Settings()
    if getattr(args, "model", None):
        s.model = args.model
    if getattr(args, "base_url", None):
        s.base_url = args.base_url
    if getattr(args, "home", None):
        s.home = Path(args.home).expanduser()
        s.db_path = s.home / "titan.db"
        s.workdir = s.home / "runs"
    s.ensure_dirs()
    return s


def _engine(args, llm=None) -> Engine:
    s = _settings(args)
    store = Store(s.db_path)
    skills = SkillIndex(s.skill_dir)
    return Engine(s, store=store, llm=llm, skills=skills,
                  interactive=getattr(args, "interactive", False))


def _need(engine: Engine, task_id: int):
    if not engine.store.get_task(task_id):
        raise SystemExit(f"no such task: {task_id}")
    return engine.store.get_task(task_id)


# ------------------------------------------------------------------ commands
def cmd_init(args) -> int:
    s = _settings(args)
    Store(s.db_path)
    sk = SkillIndex(s.skill_dir)
    store = Store(s.db_path)
    sk.register(store)
    print(f"Dewaguard Titan {VERSION}")
    print(f"  state     {s.home}")
    print(f"  database  {s.db_path}")
    print(f"  runs      {s.workdir}")
    print(f"  skills    {s.skill_dir} ({len(sk.skills)} loaded)")
    print(f"  console   http://{s.console_bind}:{s.console_port}")
    print(f"  LLM       {s.model or '(unset: set TITAN_LLM_MODEL)'} @ {s.base_url}")
    return 0


def cmd_doctor(args) -> int:
    s = _settings(args)
    ok = True
    print(f"titan {VERSION}")
    print(f"python           {sys.version.split()[0]}")
    for label, p in (("state dir", s.home), ("db", s.db_path), ("runs", s.workdir),
                     ("skills", s.skill_dir)):
        print(f"{label:<16} {p} {'ok' if p.exists() else 'MISSING'}")
        ok &= p.exists()
    sk = SkillIndex(s.skill_dir)
    print(f"skills loaded    {len(sk.skills)}: {', '.join(sorted(sk.skills))}")
    if not sk.skills:
        ok = False

    store = Store(s.db_path)
    cfg = store.settings()
    base = cfg.get("llm.base_url") or s.base_url
    model = cfg.get("llm.model") or s.model
    key = load_api_key(s)
    print(f"model            {model or '(unset - run: titan setup)'}")
    print(f"endpoint         {base}")
    print(f"api key          {mask(key)} via {key_source(s)}")
    if s.api_key and cfg.get("llm.base_url"):
        print("note             env TITAN_LLM_API_KEY overrides any key saved by setup")
    if model:
        try:
            t0 = time.time()
            LLM(base, model, key, timeout=20).chat(
                [{"role": "user", "content": "reply with: ok"}], max_tokens=8)
            print(f"llm probe        ok ({(time.time() - t0) * 1000:.0f} ms)")
        except Exception as e:  # noqa: BLE001
            print(f"llm probe        FAILED: {e}")
            ok = False
    else:
        print("llm probe        skipped (no model configured)")
    print("status           " + ("ready" if ok else "incomplete"))
    return 0 if ok else 1


# ------------------------------------------------------------------ setup wizard
def _ask(label: str, default: str = "", secret: bool = False, allow_empty: bool = False) -> str:
    hint = f" [{default}]" if default else ""
    while True:
        try:
            if secret:
                import getpass
                val = getpass.getpass(f"{label}{hint}: ")
            else:
                val = input(f"{label}{hint}: ")
        except EOFError:
            val = ""
        val = (val or "").strip()
        if not val and default:
            return default
        if val or allow_empty:
            return val
        print("  a value is required (Ctrl-C to abort)")


def _list_models(base: str, key: str, timeout: int = 15) -> list[str]:
    return list_models(base, key, timeout)


def cmd_setup(args) -> int:
    s = _settings(args)
    store = Store(s.db_path)
    cfg = store.settings()
    base = cfg.get("llm.base_url") or s.base_url
    model = cfg.get("llm.model") or s.model
    key = load_api_key(s)

    if args.show:
        print(f"endpoint   {base}")
        print(f"model      {model or '(unset)'}")
        print(f"api key    {mask(key)} via {key_source(s)}")
        for k in ("llm.timeout", "llm.max_tokens", "llm.temperature", "run.rps",
                  "run.max_workers", "run.noise_profile"):
            if cfg.get(k):
                print(f"{k:<18} {cfg[k]}")
        return 0

    interactive = not args.url and sys.stdin.isatty()
    print(f"Dewaguard Titan {VERSION} - model setup")
    print("Press Enter to keep the value shown in brackets.\n")

    if args.url:
        base = args.url
    elif interactive:
        base = _ask("base URL (OpenAI-compatible, e.g. http://127.0.0.1:11434/v1)", base)
    while not base.startswith(("http://", "https://")):
        if not interactive:
            print("ERROR: --url must start with http:// or https://", file=sys.stderr)
            return 2
        base = _ask("base URL must start with http:// or https://", base)

    print(f"\napi key: {mask(key)} via {key_source(s)}")
    if getattr(args, "api_key_stdin", False):
        key = sys.stdin.readline().strip()
    elif args.api_key is not None:
        key = args.api_key
    elif interactive:
        entered = _ask("api key (hidden; blank keeps the current one)", "", secret=True,
                       allow_empty=True)
        if entered:
            key = entered

    models: list[str] = []
    if not args.no_probe:
        try:
            models = _list_models(base, key)
            print(f"\nendpoint reachable, {len(models)} model(s) available")
        except Exception as e:  # noqa: BLE001
            print(f"\ncould not list models ({type(e).__name__}: {e}) - continuing anyway")

    if args.model:
        model = args.model
    elif interactive:
        if models:
            for i, m in enumerate(models[:30], 1):
                print(f"  {i:>2}. {m}")
            choice = _ask("model (number or id)", model or (models[0] if models else ""))
            if choice.isdigit() and 1 <= int(choice) <= min(len(models), 30):
                model = models[int(choice) - 1]
            else:
                model = choice
        else:
            model = _ask("model id", model)

    timeout = args.timeout or int(cfg.get("llm.timeout") or s.request_timeout)
    max_tokens = args.max_tokens if args.max_tokens is not None else int(cfg.get("llm.max_tokens") or 0)
    temperature = args.temperature if args.temperature is not None else float(
        cfg.get("llm.temperature") or s.temperature)
    if interactive and not args.url:
        adv = _ask("advanced settings (timeout/max_tokens/temperature)? [y/N]", "N")
        if adv.lower().startswith("y"):
            timeout = int(_ask("request timeout seconds", str(timeout)))
            max_tokens = int(_ask("max tokens (0 = endpoint default)", str(max_tokens)))
            temperature = float(_ask("temperature", str(temperature)))
            rps = _ask("requests per second per host", cfg.get("run.rps") or str(s.rps))
            workers = _ask("parallel workers", cfg.get("run.max_workers") or str(s.max_workers))
            noise = _ask("noise profile (quiet/balanced/aggressive/off)",
                         cfg.get("run.noise_profile") or s.noise_profile)
            store.set_setting("run.rps", rps)
            store.set_setting("run.max_workers", workers)
            store.set_setting("run.noise_profile", noise)

    store.set_setting("llm.base_url", base)
    store.set_setting("llm.model", model)
    store.set_setting("llm.timeout", str(timeout))
    store.set_setting("llm.max_tokens", str(max_tokens))
    store.set_setting("llm.temperature", str(temperature))
    key_file = save_api_key(s, key) if key else None

    print("\nsaved:")
    print(f"  endpoint   {base}")
    print(f"  model      {model}")
    print(f"  settings   {s.db_path} (no secrets)")
    print(f"  api key    {mask(key)} -> {key_file} (0600)" if key_file
          else "  api key    (unset - only works for unauthenticated endpoints)")
    if s.api_key:
        print("  warning    TITAN_LLM_API_KEY is set in the environment and takes precedence")

    if args.no_test:
        return 0
    print("\ntesting a real completion...")
    try:
        t0 = time.time()
        reply = LLM(base, model, key, min(timeout, 60), 32, temperature).chat(
            [{"role": "system", "content": "Answer with one word."},
             {"role": "user", "content": "Say exactly: ok"}])
        ms = (time.time() - t0) * 1000
        print(f"  ok in {ms:.0f} ms: {reply.content.strip()[:80] or '(empty content)'}")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"  FAILED: {e}")
        print("  the settings are saved; fix the endpoint/key and run 'titan setup' again")
        return 1

def cmd_new(args) -> int:
    eng = _engine(args)
    scope = []
    for raw in args.scope or []:
        if "=" not in raw:
            raise SystemExit(f"--scope expects kind=value, got {raw!r}")
        k, v = raw.split("=", 1)
        scope.append({"kind": k.strip(), "value": v.strip()})
    if not scope:
        print("warning: no --scope given; every target will be refused by the guard")
    tid = eng.new_task(args.goal, args.title or "", args.desc or "", scope,
                       getattr(args, "workdir", "") or "",
                       "approval" if getattr(args, "approval", False) else "autonomous")
    print(f"task #{tid} created")
    for g in eng.store.goals(tid):
        print(f"  goal {g['id']}: {g['text']}")
    return 0


def cmd_run(args) -> int:
    eng = _engine(args)
    task = _need(eng, args.task)
    mode = "approval" if getattr(args, "approval", False) else (task["mode"] or "autonomous")
    if mode == "approval" and sys.stdin.isatty() and not getattr(args, "no_prompt", False):
        eng.approver = lambda tid, s: _ask(f"proceed with the next round? ({s[:120]}) [Y/n]",
                                           "Y").lower().startswith("y")
    res = eng.run_task(args.task, rounds=args.rounds, workers=args.workers, mode=mode)
    print_summary(res)
    return 0


def print_summary(res: dict) -> None:
    print("\n" + "-" * 60)
    print(f"task #{res['task_id']}  status={res['status']}  rounds={res['rounds']}")
    print(f"coverage {res['coverage']['pct']}% ({res['coverage']['tested']}/{res['coverage']['assets']})"
          f"  findings={res['findings']}  facts={res['facts']}  tokens={res['usage']['tokens_in']}+"
          f"{res['usage']['tokens_out']}")
    for g in res["goals"]:
        print(f"  [{g['state']:<9}] {g['text']}")


def cmd_status(args) -> int:
    eng = _engine(args)
    _need(eng, args.task)
    ov = eng.store.graph_overview(args.task)
    print(f"task #{ov['task_id']}  {ov['title']}")
    print(f"goal      {ov['goal']}")
    print(f"status    {ov['status']}   round {ov['round']}")
    print(f"assets    {ov['assets']}")
    print(f"coverage  {ov['coverage']['pct']}% ({ov['coverage']['tested']}/{ov['coverage']['assets']})"
          f"  facts {ov['facts_total']}  findings {ov['findings_total']}")
    print("goals:")
    for g in ov["goals"]:
        print(f"  [{g['state']:<9}] {g['id']}  {g['text']}")
    print("open intents:")
    for i in ov["open_intents"] + ov["running_intents"]:
        print(f"  [{i['state']:<7}] {i['id']}  {i['summary']}")
    print("recent facts:")
    for f in ov["recent_facts"]:
        print(f"  {f['id']:>4}  ({f.get('confidence')}/{f.get('source')}) {f['summary'][:120]}")
    for f in eng.store.findings(args.task):
        print(f"FINDING {f['id']} [{f['severity']}] {f['vulnclass']} @ {f['endpoint']} "
              f"— {f['summary'][:100]}")
    return 0


def cmd_graph(args) -> int:
    eng = _engine(args)
    _need(eng, args.task)
    ov = eng.store.graph_overview(args.task)
    print(json.dumps(ov, indent=1, ensure_ascii=False))
    return 0


def cmd_findings(args) -> int:
    eng = _engine(args)
    _need(eng, args.task)
    fs = eng.store.findings(args.task)
    if not fs:
        print("no findings")
        return 0
    for f in fs:
        print(f"#{f['id']}  {f['severity'].upper():<8} {f['vulnclass']}  ({f['proof_basis']})")
        print(f"   {f['summary']}")
        print(f"   endpoint {f['endpoint'] or '-'}  param {f['parameter'] or '-'}  "
              f"status {f['status']}  traffic {f['traffic_refs']}")
        if f.get("evidence"):
            print("   evidence: " + f["evidence"].strip().replace("\n", "\n             ")[:1200])
        print()
    return 0


def cmd_assets(args) -> int:
    eng = _engine(args)
    _need(eng, args.task)
    rows = eng.store.assets(args.task, limit=args.limit)
    for a in rows:
        key = a["url"] or a["domain"] or a["ip"] or a["app_name"] or ""
        print(f"{a['id']:>4}  {a['type']:<11} {key[:80]:<80} "
              f"{a['status_code'] or ''} {' '.join(a['technologies'][:6])}")
    print(f"({len(rows)} assets)")
    return 0


def cmd_skills(args) -> int:
    s = _settings(args)
    sk = SkillIndex(s.skill_dir)
    if args.read:
        print(sk.read(args.read))
        return 0
    for name, skill in sorted(sk.skills.items()):
        print(f"{name:<24} {skill.description[:110]}")
    print(f"\n{len(sk.skills)} skills from {s.skill_dir}")
    return 0


def cmd_tasks(args) -> int:
    eng = _engine(args)
    for t in eng.store.list_tasks(args.limit):
        print(f"{t['id']:>4}  {t['status']:<9} {t['round_no']:>3}r  {t['title'][:60]}")
    return 0


def cmd_ask(args) -> int:
    eng = _engine(args)
    _need(eng, args.task)
    print(eng.chat(args.task, args.message))
    return 0


def cmd_export(args) -> int:
    eng = _engine(args)
    t = _need(eng, args.task)
    ov = eng.store.graph_overview(args.task)
    out = Path(args.out) if args.out else Path(f"titan-task-{args.task}.md")
    L = [f"# Engagement report — task #{args.task}", "", f"**Goal:** {t['goal']}", "",
         f"**Status:** {t['status']} · **Coverage:** {ov['coverage']['pct']}% "
         f"({ov['coverage']['tested']}/{ov['coverage']['assets']}) · "
         f"**Findings:** {ov['findings_total']}", "", "## Goals", ""]
    L += [f"- [{g['state']}] {g['text']}" for g in ov["goals"]]
    L += ["", "## Findings", ""]
    for f in eng.store.findings(args.task):
        L += [f"### {f['vulnclass']} — {f['severity'].upper()}", "",
              f"- Endpoint: `{f['endpoint'] or '-'}`  Parameter: `{f['parameter'] or '-'}`",
              f"- Proof basis: {f['proof_basis']} · Confidence: {f['confidence']} · "
              f"Status: {f['status']}", "", f["summary"], "", "**Evidence**", "", "```",
              (f["evidence"] or "").strip(), "```", ""]
        if f.get("poc"):
            L += ["**PoC**", "", "```", f["poc"].strip(), "```", ""]
        if f.get("counterevidence"):
            L += [f"*Counter-evidence tested:* {f['counterevidence']}", ""]
    L += ["", "## Exploration facts", ""]
    for f in eng.store.list_facts(args.task, limit=200):
        L.append(f"- {f['summary']} *({f.get('confidence')}/{f.get('source')})*")
    out.write_text("\n".join(L) + "\n")
    print(f"wrote {out} ({len(L)} lines)")
    return 0


def cmd_approve(args) -> int:
    eng = _engine(args)
    t = _need(eng, args.task)
    if not eng.store.pending_approval(args.task):
        print(f"task {args.task} is not waiting for approval (status {t['status']})")
        return 1
    eng.store.decide_approval(args.task, "deny" if args.deny else "approve", "cli")
    print(("denied" if args.deny else "approved") + f" task {args.task}")
    return 0


def cmd_serve(args) -> int:
    from .server import serve
    s = _settings(args)
    return serve(s, args.task or 0)


# ------------------------------------------------------------------ demo
def demo_script() -> list:
    """A scripted cycle so the machinery can be exercised without an LLM."""
    def tc(i, name, args):
        return {"id": f"c{i}", "name": name, "arguments": json.dumps(args)}
    return [
        # goals decomposer
        Reply(content=json.dumps({"goals": ["Demonstrate the dual-graph loop on the local lab"],
                                  "constraints": []})),
        # planner round 1
        Reply(content="", tool_calls=[tc(1, "add_intent", {
            "intents": [{"summary": "Enumerate the local demo service on http://127.0.0.1:PORT and "
                                    "record what it exposes"}]})]),
        Reply(content="dispatched one intent"),
        # worker
        Reply(content="", tool_calls=[tc(2, "insert_assets", {"items": [
            {"type": "service", "url": "http://127.0.0.1:PORT", "service_type": "http",
             "status_code": 200, "page_title": "demo", "technologies": ["python-http"]}]})]),
        Reply(content="", tool_calls=[tc(3, "record_fact", {
            "summary": "Demo service answers 200 with a directory listing",
            "detail": "GET / returns 200 and an index listing; no auth.",
            "source": "target_response", "confidence": "observed",
            "evidence": "curl -i http://127.0.0.1:PORT -> HTTP/1.0 200"})]),
        Reply(content="Intent complete: one service asset and one fact recorded."),
        # planner round 2
        Reply(content="", tool_calls=[tc(4, "prove_goal", {
            "goal_id": 0, "evidence_id": 0, "reason": "demo cycle complete"})]),
        Reply(content="goal met"),
    ]


def cmd_demo(args) -> int:
    s = _settings(args)
    s.noise_profile = "off"
    store = Store(s.db_path)
    sk = SkillIndex(s.skill_dir)
    eng = Engine(s, store=store, llm=MockLLM([]), skills=sk)
    tid = store.create_task("Demonstrate the dual-graph loop", "demo")
    store.add_asset(tid, {"type": "service", "url": "http://127.0.0.1:8080", "service_type": "http",
                          "status_code": 200, "page_title": "demo"})
    store.add_fact(tid, "demo fact", source="target_response", confidence="observed")
    print(f"demo task #{tid} seeded (assets/facts/goals=1). "
          f"Inspect with: titan status {tid}")
    print("Full scripted cycle: python3 tests/test_cycle.py")
    return 0


# ------------------------------------------------------------------ parser
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="titan", description="Dewaguard Titan — autonomous, "
                                                         "graph-driven pentest harness")
    p.add_argument("--home", help="state directory (default ~/.titan)")
    p.add_argument("--model", help="LLM model id")
    p.add_argument("--base-url", help="OpenAI-compatible base URL")
    p.add_argument("-v", "--version", action="version", version=f"Dewaguard Titan {VERSION}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create state dirs, database and skill index").set_defaults(fn=cmd_init)
    sub.add_parser("doctor", help="verify the install").set_defaults(fn=cmd_doctor)

    su = sub.add_parser("setup", help="configure the model endpoint and key (interactive)")
    su.add_argument("--url", help="OpenAI-compatible base URL (skips the prompt)")
    su.add_argument("--model", help="model id (skips the prompt)")
    su.add_argument("--api-key", dest="api_key", default=None,
                    help="API key; omit to keep the stored one (leaks into shell history)")
    su.add_argument("--api-key-stdin", action="store_true",
                    help="read the API key from stdin (no shell history)")
    su.add_argument("--timeout", type=int)
    su.add_argument("--max-tokens", dest="max_tokens", type=int)
    su.add_argument("--temperature", type=float)
    su.add_argument("--no-probe", action="store_true", help="do not list models")
    su.add_argument("--no-test", action="store_true", help="do not send a test completion")
    su.add_argument("--show", action="store_true", help="print the current config and exit")
    su.set_defaults(fn=cmd_setup)

    n = sub.add_parser("new", help="create a task from a goal")
    n.add_argument("goal")
    n.add_argument("--title", default="")
    n.add_argument("--desc", default="")
    n.add_argument("--scope", action="append", metavar="KIND=VALUE",
                   help="authorized target: domain=, ip=, cidr=, url=, keyword=")
    n.add_argument("--approval", action="store_true",
                   help="create the engagement in approval mode (confirm each round)")
    n.add_argument("--workdir", default="",
                   help="directory for this engagement's artifacts (default under ~/.titan/runs)")
    n.set_defaults(fn=cmd_new)

    r = sub.add_parser("run", help="run the orchestrator on a task")
    r.add_argument("task", type=int)
    r.add_argument("--rounds", type=int,
                   help="hard cap on rounds (default: run until done or stopped)")
    r.add_argument("--approval", action="store_true",
                   help="pause before each round for a yes/no confirmation")
    r.add_argument("--no-prompt", action="store_true", help="with --approval, wait for "
                   "`titan approve <task>` instead of prompting")
    r.add_argument("--workers", type=int)
    r.add_argument("--interactive", action="store_true", help="answer ask_operator prompts on stdin")
    r.set_defaults(fn=cmd_run)

    st = sub.add_parser("status", help="task overview")
    st.add_argument("task", type=int)
    st.set_defaults(fn=cmd_status)

    g = sub.add_parser("graph", help="dump the exploration graph as JSON")
    g.add_argument("task", type=int)
    g.set_defaults(fn=cmd_graph)

    f = sub.add_parser("findings", help="list findings")
    f.add_argument("task", type=int)
    f.set_defaults(fn=cmd_findings)

    a = sub.add_parser("assets", help="list assets")
    a.add_argument("task", type=int)
    a.add_argument("--limit", type=int, default=60)
    a.set_defaults(fn=cmd_assets)

    sk = sub.add_parser("skills", help="list or read skills")
    sk.add_argument("--read", default="")
    sk.set_defaults(fn=cmd_skills)

    t = sub.add_parser("tasks", help="list tasks")
    t.add_argument("--limit", type=int, default=30)
    t.set_defaults(fn=cmd_tasks)

    ask = sub.add_parser("ask", help="talk to the main agent about a task")
    ask.add_argument("task", type=int)
    ask.add_argument("message")
    ask.set_defaults(fn=cmd_ask)

    ex = sub.add_parser("export", help="write a markdown report")
    ex.add_argument("task", type=int)
    ex.add_argument("--out", default="")
    ex.set_defaults(fn=cmd_export)

    sv = sub.add_parser("serve", help="web GUI + JSON API (localhost)")
    sv.add_argument("--task", type=int, default=0)
    sv.set_defaults(fn=cmd_serve)

    ap = sub.add_parser("approve", help="approve the next round of a paused engagement")
    ap.add_argument("task", type=int)
    ap.add_argument("--deny", action="store_true")
    ap.set_defaults(fn=cmd_approve)

    sub.add_parser("demo", help="seed a demo task (no LLM needed)").set_defaults(fn=cmd_demo)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
