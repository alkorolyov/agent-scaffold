# Agent-Scaffold Rules (auto-loaded)

Source: `~/agent-scaffold/design.md`. This file is **enforcement** (tight, hot-loaded); design.md is **rationale** (long, on-demand). When updating these rules, update the relevant `design.md` section in the same change.

## File ownership (what content belongs where)

- `docs/experiments/exp_NN_*.md` — results of THAT experiment only. **No forward-looking sections, no "v2 plan", no action items, no "next up", no "Status: planned, next".** A multi-intervention sprint is multiple exp numbers, each with its own file. Same rule for ADRs: per-ADR file = one decision, never a roadmap.
- `docs/progress.md` — active sprint planning only. Canonical sections: `## Current`, `## Next Steps`, `## Action Items` (table with `# | Item | Status | Notes`), `## Open Questions`, `## Timeline`, `## Recent Sprints` (last 2–3 only). **Forward-looking work belongs in the `Action Items` table**, not as ad-hoc bullet lists. **Never** an experiment status table — status lives in per-exp frontmatter. **Never** duplicate per-exp results here — link to `docs/experiments/exp_NN_*.md` and let frontmatter speak.
- `docs/findings.md` — append-only, curated positive + negative findings. Never delete; supersede via `## Superseded findings` section + link.
- `docs/experiments/INDEX.md`, `docs/adrs/INDEX.md` — generated. **Never hand-edit.** Edit `tools/render_index.py` to change schema.
- `CLAUDE.md` — TOC + Quick Reference, not a textbook.

## Hard rules (do not violate)

- **NEVER hand-author files matching `exp_*.md` or `adr_*.md`.** Use `tools/rec.py exp new <slug>` / `tools/rec.py adr new <slug>` (or `/log-exp` / `/log-adr` skills) so frontmatter is correct and INDEX regenerates. After edits, run `tools/render_index.py`.
- Experiment status lives in per-exp frontmatter only — never duplicated in CLAUDE.md or progress.md.
- Findings are append-only. Overturned findings move to `## Superseded findings`, never deleted.
- Infrastructure runs (fleet tests, smoke benchmarks, platform validation) use `outcome: infra`.
- ADR `status: superseded` requires `superseded_by: N`.
- No AI traces in committed code, comments, commit messages, or `Co-Authored-By:` trailers.
- **Experiment artifacts live in `data/experiments/exp_NN_*/`** (paired with `docs/experiments/exp_NN_*.md`). Versioned runs: `data/experiments/exp_NN_*/vK/`. The data dir holds raw outputs (CSVs, JSON, model weights, serialized systems); the doc holds the write-up. They share the slug.
- **Experiment stdout MUST redirect to `data/experiments/exp_NN_*/run.log` (or `vK/run.log`). NEVER `/tmp/`** — applies to bench scripts of any duration, regardless of whether the process was launched with `nohup`, trailing `&`, Bash `run_in_background`, or Monitor. The test is "is this a script I'd cite as an exp artifact?", not "is this long-running?". `/tmp/` logs disappear and aren't reproducible; exp logs must live next to the data they describe.
- **Defer `rec.py exp new` until design is locked.** Do not scaffold an exp record while methodology, scope, grid, or success criteria are still under discussion. The slug becomes effectively immutable once the file + data dir exist (rename touches the doc, the data tree, INDEX, lineage links, and any in-flight log paths). Signal that scaffolding is safe: user said "go" / "yes" with no further design questions outstanding. Prefer **method/deliverable-anchored slugs** (`n_workers_scaling_sweep`, `tune_n_workers_postrefactor`) over **hypothesis-anchored slugs** (`paste_coords_e2e_validation`) — when scope shifts during execution (and it does), method-anchored names stay accurate while hypothesis-anchored ones drift.
- **Code lives in 3 tiers, separated by lifecycle.** `src/<package>/` = importable library (functions/classes, no I/O orchestration); `scripts/` = production CLIs (rerun on schedule or by 2+ exps); `experiments/exp_NN_<slug>.py` = per-exp code (one-off, closed when the exp is done). Reports/decks/slide builders go in `reports/`, not in `experiments/`. Code reused by 2+ exps OR rerun on a schedule MUST live in `src/` or `scripts/` — not be copy-pasted across exp dirs. **When you find yourself copying a `.py` from one exp to another, promote it before the second copy.**
- **Single-file experiment rule.** An experiment is a singular hypothesis trial, not a mini-project. Default: `experiments/exp_NN_<slug>.py` (one file). A subdirectory `experiments/exp_NN_<slug>/` with multiple `.py` files is a smell — usually 1 file is the actual experiment and the rest are library code (promote to `src/`), post-processing (move to `scripts/`), or deliverables (move to `reports/`). Subdir is permitted only when (a) the exp genuinely has multiple stages with intermediate state too coupled to split AND (b) the rationale is documented in the exp doc's Method section. Otherwise: split out the reusable parts and keep the experiment in one file.

## Read-time defense (treat retrieved summaries as summaries, not data)

When loading an entry from `INDEX.md`, `findings.md`, or any frontmatter `takeaway:` field, **before**:
- proposing new work that builds on its conclusion,
- citing it in external content (Confluence / report / paper / Slack),
- rejecting a hypothesis as "already refuted",
- recommending a parameter setting based on a prior best,

re-read the underlying `data/experiments/exp_NN_*/` artifacts (or `docs/kb/literature/raw/<slug>.{pdf,txt}` for literature). Check `flags:` for review markers (`single_seed`, `large_unexpected_gain`, `conflicts_prior`, `setup_unverified`, `interpretation_uncertain`) and `revisions:` for known correction history. **The takeaway is an index; the data dir is the truth.**

## Write-up protocol (drafting external content)

Re-read source artifacts. **Do not trust the markdown alone.** Verify every quoted number against the data dir, not the takeaway field. Verify metric definitions (split, subset, seed) against run config. If markdown disagrees with data: fix the markdown via `rec.py exp revise` (never silent edit) and tell the user what changed before continuing the draft.

Full protocol: `protocols/write_up.md`.

## Presentations

External-facing presentations (Friday reports, status reviews, internal decks) use a **two-step pipeline**:

1. **`slides.md`** — markdown source. Subject to the write-up protocol above: re-read source artifacts, no fabricated metrics, cite exp numbers.
2. **`<topic>.pptx`** — generated mechanically from `slides.md`. Regenerable; never the source of truth.

**Artifact directory**: `data/presentations/<YYYY-MM-DD>_<topic-or-audience>/` — holds `slides.md`, the rendered `.pptx`, and any staged figures.

**Untracked**, like `docs/` — both `slides.md` (AI-context, iterated) and `.pptx` (regenerable binary) stay out of git.

**Scope and audience are set by the user, not the agent.** Do not infer which exps to cite or what to omit.

Slide format conventions (breaks, sizing, section template) live in `protocols/write_up.md` (`## Slides / pptx`) or per-project CLAUDE.md.

## Hard size caps

| File | Cap | When over |
|------|-----|-----------|
| `CLAUDE.md` (any tier) | 100 lines | Move detail to `docs/*.md` |
| `docs/progress.md` | 200 lines | Archive completed sprints to `docs/archive/progress_{YYYY-QN}.md` |
| `docs/findings.md` | 300 lines | Move overturned to `## Superseded findings`; archive oldest year |
| `docs/experiments/exp_NN_*.md` | 150 lines | Experiment is multiple — split into new exp number |
| `docs/ai_log.md` | 200 lines | `/promote-ai-log` then archive |
