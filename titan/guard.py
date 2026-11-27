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
    """Authorized target set for one task.

    Matching rules
    --------------
    domain=example.com   the apex, every subdomain, and any address those names
                         resolve to (so a port scan against the IP is in scope)
    subdomain=a.example.com   that host only, no siblings, no parent
    ip / cidr            literal addresses and ranges
    url=...              host plus the port in the URL (no port = any port)
    keyword=...          literal string match, for bucket and tenant names
    exclude=...          always wins; host or domain suffix

    An address is also allowed when it resolves from an allowed host, which is what
    makes "domain=example.com" usable against a scan that only speaks IPs.
    """

    def __init__(self, entries: list[dict] | None = None, resolver=None, ttl: float = 300.0):
        self.hosts: dict[str, dict] = {}      # host -> {"ports": set(), "subdomains": bool}
        self.nets: list[ipaddress._BaseNetwork] = []
        self.keywords: set[str] = set()
        self.excludes: list[str] = []
        self.allow_local = True
        self._resolver = resolver or _resolver
        self._ttl = ttl
        self._dns: dict[str, tuple[float, set[str]]] = {}
        for e in entries or []:
            self.add(e.get("kind", ""), e.get("value", ""))

    # ------------------------------------------------------------------ build
    def add(self, kind: str, value: str) -> None:
        """One entry may carry several targets, wildcards and host:port pairs."""
        raw = (value or "").strip()
        if not raw:
            return
        for token in re.split(r"[,\s]+", raw):
            self._add_one(kind, token)

    def _add_one(self, kind: str, token: str) -> None:
        v = token.strip().strip("\"'")
        if not v:
            return
        kind = (kind or "").strip().lower()
        if kind == "exclude":
            self._add_exclude(v)
            return
        if kind in ("ip", "cidr"):
            try:
                self.nets.append(ipaddress.ip_network(v, strict=False))
            except ValueError:
                self._add_host(v, subdomains=False)
            return
        v = re.sub(r"^(ip|cidr|domain|subdomain|url|keyword|exclude)\s*:\s*", "", v, flags=re.I)
        if v.startswith("*."):
            v = v[2:]
            subdomains = True
        else:
            subdomains = kind in ("domain", "")
        if re.match(r"^[a-z]+://", v, re.I):
            from urllib.parse import urlparse

            u = urlparse(v)
            host = (u.hostname or "").strip("[]").lower()
            if not host:
                return
            ports = {u.port} if u.port else set()
            self.hosts.setdefault(host, {"ports": set(), "subdomains": False})["ports"].update(ports)
            return
        v = v.split("/")[0].rstrip("*").strip()
        if not v:
            return
        port = None
        if not re.fullmatch(r"\[[0-9a-f:]+\]", v) and v.count(":") == 1:
            host, _, maybe_port = v.partition(":")
            if maybe_port.isdigit():
                port, v = int(maybe_port), host
        try:
            self.nets.append(ipaddress.ip_network(v, strict=False))
            return
        except ValueError:
            pass
        if kind == "keyword":
            self.keywords.add(v.lower())
            return
        self._add_host(v.lower(), subdomains=subdomains, port=port)

    def _add_host(self, host: str, subdomains: bool, port: int | None = None) -> None:
        host = host.strip().strip(".").lower()
        if not host:
            return
        rec = self.hosts.setdefault(host, {"ports": set(), "subdomains": subdomains})
        rec["subdomains"] = rec["subdomains"] or subdomains
        if port:
            rec["ports"].add(port)

    def _add_exclude(self, v: str) -> None:
        v = re.sub(r"^(exclude|domain|host)\s*:\s*", "", v, flags=re.I)
        v = re.sub(r"^https?://", "", v, flags=re.I).split("/")[0].split(":")[0]
        v = v.strip().strip(".").lower()
        if v:
            self.excludes.append(v)

    def empty(self) -> bool:
        return not (self.hosts or self.nets or self.keywords)

    def summary(self) -> list[str]:
        out = [f"domain={h}" for h, r in self.hosts.items() if r["subdomains"]]
        out += [f"subdomain={h}" for h, r in self.hosts.items() if not r["subdomains"]]
        out += [f"net={n}" for n in self.nets]
        out += [f"keyword={k}" for k in self.keywords]
        out += [f"exclude={e}" for e in self.excludes]
        return out

    # ----------------------------------------------------------------- decide
    @staticmethod
    def _clean(host: str) -> str:
        h = (host or "").strip().strip("[]").lower().rstrip(".")
        if "://" in h:
            from urllib.parse import urlparse

            h = (urlparse(h).hostname or "").strip("[]").lower()
        return h

    def _excluded(self, host: str) -> bool:
        return any(host == e or host.endswith("." + e) for e in self.excludes)

    def _resolved(self, host: str) -> set[str]:
        hit = self._dns.get(host)
        if hit and time.time() - hit[0] < self._ttl:
            return hit[1]
        try:
            ips = {str(a[4][0]) for a in self._resolver(host)}
        except Exception:  # noqa: BLE001 - DNS is best effort
            ips = set()
        self._dns[host] = (time.time(), ips)
        return ips

    def hosts_for(self, host: str) -> bool:
        """Hostname match without touching DNS."""
        for key, rec in self.hosts.items():
            if host == key:
                return True
            if rec["subdomains"] and host.endswith("." + key):
                return True
        return False

    def is_subdomain(self, host: str) -> bool:
        h = self._clean(host)
        return any(rec["subdomains"] and h.endswith("." + key) and h != key
                   for key, rec in self.hosts.items())

    def allows_host(self, host: str, port: int | None = None) -> bool:
        h = self._clean(host)
        if not h:
            return True
        if self.allow_local and h in LOOPBACK:
            return True
        if self._excluded(h):
            return False
        for key, rec in self.hosts.items():
            matched = h == key or (rec["subdomains"] and h.endswith("." + key))
            if matched:
                if not rec["ports"] or port is None or port in rec["ports"]:
                    return True
                continue
        try:
            ip = ipaddress.ip_address(h)
        except ValueError:
            return False
        if ip.is_loopback and self.allow_local:
            return True
        if any(ip in net for net in self.nets):
            return True
        # an address that resolves from an allowed name is in scope by proxy
        for key in list(self.hosts)[:24]:
            if h in self._resolved(key):
                return True
        return False

    def check_text(self, text: str) -> tuple[bool, str, str]:
        """(allowed, reason, offending host) for every concrete target in `text`."""
        text = text or ""
        if self.empty():
            return False, "no scope configured for this task", ""
        for m in RE_URL.finditer(text):
            raw = m.group(1)
            host = raw.split("/")[0]
            port = None
            if host.count(":") == 1:
                hh, _, pp = host.partition(":")
                if pp.isdigit():
                    host, port = hh, int(pp)
            if not self.allows_host(host, port):
                return False, f"host {host} is outside the authorized scope", host
        for m in RE_IPV4.finditer(text):
            if not self.allows_host(m.group(0)):
                return False, f"address {m.group(0)} is outside the authorized scope", m.group(0)
        for m in RE_DOMAIN.finditer(text):
            cand = m.group(0).lower()
            ext = cand.rsplit(".", 1)[-1]
            if ext in FILE_EXT:
                continue
            before = text[max(0, m.start() - 8):m.start()]
            if before.endswith(("/", "@", ".", "-", "_")) or "://" in before:
                continue
            if not self.allows_host(cand):
                return False, f"host {cand} is outside the authorized scope", cand
        return True, "", ""

    def allows_text(self, text: str) -> tuple[bool, str]:
        ok, why, _ = self.check_text(text)
        return ok, why


