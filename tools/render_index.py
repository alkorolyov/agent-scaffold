#!/usr/bin/env python3
"""Regenerate docs/experiments/INDEX.md from per-exp frontmatter."""
import re
import sys
import yaml
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "docs" / "experiments"
FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def fmt_metric(m):
    if not m:
        return ""
    if isinstance(m, dict):
        return ", ".join(f"{k}={v}" for k, v in m.items())
    return str(m)


def load_exps():
    exps = []
    for p in sorted(EXP_DIR.glob("exp_*.md")):
        m = FM_RE.match(p.read_text())
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        if "exp" not in fm:
            continue
        exps.append(fm)
    exps.sort(key=lambda r: r["exp"])
    return exps


def build_index(exps):
    best_by_track = {}
    for e in exps:
        if e.get("track") and e.get("metric") and e.get("outcome") in ("improved", "parity"):
            v = next(iter(e["metric"].values()), None) if isinstance(e.get("metric"), dict) else None
            if v is None:
                continue
            cur = best_by_track.get(e["track"])
            if cur is None or v > cur[1]:
                best_by_track[e["track"]] = (e, v)

    refuted = [e for e in exps if e.get("outcome") == "refuted"]
    open_inc = [e for e in exps if e.get("status") == "running" or e.get("outcome") == "inconclusive"]
    children = defaultdict(list)
    for e in exps:
        if e.get("parent"):
            children[e["parent"]].append(e["exp"])
    roots = [e for e in exps if not e.get("parent")]

    out = [
        "# Experiment Index",
        "",
        "_Generated from `docs/experiments/exp_*.md` frontmatter. Do not edit by hand._",
        "_Run `tools/render_index.py` to regenerate._",
        "",
        "## All Experiments",
        "",
        "| # | Title | Status | Outcome | Takeaway | Tags |",
        "|---|-------|--------|---------|----------|------|",
    ]
    for e in exps:
        tags = ", ".join(e.get("tags", []))
        takeaway = e.get("takeaway", "")
        out.append(f"| {e['exp']} | {e['title']} | {e.get('status', '')} | "
                   f"{e.get('outcome', '')} | {takeaway} | {tags} |")

    out += ["", "## Best by Track", "", "| Track | Best Exp | Metric |", "|-------|----------|--------|"]
    for track, (e, _) in sorted(best_by_track.items()):
        out.append(f"| {track} | {e['exp']} | {fmt_metric(e.get('metric'))} |")

    out += ["", "## Refuted Hypotheses (do not re-try)", "", "| # | Takeaway | Date |", "|---|----------|------|"]
    for e in refuted:
        out.append(f"| {e['exp']} | {e.get('takeaway', '')} | {e.get('date', '')} |")

    out += ["", "## Open / Inconclusive", "", "| # | Title | Tags |", "|---|-------|------|"]
    for e in open_inc:
        tags = ", ".join(e.get("tags", []))
        out.append(f"| {e['exp']} | {e['title']} | {tags} |")

    out += ["", "## Lineage Roots", "", "| # | Title | Children |", "|---|-------|----------|"]
    for e in roots:
        kids = ", ".join(map(str, children.get(e["exp"], []))) or "—"
        out.append(f"| {e['exp']} | {e['title']} | {kids} |")

    return "\n".join(out) + "\n"


def main():
    exps = load_exps()
    content = build_index(exps)
    idx = EXP_DIR / "INDEX.md"
    idx.write_text(content)
    n_refuted = sum(1 for e in exps if e.get("outcome") == "refuted")
    print(f"Wrote {idx.relative_to(ROOT)} ({len(exps)} experiments, {n_refuted} refuted).")


if __name__ == "__main__":
    main()
