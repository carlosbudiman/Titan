# Architecture

## 1. Data model

One SQLite file (`~/.titan/titan.db`, WAL). Threads share it; writes are serialised
by a lock, reads are cheap.

### Graph 1 — assets (global)

```
assets(id, type, ukey, domain, root_domain, ip, port, url, service_type,
       service_name, status_code, content_length, page_title, technologies[],
       params[], auth[], extra{}, task_ids[], first_seen, last_seen)
UNIQUE(type, ukey)
```

`ukey` is the natural key per type — this is what makes the graph idempotent when
five workers see the same endpoint:

| type | ukey |
|---|---|
| root_domain | domain |
| ip | ip |
| subdomain | domain + record_type |
| app | bundle_id or app_name |
| service (http) | url |
| service (other) | domain/ip + port + service_name |
| endpoint | url + method |

Upsert merges: technologies and params union, `task_ids` union, non-null scalar
fields overwrite. Assets are *shared*: two tasks that touch the same host see one
row, and each is recorded in `task_ids`.

### Graph 2 — exploration (per task)

```
explorations(id, title, goal, description, status, round_no)
exploration_nodes(id, exploration_id, kind, payload{}, priority, state, origin,
                  owner, blocked_reason, claim_token, heartbeat_at,
                  content_version, created_at, updated_at, completed_at)
exploration_edges(exploration_id, src_id, dst_id, rel)
exploration_anchors(node_id, asset_id)
task_constraints(task_id, kind{allow|deny}, text)
task_coverage(task_id, asset_id, tested_at)
```

Node kinds and legal states:

| kind | states | payload |
|---|---|---|
| begin | open | goal + initial scope |
| goal | open / met / abandoned | text, reason, evidence_id |
| intent | open / running / paused / done / blocked / exhausted / stopped / deleted | summary, asset_ids |
| fact | confirmed / dismissed / origin | summary, detail, source, confidence, evidence |
| finding | confirmed / dismissed | summary, vulnclass, severity, evidence, poc, traffic_refs |
| hint | active / consumed | text |
| digest | active / superseded | (reserved; folding is not implemented) |

Edge relations: `spawns` (parent → intent), `yields` (intent → fact/finding),
`proves` (fact/finding → goal), `derived_from` (alternative lineage), `covers`
(reserved for digests).

Why a separate `findings` table as well as finding nodes: nodes are the reasoning
object the planner reads; the table is the reportable object (severity, endpoint,
parameter, status, traffic refs, dedupe key).

## 2. Lifecycle

### Task creation

1. `explorations` row + `begin` node.
2. **goals** agent: one LLM call, strict JSON → 1–6 goals and operator
   constraints. Failure is non-fatal: the raw goal becomes the goal.
3. Scope rows are written to `task_scope`; the guard reads them, never the prompt.

### Planning round

1. `graph_overview(task)` assembles: goal, assets by type, goals+states,
   open/running intents, last 12 finished intents, recent 12 facts with
   source/confidence/from_intent, findings total, coverage %, hints, constraints.
2. If `frontier_open == 0` and nothing is running, the lead text says the task has
   stalled and demands ≥1 new intent.
3. Planner runs with its tool subset, max `TITAN_PLANNER_TURNS` tool turns. Its only
   legal mutations are `add_intent` (≤4, deduped against open+running+recently
   finished summaries, default parent = first goal) and `prove_goal`.
4. Engine safety net: if a round ends with zero intents and zero pending work, a
   stall counter increments; at 3 consecutive stalls the task is marked `failed`
   rather than looping forever. Before that, a low-priority intent is injected so the
   run cannot deadlock on a lazy model.

### Worker lifecycle

1. `claim_intent`: `BEGIN IMMEDIATE`; select the highest-priority `open` intent, or a
   `running` one whose heartbeat is older than `TITAN_INTENT_LEASE`; set
   `state=running`, fresh `claim_token`, stamp heartbeat.
2. Worker prompt: intent summary + operator constraints + noise profile + assets
   already anchored to the intent + skill index + its work directory.
3. Tool loop (`TITAN_WORKER_TURNS`). Between turns the loop drains the steer inbox
   and checks the kill flag, so `steer_work`/`kill_work` land mid-run.