def _resolver(host: str):
    import socket

    return socket.getaddrinfo(host, None)


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
        self._built = time.time()

    def refresh(self, max_age: float = 3.0) -> None:
        """Pick up scope changes and approvals made while this intent is running."""
        if time.time() - self._built < max_age:
            return
        try:
            self.scope = Scope(self.store.scope(self.task_id))
            self._built = time.time()
        except Exception:  # noqa: BLE001 - a stale scope must not kill the run
            self._built = time.time()

    def scope_summary(self) -> str:
        entries = [f"{'exclude' if s['kind'] == 'exclude' else s['kind']}={s['value']}"
                   for s in self.store.scope(self.task_id)]
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
            self.refresh()
            ok, why, host = self.scope.check_text(cmd)
            if not ok:
                policy = self.store.scope_policy(self.task_id)
                # a subdomain of an approved domain is in scope by many engagement
                # rules; approve it automatically when the operator allows that
                auto_ok = bool(host) and (
                    bool(policy.get("auto_any"))
                    or (policy.get("auto_subdomains") and self.scope.is_subdomain(host))
                )
                if auto_ok:
                    self.store.add_scope(self.task_id, "domain", host,
                                         "auto:" + ("policy" if policy.get("auto_any") else "subdomain"))
                    self.scope = Scope(self.store.scope(self.task_id))
                    self._built = time.time()
                    ok, why, host = self.scope.check_text(cmd)
                    if ok:
                        self.store.audit(self.task_id, self.worker, tool, "allow",
                                         f"auto-approved subdomain {host}", cmd)
                        return True, ""
                self.store.audit(self.task_id, self.worker, tool, "block", why, cmd)
                queued = ""
                if host:
                    cid = self.store.add_scope_candidate(
                        self.task_id, host, source=f"{tool} from {self.worker}",
                        evidence=cmd[:400], detail=why)
                    if cid:
                        queued = (" A scope request for this host is now waiting for the "
                                  "operator in the Scope tab. Do not retry it this way and do "
                                  "not look for a workaround; continue with in-scope targets.")
                return False, (f"{BANNER} This call was intercepted. Reason: {why}. "
                               f"{self.scope_summary()}.{queued}")
        self.store.audit(self.task_id, self.worker, tool, "allow", "", cmd)
        return True, ""

    def note_result(self, is_error: bool, result: str) -> None:
        if re.search(r"(?i)\b(403|429|forbidden|waf|blocked|rate.?limit|captcha)\b", result or ""):
            self.attrib["blocked"] += 1
        elif is_error:
            self.attrib["error"] += 1
        else:
            self.attrib["ok"] += 1
