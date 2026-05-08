#!/usr/bin/env python3
"""Unified record CLI — experiments, ADRs, and more.

rec.py exp new <slug>
rec.py exp update <N> [--status=] [--outcome=] [--takeaway=] [--track=] [--benchmark=]
                      [--metric="auc=0.84±0.02"] [--n-seeds=N] [--parent=N] [--related="N,M,..."]
                      [--wandb=URL] [--mlflow=run_id] [--dois="DOI,DOI"] [--adr=N]
                      [--source-artifacts="path,path"] [--flags="single_seed,large_unexpected_gain,..."]
                      [--tags=]
rec.py exp revise <N> --reason="..." --new-takeaway="..." [--by=user|agent]
rec.py exp show <N>
rec.py exp list [--tag=X] [--status=X] [--outcome=X] [--benchmark=X]
rec.py exp lineage <N>
rec.py exp finding <N> "<text>" [--negative]

rec.py adr new <slug>
rec.py adr update <N> [--status=] [--decision=] [--context=] [--consequences=] [--superseded-by=] [--tags=]
rec.py adr show <N>
rec.py adr list [--status=X]
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
ADR_DIR = ROOT / "docs" / "adrs"
FINDINGS = ROOT / "docs" / "findings.md"
FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


# ── shared utilities ──────────────────────────────────────────────────────────

def _load(directory: Path, kind: str) -> dict:
    """Load all records of a given kind from directory. Returns {N: (path, fm)}."""
    records = {}
    if not directory.exists():
        return records
    for p in sorted(directory.glob(f"{kind}_*.md")):
        m = FM_RE.match(p.read_text())
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        if kind in fm:
            records[fm[kind]] = (p, fm)
    return records


def _next_num(records: dict) -> int:
    return max(records.keys(), default=0) + 1


def _write(path: Path, fm: dict, body: str = "") -> None:
    path.write_text("---\n" + yaml.dump(fm, default_flow_style=False, sort_keys=False) + "---\n" + body)


def _render() -> None:
    render = ROOT / "tools" / "render_index.py"
    if render.exists():
        import subprocess
        subprocess.run([sys.executable, str(render)], check=False)


# ── info ──────────────────────────────────────────────────────────────────────

def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def info(_args=None):
    """Print project layout and agent-scaffold conventions.

    Single source of truth for an agent-scaffold project's directory layout.
    Anything that wants to know "where do experiments live?" should call this
    instead of hardcoding paths. Layout changes happen in this file's
    constants (EXP_DIR, ADR_DIR, FINDINGS) — every consumer follows.
    """
    skills_dir = ROOT / "skills"
    skill_names = sorted(p.parent.name for p in skills_dir.glob("*/SKILL.md")) \
        if skills_dir.exists() else []

    lines = [
        f"agent-scaffold project at {ROOT}",
        "",
        "Records:",
        f"  experiments → {_rel(EXP_DIR)}/   (rec.py exp new <slug>)",
        f"  ADRs        → {_rel(ADR_DIR)}/   (rec.py adr new <slug>)",
        f"  findings    → {_rel(FINDINGS)}",
        "",
        "Indexes (recall tier — load on session start):",
        f"  {_rel(EXP_DIR / 'INDEX.md')}",
        f"  {_rel(ADR_DIR / 'INDEX.md')}",
        "",
    ]
    if skill_names:
        lines.append("Project skills:")
        for s in skill_names:
            lines.append(f"  /{s}")
        lines.append("")
    lines.extend([
        "Rules:",
        "  - NEVER hand-author exp_*.md or adr_*.md. Use rec.py; INDEX.md is generated.",
        "  - Treat INDEX.md takeaways as summaries — re-read source artifacts in",
        "    data/experiments/exp_NN_*/ before propagating any conclusion.",
        "  - Use outcome='infra' for infrastructure runs (fleet tests, smoke tests,",
        "    benchmarks of the platform itself).",
        "",
        "Reference: ~/projects/personal/agent-scaffold/design.md",
    ])
    print("\n".join(lines))


# ── exp commands ──────────────────────────────────────────────────────────────

EXP_OUTCOMES = {"confirmed", "refuted", "improved", "parity", "regression", "infra", "inconclusive"}


def exp_new(args):
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    records = _load(EXP_DIR, "exp")
    n = _next_num(records)
    slug = args.slug.replace(" ", "_").lower()
    path = EXP_DIR / f"exp_{n:02d}_{slug}.md"
    fm = {"exp": n, "title": args.slug, "status": "planned", "date": str(date.today()), "tags": []}
    body = f"\n# Exp {n} — {args.slug}\n\n**Goal**: \n\n**Method**: \n\n**Results**: \n\n**Takeaway**: \n"
    _write(path, fm, body)
    print(f"Created {path.relative_to(ROOT)} (status=planned)")


def exp_update(args):
    records = _load(EXP_DIR, "exp")
    if args.n not in records:
        sys.exit(f"exp_{args.n} not found.")
    path, fm = records[args.n]
    body = FM_RE.sub("", path.read_text())

    updates = {}
    if args.status:
        updates["status"] = args.status
    if args.outcome:
        if args.outcome not in EXP_OUTCOMES:
            sys.exit(f"--outcome must be one of: {', '.join(sorted(EXP_OUTCOMES))}")
        updates["outcome"] = args.outcome
    if args.takeaway:
        updates["takeaway"] = args.takeaway
    if args.track:
        updates["track"] = args.track
    if args.benchmark:
        updates["benchmark"] = args.benchmark
    if args.metric:
        # Accept either "key=val" or "key=val±sd" (the literature-recommended form);
        # multiple comma-separated key=val pairs are also accepted.
        metric_dict = {}
        for piece in args.metric.split(","):
            piece = piece.strip()
            if not piece:
                continue
            k, v = piece.split("=", 1)
            k, v = k.strip(), v.strip()
            sd = None
            for sep in ("±", "+/-", "+-"):
                if sep in v:
                    v, sd = v.split(sep, 1)
                    v, sd = v.strip(), sd.strip()
                    break
            try:
                v = float(v)
            except ValueError:
                pass
            metric_dict[k] = v
            if sd is not None:
                try:
                    sd = float(sd)
                except ValueError:
                    pass
                metric_dict[f"{k}_sd"] = sd
        updates["metric"] = metric_dict
    if args.parent is not None:
        if args.parent not in records:
            sys.exit(f"Parent exp_{args.parent} does not exist.")
        if records[args.parent][1].get("status") == "superseded":
            sys.exit(f"Parent exp_{args.parent} is superseded — dangling lineage.")
        updates["parent"] = args.parent
    if args.related:
        related = []
        for tok in args.related.split(","):
            tok = tok.strip()
            if not tok:
                continue
            try:
                n = int(tok)
            except ValueError:
                sys.exit(f"--related: '{tok}' is not an integer experiment number.")
            if n == args.n:
                sys.exit(f"--related cannot include self (exp_{n}).")
            if n not in records:
                sys.exit(f"--related: exp_{n} does not exist.")
            related.append(n)
        updates["related"] = sorted(set(related))
    if args.wandb:
        updates["wandb_run"] = args.wandb
    if args.mlflow:
        updates["mlflow_run"] = args.mlflow
    if args.dois:
        updates["paper_dois"] = [d.strip() for d in args.dois.split(",") if d.strip()]
    if args.adr is not None:
        updates["adr"] = args.adr
    if args.n_seeds is not None:
        updates["n_seeds"] = args.n_seeds
    if args.source_artifacts:
        updates["source_artifacts"] = [s.strip() for s in args.source_artifacts.split(",") if s.strip()]
    if args.flags:
        valid_flags = {"single_seed", "large_unexpected_gain", "conflicts_prior",
                       "setup_unverified", "interpretation_uncertain"}
        flags = [f.strip() for f in args.flags.split(",") if f.strip()]
        for f in flags:
            if f not in valid_flags:
                sys.exit(f"--flags: '{f}' not recognized. Valid: {sorted(valid_flags)}")
        updates["flags"] = sorted(set(flags))
    if args.tags:
        updates["tags"] = [t.strip() for t in args.tags.split(",")]

    new_status = updates.get("status", fm.get("status"))
    new_outcome = updates.get("outcome", fm.get("outcome"))
    if new_status in ("done", "failed") and not (updates.get("outcome") or fm.get("outcome")):
        sys.exit("--status=done|failed requires --outcome.")
    if new_status in ("done", "failed") and not (updates.get("takeaway") or fm.get("takeaway")):
        sys.exit("--status=done|failed requires --takeaway.")
    if new_outcome in ("improved", "parity", "regression"):
        if not (updates.get("track") or fm.get("track")):
            sys.exit(f"--outcome={new_outcome} requires --track.")
        if not (updates.get("metric") or fm.get("metric")):
            sys.exit(f"--outcome={new_outcome} requires --metric.")

    old_status = fm.get("status")
    fm.update(updates)
    _write(path, fm, body)
    print(f"Updated exp_{args.n} (status: {old_status} → {fm['status']}).")
    _render()


def exp_revise(args):
    """Append-only correction: don't lose the original takeaway, capture why it changed."""
    records = _load(EXP_DIR, "exp")
    if args.n not in records:
        sys.exit(f"exp_{args.n} not found.")
    path, fm = records[args.n]
    body = FM_RE.sub("", path.read_text())
    previous = fm.get("takeaway") or ""
    if not previous:
        sys.exit(f"exp_{args.n} has no takeaway to revise. Use 'rec.py exp update' first.")
    if args.new_takeaway.strip() == previous.strip():
        sys.exit("--new-takeaway is identical to the existing takeaway.")
    revisions = list(fm.get("revisions") or [])
    revisions.append({
        "date": str(date.today()),
        "by": args.by,
        "reason": args.reason,
        "previous_takeaway": previous,
        "new_takeaway": args.new_takeaway,
    })
    fm["revisions"] = revisions
    fm["takeaway"] = args.new_takeaway
    _write(path, fm, body)
    print(f"Revised exp_{args.n} takeaway. {len(revisions)} revision(s) on record.")
    _render()


