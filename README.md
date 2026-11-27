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
- When the round budget ends with goals still open, the engine runs one
  **judgement-only** planner pass: `add_intent` is removed from its toolset, so
  evidence already in the graph can close a goal instead of costing another run.

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
  local web GUI: create/run/stop, live agent cards, per-intent steer and kill,
  settings page with model picker and connection test, skills browser, traffic
  viewer, SVG graph of the exploration nodes, finding triage, report download

Dropped on purpose (this is the "lightweight" part):

- Docker, PostgreSQL, `pgx`, migrations, background compaction daemons
- Next.js web IDE, auth, multi-user, task archives, templates, LLM profile CRUD,
  Bedrock/Anthropic gateways, LLM judge, MCP host, custom tool builder, browser
  automation server, intercept UI, digests/cold-node folding
- Redis-less horizontal scale (one process, N threads; SQLite is the blackboard)

## Install (no Docker, no server, no pip packages)

Requirements: Linux or macOS, Python >= 3.10, git. Nothing else: no Docker, no
database server, no pip packages. All state is one SQLite file.

```bash
cd ~/Dewaguard/Titan
./install.sh
```

The installer

1. refuses Python < 3.10,
2. links the launcher to `~/.local/bin/titan` (and tells you if that directory is
   not on `PATH`),
3. creates `~/.titan/` — database, run directories, skill index,
4. runs `titan doctor` and prints the next steps.

Manual equivalent, if you prefer to see every step:

```bash
chmod +x bin/titan
ln -sf "$PWD/bin/titan" ~/.local/bin/titan
export PATH="$HOME/.local/bin:$PATH"      # if not already on PATH
titan init
```

`titan init` is idempotent: it creates `~/.titan/titan.db`, the `runs/` tree and
indexes `skills/` (11 skills). No network, no service, no root.

Optional editable install, only if something else needs `import titan`:

```bash
python3 -m pip install --user -e .
```

## Configure a model: `titan setup`

Titan is model-agnostic: any endpoint that speaks OpenAI `/chat/completions` with
function calling (Ollama, vLLM, LM Studio, DeepSeek, OpenRouter, an internal gateway).

```bash
titan setup
```

Interactive, Hermes-style:

```
Dewaguard Titan 0.4.0 - model setup
Press Enter to keep the value shown in brackets.

base URL (OpenAI-compatible, e.g. http://127.0.0.1:11434/v1) [http://127.0.0.1:11434/v1]:
api key (hidden; blank keeps the current one):
endpoint reachable, 3 model(s) available
   1. qwen2.5:14b
   2. llama3.1:8b
   3. nomic-embed-text
model (number or id) [qwen2.5:14b]:
advanced settings (timeout/max_tokens/temperature)? [y/N]:
saved:
  endpoint   http://127.0.0.1:11434/v1
  model      qwen2.5:14b
  settings   ~/.titan/titan.db (no secrets)
  api key    sk-a...cdef (len 51) -> ~/.titan/secrets.json (0600)
testing a real completion...
  ok in 812 ms: ok
```

Where things are stored, and why:

| Item | Location | Protection |
|---|---|---|
| endpoint, model, timeout, max_tokens, temperature, pacing | `~/.titan/titan.db` (`settings` table) | no secrets in it, safe to copy/back up |
| API key | `~/.titan/secrets.json` | mode `0600`, written with `os.open(0o600)` + atomic rename |
| key precedence | `TITAN_LLM_API_KEY` env > `secrets.json` | env wins, and `doctor` says so when both exist |

The key is never written to the database, never printed (only `sk-a...cdef (len 51)`),
and `titan setup --api-key-stdin` reads it from a pipe so it never lands in shell
history.

Non-interactive and inspection modes:

```bash
titan setup --show                     # endpoint, model, masked key, pacing
printf '%s' "$KEY" | titan setup --url https://api.deepseek.com/v1 \
  --model deepseek-chat --api-key-stdin          # scripted, no history leak
```

Environment variables still work and are the right choice for CI; everything in the
settings table takes precedence over them except the key.

Verify at any time:

```bash
titan doctor
# ... model qwen2.5:14b, endpoint ..., api key sk-a...cdef via file: ... (0600),
#     llm probe ok (812 ms), status ready
```

### Scope and the artifact directory

Every engagement carries its own authorized scope and its own artifact directory:

```bash
titan new "..." --scope domain=zing-id.com --scope ip=192.168.168.98 \
  --workdir ~/cases/zing-id
```

`--scope` can be repeated, and one value may hold several targets
(`--scope domain="https://a.com/, *.a.com/*"`). Hostnames, IPs, CIDRs, URLs and
keywords are all normalised; an IP written as `domain=` still works. Anything outside
the scope is refused by the guard with a message naming the current scope, so the
agent can tell "not authorized" from "not reachable". The scope is also editable from
the engagement's overview panel.

`--workdir` is where every artifact of that engagement goes (notes, loot, scan output);
workers get a subdirectory per intent (`<workdir>/i<intent>`). Without it the default
is `~/.titan/runs/tasks/<id>`. The path is shown in the engagement header and enforced:
file writes outside it are blocked.

