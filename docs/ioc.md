# Wire identity: how Titan differs from ARTEX

Goal: no ARTEX fingerprint on the wire, no shared default infrastructure, no shared
identifiers a defender (or a detection rule written from the November 2026 advisories)
would match. Facts below are from the BaaRai/ARTEX tree inspected at build time.

## What ARTEX exposes (verified in-repo)

| Surface | ARTEX value | Where |
|---|---|---|
| Outbound User-Agent | `ARTEX-Assessment/1.0` (+ ` (engagement=…)`) | `config/task_user_agents.go` |
| Console | `127.0.0.1:8787`, Next.js app, `/api/*` | `docker-compose.yml`, `web/` |
| Database | PostgreSQL 5433, user/db `artex` | `config.example.json` |
| Env namespace | `ARTEX_*` (`ARTEX_PG_DSN`, `ARTEX_SKILL_DIR`, `ARTEX_BIND_ADDR`, `ARTEX_LLM_*`) | `.env.example` |
| Install paths | `/opt/artex/skills`, `/data`, `artex` binary, `start.sh` | `config.example.json`, `Dockerfile` |
| Process/container names | `artex`, `artex-db`, image tags `ghcr.io/.../artex` | `docker-compose*.yml` |
| Prompt/banner strings | `[ARTEX platform control, not target defence]`, `ARTEX paces its own…` | `guard/guard.go`, `agent/noise_profile.go` |
| Session ids | `exp<id>-planner`, `sessions/<id>` | `agent/planner.go` |
| Tool names sent to the LLM | `add_intent`, `record_fact`, `report_finding`, … | `agent/tools.go` |

## What Titan uses instead

| Surface | Titan value | Configurable |
|---|---|---|
| Outbound UA | `Titan-Assessment/0.2.0` | `TITAN_USER_AGENT` |
| Console | `127.0.0.1:9911`, no JS framework, 3 routes (`/`, `/api/overview`, `/api/findings`) | `TITAN_CONSOLE_PORT`, `TITAN_CONSOLE_BIND` |
| Database | SQLite `~/.titan/titan.db`, no network listener | `TITAN_DB` |
| Env namespace | `TITAN_*` | — |
| Install paths | `~/.titan/` (state), `<repo>/skills`, `bin/titan` | `TITAN_HOME` |
| Process name | `python3 …/bin/titan` | run via your own wrapper if needed |
| Prompt/banner strings | `[Titan platform control, not target defence]`, "Dewaguard Titan, an authorized penetration-test platform" | edit `titan/agents.py`, `titan/guard.py` |
| Session ids | none (no provider session header) | — |
| Dependencies | none (stdlib) — no `pip install`, no `docker` | — |

Result: a defender's ARTEX rules (UA regex, 8787, `/api/v1/tasks` paths, Postgres/`artex`
strings, docker image names, `ARTEX_` env leaks) do not match Titan.

## Residual overlap you must manage yourself

These are *behavioural*, not branded, so no string change removes them:

1. **The skills text is identical.** `SKILL.md` bodies are copied verbatim, and they
   are sent to your LLM provider (and only there). If your provider logs prompts, the
   text is attributable to ARTEX skill content. Keep the endpoint inside your trust
   boundary, or rewrite bodies you intend to use on engagements with that risk.
2. **Tool names and graph vocabulary are the same** (`add_intent`, `record_fact`,
   `report_finding`, `exploration_nodes`). Only visible to the model provider, never
   to the target — unless you paste tool output containing them into a request.
3. **Command shape.** Both tools call the same external scanners with similar flags:
   `nmap -sV`, `nuclei -rl`, `ffuf -rate`, `sqlmap --delay`. That is what the tools do;
   the rate flags reduce the pattern, they do not remove it. Prefer passive sources
   first, and one host at a time.
4. **Pacing and burst profile.** ARTEX defaults are aggressive-ish; Titan defaults to
   `balanced` at 2 rps/host, 1 in flight, and the prompt forbids parallel scanners on
   one host. Lower it (`TITAN_RPS=0.5`, `TITAN_NOISE_PROFILE=quiet`) if the client's
   SOC is sensitive.
5. **Prompt-injection framing.** If your traffic is inspected at the LLM gateway, the
   planner/worker system prompts are distinctive. Run your own gateway or a local
   model for anything sensitive.

## Hardening checklist before a real engagement

- [ ] `TITAN_USER_AGENT` set to the engagement label your RoE specifies (e.g.
      `AcmePentest/2026-Q4 (contact: soc@acme.test)`), or to your firm's standard.
- [ ] Console bound to `127.0.0.1` and not forwarded through any tunnel.
- [ ] `TITAN_RPS` ≤ the RoE's stated limit; `TITAN_NOISE_PROFILE=quiet` for prod.
- [ ] `--scope` lists exactly the authorized roots; no wildcard "just in case".
- [ ] Operator constraints encode every exclusion (hosts, ports, modules, windows).
- [ ] `TITAN_DENY_RULES` adds the engagement's forbidden actions.
- [ ] Model endpoint is self-hosted or contractually no-retention.
- [ ] `~/.titan/runs` is on encrypted storage; it holds target responses and loot.

## Detection (for blue team use of this repo)

If you are using Titan to *test detection*, the patterns it produces are: a single
egress IP hitting several hosts at fixed low rates, `Titan-Assessment/<version>` in
`User-Agent` for `webfetch` traffic, scanner fingerprints from the underlying tools,
and no interactive browser traffic. Bash-driven `curl`/`nmap` inherit whatever UA
the underlying tool sends unless you pass `-A`/`-H` yourself.