def exp_show(args):
    records = _load(EXP_DIR, "exp")
    if args.n not in records:
        sys.exit(f"exp_{args.n} not found.")
    _, fm = records[args.n]
    parts = [f"exp: {fm['exp']}  status: {fm.get('status', '')}"]
    for field in ("outcome", "metric", "n_seeds", "track", "benchmark", "parent", "related",
                  "wandb_run", "mlflow_run", "paper_dois", "adr",
                  "source_artifacts", "flags", "takeaway", "tags"):
        if fm.get(field):
            v = ", ".join(str(x) for x in fm[field]) if isinstance(fm[field], list) else fm[field]
            parts.append(f"{field}: {v}")
    if fm.get("revisions"):
        parts.append(f"revisions: {len(fm['revisions'])} (latest: {fm['revisions'][-1].get('date', '?')})")
    print("  ".join(parts))


def exp_list(args):
    records = _load(EXP_DIR, "exp")
    for n, (_, fm) in sorted(records.items()):
        if args.tag and args.tag not in fm.get("tags", []):
            continue
        if args.status and fm.get("status") != args.status:
            continue
        if args.outcome and fm.get("outcome") != args.outcome:
            continue
        if args.benchmark and fm.get("benchmark") != args.benchmark:
            continue
        metric = fm.get("metric", "")
        if metric and isinstance(metric, dict):
            metric = ", ".join(f"{k}={v}" for k, v in metric.items())
        takeaway = (fm.get("takeaway") or "")[:60]
        print(f"{n:3d}  {fm.get('status', ''):10s}  {fm.get('outcome', ''):12s}  {str(metric):15s}  {takeaway}")


