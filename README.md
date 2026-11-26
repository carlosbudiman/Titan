# Dewaguard Titan

A lightweight, self-hosted **autonomous penetration-test harness** built around the
idea that made ARTEX effective — a **dual graph** (what exists, and what you have
reasoned about) driven by a **planner / worker / guard** loop — without the
PostgreSQL server, the Docker stack, the web IDE, the MCP orchestration or the
~100k lines of Go.

Python 3.10+, standard library only, one SQLite file. Installs in one command, runs
on the box you already work on.

```
titan new "Find a reproducible unauthenticated RCE on app.example.com" --scope domain=example.com
titan run 1
titan status 1
```

Authorized testing only. See [Safety](#safety) and `docs/ioc.md` before pointing it
at anything.

---

## What it is

Three agent roles over two graphs, all persisted in SQLite:

| Role | Job | Tools |
|------|-----|-------|
| **goals** | turn the engagement request into 1–6 verifiable goals + operator constraints | none (JSON out) |
| **planner** | read the graph on every wake, judge goals, dispatch 0–4 non-duplicate intents | `add_intent`, `prove_goal`, `steer_work`, `kill_work`, `node_detail`, `list_*`, `bash`/`webfetch` for at most a couple of read-only probes |
| **worker** | own exactly one intent, run real tools, write facts/findings/assets back, stop | `bash`, `webfetch`, file tools, `insert_assets`, `record_fact`, `report_finding`, `traffic_*`, `read_skill` |

A **guard** sits in front of every tool call: built-in deny rules for
irreversible/hostile actions, operator constraints extracted from the goal, and a
hard scope check on every host in every command. Every decision is audited.

### The two graphs

**Graph 1 — assets (global, shared across tasks)**
`root_domain · ip · subdomain · app · service · endpoint`
Only things that *exist*. Deduplicated by type + natural key.

**Graph 2 — exploration (per task)**
Nodes: `begin · goal · intent · fact · finding · hint · digest`
Edges: `spawns · derived_from · yields · proves · covers`
Nodes anchor to assets (`exploration_anchors`), which is what produces coverage.

Why two graphs: assets outlive the engagement and are reused; reasoning is scoped
to one goal and gets thrown away. Mixing them is what turns pentest notes into an
unqueryable swamp.

### The loop

```
            ┌──────────── graph change (worker done, finding, hint) ────────────┐
            ▼                                                                  │
   planner round ──► add_intent (≤4) ──► claim (lease+heartbeat) ──► worker ────┘
            │                                                          │
            └── prove_goal(last unmet goal) ──► task achieved           └─ assets/facts/findings
```

- The planner is woken on every graph change and on stall. **Hard floor**: goal
  unmet + zero open/running intents ⇒ it must emit at least one intent.
- Intents are claimed atomically with a lease; a crashed worker's claim expires and
  the intent is retaken. Kill the process mid-run and `titan run` continues.
- A worker that writes back nothing is marked `exhausted`, not `done`, so the
  planner sees the difference between "tested, negative" and "never ran".
- Completion comes only from `prove_goal` on each goal. No "finish" button, no
  self-declared victory.

### Evidence discipline (inherited deliberately)

- `report_finding` refuses an empty evidence field, refuses `confidence=inferred`
  as a confirmed finding, refuses a duplicate `class+endpoint+parameter`, and
  refuses non-existent traffic refs. Version/CVE matching is not a finding.
- `prove_goal` refuses a `target_response` fact (the target can plant it), a
  finding labelled `false_positive/duplicate/ignored`, and a finding with no bound
  traffic. Facts must be `tool_output` or an executed finding.
- `webfetch` records request/response as traffic rows, so findings cite real
  evidence ids.
- Every asset also carries `technologies/params/extra`, so state stays structured.

## What is included from ARTEX, and what is not

Included (behavioural parity where it matters):

- dual-graph model, node kinds, edge rels, anchors, coverage ledger
- planner wake-on-change, hard floor, no-duplicate rule, serial-chain discipline,
  depth-over-breadth, negative-result re-examination (once)
- worker one-intent rule, write-back-as-you-go, source/confidence taxonomy,
  adversarial gate, measured-impact requirement
- goal judgement with quantitative acceptance checks
- guard: built-in denies, operator constraints, target scope, audit, failure
  attribution (blocked/error/ok)
- skills folder **copied verbatim** from ARTEX (`skills/`), progressive disclosure
  (name+description in prompt, full body via `read_skill`), `references/` and
  `scripts/` shipped alongside
- noise profile → concrete scanner rate flags in the prompt
- traffic capture + evidence binding
- hint / steer / kill, activity trail, token accounting, markdown export,
  read-only console

Dropped on purpose (this is the "lightweight" part):

- Docker, PostgreSQL, `pgx`, migrations, background compaction daemons
- Next.js web IDE, auth, multi-user, task archives, templates, LLM profile CRUD,
  Bedrock/Anthropic gateways, LLM judge, MCP host, custom tool builder, browser
  automation server, intercept UI, digests/cold-node folding
- Redis-less horizontal scale (one process, N threads; SQLite is the blackboard)

## Install (no Docker, no server, no pip packages)

```bash
cd ~/Dewaguard/Titan
./install.sh
```

That checks Python ≥ 3.10, links `~/.local/bin/titan`, creates `~/.titan/`, seeds
the skill index and runs `titan doctor`.

Manual equivalent:

```bash
chmod +x bin/titan
ln -sf "$PWD/bin/titan" ~/.local/bin/titan
./bin/titan init
```

Optional editable install (only if you want `import titan` elsewhere):

```bash
python3 -m pip install --user -e .
```

## Configure a model

Any OpenAI-compatible `/chat/completions` endpoint: Ollama, vLLM, LM Studio,
llama.cpp server, DeepSeek, OpenRouter, an internal gateway.

```bash
export TITAN_LLM_BASE_URL=http://127.0.0.1:11434/v1
export TITAN_LLM_MODEL=qwen2.5:14b
# or
export TITAN_LLM_BASE_URL=https://api.deepseek.com/v1
export TITAN_LLM_MODEL=deepseek-chat
export TITAN_LLM_API_KEY=...
```

Put these in `~/.titan/env` and `source` it, or export them in your shell rc.

### All settings

| Variable | Default | Meaning |
|---|---|---|
| `TITAN_HOME` | `~/.titan` | state dir (db, runs) |
| `TITAN_DB` | `$TITAN_HOME/titan.db` | SQLite file |
| `TITAN_WORKDIR` | `$TITAN_HOME/runs` | per-task / per-intent work dirs |
| `TITAN_SKILL_DIR` | `<repo>/skills` | skill root |
| `TITAN_LLM_BASE_URL` | `http://127.0.0.1:11434/v1` | OpenAI-compatible base |
| `TITAN_LLM_MODEL` | *(empty)* | model id |
| `TITAN_LLM_API_KEY` | `$OPENAI_API_KEY` | bearer token |
| `TITAN_LLM_TIMEOUT` | `600` | per-request seconds |
| `TITAN_LLM_MAX_TOKENS` | `0` | 0 = endpoint default |
| `TITAN_MAX_WORKERS` | `2` | parallel intents |
| `TITAN_PLANNER_TURNS` | `12` | planner tool turns per round |
| `TITAN_WORKER_TURNS` | `40` | worker tool turns per intent |
| `TITAN_MAX_ROUNDS` | `200` | hard stop |
| `TITAN_TASK_DEADLINE` | `0` | seconds, 0 = none |
| `TITAN_INTENT_LEASE` | `900` | claim expiry |
| `TITAN_RPS` | `2.0` | per-host request rate |
| `TITAN_MAX_PER_HOST` | `1` | in-flight per host |
| `TITAN_NOISE_PROFILE` | `balanced` | `quiet` \| `balanced` \| `aggressive` \| `off` |
| `TITAN_USER_AGENT` | `Titan-Assessment/0.2.0` | outbound UA |
| `TITAN_CONSOLE_PORT` | `9911` | read-only console (localhost) |
| `TITAN_CONSOLE_BIND` | `127.0.0.1` | console bind address |
| `TITAN_ALLOW_SHELL` | `1` | `0` disables `bash`/`webfetch` scope checks — do not |
| `TITAN_DENY_RULES` | *(empty)* | file of extra deny regexes, one per line |

## Usage

```bash
titan init                     # create state, seed skills
titan doctor                   # verify install + model reachability
titan new "GOAL" --title "client" --desc "context" \
      --scope domain=example.com --scope cidr=10.0.0.0/24
titan run 1 --rounds 20 --workers 3
titan status 1                 # graph summary, one screen
titan graph 1                  # full overview as JSON
titan findings 1               # findings with evidence and traffic refs
titan assets 1
titan ask 1 "any auth bypass candidate yet?"
titan export 1 --out report.md
titan serve                    # read-only console on 127.0.0.1:9911
titan skills --read php2shell
```

`--scope` accepts `domain=`, `ip=`, `cidr=`, `url=`, `keyword=`. **No scope ⇒ every
targeted command is refused** (this is intentional: an unscoped run is an
unauthorized run).

Run directories: `~/.titan/runs/tasks/<task>/main` for the planner, `.../i<intent>`
for a worker. Artifacts stay there, never in `/tmp`.

## Skills

`skills/` is ARTEX's skill folder **copied unchanged** (11 skills):
`api-recon`, `api-security`, `bbot-recon`, `codeaudit`, `edr-bypass-re`,
`patch-diff`, `php2shell`, `playwright-cli`, `rea`, `scopesentry`,
`third-party-code-review`.

They load by progressive disclosure: the system prompt carries only
`name: description`, and the model calls `read_skill(name)` to pull the body plus
the list of bundled `scripts/` and `references/` files.

Add a skill by dropping a directory in `skills/` with a `SKILL.md`:

```markdown
---
name: my-skill
description: Use when ... (this line is what the planner/worker sees)
---
# body
```

`titan init` (or any `titan` command) re-indexes the folder. Skills that reference
`sessions`/MCP servers (`rea`, `scopesentry`, `playwright-cli`) describe the
external service they expect — the SKILL.md text is intact, the MCP wiring is not
part of Titan; use the bundled scripts, or call the service with `bash`/`webfetch`.

## Layout

```
bin/titan              launcher (works without install)
titan/config.py        settings, identity, OPSEC defaults
titan/store.py         SQLite schema + both graphs, coverage, traffic, audit
titan/tools.py         tool catalog: specs + handlers
titan/agents.py        prompts, prompt assembly, tool-calling loop
titan/engine.py        orchestrator: goals → planner rounds → workers → judgement
titan/guard.py         deny rules, scope, pacing, audit, failure attribution
titan/skills.py        SKILL.md index + on-demand load
titan/server.py        read-only console (localhost)
titan/cli.py           command line
skills/                ARTEX skills, verbatim
docs/architecture.md   data model, lifecycle, design notes
docs/ioc.md            how Titan differs from ARTEX on the wire
tests/test_cycle.py    orchestrator proof: graphs, guard, evidence gates
tests/test_cli.py      CLI + real HTTP provider + SQLite persistence + console
```

## Tests

```bash
make test          # 9 tests, ~7 s, no model, no internet
```

or individually:

```bash
python3 tests/test_cycle.py      # planner -> worker -> facts -> finding -> prove_goal
python3 tests/test_cli.py        # CLI end-to-end against a fake OpenAI-compatible endpoint
```

`test_cycle` runs a real local HTTP server as target and a scripted provider and
asserts: planner dispatch → worker assets/fact/finding → traffic evidence → coverage
100% → `prove_goal` → `achieved`; plus guard scope/deny/constraint blocks, the
`target_response` proof refusal, finding dedupe, and the inferred-candidate refusal.
`test_cli` additionally proves the urllib transport, tool-call parsing, cross-process
SQLite persistence, markdown export and the read-only console.

## Limitations

- Single process. N worker threads; SQLite serialises writes, so past ~6 workers the
  bottleneck is the lock, not the network.
- No digests/compaction: very long engagements rely on the 12-fact / 12-intent
  overview window. Backfill with `list_facts(limit=…)` if you need more.
- No built-in browser automation, MCP host, or traffic rewriting. `bash` can run
  whatever you install; the skills that reference an MCP server (rea, scopesentry,
  playwright-cli) ship their instructions, not the server.
- The model must support OpenAI-style function calling. Models that only emit JSON
  in content will not drive the loop.

## Safety

- Use only on systems you are authorized to test. `--scope` is the authorization
  record; the guard is enforcement, not a substitute for a signed scope.
- Built-in denies block irreversible host actions (disk writes, `rm -rf /`, fork
  bombs, piping downloads to a shell, reading local credential stores).
- Non-destructive is not the same as read-only: `report_finding`'s prompt requires
  proving on your own objects first and touching at most three non-owned objects
  with the smallest demonstrating request.
- The console is read-only and binds `127.0.0.1`. There is no auth; do not expose
  it.

## Licence

AGPL-3.0 (`LICENSE`), because `skills/` is derived from
[BaaRai/ARTEX](https://github.com/BaaRai/ARTEX) (upstream `Autumn-27/ARTEX`), which
is AGPL-3.0. The skills carry their own attribution; see `NOTICE`.
If you redistribute Titan, the AGPL obligations apply to the whole work.
