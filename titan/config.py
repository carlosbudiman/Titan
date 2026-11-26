"""Runtime settings. Everything is env-overridable; no secrets are baked in.

Defaults are deliberately *not* ARTEX's: different UA, port, paths, DB engine and
file names, so a defender's ARTEX signatures do not match this tool.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

VERSION = "0.5.0"
TOOL_NAME = "titan"


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    home: Path = field(default_factory=lambda: Path(_env("TITAN_HOME", str(Path.home() / ".titan"))).expanduser())
    db_path: Path | None = None
    workdir: Path | None = None
    skill_dir: Path | None = None

    # LLM (OpenAI-compatible /chat/completions)
    base_url: str = field(default_factory=lambda: _env("TITAN_LLM_BASE_URL", "http://127.0.0.1:11434/v1"))
    model: str = field(default_factory=lambda: _env("TITAN_LLM_MODEL", ""))
    api_key: str = field(default_factory=lambda: _env("TITAN_LLM_API_KEY", _env("OPENAI_API_KEY", "")))
    temperature: float = field(default_factory=lambda: _env_float("TITAN_LLM_TEMPERATURE", 0.2))
    request_timeout: int = field(default_factory=lambda: _env_int("TITAN_LLM_TIMEOUT", 600))
    max_tokens: int = field(default_factory=lambda: _env_int("TITAN_LLM_MAX_TOKENS", 0))

    # Orchestration budgets
    max_workers: int = field(default_factory=lambda: _env_int("TITAN_MAX_WORKERS", 2))
    planner_turns: int = field(default_factory=lambda: _env_int("TITAN_PLANNER_TURNS", 12))
    worker_turns: int = field(default_factory=lambda: _env_int("TITAN_WORKER_TURNS", 40))
    max_rounds: int = field(default_factory=lambda: _env_int("TITAN_MAX_ROUNDS", 200))
    task_deadline_s: int = field(default_factory=lambda: _env_int("TITAN_TASK_DEADLINE", 0))
    heartbeat_s: int = field(default_factory=lambda: _env_int("TITAN_HEARTBEAT", 30))
    intent_lease_s: int = field(default_factory=lambda: _env_int("TITAN_INTENT_LEASE", 900))

    # Identity / OPSEC
    user_agent: str = field(default_factory=lambda: _env("TITAN_USER_AGENT", f"Titan-Assessment/{VERSION}"))
    rps: float = field(default_factory=lambda: _env_float("TITAN_RPS", 2.0))
    max_per_host: int = field(default_factory=lambda: _env_int("TITAN_MAX_PER_HOST", 1))
    noise_profile: str = field(default_factory=lambda: _env("TITAN_NOISE_PROFILE", "balanced"))
    console_port: int = field(default_factory=lambda: _env_int("TITAN_CONSOLE_PORT", 9911))
    console_bind: str = field(default_factory=lambda: _env("TITAN_CONSOLE_BIND", "127.0.0.1"))
    console_token: str = field(default_factory=lambda: _env("TITAN_CONSOLE_TOKEN", ""))

    # Guard
    deny_rules_file: str = field(default_factory=lambda: _env("TITAN_DENY_RULES", ""))
    allow_shell: bool = field(default_factory=lambda: _env("TITAN_ALLOW_SHELL", "1") != "0")

    def __post_init__(self) -> None:
        self.home = Path(self.home).expanduser()
        self.db_path = Path(self.db_path or _env("TITAN_DB", str(self.home / "titan.db"))).expanduser()
        self.workdir = Path(self.workdir or _env("TITAN_WORKDIR", str(self.home / "runs"))).expanduser()
        self.skill_dir = Path(self.skill_dir or _env("TITAN_SKILL_DIR", str(REPO_ROOT / "skills"))).expanduser()

    def ensure_dirs(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def run_dir(self, task_id: int, intent_id: int = 0) -> Path:
        leaf = "main" if intent_id <= 0 else f"i{intent_id}"
        p = self.workdir / "tasks" / str(task_id) / leaf
        p.mkdir(parents=True, exist_ok=True)
        return p

    def public_identity(self) -> dict:
        return {
            "tool": TOOL_NAME,
            "version": VERSION,
            "user_agent": self.user_agent,
            "console": f"{self.console_bind}:{self.console_port}",
            "state_dir": str(self.home),
        }


# --------------------------------------------------------------------- secrets
# The API key never goes into the database (which gets copied into reports/backups)
# and is never printed. Precedence: environment, then ~/.titan/secrets.json (0600).

def secrets_path(settings: "Settings") -> Path:
    return Path(settings.home) / "secrets.json"


def load_api_key(settings: "Settings") -> str:
    if settings.api_key:
        return settings.api_key
    p = secrets_path(settings)
    try:
        data = json.loads(p.read_text())
    except (OSError, ValueError):
        return ""
    key = data.get("llm_api_key") if isinstance(data, dict) else ""
    return key if isinstance(key, str) else ""


def save_api_key(settings: "Settings", key: str) -> Path:
    """Write the key to a 0600 file, atomically, without touching the database."""
    p = secrets_path(settings)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    payload = {"llm_api_key": key}
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(payload, fh)
            fh.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, p)
        os.chmod(p, 0o600)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    return p


def key_source(settings: "Settings") -> str:
    if settings.api_key:
        return "env: TITAN_LLM_API_KEY"
    if secrets_path(settings).exists():
        return f"file: {secrets_path(settings)} (0600)"
    return "unset"


def mask(secret: str) -> str:
    if not secret:
        return "(unset)"
    if len(secret) <= 8:
        return "****"
    return f"{secret[:4]}...{secret[-4:]} (len {len(secret)})"