def exp_lineage(args):
    records = _load(EXP_DIR, "exp")
    if args.n not in records:
        sys.exit(f"exp_{args.n} not found.")
    chain = [args.n]
    current = args.n
    while True:
        parent = records[current][1].get("parent")
        if not parent or parent not in records:
            break
        chain.append(parent)
        current = parent
    children = defaultdict(list)
    for num, (_, fm) in records.items():
        if fm.get("parent"):
            children[fm["parent"]].append(num)
    chain_str = " ← ".join(str(x) for x in chain)
    if children.get(args.n):
        chain_str += f" → children: {children[args.n]}"
    print(chain_str)
    _, fm = records[args.n]
    if fm.get("consumes"):
        print(f"consumes: {fm['consumes']}")
    if fm.get("produces"):
        print(f"produces: {fm['produces']}")


def exp_finding(args):
    records = _load(EXP_DIR, "exp")
    if args.n not in records:
        sys.exit(f"exp_{args.n} not found.")
    _, fm = records[args.n]
    if not FINDINGS.exists():
        sys.exit("docs/findings.md not found.")
    content = FINDINGS.read_text()
    section = "## Negative findings (what doesn't work)\n" if args.negative else "## Positive findings (what works)\n"
    if section not in content:
        sys.exit(f"findings.md missing section: {section.strip()}")
    line = f"- **{fm['title']}**: {args.text} — Exp {args.n}\n"
    FINDINGS.write_text(content.replace(section, section + "\n" + line))
    print("Appended to docs/findings.md.")


