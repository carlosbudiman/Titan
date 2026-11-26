"""Skills: directory scan, frontmatter parse, index + on-demand load.

Same layouts as ARTEX's skills/ (one directory per skill, SKILL.md with YAML
frontmatter, optional references/ and scripts/), so the copied skills work
unchanged. Progressive disclosure: only name+description go into the system
prompt; the body is loaded by the read_skill tool.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Skill:
    name: str
    description: str
    path: Path
    meta: dict = field(default_factory=dict)

    def body(self) -> str:
        text = self.path.read_text(encoding="utf-8", errors="replace")
        return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()

    def index_line(self) -> str:
        return f"- {self.name}: {self.description}"


def _frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    meta: dict = {}
    key = None
    for line in m.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if re.match(r"^\s", line) and key:
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            meta[key] = val
    return meta, m.group(2)


class SkillIndex:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.skills: dict[str, Skill] = {}
        self.load()

    def load(self) -> None:
        self.skills.clear()
        if not self.root.is_dir():
            return
        for d in sorted(self.root.iterdir()):
            f = d / "SKILL.md"
            if not (d.is_dir() and f.is_file()):
                continue
            try:
                meta, _ = _frontmatter(f.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            name = (meta.get("name") or d.name).strip()
            desc = (meta.get("description") or "").strip()
            self.skills[name] = Skill(name=name, description=desc, path=f, meta=meta)

    def index(self) -> str:
        if not self.skills:
            return ""
        lines = ["Available skills (load one with read_skill(name) when it matches the job):"]
        lines += [s.index_line() for s in self.skills.values()]
        return "\n".join(lines)

    def read(self, name: str) -> str:
        s = self.skills.get(name) or self.skills.get(Path(name).name)
        if not s:
            return f"ERROR: no skill named {name!r}. Known: {', '.join(sorted(self.skills)) or '(none)'}"
        files = sorted(str(p.relative_to(self.root)) for p in s.path.parent.rglob("*") if p.is_file())
        return (f"# SKILL: {s.name}\n\n{s.body()}\n\n"
                f"## Files bundled with this skill (paths relative to {self.root})\n"
                + "\n".join(f"- {f}" for f in files[:60]))

    def register(self, store) -> None:
        for s in self.skills.values():
            store.upsert_skill(s.name, s.description, str(s.path), s.meta)
