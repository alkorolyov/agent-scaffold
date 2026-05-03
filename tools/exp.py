#!/usr/bin/env python3
"""Experiment record CLI.

Usage:
  tools/exp.py new <slug>                        # create exp file
  tools/exp.py update <N> [options]              # update frontmatter
  tools/exp.py show <N>                          # print frontmatter
  tools/exp.py list [--tag=X] [--status=X] [--outcome=X]
  tools/exp.py lineage <N>                       # walk DAG
  tools/exp.py finding <N> "<text>"              # append to findings.md
"""
import argparse
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "docs" / "experiments"
FINDINGS = ROOT / "docs" / "findings.md"
FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _load_all():
    exps = {}
    for p in sorted(EXP_DIR.glob("exp_*.md")):
        m = FM_RE.match(p.read_text())
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        exps[fm["exp"]] = (p, fm)
    return exps


def _next_num(exps):
    return max(exps.keys(), default=0) + 1


def _write_fm(path, fm, body=""):
    text = "---\n" + yaml.dump(fm, default_flow_style=False, sort_keys=False) + "---\n" + body
    path.write_text(text)


def _render_index():
    render = ROOT / "tools" / "render_index.py"
    if render.exists():
        import subprocess
        subprocess.run([sys.executable, str(render)], check=False)


def cmd_new(args):
    exps = _load_all()
    n = _next_num(exps)
    slug = args.slug.replace(" ", "_").lower()
    fname = f"exp_{n:02d}_{slug}.md"
    path = EXP_DIR / fname
    fm = {
        "exp": n,
        "title": args.slug,
        "status": "planned",
        "date": str(date.today()),
        "tags": [],
    }
    body = f"\n# Exp {n} — {args.slug}\n\n**Goal**: \n\n**Method**: \n\n**Results**: \n\n**Takeaway**: \n"
    _write_fm(path, fm, body)
    print(f"Created {path.relative_to(ROOT)} (status=planned)")


def cmd_update(args):
    exps = _load_all()
    n = args.n
    if n not in exps:
        sys.exit(f"exp_{n} not found.")
    path, fm = exps[n]
    body = FM_RE.sub("", path.read_text())

    updates = {}
    if args.status:
        updates["status"] = args.status
    if args.outcome:
        updates["outcome"] = args.outcome
    if args.takeaway:
        updates["takeaway"] = args.takeaway
    if args.track:
        updates["track"] = args.track
    if args.metric:
        k, v = args.metric.split("=", 1)
        try:
            v = float(v)
        except ValueError:
            pass
        updates["metric"] = {k: v}
    if args.parent is not None:
        if args.parent not in exps:
            sys.exit(f"Parent exp_{args.parent} does not exist.")
        if exps[args.parent][1].get("status") == "superseded":
            sys.exit(f"Parent exp_{args.parent} is superseded — dangling lineage.")
        updates["parent"] = args.parent
    if args.tags:
        updates["tags"] = [t.strip() for t in args.tags.split(",")]

    # Validate
    new_status = updates.get("status", fm.get("status"))
    new_outcome = updates.get("outcome", fm.get("outcome"))
    if new_status in ("done", "failed") and not updates.get("outcome", fm.get("outcome")):
        sys.exit("--status=done|failed requires --outcome.")
    if new_status in ("done", "failed") and not updates.get("takeaway", fm.get("takeaway")):
        sys.exit("--status=done|failed requires --takeaway.")
    if new_outcome in ("improved", "parity", "regression"):
        if not updates.get("track", fm.get("track")):
            sys.exit(f"--outcome={new_outcome} requires --track.")
        if not updates.get("metric", fm.get("metric")):
            sys.exit(f"--outcome={new_outcome} requires --metric.")

    old_status = fm.get("status")
    fm.update(updates)
    _write_fm(path, fm, body)
    print(f"Updated exp_{n} (status: {old_status} → {fm['status']}).")
    _render_index()