## First run

```bash
# 1. authorize a target -- without --scope every targeted command is refused
titan new "Enumerate http://127.0.0.1:8080 and record what it exposes; no exploitation" \
  --title "local lab" --scope url=http://127.0.0.1:8080

# 2. run it — autonomous: it keeps going until the goal is met or you stop it
titan run 1

# 3. read the result
titan status 1
titan findings 1
```

The model decomposes the goal into 1-6 measurable goals, the planner dispatches
intents, each worker runs real commands in the engagement's artifact directory and
writes facts, assets and findings back into the graph. Ctrl-C is safe: open intents
stay claimable, so `titan run 1` resumes where it stopped.

### Run modes

No round counting: you choose how much autonomy the agent gets.

| Mode | Behaviour |
|---|---|
| **autonomous** (default) | runs round after round until every goal is proven, you press Stop, or it stops making progress |
| **approval** | same loop, but pauses before each round and waits for Approve / Deny |

```bash
titan run 8                      # autonomous
titan run 8 --approval           # confirm each round in the terminal
titan run 8 --approval --no-prompt   # wait for: titan approve 8  (from anywhere)
titan approve 8                  # release a paused engagement
titan approve 8 --deny           # stop it instead
```

Stop conditions in autonomous mode: all goals met (`prove_goal`), operator Stop,
`TITAN_TASK_DEADLINE` if set, `TITAN_NO_PROGRESS` consecutive rounds with no new facts
or findings (default 4), or the safety cap `TITAN_MAX_ROUNDS` (default 200). A stop is
recorded in the activity trail with the reason, and `--rounds N` is still available as
an explicit hard cap for a first cheap run.

In the GUI the mode is a selector next to Start/Stop, and a pending approval shows as
a burgundy banner with **Approve & continue** / **Stop here**. Changing the mode or the
worker count while an engagement is running applies from the next round — no restart,
no reload; switching from approval back to autonomous releases a paused round
immediately.

## GUI

```bash
titan serve            # http://127.0.0.1:9911
```

One process, no build step, no JavaScript dependencies, no external assets. The
component layer is [daisyUI](https://daisyui.com) 4 (vendored into
`titan/assets/daisyui.css`, served gzipped at `/static/daisyui.css`) with the theme
tokens remapped to the burgundy palette, so buttons, inputs, tabs, badges, dialogs and
the chat follow one system in both themes.

| View | What it does |
|---|---|
| **Overview** | intent timeline (one lane per worker, bar = wall-clock duration, click to open), goals, constraints, queue with steer/stop, operator notes, scope editor, live agents, untested assets |
| **Scope** | approved targets with what they resolve to, discovered hosts waiting for approval, exclusions, and the auto-approval policy |
| **Commands** | commands the guard holds for a human decision — state-changing requests, privileged actions, exploitation tooling, installs, writes outside the folder — with approve/reject, history, and an auto-approve switch |
| **Enumeration** | per host: ports and services, web surface, discovered paths with status codes, and observations tagged observed/inferred with the tool and time that produced them |
| **Findings** | severity and status filters, inline evidence and reproduction, status workflow, copy as markdown, report preview |
| **Artifacts** | the engagement folder itself — a tree of `enumeration/`, `findings/`, `poc/`, `evidence/`, `report/`, with a viewer for markdown, JSON, text and images, plus the recorded traffic |
| **Activity** | the trace: time, delta, worker, kind, detail; filter by worker or kind |
| **Graph** | both graphs as SVG; running intents pulse and their edges animate, so progress is visible while the run is live |

Global views live in the header menu: **Settings** (model, key, pacing, test
connection) and **Skills** (all 11 with full `SKILL.md`).

`Report` opens a client-facing page — goals, scope, findings with severity and
evidence, and what was enumerated, with internal intents, traces and reasoning left
out. It prints cleanly to PDF from the browser.

### Scope

`domain=example.com` allows the apex, every subdomain and any address those names
resolve to, so a port scan against the IP is not refused. `subdomain=` is exact,
`ip`/`cidr` are literal, `url=` carries a port restriction, `exclude=` always wins.

Approval is split in two. **Scope** decides *where* the run may go; **Commands**
decides *what* it may do there (state-changing requests, sudo, exploitation tooling,
installs, writes outside the folder). Both have their own auto-approve switch, and an
approved host does not approve a risky command.

Anything the guard refuses is recorded instead of silently dropped: the host appears
in **Scope → Discovered** with the tool and command that found it, and one click
approves it. Approval is picked up by running workers within a couple of seconds —
no restart. Subdomains of an approved domain can be auto-approved (on by default),
and every auto-approval is tagged in the audit log.

### Artifacts on disk

Every round rewrites the engagement folder, so the output exists without the console:

```
<workdir>/
  00-meta.json                 goal, scope, policy, counts
  enumeration/hosts.json       index, plus <host>/summary.md, paths.txt, http.txt
  findings/F-01-<slug>.md      Title/severity/asset/evidence/reproduction
  findings/index.json
  poc/F-01-<slug>/             request.http, response.http, poc.sh, README.md
  evidence/traffic.jsonl       every recorded request/response
  evidence/observations.jsonl
  report/report.md
```