4. Finalisation:
   - killed → `stopped`
   - exception → `blocked` with the error in `blocked_reason`
   - `yields` count unchanged since claim → `exhausted` ("no fact or finding written
     back")
   - otherwise → `done`, and every anchored asset is written to `task_coverage`
5. `insert_assets` and `report_finding` auto-anchor the running intent to the asset,
   which is how coverage is earned without the model managing anchors.

### Completion

`prove_goal` validates the evidence (see README), marks the goal `met`, adds a
`proves` edge, and if every goal is met sets the task to `achieved`. The engine also
re-checks after each round.

## 3. Guard

Order of evaluation for every tool call, before the handler runs:

1. **Built-in denies** (`guard.BUILTIN_DENY`): disk writes, `rm -rf /`, fork bomb,
   `curl | sh`, host power state, reading local credential stores, and anything in
   `TITAN_DENY_RULES`.
2. **Operator constraints**: literal substring match against the command, from
   `task_constraints` (extracted by the goals agent, editable via SQL/CLI additions).
3. **Scope**: every URL host, IPv4 and bare DNS name in the command must resolve into
   `task_scope` (domain suffix match, CIDR containment). Loopback is allowed for
   labs. File tools must resolve inside the work directory.
4. **Allow** → audit row, handler runs.

A block message is prefixed `[Titan platform control, not target defence]` so the
model does not read its own policy as a WAF and start "bypassing" it.

Post-call, results are attributed `blocked` / `error` / `ok`, which is what makes
"the target blocked me" distinguishable from "my command was wrong".

## 4. Context economy

- Graph overview is assembled live, capped (12 recent facts, 12 finished intents).
- Tool output is clipped at 16k chars in the loop, 20k in handlers; artifacts go to
  the per-intent work dir and the model reads back only what it needs.
- Skills are progressive: descriptions only, full text on `read_skill`.
- Prompts are built per call, so budget/turn changes take effect immediately.

## 5. Deliberate omissions and why

| ARTEX feature | Titan decision |
|---|---|
| PostgreSQL + migrations + 60 tables | SQLite, 14 tables. Single box, one file to back up. |
| Next.js console, auth, users, CSRF | single-page localhost console + JSON API, token-gated off-localhost. |
| Cold-node digests, compaction daemons, NOA | not implemented; overview caps suffice at this scale. |
| LLM fallback judge on every tool call | replaced by deterministic deny regexes + scope; fewer tokens, predictable. |
| MCP host, custom tool builder, traffic rewrite/tamper, browser MCP | out of scope; `bash` + `webfetch` cover the same ground. |
| Task archives, templates, categories, rotation | single-operator tool. |
| Postgres-backed multi-process workers | threads + claim lease; same crash-safety property. |

## 6. Extension points

- New tool: add a function to `titan/tools.py`, register it in `Registry._build`, add
  the name to `AGENT_TOOLS`.
- New agent role: new prompt constant in `agents.py`, tool subset in
  `AGENT_TOOLS`, and a method on `Engine`.
- New node kind/edge rel: extend the schema doc and `NODE_STATES`; SQLite has no
  CHECK on kinds, so no migration is required.
- Provider-specific quirks (tool-call parsing, no-tools models): `titan/llm.py`.

## 7. Console

`titan/server.py` serves one HTML document and a JSON API from the same process as
the engine. The engine is instantiated once; `/api/run` starts `run_task` on a
daemon thread and refuses a second concurrent run of the same task (409). `/api/stop`
sets the engine's per-task stop flag, which the round loop and the worker poll
check, so a stop lands between rounds or inside a running intent.

Endpoints: `GET /`, `/api/tasks`, `/api/state?task=N`, `/api/export?task=N`;
`POST /api/task`, `/api/run`, `/api/stop`, `/api/hint`, `/api/steer`, `/api/kill`.

Auth: loopback-only by default. If `TITAN_CONSOLE_BIND` is not a loopback address the
process refuses to start without `TITAN_CONSOLE_TOKEN`, and then requires
`X-Titan-Token` on every request. There is no CSRF token: the API is JSON-only and
the console is not meant to be exposed.
