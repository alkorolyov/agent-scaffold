# Write-Up Protocol

Use when the user asks to draft external-facing content: Confluence page, daily report, paper section, slides outline, status email, README. The KB (experiments + literature) is agent-maintained state read only at this moment for review — so this is when fabrication and drift become user-visible.

## The core rule

**Re-read source artifacts. Do not trust the markdown alone.**

Experiment markdown summaries are written once at exp close. The data dir (`data/experiments/exp_NN/`, run logs, output CSVs) is the actual record of the run. When generating external content:

- Verify every quoted number against the source artifact, not the takeaway field.
- Verify metric definitions (which split, which subset, which seed) against the run config — takeaways drop these qualifiers.
- For literature claims, re-read `docs/kb/literature/raw/<slug>*` (or `<slug>.txt` sidecar) — never reuse summaries verbatim across documents.

The takeaway field is an index. The data dir is the truth. Cite from the data dir.

### Always check the flags and revisions

Before citing any experiment, read its frontmatter:

- **`flags:`** — `single_seed`, `large_unexpected_gain`, `conflicts_prior`, `setup_unverified`, `interpretation_uncertain`. Each flag means the takeaway is provisional. Cite with explicit caveat ("preliminary, single seed") or, if the audience is high-stakes, do not cite at all without re-running.
- **`revisions:`** — if the takeaway has been revised, read the revision history. Both the original error and the correction are informative. Never quote a prior version of a takeaway as if it were current.
- **`source_artifacts:`** — these are the files the takeaway depends on. Open them and verify your quoted numbers come from them.

If the markdown summary disagrees with the underlying data, **fix the markdown via `rec.py exp revise`** (not silent edit) and tell the user what changed before continuing the draft.

## Steps

1. **Identify scope and audience.** What document? For whom (CEO / CTO / paper reviewer / oncall / public)? Audience changes what gets included, what assumptions to skip, what tone to use.
2. **List sources up front.** Before drafting, list:
   - Experiments to cite (`exp_NN`, ...) — load each via `rec.py exp show <N>` to spot the run dir.
   - Papers to cite (`<slug>`, ...) — read the entry first, then the raw source.
   Show this list to the user so they can correct it before the draft is written.
3. **Re-read source artifacts.** For each cited experiment, open its `data/experiments/exp_NN_*/` (or wherever the run wrote its outputs). Verify every quantitative claim you intend to use against the actual files. For each cited paper, open `raw/<slug>.pdf` (or `<slug>.txt` sidecar) and verify the claim is in the source.
4. **Flag drift.** If the experiment markdown summary disagrees with the underlying data, fix the markdown (`rec.py exp update`, then `tools/render_index.py`) and tell the user what changed before continuing the draft. Drift discovered at write-up time is the single most common silent failure of an agent-maintained KB.
5. **Draft from sources.** Write the document. Cite experiment numbers and DOIs explicitly so the user can spot-check. Match metric qualifiers exactly (split, seed, benchmark version) — never round, never extrapolate.
6. **Hand off for review.** The user reviews. Iterate. Do not commit, post, send, or otherwise publish without explicit user approval.

## Literature is consulted here, not during experiments

Literature KB has rare access patterns: project kickoff, sprint planning, and write-up. Daily experiment work does not trigger lit KB reads. So the write-up step is the primary moment when `/find-kb` (or grep) gets used. Plan for it: when an experiment was originally motivated by a paper, surface that link only at write-up time, not as a per-experiment cross-reference.

## Memory-tier interaction

Write-up draws across all three tiers in `protocols/memory_tiers.md`:

- **Working** (CLAUDE.md, progress.md): scope, audience, deadlines.
- **Recall** (INDEX.md, findings.md, ADR INDEX): what exists worth citing.
- **Archival** (per-exp markdown, raw papers, **and `data/experiments/exp_NN/` artifacts**): the truth being cited.

Write-up is the one moment the agent loads archival content systematically — and the one moment fabricated drift becomes user-visible. Treat it as the verification gate.

## Slides / pptx (two-step)

Presentation drafts (Friday reports, internal decks, status reviews) use a two-step pipeline so the write-up protocol applies cleanly to the markdown step:

1. **Draft `slides.md`** — markdown source under `data/presentations/<YYYY-MM-DD>_<topic-or-audience>/`. Apply the protocol above: re-read source artifacts, verify every metric against the data dir, flag drift, cite exp numbers explicitly. The user selects scope and audience — do not infer.
2. **Render `<topic>.pptx`** — mechanical conversion from `slides.md` (e.g. `python-pptx`, pandoc). No new content introduced at this step. The pptx is regenerable; the markdown is the only source of truth worth diffing.

**Untracked**: the presentations dir is AI-context (like `docs/`). Do not stage `slides.md` or `.pptx` to git.

**Figures**: source from `data/experiments/exp_NN_*/plots/` (or wherever the exp wrote them). Stage copies into the presentation dir if the slide layout requires resizing/cropping — do not edit exp plots in place.

<!-- Project-specific slide format conventions (slide breaks, sizing, section template, audience tone) belong here or in the project's CLAUDE.md. -->

## What this protocol does NOT do

- It does not generate Confluence/Jira/Slack posts directly. Drafts go to the user for review first.
- It does not modify the source artifacts (data dirs, raw papers). If a number is wrong in a data dir, raise it — do not silently rewrite output files.
- It does not invent citations. If a claim has no source in either the exp KB or the lit KB, either (a) drop it, or (b) tell the user it needs new evidence and offer to scaffold an experiment or fetch a paper.
