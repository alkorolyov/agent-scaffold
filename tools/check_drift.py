#!/usr/bin/env python3
"""Drift detector — run as a Stop hook or pre-commit.

Checks:
- INDEX.md is not stale (older than any exp_*.md)
- findings.md / CLAUDE.md cite only existing, non-superseded exps
- parent: references exist and are not superseded
- consumes: file paths exist on disk
"""
import re
import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "docs" / "experiments"
FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
EXP_REF = re.compile(r"\bExp\s*(\d+)\b")

issues = []

if not EXP_DIR.exists():
    print("OK (no docs/experiments/ yet).")
    sys.exit(0)

exps = {}
for p in EXP_DIR.glob("exp_*.md"):
    m = FM_RE.match(p.read_text())
    if not m:
        continue
    fm = yaml.safe_load(m.group(1)) or {}
    if "exp" in fm:
        exps[fm["exp"]] = (p, fm)

# INDEX.md staleness
idx = EXP_DIR / "INDEX.md"
if idx.exists() and exps:
    idx_mtime = idx.stat().st_mtime
    for p, _ in exps.values():
        if p.stat().st_mtime > idx_mtime:
            issues.append(f"INDEX.md is stale (older than {p.name}). Run tools/render_index.py.")
            break

# findings.md and CLAUDE.md reference valid exps
for f in [ROOT / "docs" / "findings.md", ROOT / "CLAUDE.md"]:
    if not f.exists():
        continue
    for n in map(int, EXP_REF.findall(f.read_text())):
        if n not in exps:
            issues.append(f"{f.name} references Exp {n} but exp_{n:02d}_*.md does not exist.")
        elif exps[n][1].get("status") == "superseded":
            issues.append(f"{f.name} references Exp {n} which is superseded.")

# Lineage and artifact integrity
for n, (_, fm) in exps.items():
    parent = fm.get("parent")
    if parent and parent not in exps:
        issues.append(f"exp_{n}: parent={parent} does not exist.")
    elif parent and exps[parent][1].get("status") == "superseded":
        issues.append(f"exp_{n}: parent={parent} is superseded.")
    for path in fm.get("consumes") or []:
        if not (ROOT / path).exists():
            issues.append(f"exp_{n}: consumes '{path}' but file is missing.")

if issues:
    print("DRIFT DETECTED:")
    for i in issues:
        print(f"  - {i}")
    sys.exit(1)

print(f"OK ({len(exps)} experiments, no drift detected).")