# ── adr commands ──────────────────────────────────────────────────────────────

ADR_STATUSES = {"proposed", "accepted", "superseded"}


def adr_new(args):
    ADR_DIR.mkdir(parents=True, exist_ok=True)
    records = _load(ADR_DIR, "adr")
    n = _next_num(records)
    slug = args.slug.replace(" ", "_").lower()
    path = ADR_DIR / f"adr_{n:02d}_{slug}.md"
    fm = {"adr": n, "title": args.slug, "status": "proposed", "date": str(date.today()), "tags": []}
    body = (f"\n# ADR {n} — {args.slug}\n\n"
            f"**Context**: \n\n**Decision**: \n\n**Consequences**: \n")
    _write(path, fm, body)
    print(f"Created {path.relative_to(ROOT)} (status=proposed)")


def adr_update(args):
    records = _load(ADR_DIR, "adr")
    if args.n not in records:
        sys.exit(f"adr_{args.n} not found.")
    path, fm = records[args.n]
    body = FM_RE.sub("", path.read_text())

    updates = {}
    if args.status:
        if args.status not in ADR_STATUSES:
            sys.exit(f"--status must be one of: {', '.join(sorted(ADR_STATUSES))}")
        updates["status"] = args.status
    if args.superseded_by is not None:
        if args.superseded_by not in records:
            sys.exit(f"adr_{args.superseded_by} does not exist.")
        updates["superseded_by"] = args.superseded_by
    if args.decision:
        updates["decision"] = args.decision
    if args.context:
        updates["context"] = args.context
    if args.consequences:
        updates["consequences"] = args.consequences
    if args.tags:
        updates["tags"] = [t.strip() for t in args.tags.split(",")]

    new_status = updates.get("status", fm.get("status"))
    if new_status == "superseded" and not (updates.get("superseded_by") or fm.get("superseded_by")):
        sys.exit("--status=superseded requires --superseded-by.")

    old_status = fm.get("status")
    fm.update(updates)
    _write(path, fm, body)
    print(f"Updated adr_{args.n} (status: {old_status} → {fm['status']}).")
    _render()


def adr_show(args):
    records = _load(ADR_DIR, "adr")
    if args.n not in records:
        sys.exit(f"adr_{args.n} not found.")
    _, fm = records[args.n]
    print(f"adr: {fm['adr']}  status: {fm.get('status', '')}  title: {fm.get('title', '')}")
    for field in ("decision", "context", "consequences", "superseded_by", "tags"):
        if fm.get(field):
            v = ", ".join(str(x) for x in fm[field]) if isinstance(fm[field], list) else fm[field]
            print(f"{field}: {v}")


def adr_list(args):
    records = _load(ADR_DIR, "adr")
    for n, (_, fm) in sorted(records.items()):
        if args.status and fm.get("status") != args.status:
            continue
        decision = (fm.get("decision") or "")[:55]
        sb = f" → adr_{fm['superseded_by']}" if fm.get("superseded_by") else ""
        print(f"{n:3d}  {fm.get('status', ''):10s}  {fm.get('title', ''):30s}  {decision}{sb}")


