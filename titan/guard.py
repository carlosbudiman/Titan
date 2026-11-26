"""Pre-tool safety boundary: built-in denies, operator constraints, target scope.

Every tool call passes through Guard.check() before the handler runs. A blocked
call returns a message prefixed with the platform banner so the model does not
mistake it for target-side defence (WAF/403) and try to "bypass" its own policy.
"""
from __future__ import annotations

import ipaddress
import re
import threading
import time
from pathlib import Path

BANNER = "[Titan platform control, not target defence]"

# Built-in denies: things that damage the operator's box, the network fabric or
# produce irreversible side effects outside any engagement.
BUILTIN_DENY = [
    r"\brm\s+(-[a-zA-Z]*\s+)*-(?:[a-zA-Z]*r[a-zA-Z]*f|f[a-zA-Z]*r)\s+/(?:\s|$)",
    r"\brm\s+-rf\s+/\*",
    r"\bmkfs(\.\w+)?\b",
    r"\bdd\b[^\n]*\bof=/dev/(sd|nvme|hd|vd)",
    r"\bwipefs\b",
    r"\b(fdisk|parted|sgdisk)\s+/dev/",
    r"\b(shutdown|reboot|poweroff|halt)\b",
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",
    r"\bchmod\s+-R\s+777\s+/(?:\s|$)",
    r"\bchown\s+-R\s+[^\n]*\s+/(?:\s|$)",
    r">\s*/dev/(sd|nvme|hd|vd)",
    r"\b(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(ba|z|k)?sh\b",
    r"\bmkfs\b|\bcryptsetup\b",
    r"\bhistory\s+-c\b",
    r"\b(?:cat|cp|scp|rsync|tar)\b[^\n]*(?:/etc/shadow|\.ssh/id_|\.aws/credentials|\.gnupg/)",
]

RE_URL = re.compile(r"https?://([A-Za-z0-9._\-\[\]:]+)", re.I)
RE_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
RE_DOMAIN = re.compile(r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}\b")

FILE_EXT = {"php", "html", "htm", "js", "mjs", "json", "jsonl", "txt", "aspx", "jsp", "md",
            "py", "sh", "bash", "yaml", "yml", "xml", "log", "conf", "ini", "bak", "sql",
            "zip", "tar", "gz", "tgz", "csv", "png", "jpg", "jpeg", "gif", "svg", "css", "pdf",
            "doc", "docx", "xls", "xlsx", "bin", "so", "dll", "exe", "pem", "crt", "key"}

LOOPBACK = {"127.0.0.1", "::1", "localhost", "0.0.0.0"}


class Scope:
    """Authorized target set for one task."""

    def __init__(self, entries: list[dict] | None = None):
        self.domains: set[str] = set()
        self.ips: set[ipaddress._BaseNetwork] = set()
        self.keywords: set[str] = set()
        self.allow_local = True
        for e in entries or []:
            self.add(e.get("kind", ""), e.get("value", ""))

    def add(self, kind: str, value: str) -> None:
        """One entry may carry several targets and wildcards ("https://a.com/, *.b.com/*")."""
        raw = (value or "").strip()
        if not raw:
            return
        for token in re.split(r"[,\s]+", raw):
            self._add_one(kind, token)

    def _add_one(self, kind: str, token: str) -> None:
        v = token.strip().strip("\"'")
        if not v:
            return
        if kind in ("ip", "cidr"):
            try:
                self.ips.add(ipaddress.ip_network(v, strict=False))
            except ValueError:
                self.domains.add(v.lower())
            return
        if v.startswith("*."):
            v = v[2:]
        v = re.sub(r"^https?://", "", v, flags=re.I)
        v = v.split("/")[0].rstrip("*").strip()
        if not v:
            return
        if not re.fullmatch(r"\[[0-9a-f:]+\]", v) and v.count(":") == 1:
            v = v.split(":")[0]            # host:port -> host (IPv6 stays intact)
        v = v.lower()
        try:
            self.ips.add(ipaddress.ip_network(v, strict=False))
            return
        except ValueError:
            pass
        if kind in ("domain", "url"):
            self.domains.add(v)
        elif kind == "keyword":
            self.keywords.add(v)

    def empty(self) -> bool:
        return not (self.domains or self.ips or self.keywords)

    def allows_host(self, host: str) -> bool:
        h = (host or "").strip().lower().strip("[]")
        if not h:
            return True
        if self.allow_local and h in LOOPBACK:
            return True
        if h in self.domains:          # exact entry, incl. a legacy IP-in-domain row
            return True
        try:
            ip = ipaddress.ip_address(h)
        except ValueError:
            ip = None
        if ip is not None:
            if ip.is_loopback and self.allow_local:
                return True
            if any(ip in net for net in self.ips):
                return True
            return any(str(ip) == d for d in self.domains)
        for d in self.domains:
            if h == d or h.endswith("." + d):
                return True
        return False

    def allows_text(self, text: str) -> tuple[bool, str]:
        """True when every concrete host in `text` is in scope."""
        text = text or ""
        if self.empty():
            return False, "no scope configured for this task"
        for m in RE_URL.finditer(text):
            host = m.group(1).split(":")[0].split("/")[0]
            if not self.allows_host(host):
                return False, f"host {host} is outside the authorized scope"
        for m in RE_IPV4.finditer(text):
            if not self.allows_host(m.group(0)):
                return False, f"address {m.group(0)} is outside the authorized scope"
        for m in RE_DOMAIN.finditer(text):
            cand = m.group(0).lower()
            ext = cand.rsplit(".", 1)[-1]
            if ext in FILE_EXT:
                continue
            before = text[max(0, m.start() - 8):m.start()]
            if before.endswith(("/", "@", ".", "-", "_")) or "://" in before:
                continue  # URL host or path fragment, already handled above
            if not self.allows_host(cand):
                return False, f"host {cand} is outside the authorized scope"
        return True, ""


