#!/usr/bin/env python3
"""Regenerate docs/experiments/INDEX.md and docs/adrs/INDEX.md from frontmatter."""
import re
import yaml
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "docs" / "experiments"
ADR_DIR = ROOT / "docs" / "adrs"
FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def fmt_metric(m):
    if not m:
        return ""
    if isinstance(m, dict):
        # Pair "<k>" with "<k>_sd" and render as "k=v±sd"; keep solo keys plain.
        parts = []
        seen = set()
        for k, v in m.items():
            if k.endswith("_sd") or k in seen:
                continue
            sd = m.get(f"{k}_sd")
            if sd is not None:
                parts.append(f"{k}={v}±{sd}")
                seen.add(f"{k}_sd")
            else:
                parts.append(f"{k}={v}")
            seen.add(k)
        return ", ".join(parts)
    return str(m)


def load_kind(directory, kind):
    records = []
    if not directory.exists():
        return records
    for p in sorted(directory.glob(f"{kind}_*.md")):
        m = FM_RE.match(p.read_text())
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        if kind in fm:
            records.append(fm)
    records.sort(key=lambda r: r[kind])
    return records


def build_exp_index(exps):
    # Auto-flag rule: n_seeds==1 implies single_seed (rule-based, not vibes-based).
    # Verbalized confidence is empirically miscalibrated (UQ Survey 2503.15850), so we
    # use deterministic flags instead of asking the agent to self-rate.
    for e in exps:
        if e.get("n_seeds") == 1:
            flags = list(e.get("flags") or [])
            if "single_seed" not in flags:
                flags.append("single_seed")
                e["flags"] = sorted(set(flags))

    # Best is keyed by (track, benchmark). Splitting on benchmark keeps prior bests
    # visible after a benchmark change instead of being silently shadowed by a newer
    # run on a different evaluation setup.
    best_by_track_bench = {}
    for e in exps:
        if e.get("track") and e.get("metric") and e.get("outcome") in ("improved", "parity"):
            v = next(iter(e["metric"].values()), None) if isinstance(e.get("metric"), dict) else None
            if v is None:
                continue
            key = (e["track"], e.get("benchmark") or "—")
            cur = best_by_track_bench.get(key)
            if cur is None or v > cur[1]:
                best_by_track_bench[key] = (e, v)

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
        out.append(f"| {e['exp']} | {e['title']} | {e.get('status', '')} | "
                   f"{e.get('outcome', '')} | {e.get('takeaway', '')} | {tags} |")

    out += ["", "## Best by Track / Benchmark", "",
            "| Track | Benchmark | Best Exp | Metric | Flags |",
            "|-------|-----------|----------|--------|-------|"]
    for (track, bench), (e, _) in sorted(best_by_track_bench.items()):
        flags = ", ".join(e.get("flags") or []) or "—"
        out.append(f"| {track} | {bench} | {e['exp']} | {fmt_metric(e.get('metric'))} | {flags} |")

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

    related_rows = [e for e in exps if e.get("related")]
    if related_rows:
        out += ["", "## Related Networks", "",
                "_Non-parent links — same-topic, contrasting-method, or shared-component experiments._",
                "", "| # | Title | Related to |", "|---|-------|------------|"]
        for e in related_rows:
            rel = ", ".join(map(str, e["related"]))
            out.append(f"| {e['exp']} | {e['title']} | {rel} |")

    ext_rows = [e for e in exps if any(e.get(f) for f in
                ("wandb_run", "mlflow_run", "paper_dois", "adr"))]
    if ext_rows:
        out += ["", "## External Pointers", "",
                "_Where to follow when the markdown isn't enough — telemetry, decisions, motivating papers._",
                "", "| # | W&B | MLFlow | DOIs | ADR |",
                "|---|-----|--------|------|-----|"]
        for e in ext_rows:
            wb = e.get("wandb_run") or "—"
            mlf = e.get("mlflow_run") or "—"
            dois = ", ".join(e["paper_dois"]) if e.get("paper_dois") else "—"
            adr = f"adr_{e['adr']}" if e.get("adr") else "—"
            out.append(f"| {e['exp']} | {wb} | {mlf} | {dois} | {adr} |")

    review_rows = [e for e in exps if e.get("flags")]
    if review_rows:
        out += ["", "## Needs Review", "",
                "_Experiments with one or more deterministic review flags. Re-verify before propagating "
                "the takeaway into a new experiment, write-up, or refuted-list rejection._",
                "", "| # | Title | Flags | Takeaway |",
                "|---|-------|-------|----------|"]
        for e in review_rows:
            flags = ", ".join(e["flags"])
            out.append(f"| {e['exp']} | {e['title']} | {flags} | {e.get('takeaway', '')} |")

    prov_rows = [e for e in exps if e.get("source_artifacts")]
    if prov_rows:
        out += ["", "## Source Artifacts (provenance)", "",
                "_Per-experiment data files the takeaway is derived from. When an artifact is "
                "found wrong, grep this section to find every dependent claim (FAIR R1.2)._",
                "", "| # | Sources |", "|---|---------|"]
        for e in prov_rows:
            srcs = ", ".join(e["source_artifacts"])
            out.append(f"| {e['exp']} | {srcs} |")

    revised_rows = [e for e in exps if e.get("revisions")]
    if revised_rows:
        # Most recent revisions first, capped at the latest 10 across all experiments.
        all_revs = []
        for e in revised_rows:
            for r in e["revisions"]:
                all_revs.append((r.get("date", ""), e["exp"], e["title"], r))
        all_revs.sort(key=lambda x: x[0], reverse=True)
        out += ["", "## Recent Revisions", "",
                "_Append-only correction log. Original takeaway preserved; reason captures why it was wrong._",
                "", "| Date | # | Title | By | Reason |",
                "|------|---|-------|-----|--------|"]
        for d, n, t, r in all_revs[:10]:
            out.append(f"| {d} | {n} | {t} | {r.get('by', '')} | {r.get('reason', '')} |")

    return "\n".join(out) + "\n"


