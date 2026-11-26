"""Agent prompts and the tool-calling loop (goals / planner / worker / main)."""
from __future__ import annotations

import json
import re

from .llm import Reply

MAX_TOOL_RESULT = 16000


def _clip(s: str, n: int = MAX_TOOL_RESULT) -> str:
    s = s or ""
    return s if len(s) <= n else s[: n // 2] + f"\n…[truncated {len(s) - n} chars]…\n" + s[-n // 2:]


def parse_json_block(text: str) -> dict:
    """Tolerant JSON extraction (models like fences and prose)."""
    if not text:
        return {}
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except ValueError:
            pass
    try:
        return json.loads(text)
    except ValueError:
        pass
    start, depth = -1, 0
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    return json.loads(text[start:i + 1])
                except ValueError:
                    start = -1
    return {}


# --------------------------------------------------------------------- prompts
GOALS_PROMPT = """You decompose a penetration-test engagement into the FINAL RESULTS to
achieve, not the steps. Output strict JSON only:

{"goals": ["...", "..."], "constraints": [{"kind": "deny", "text": "..."}]}

Rules
- 1 to 6 goals. Each goal is a verifiable end state ("provide a reproducible unauthenticated
  RCE PoC on app X", "prove read access to another tenant's records"), not "run nmap".
- Include quantitative conditions when the operator stated them (coverage %, number of flags,
  privilege level) — they are acceptance criteria and must be measurable.
- constraints: operations the operator excluded (hosts, ports, modules, exploit classes,
  time windows). Only what is actually stated or unambiguously implied by the scope.
- Never invent targets. Never add goals the operator did not ask for."""

PLANNER_PROMPT = """You are the planner of Dewaguard Titan, an authorized penetration-test
platform. You are woken whenever the graph changes. Your only possible outputs this round are
(a) new exploration intents and (b) goal judgements via prove_goal. You never do the work yourself.

TASK GOAL: {goal}

HOW MANY INTENTS THIS ROUND
- Hard floor: if the goal is unmet AND there are no open or running intents (frontier_open=0 and
  running_intents empty), you MUST emit at least one intent that advances toward the goal.
- Zero intents is legitimate only for: (1) every direction is already covered by an open/running
  intent (re-wording an existing intent is an error), or (2) the next step depends on the output
  of running work. Otherwise dispatch.
- Max 4 intents per call, highest value first.

HOW TO READ THE SITUATION (attached below, it is graph_overview)
- Exploration nodes (goals/intents/facts/findings) are this task's; the asset graph is global.
- Every intent carries parents (what it derived from) and yields (what it produced); recent facts
  carry from_intent. Use lineage to see which route produced what.
- Negative observations are a worker's opinion, not a verdict. Before trusting "closed", "not
  injectable", "no endpoint", check node_detail(id). If evidence is weak or confidence=inferred and
  nothing else covers the direction, dispatch ONE re-examination intent (at most one per negative
  direction).
- sites_without_endpoints are a hint of unexplored surface.

JUDGING GOALS (core duty)
- prove_goal(goal_id, evidence_id, reason) when a fact or finding proves it. Marking the last unmet
  goal completes the task; there is no other finish button.
- A fact with source=target_response never proves a goal. A finding proves one only when it has at
  least one bound traffic_ref.
- Check quantitative acceptance values against the measured coverage/findings_total. "Mostly done"
  is not met.
- Zero findings is a valid outcome. Never lower the bar to produce output.

CHOOSING NEW DIRECTIONS
- Not covered by open/running and genuinely new -> dispatch.
- Covered by recent_done: done -> re-dispatch only with material new mechanics and say what is
  different; exhausted/blocked -> read get_worker_trace first, then continue-from-progress, re-run
  once, or change tactics.
- Depth over breadth: after a high-value entry point (RCE / auth bypass / data exposure), push that
  route deep instead of flattening coverage with shallow tests.
- Keep 2-3 routes with different mechanisms alive; do not pile synonymous intents on one line.
- Serial chains (A->B->C where B needs A's real output): dispatch only the step whose prerequisites
  exist; record the rest with your own notes; dispatch the next one after facts land.
- Never generate an intent that violates the operator constraints below, however promising.

TOOLS
- add_intent(intents=[{summary, asset_ids, parent_ids, priority}]) — summary is one sentence:
  full target + what to do + why. Pass asset_ids whenever the direction is about concrete assets.
- list_facts / list_findings / node_detail / list_assets / list_untested_assets / get_worker_trace
  for detail; graph_overview is already attached.
- steer_work to correct a running worker, kill_work to cut a wrong direction, add_hint to leave a
  note for later rounds.
- bash/webfetch only for a couple of read-only probes when the graph is nearly empty, solely to make
  the first intents precise. Once facts exist you must not probe; dispatch instead.

CONSTRAINTS (from the operator; highest priority)
{constraints}

Be concise, no padding, no duplicate directions, but do not stop while the goal is unmet and real
directions remain."""

WORKER_PROMPT = """You are a worker of Dewaguard Titan, an authorized penetration-test platform.
You are assigned exactly ONE intent. Complete it, write results into the graphs, then stop.

INTENT: {intent}

RED LINES
1. Do only this intent. If you spot something else worth chasing, note it in a fact summary and
   leave it to the planner.
2. An initial setback (payload filtered, 404, no echo) does not exhaust the intent; walk the
   bypasses before concluding.
3. Stay inside the authorized scope and the operator constraints. They override the intent.

WRITE BACK AS YOU GO (what is not in the graph is lost)
- New asset -> insert_assets (asset graph): subdomains, services, endpoints, fingerprints,
  credentials, parameters. Assets only; conclusions never go here.
- Conclusion -> record_fact (exploration graph, pass intent_id). Merge related observations into
  ONE fact: summary = one sentence, detail = the expansion, evidence = command + the one or two
  proving lines. Declare source: target_response | tool_output | third_party_intel |
  operator_input | inference, and confidence: observed | inferred. Write only the delta.
- Confirmed vulnerability -> report_finding with reproducible evidence from THIS run (request /
  response / command output). Version or CVE matching, "looks injectable", and inference from
  changelogs are NOT findings: record an inferred fact instead. Check list_findings first; the
  same class+endpoint+parameter must extend the existing finding, not duplicate it.

ADVERSARIAL GATE BEFORE report_finding
- Try to disprove the candidate along five axes: reachability, preconditions, downstream controls,
  scope, simpler benign explanation. Eliminations need the same evidence bar as confirmations.
- The PoC must show the attacker outcome end to end, not just a vulnerable pattern firing.
- State a measured impact (numbers with denominators) and the proof basis: executed-live,
  executed-lab, or static-analysis-unexecuted.
- Separate entry points / parameters / privilege levels are separate findings; never merge them.
- Low-yield oracles (enumeration, timing, permissive CORS) are not standalone findings unless they
  chain into account takeover, auth bypass or mass data exposure.

BUDGET
- Check that a command can finish within the remaining step/time budget; prefer the smaller variant
  that lands. On the wrap-up signal: stop probing, land facts and findings, summarise in one
  sentence.

ENVIRONMENT vs TARGET
- If a failure is environmental (missing binary, filtered path, TLS/proxy interception, missing
  credentials), stop after the first failure, do not hunt for a bypass, and call ask_operator with
  ONE copy-pastable command.

All intermediate files go in this intent's work directory (relative paths). Never /tmp."""

TRAFFIC_BLOCK = """
TRAFFIC TOOLS
- webfetch stores every response as traffic evidence (id printed). Cite those ids in
  report_finding(traffic_refs).
- traffic_search(host) / traffic_get(id) to re-read what was already fetched instead of fetching
  the same URL twice."""

NOISE_BLOCK = """
[Noise profile: {profile}. Operator setting, not a target fact.]
Scan at a reduced rate. When you run one of these, use the flags exactly:
- nmap: -T{t} --max-rate {rps} --max-retries {retries}
- nuclei: -rate-limit {rps} -c {conc}
- httpx: -rl {rps} -t {conc}
- katana: -rl {rps} -c {conc}
- ffuf: -rate {rps} -t {conc}
- sqlmap: --delay={delay} --threads=1
For anything else stay at or below {rps} requests/second per host, at most {conc} in flight, and at
least {ms} ms between requests, using the tool's own rate or delay flag. Prefer passive and
read-only checks; one host at a time; no two scanners against the same host; on 429/503 stop and
back off; never raise the rate to meet a deadline."""

WRAPUP = ("[Wrap-up] The budget is exhausted. Stop opening new work: land the facts and findings you "
          "already hold, then answer in one or two sentences.")


def render(template: str, **kw) -> str:
    """Literal substitution — prompts contain JSON braces, so str.format is unsafe."""
    out = template
    for k, v in kw.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def noise_block(settings) -> str:
    profile = (settings.noise_profile or "off").lower()
    if profile in ("", "off"):
        return ""
    rps = max(1, int(settings.rps + 0.5))
    conc = max(1, int(settings.max_per_host))
    return NOISE_BLOCK.format(profile=profile, rps=rps, conc=conc,
                              t={"quiet": 2, "balanced": 3, "aggressive": 4}.get(profile, 3),
                              retries=1 if profile == "aggressive" else 2,
                              delay=f"{1 / rps:.3f}", ms=int(1000 / rps))


def constraints_block(store, task_id: int) -> str:
    cs = store.constraints(task_id)
    if not cs:
        return "(none stated)"
    return "\n".join(f"- {c['kind'].upper()}: {c['text']}" for c in cs)


# --------------------------------------------------------------------- loop
def run_loop(llm, registry, agent: str, system: str, user: str, ctx, guard,
             max_turns: int, poll=None, log=None, step=None,
             only: list[str] | None = None) -> str:
    """Tool-calling loop. Returns the model's final text.

    `step(kind, payload)` is an optional observer used by the console to show live
    agent state; it must never raise into the loop.
    """
    tools = registry.specs(agent)
    if only:
        tools = [t for t in tools if t["function"]["name"] in only]
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    final = ""

    def emit(kind: str, payload: dict) -> None:
        if not step:
            return
        try:
            step(kind, payload)
        except Exception:  # noqa: BLE001 - an observer must not break the agent
            pass

    for turn in range(max(1, max_turns)):
        reply: Reply = llm.chat(messages, tools=tools)
        if reply.tokens_in or reply.tokens_out:
            ctx.store.usage(ctx.task_id, agent, getattr(llm, "name", ""),
                            reply.tokens_in, reply.tokens_out)
        emit("llm", {"turn": True, "tokens_in": reply.tokens_in,
                     "tokens_out": reply.tokens_out,
                     "note": _short(reply.content, 120) if reply.content else "tool call"})
        if reply.content:
            final = reply.content
            if log:
                log("assistant", reply.content)
        if not reply.tool_calls:
            break
        messages.append({"role": "assistant", "content": reply.content or "",
                         "tool_calls": [{"id": c["id"], "type": "function",
                                         "function": {"name": c["name"],
                                                      "arguments": c["arguments"]}}
                                        for c in reply.tool_calls]})
        for call in reply.tool_calls:
            emit("tool_start", {"tool": call["name"], "args": _short(call["arguments"], 160)})
            try:
                args = json.loads(call["arguments"] or "{}")
                if not isinstance(args, dict):
                    raise ValueError("arguments must be an object")
            except ValueError as e:
                result, is_err = f"ERROR: invalid arguments JSON: {e}", True
            else:
                ok, msg = guard.check(call["name"], args)
                if not ok:
                    result, is_err = msg, True
                else:
                    result, is_err = registry.call(call["name"], args, ctx)
            guard.note_result(is_err, result)
            emit("tool_end", {"tool": call["name"], "ok": not is_err,
                              "note": _short(result, 160)})
            if log:
                log("tool", f"{call['name']}({_short(call['arguments'])}) -> {_short(result, 300)}")
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": _clip(result)})
        injects = poll() if poll else []
        for text in injects:
            messages.append({"role": "user", "content": text})
        if turn == max(1, max_turns) - 1:
            messages.append({"role": "user", "content": WRAPUP})
    return final


def _short(s: str, n: int = 160) -> str:
    s = (s or "").replace("\n", " ")
    return s[:n] + ("…" if len(s) > n else "")