Notifications live behind the bell in the header: findings, observations and scope
requests are kept in a list with new/viewed state, so a reload does not replay what
you already read. The ✦ button opens a chat with the planner — ask what it is doing,
why a step failed, or tell it to change course; it has the same tools as the CLI's
`titan ask`, so it can queue hints and steer running intents.

Scope accepts pasted commands: `nmap -p- 10.0.0.5 -oN out.txt` is reduced to
`ip=10.0.0.5`, never stored as a string. Auto-approval has three levels —
subdomains of an approved domain (default), hosts sharing an approved address, and
any host at all — so a hands-off run can proceed without a click.

A density toggle (compact / comfortable) is in the header menu and is remembered per
browser. Keyboard: `g` then `o/f/e/v/a/r` for the tabs, `/` to focus the filter,
`?` for the list, `esc` to close.

Light and dark themes (burgundy on white / burgundy on near-black), a toggle in the
header, and the choice is remembered per browser. The sidebar and the open engagement
refresh themselves every 3 s with no manual reload, but the poll is inert when nothing
changed and preserves your scroll position and focused field — reading a long fact
list or typing a hint is not interrupted.

It is loopback-only: binding off `127.0.0.1` is refused unless
`TITAN_CONSOLE_TOKEN` is set, and then every request needs `X-Titan-Token`.

### All settings

| Variable | Default | Meaning |
|---|---|---|
| `TITAN_HOME` | `~/.titan` | state dir (db, runs) |
| `TITAN_DB` | `$TITAN_HOME/titan.db` | SQLite file |
| `TITAN_WORKDIR` | `$TITAN_HOME/runs` | per-task / per-intent work dirs |
| `TITAN_SKILL_DIR` | `<repo>/skills` | skill root |
| `TITAN_LLM_BASE_URL` | `http://127.0.0.1:11434/v1` | OpenAI-compatible base |
| `TITAN_LLM_MODEL` | *(empty)* | model id |
| `TITAN_LLM_API_KEY` | `$OPENAI_API_KEY` | bearer token (overrides `~/.titan/secrets.json`) |
| `TITAN_LLM_TIMEOUT` | `600` | per-request seconds |
| `TITAN_LLM_MAX_TOKENS` | `0` | 0 = endpoint default |
| `TITAN_MAX_WORKERS` | `2` | parallel intents |
| `TITAN_PLANNER_TURNS` | `12` | planner tool turns per round |
| `TITAN_WORKER_TURNS` | `40` | worker tool turns per intent |
| `TITAN_MAX_ROUNDS` | `200` | hard stop |
| `TITAN_TASK_DEADLINE` | `0` | seconds, 0 = none |
| `TITAN_INTENT_LEASE` | `900` | claim expiry |
| `TITAN_APPROVAL_TIMEOUT` | `1800` | seconds to wait for an approval decision |
| `TITAN_NO_PROGRESS` | `4` | consecutive rounds with no new facts/findings before stopping |
| `TITAN_RPS` | `2.0` | per-host request rate |
| `TITAN_MAX_PER_HOST` | `1` | in-flight per host |
| `TITAN_NOISE_PROFILE` | `balanced` | `quiet` \| `balanced` \| `aggressive` \| `off` |
| `TITAN_USER_AGENT` | `Titan-Assessment/0.3.0` | outbound UA |
| `TITAN_CONSOLE_PORT` | `9911` | web GUI port |
| `TITAN_CONSOLE_BIND` | `127.0.0.1` | GUI bind address |
| `TITAN_CONSOLE_TOKEN` | *(empty)* | required header `X-Titan-Token` when bound off-localhost |
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
titan serve                    # web GUI on 127.0.0.1:9911
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
titan/gui.py           the console page (one HTML document, no build step)
titan/server.py        web GUI + JSON API (localhost, token-gated off-localhost)
titan/cli.py           command line
skills/                ARTEX skills, verbatim
docs/architecture.md   data model, lifecycle, design notes
docs/ioc.md            how Titan differs from ARTEX on the wire
tests/test_cycle.py    orchestrator proof: graphs, guard, evidence gates
tests/test_cli.py      CLI + real HTTP provider + SQLite persistence + console
```

## Tests

```bash
make test          # 11 tests, ~10 s, no model, no internet
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
SQLite persistence, markdown export and the GUI's API (hint queue, 404 handling, report download).

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
- The GUI binds `127.0.0.1` and has no auth there. Binding it elsewhere is refused
  unless `TITAN_CONSOLE_TOKEN` is set; then every request needs `X-Titan-Token`.

## Licence

AGPL-3.0 (`LICENSE`), because `skills/` is derived from
[BaaRai/ARTEX](https://github.com/BaaRai/ARTEX) (upstream `Autumn-27/ARTEX`), which
is AGPL-3.0. The skills carry their own attribution; see `NOTICE`.
If you redistribute Titan, the AGPL obligations apply to the whole work.