class Pacer:
    """Per-host token bucket. Honours the noise profile's requests-per-second."""

    def __init__(self, rps: float, max_per_host: int = 1):
        self.rps = max(0.05, float(rps or 1))
        self.max_per_host = max(1, int(max_per_host or 1))
        self.min_interval = 1.0 / self.rps
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, host: str) -> float:
        with self._lock:
            t = time.monotonic()
            prev = self._last.get(host, 0.0)
            delta = t - prev
            sleep = self.min_interval - delta
            if sleep > 0:
                time.sleep(sleep)
            self._last[host] = time.monotonic()
            return max(0.0, sleep)


class Guard:
    def __init__(self, store, settings, task_id: int, worker: str, scope: Scope,
                 workdir: str | Path | None = None):
        self.store = store
        self.settings = settings
        self.task_id = task_id
        self.worker = worker
        self.scope = scope
        self.workdir = Path(workdir).expanduser() if workdir else Path(settings.workdir)
        self.builtin = [re.compile(p, re.I) for p in BUILTIN_DENY]
        extra = []
        if settings.deny_rules_file:
            p = Path(settings.deny_rules_file)
            if p.is_file():
                extra = [re.compile(l.strip(), re.I) for l in p.read_text().splitlines()
                         if l.strip() and not l.strip().startswith("#")]
        self.extra = extra
        self.attrib = {"ok": 0, "blocked": 0, "error": 0}

    def scope_summary(self) -> str:
        entries = [f"{s['kind']}={s['value']}" for s in self.store.scope(self.task_id)]
        return "Authorized scope: " + (", ".join(entries) if entries else "empty")

    def _deny_hit(self, text: str) -> str:
        for rx in self.builtin + self.extra:
            if rx.search(text or ""):
                return rx.pattern
        return ""

    def deny_text(self, tool: str, args: dict) -> str:
        cmd = ""
        if tool == "bash":
            cmd = str(args.get("command", ""))
        elif tool == "webfetch":
            cmd = str(args.get("url", ""))
        elif tool in ("write_file", "edit_file"):
            p = str(args.get("path", ""))
            wd = self.workdir.resolve()
            try:
                if not Path(p).expanduser().resolve().is_relative_to(wd):
                    return f"file path {p} is outside the engagement work directory {wd}"
            except (OSError, ValueError):
                return f"file path {p} cannot be resolved"
        else:
            cmd = " ".join(str(v) for v in args.values() if isinstance(v, str))
        return self._deny_hit(cmd)

    def check(self, tool: str, args: dict) -> tuple[bool, str]:
        """Return (allowed, message). Records the decision in the audit log."""
        cmd = str(args.get("command") or args.get("url") or "")
        pat = self.deny_text(tool, args)
        if pat:
            self.store.audit(self.task_id, self.worker, tool, "block",
                             f"built-in deny rule {pat}", cmd)
            return False, (f"{BANNER} This call was intercepted. Reason: built-in deny rule "
                           f"({pat}). This operation is forbidden.")
        for c in self.store.constraints(self.task_id):
            if c["kind"] == "deny" and c["text"] and c["text"].lower() in cmd.lower():
                self.store.audit(self.task_id, self.worker, tool, "block",
                                 f"operator constraint: {c['text']}", cmd)
                return False, (f"{BANNER} This call was intercepted. Reason: operator "
                               f"constraint '{c['text']}'. This operation is forbidden.")
        if tool in ("bash", "webfetch") and self.settings.allow_shell:
            ok, why = self.scope.allows_text(cmd)
            if not ok:
                self.store.audit(self.task_id, self.worker, tool, "block", why, cmd)
                return False, (f"{BANNER} This call was intercepted. Reason: {why}. "
                               f"{self.scope_summary()}. Do not reach it another way: either "
                               f"stay inside that scope or record a fact that it is unreachable.")
        self.store.audit(self.task_id, self.worker, tool, "allow", "", cmd)
        return True, ""

    def note_result(self, is_error: bool, result: str) -> None:
        if re.search(r"(?i)\b(403|429|forbidden|waf|blocked|rate.?limit|captcha)\b", result or ""):
            self.attrib["blocked"] += 1
        elif is_error:
            self.attrib["error"] += 1
        else:
            self.attrib["ok"] += 1