# ── dispatch ──────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Unified record CLI")
    kind_sub = p.add_subparsers(dest="kind", required=True)

    # exp
    exp_p = kind_sub.add_parser("exp", help="Experiment records")
    exp_sub = exp_p.add_subparsers(dest="cmd", required=True)

    s = exp_sub.add_parser("new"); s.add_argument("slug")

    s = exp_sub.add_parser("update"); s.add_argument("n", type=int)
    s.add_argument("--status"); s.add_argument("--outcome"); s.add_argument("--takeaway")
    s.add_argument("--track"); s.add_argument("--benchmark")
    s.add_argument("--metric", help='key=val or key=val±sd; "auc=0.84±0.02" stores auc + auc_sd')
    s.add_argument("--n-seeds", type=int, dest="n_seeds",
                   help="Number of seeds aggregated. n_seeds=1 auto-flags single_seed.")
    s.add_argument("--parent", type=int)
    s.add_argument("--related", help="Comma-separated exp numbers, e.g. '3,7,12'")
    s.add_argument("--wandb",  help="W&B run URL or run_id")
    s.add_argument("--mlflow", help="MLFlow run_id")
    s.add_argument("--dois",   help="Comma-separated DOIs of motivating papers")
    s.add_argument("--adr",    type=int, help="Related ADR number")
    s.add_argument("--source-artifacts", dest="source_artifacts",
                   help="Comma-separated paths the takeaway depends on (FAIR R1.2 provenance)")
    s.add_argument("--flags",
                   help="Comma-separated review flags. Allowed: single_seed, large_unexpected_gain, "
                        "conflicts_prior, setup_unverified, interpretation_uncertain")
    s.add_argument("--tags")

    s = exp_sub.add_parser("revise", help="Append a correction to an existing takeaway (FAIR-style errata)")
    s.add_argument("n", type=int)
    s.add_argument("--reason", required=True, help="Why the previous takeaway was wrong/incomplete")
    s.add_argument("--new-takeaway", dest="new_takeaway", required=True,
                   help="Replacement takeaway. Original is preserved in revisions log.")
    s.add_argument("--by", default="user", choices=("user", "agent"),
                   help="Who authored the revision (default: user)")

    s = exp_sub.add_parser("show"); s.add_argument("n", type=int)

    s = exp_sub.add_parser("list")
    s.add_argument("--tag"); s.add_argument("--status"); s.add_argument("--outcome")
    s.add_argument("--benchmark")

    s = exp_sub.add_parser("lineage"); s.add_argument("n", type=int)

    s = exp_sub.add_parser("finding"); s.add_argument("n", type=int); s.add_argument("text")
    s.add_argument("--negative", action="store_true", help="Append to negative findings section")

    # adr
    adr_p = kind_sub.add_parser("adr", help="Architecture Decision Records")
    adr_sub = adr_p.add_subparsers(dest="cmd", required=True)

    s = adr_sub.add_parser("new"); s.add_argument("slug")

    s = adr_sub.add_parser("update"); s.add_argument("n", type=int)
    s.add_argument("--status"); s.add_argument("--superseded-by", type=int, dest="superseded_by")
    s.add_argument("--decision"); s.add_argument("--context"); s.add_argument("--consequences")
    s.add_argument("--tags")

    s = adr_sub.add_parser("show"); s.add_argument("n", type=int)
    s = adr_sub.add_parser("list"); s.add_argument("--status")

    # info — print layout + conventions; no subcommand
    kind_sub.add_parser("info", help="Print project layout and agent-scaffold conventions")

    args = p.parse_args()
    if args.kind == "info":
        info(args)
        return
    {
        ("exp", "new"): exp_new,
        ("exp", "update"): exp_update,
        ("exp", "revise"): exp_revise,
        ("exp", "show"): exp_show,
        ("exp", "list"): exp_list,
        ("exp", "lineage"): exp_lineage,
        ("exp", "finding"): exp_finding,
        ("adr", "new"): adr_new,
        ("adr", "update"): adr_update,
        ("adr", "show"): adr_show,
        ("adr", "list"): adr_list,
    }[(args.kind, args.cmd)](args)


if __name__ == "__main__":
    main()