def cmd_show(args):
    exps = _load_all()
    n = args.n
    if n not in exps:
        sys.exit(f"exp_{n} not found.")
    _, fm = exps[n]
    parts = [f"exp: {fm['exp']}  status: {fm.get('status','')}"]
    if fm.get("outcome"):
        parts.append(f"outcome: {fm['outcome']}")
    if fm.get("metric"):
        parts.append(f"metric: {fm['metric']}")
    if fm.get("track"):
        parts.append(f"track: {fm['track']}")
    if fm.get("parent"):
        parts.append(f"parent: {fm['parent']}")
    if fm.get("takeaway"):
        parts.append(f"takeaway: {fm['takeaway']}")
    if fm.get("tags"):
        parts.append(f"tags: {', '.join(fm['tags'])}")
    print("  ".join(parts))


def cmd_list(args):
    exps = _load_all()
    for n, (_, fm) in sorted(exps.items()):
        if args.tag and args.tag not in fm.get("tags", []):
            continue
        if args.status and fm.get("status") != args.status:
            continue
        if args.outcome and fm.get("outcome") != args.outcome:
            continue
        metric = fm.get("metric", "")
        if metric and isinstance(metric, dict):
            metric = ", ".join(f"{k}={v}" for k, v in metric.items())
        takeaway = fm.get("takeaway", "")
        if takeaway and len(takeaway) > 60:
            takeaway = takeaway[:57] + "..."
        print(f"{n:3d}  {fm.get('status',''):10s}  {fm.get('outcome',''):12s}  {metric:15s}  {takeaway}")


def cmd_lineage(args):
    exps = _load_all()
    n = args.n
    if n not in exps:
        sys.exit(f"exp_{n} not found.")

    chain = [n]
    current = n
    while True:
        parent = exps[current][1].get("parent")
        if not parent or parent not in exps:
            break
        chain.append(parent)
        current = parent

    children = defaultdict(list)
    for num, (_, fm) in exps.items():
        if fm.get("parent"):
            children[fm["parent"]].append(num)

    chain_str = " ← ".join(str(x) for x in chain)
    if children.get(n):
        chain_str = chain_str + f" → children: {children[n]}"
    print(chain_str)

    _, fm = exps[n]
    if fm.get("consumes"):
        print(f"consumes: {fm['consumes']}")
    if fm.get("produces"):
        print(f"produces: {fm['produces']}")


def cmd_finding(args):
    exps = _load_all()
    n = args.n
    if n not in exps:
        sys.exit(f"exp_{n} not found.")
    _, fm = exps[n]
    line = f"- **{fm['title']}**: {args.text} — Exp {n}\n"
    if not FINDINGS.exists():
        sys.exit("docs/findings.md not found.")
    content = FINDINGS.read_text()
    marker = "## Positive findings (what works)\n"
    if marker not in content:
        sys.exit("findings.md missing '## Positive findings' section.")
    content = content.replace(marker, marker + "\n" + line)
    FINDINGS.write_text(content)
    print(f"Appended to docs/findings.md.")


def main():
    p = argparse.ArgumentParser(description="Experiment record CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new"); s.add_argument("slug")

    s = sub.add_parser("update"); s.add_argument("n", type=int)
    s.add_argument("--status"); s.add_argument("--outcome")
    s.add_argument("--takeaway"); s.add_argument("--track")
    s.add_argument("--metric"); s.add_argument("--parent", type=int)
    s.add_argument("--tags")

    s = sub.add_parser("show"); s.add_argument("n", type=int)

    s = sub.add_parser("list")
    s.add_argument("--tag"); s.add_argument("--status"); s.add_argument("--outcome")

    s = sub.add_parser("lineage"); s.add_argument("n", type=int)

    s = sub.add_parser("finding"); s.add_argument("n", type=int); s.add_argument("text")

    args = p.parse_args()
    {"new": cmd_new, "update": cmd_update, "show": cmd_show,
     "list": cmd_list, "lineage": cmd_lineage, "finding": cmd_finding}[args.cmd](args)


if __name__ == "__main__":
    main()
