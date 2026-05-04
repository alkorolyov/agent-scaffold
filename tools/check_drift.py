#!/usr/bin/env python3
"""Drift detector — run as a Stop hook or pre-commit.

Checks:
- INDEX.md files are not stale
- findings.md / CLAUDE.md cite only existing, non-superseded exps
- exp parent: references exist and are not superseded
- exp consumes: file paths exist on disk
- adr superseded_by: references exist; superseded adrs have superseded_by set
- docs/ root has no orphan files outside the framework structure
"""
import re
import sys
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "docs" / "experiments"
ADR_DIR = ROOT / "docs" / "adrs"
DOCS_DIR = ROOT / "docs"
FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
EXP_REF = re.compile(r"\bExp\s*(\d+)\b")

# Standard top-level docs/ files — anything else is an orphan
KNOWN_DOCS = {"progress.md", "findings.md", "data.md", "api.md", "setup.md", "ai_log.md"}
# Known subdirectories — unexpected subdirs are silently allowed
KNOWN_SUBDIRS = {"experiments", "adrs", "kb", "ref", "archive", "sessions", "records"}

issues = []


def load_kind(directory, kind):
    records = {}
    if not directory.exists():
        return records
    for p in directory.glob(f"{kind}_*.md"):
        m = FM_RE.match(p.read_text())
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        if kind in fm:
            records[fm[kind]] = (p, fm)
    return records


exps = load_kind(EXP_DIR, "exp")
adrs = load_kind(ADR_DIR, "adr")


# 1. INDEX.md staleness
for directory, records in [(EXP_DIR, exps), (ADR_DIR, adrs)]:
    idx = directory / "INDEX.md"
    if idx.exists() and records:
        idx_mtime = idx.stat().st_mtime
        for p, _ in records.values():
            if p.stat().st_mtime > idx_mtime:
                issues.append(f"{idx.relative_to(ROOT)} is stale (older than {p.name}). Run tools/render_index.py.")
                break


# 2. findings.md / CLAUDE.md cite valid exps
for f in [DOCS_DIR / "findings.md", ROOT / "CLAUDE.md"]:
    if not f.exists():
        continue
    for n in map(int, EXP_REF.findall(f.read_text())):
        if n not in exps:
            issues.append(f"{f.name} references Exp {n} but exp_{n:02d}_*.md does not exist.")
        elif exps[n][1].get("status") == "superseded":
            issues.append(f"{f.name} references Exp {n} which is superseded.")


# 3. exp lineage and artifact integrity
for n, (_, fm) in exps.items():
    parent = fm.get("parent")
    if parent and parent not in exps:
        issues.append(f"exp_{n}: parent={parent} does not exist.")
    elif parent and exps[parent][1].get("status") == "superseded":
        issues.append(f"exp_{n}: parent={parent} is superseded.")
    for path in fm.get("consumes") or []:
        if not (ROOT / path).exists():
            issues.append(f"exp_{n}: consumes '{path}' but file is missing.")


# 4. adr integrity
for n, (_, fm) in adrs.items():
    sb = fm.get("superseded_by")
    if sb is not None and sb not in adrs:
        issues.append(f"adr_{n}: superseded_by={sb} does not exist.")
    if fm.get("status") == "superseded" and not sb:
        issues.append(f"adr_{n}: status=superseded but superseded_by is not set.")


# 5. orphan docs in docs/ root
if DOCS_DIR.exists():
    for f in DOCS_DIR.iterdir():
        if not (f.is_file() and f.suffix == ".md"):
            continue
        if f.name in KNOWN_DOCS:
            continue
        # Allow domain/reference docs that declare themselves via frontmatter
        m = FM_RE.match(f.read_text())
        if m and (yaml.safe_load(m.group(1)) or {}).get("kind") in ("domain-doc", "reference"):
            continue
        issues.append(
            f"docs/{f.name} is not a standard framework file. "
            "Design decision? → rec.py adr new. "
            "Domain reference? → add 'kind: domain-doc' frontmatter."
        )


if issues:
    print("DRIFT DETECTED:")
    for i in issues:
        print(f"  - {i}")
    sys.exit(1)

print(f"OK ({len(exps)} experiments, {len(adrs)} ADRs, no drift detected).")