def build_adr_index(adrs):
    accepted = [a for a in adrs if a.get("status") == "accepted"]
    superseded = [a for a in adrs if a.get("status") == "superseded"]

    out = [
        "# ADR Index",
        "",
        "_Generated from `docs/adrs/adr_*.md` frontmatter. Do not edit by hand._",
        "_Run `tools/render_index.py` to regenerate._",
        "",
        "## All Decisions",
        "",
        "| # | Title | Status | Decision | Tags |",
        "|---|-------|--------|----------|------|",
    ]
    for a in adrs:
        tags = ", ".join(a.get("tags", []))
        status = a.get("status", "")
        if a.get("superseded_by"):
            status += f" → adr_{a['superseded_by']}"
        out.append(f"| {a['adr']} | {a['title']} | {status} | {a.get('decision', '')} | {tags} |")

    if accepted:
        out += ["", "## Active Decisions", "", "| # | Title | Decision |", "|---|-------|----------|"]
        for a in accepted:
            out.append(f"| {a['adr']} | {a['title']} | {a.get('decision', '')} |")

    if superseded:
        out += ["", "## Superseded (history only)", "", "| # | Title | Superseded by |", "|---|-------|--------------|"]
        for a in superseded:
            sb = f"adr_{a['superseded_by']}" if a.get("superseded_by") else "—"
            out.append(f"| {a['adr']} | {a['title']} | {sb} |")

    return "\n".join(out) + "\n"


def main():
    totals = []

    exps = load_kind(EXP_DIR, "exp")
    if exps or EXP_DIR.exists():
        EXP_DIR.mkdir(parents=True, exist_ok=True)
        (EXP_DIR / "INDEX.md").write_text(build_exp_index(exps))
        n_refuted = sum(1 for e in exps if e.get("outcome") == "refuted")
        totals.append(f"{len(exps)} experiments ({n_refuted} refuted)")

    adrs = load_kind(ADR_DIR, "adr")
    if adrs or ADR_DIR.exists():
        ADR_DIR.mkdir(parents=True, exist_ok=True)
        (ADR_DIR / "INDEX.md").write_text(build_adr_index(adrs))
        totals.append(f"{len(adrs)} ADRs")

    if totals:
        print(f"Rendered: {', '.join(totals)}.")
    else:
        print("Nothing to render (no docs/experiments/ or docs/adrs/ yet).")


if __name__ == "__main__":
    main()
