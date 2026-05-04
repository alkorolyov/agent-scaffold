# ML/Data Science Project Organization Template

A comprehensive prompt for organizing new ML/data science projects with AI-assisted development. Covers directory structure, CLAUDE.md structure, reference documentation, experiment tracking, naming conventions, and operational patterns.

---

## Architecture & Prior Art

This template implements **structured note-taking + a thin vector index for prose** — the canonical hybrid that emerged in 2024–2025 for managing AI-assistant context on long-running technical projects. It is grounded in published practice, not bespoke.

**Pattern named**: Anthropic's [*Effective context engineering for AI agents*](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (2025) identifies three primitives for long-horizon agent work — **compaction**, **structured note-taking**, and **sub-agents**. This template is squarely the *structured note-taking* branch: the agent reads/writes durable structured records (per-exp YAML frontmatter) outside the context window via deterministic CLI tools, instead of accumulating state in the prompt.

**Influences worth borrowing from**:

| Source | What we use |
|--------|-------------|
| [Anthropic — Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Three-pillar frame; "smallest set of high-signal tokens" principle. |
| [Anthropic — long-running Claude](https://www.anthropic.com/research/long-running-Claude) | "Lab notebook" pattern; explicit logging of failed approaches as first-class entries. |
| [HumanLayer — Writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md) | <60-line CLAUDE.md target; progressive disclosure (link, don't inline). |
| [Cursor — Project Rules](https://cursor.com/docs/context/rules) | Many small scoped files with frontmatter beat one monolith. |
| MLflow / W&B / DVC | Experiment-record schema: `id`, `status`, `tags`, `metrics`, `params`, `parent`, `consumes`, `produces`. Lineage is a free DAG when stored as frontmatter. |
| [Manus — Context Engineering for AI Agents](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) | Separate storage from presentation; scope context per call. |

**Anti-pattern we explicitly avoid**: [Cline's "Memory Bank"](https://docs.cline.bot/prompting/cline-memory-bank). 5–6 overlapping markdown files (`activeContext.md`, `progress.md`, `systemPatterns.md`, …) updated in lockstep on a single "update memory bank" command. Same drift and bloat failure modes this template was designed to escape. If a fact lives in two files, it will eventually contradict itself in two files. **One fact, one place.**

**What we deliberately do *not* adopt**:

- Agentic memory frameworks (MemGPT/Letta, mem0, Zep) — they solve "agent learns user preferences from conversation," not "researcher logs authored experiments." Wrong shape.
- Knowledge-graph databases (Graphiti, Neo4j) — overkill below ~500 experiments. With `parent:` / `supersedes:` / `consumes:` in YAML frontmatter, a Python dict already *is* the graph. Revisit if cross-project queries become routine.

---

## AI Configuration Hierarchy

Claude Code loads CLAUDE.md files at three levels, from broadest to most specific. Each level inherits from the parent and can override or extend it:

```
~/.claude/CLAUDE.md                          # Global — applies to ALL projects
  └── ~/projects/{org}/CLAUDE.md             # Organization — shared across org projects
      └── ~/projects/{org}/{project}/CLAUDE.md  # Project — project-specific context
```

### What goes where

| Level | Contents | Examples |
|-------|----------|---------|
| **Global** (`~/.claude/CLAUDE.md`) | Server/workstation setup, shell preferences, cross-project coding standards, git hygiene rules | "Headless server, use SSH tunneling for localhost ports"; "Never commit AI config files"; "Use `python -u` for unbuffered output" |
| **Organization** (`{org}/CLAUDE.md`) | Shared credentials identity, org-wide conventions, cross-project patterns | Git identity (email, username); shared package conventions; org-specific tooling |
| **Project** (`{project}/CLAUDE.md`) | Everything specific to this project: data, models, experiments, terminology, findings | Dataset dimensions; experiment table; key findings; module API; terminology |

**Rules**:
- Global and org CLAUDE.md are **never committed** — they contain environment/identity info
- Project CLAUDE.md is also **never committed** (contains AI-specific context)
- Keep each level focused — don't repeat global rules in project CLAUDE.md

### Auto-Memory vs CLAUDE.md vs docs/

Claude Code also maintains **auto-memory** at `.claude/projects/*/memory/MEMORY.md` — a persistent scratchpad that survives across conversations. Use each layer for its intended purpose:

| Layer | What to store | When it's loaded | Who writes it |
|-------|--------------|------------------|---------------|
| **CLAUDE.md** | Stable project context: structure, conventions, findings, experiment index | Every conversation (automatic) | Human (with AI help) |
| **Auto-memory** (`MEMORY.md`) | Learned patterns, gotchas, debugging insights, user preferences discovered during work | Every conversation (automatic) | AI (during work) |
| **docs/*.md** | Detailed reference: full experiment specs, data catalogs, API docs | On-demand (AI reads when needed) | Human + AI |

**Key distinction**: CLAUDE.md is the **curated truth** — carefully maintained, concise, authoritative. Auto-memory is the **working notebook** — informal, append-heavy, may contain session-specific learnings that become stable patterns over time. Promote confirmed patterns from auto-memory to CLAUDE.md periodically.

---

## Directory Structure

```
project-name/
├── data/
│   ├── raw/                             # Unmodified source data
│   ├── processed/                       # Cleaned/transformed datasets
│   ├── experiments/                     # Per-experiment output directories
│   │   ├── exp{NN}_{name}/             # One dir per experiment (multi-file outputs)
│   │   └── ...
│   ├── models/                          # Saved model checkpoints
│   └── plots/                           # Generated figures
├── docs/                                # AI-context documentation (untracked)
│   ├── progress.md                      # Active sprint planning only (≤200 lines)
│   ├── findings.md                      # Curated key findings (positive + negative)
│   ├── ai_log.md                        # Per-event AI calibration log (errors ❌ / wins ✅)
│   ├── experiments/                     # Experiment records (science + infra runs)
│   │   ├── INDEX.md                     # Generated by tools/render_index.py — DO NOT hand-edit
│   │   └── exp_01_{slug}.md             # YAML frontmatter + body
│   ├── adrs/                            # Architecture Decision Records
│   │   ├── INDEX.md                     # Generated by tools/render_index.py — DO NOT hand-edit
│   │   └── adr_01_{slug}.md             # proposed | accepted | superseded
│   ├── sessions/                        # Per-session QA log (Claude Code session telemetry)
│   │   ├── INDEX.md                     # Generated trends/aggregates
│   │   └── 2026-04-22-{slug}.md         # One file per session
│   ├── ref/                             # Living reference (light frontmatter, hand-edited rarely)
│   │   ├── architecture.md              # Narrative rationale only — ADR-triggered updates
│   │   └── *_generated.md               # On-demand snapshots from tools/snapshot.py (gitignored)
│   ├── kb/                              # Knowledge base: literature, meetings, transcripts
│   │   ├── literature/
│   │   │   ├── raw/                     # Automated ingestion: PDFs + abstract_md (never hand-edited)
│   │   │   └── *.md                     # Processed summaries with frontmatter (one per paper)
│   │   ├── meetings.md
│   │   └── transcripts/
│   ├── archive/                         # Superseded sprints / phases
│   ├── data.md                          # Output file catalog
│   ├── api.md                           # Module API reference (or generated)
│   ├── setup.md                         # Environment/infra setup notes (optional)
│   └── {domain}.md                      # Domain-specific docs as needed
├── tools/                               # CLI tools the AI calls via Bash
│   ├── rec.py                           # new | update | list | show | log (writes records/, ai_log.md)
│   ├── render_index.py                  # Regenerate docs/records/INDEX.md
│   ├── check_drift.py                   # Drift detector (Stop hook)
│   ├── session.py                       # Session telemetry: parse Claude transcript → docs/sessions/
│   └── snapshot.py                      # Generate ref/*_generated.md from code (arch | schema | api)
├── .claude/
│   ├── settings.json                    # Hooks: Stop → session.py end + check_drift.py
│   └── skills/                          # Slash commands the human invokes
│       ├── log-exp/SKILL.md             # /log-exp — guided experiment write-up
│       ├── log-error/SKILL.md           # /log-error — append AI mistake to ai_log.md
│       ├── log-win/SKILL.md             # /log-win
│       ├── sync-records/SKILL.md        # /sync-records — render + drift check
│       ├── promote-ai-log/SKILL.md      # /promote-ai-log — weekly review loop
│       └── snapshot/SKILL.md            # /snapshot arch|schema|api
├── logs/                                # Training framework logs (TensorBoard, CSVLogger)
├── notebooks/                           # Polished, presentable notebooks (numbered)
├── scripts/                             # Experiment scripts (exp_*.py, untracked)
├── tests/                               # Pytest test suite
│   ├── conftest.py
│   └── test_{module}.py
├── src/{package_name}/                  # Installable Python package
│   ├── __init__.py                      # Version only — no re-exports
│   ├── config.py                        # Paths, constants, hardware config
│   ├── data.py
│   ├── models.py
│   ├── training.py
│   ├── features.py
│   └── viz.py
├── environment.yml
├── pyproject.toml
└── CLAUDE.md                            # AI assistant context (untracked, target ~60 lines)
```

### Key Principles

- **`scripts/` is the lab bench**: Rapid, disposable experiment scripts. Untracked in git. Thin wrappers that call `src/` library functions — never duplicate logic in scripts.
- **`notebooks/` is the presentation layer**: Polished, numbered, tracked. Only created after an experiment is validated.
- **`src/` is the reusable library**: Stable, tested code that scripts and notebooks import from. If a function is missing, add it to `src/` first, then import in scripts.
- **`tests/` validates the library**: Pytest suite with markers for slow/integration tests. Fast tests run by default.
- **`docs/` is the AI memory**: Detailed context docs that keep the AI assistant effective across sessions. Untracked. Layered for scale:
  - `docs/experiments/exp_NN_*.md` — one file per experiment (frontmatter-driven, ≤150 lines each). `INDEX.md` is **generated**, never hand-edited.
  - `docs/findings.md` — curated positive + negative findings. The single place new findings get promoted.
  - `docs/kb/` — long-form prose (papers, meeting notes, transcripts). Indexed by a small vector DB for semantic search; never auto-loaded into CLAUDE.md.
  - `docs/archive/` — completed sprints / superseded plans. Grep-able, not loaded.
  - Domain-specific docs (`docking.md`, `scoring.md`) sit at `docs/` root or, once they spawn siblings, get promoted to a directory (`docs/literature/` instead of `literature_a.md`, `literature_b.md`).
- **`data/experiments/` is the output sink**: Each experiment gets its own directory (`exp{NN}_{name}/`). For projects with simple single-file outputs, a flat `data/results/` with prefixed filenames also works.

### Data Directory Variants

Choose the layout that fits your project's output complexity:

**Per-experiment directories** (better for multi-file outputs, large artifacts, docking/simulation):
```
data/experiments/exp28_lgbm_screening/
  ├── results.csv
  ├── model.txt
  └── plots/
```

**Flat results directory** (simpler for single-file outputs, tabular ML):
```
data/results/
  ├── nb09_clusters.csv          # Notebook output (nb prefix)
  ├── 28_lgbm_predictions.csv    # Script output (exp number prefix)
  └── 21_feature_importance.pkl
```

### Workflow

1. **Experiment**: Create `scripts/exp_{NN}_{description}.py` → run → write `docs/experiments/exp_{NN}_{description}.md` (frontmatter + spec + result) → run `tools/render_index.py` to regenerate `docs/experiments/INDEX.md`. Status lives in the per-exp frontmatter — `progress.md` only carries active sprint planning, not the experiment table.
2. **Notebook**: Once validated, create polished notebook in `notebooks/`
3. **Report**: If the result changes understanding, append a one-liner to `docs/findings.md`. CLAUDE.md only links to `findings.md` — never list findings directly there.
4. **Archive**: When `progress.md` exceeds ~200 lines, move completed sprints to `docs/archive/progress_{YYYY-QN}.md`.

### Test Conventions

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "-m 'not slow and not integration'"
markers = [
    "slow: tests >1s or using heavy deps",
    "integration: requires external resources (GPU, Docker, network)",
]
```

- `pytest` — fast unit tests only (default)
- `pytest -m slow` — heavy dependency tests
- `pytest -m integration` — external resource tests
- `pytest -m "slow or not slow"` — everything

### .gitignore Template

```gitignore
# === Working directories (untracked) ===
docs/                    # AI-context documentation
scripts/                 # Experiment scripts (disposable)

# === Data & outputs ===
data/                    # All data (raw, processed, experiments, models)
*.log                    # Experiment run logs
*.db                     # Optuna databases

# === Training framework ===
logs/                    # TensorBoard / CSVLogger
lightning_logs/
wandb/

# === Python ===
__pycache__/
*.egg-info/
dist/
build/

# === Environment ===
.env
```

**Tracked vs untracked**:

| Tracked (committed) | Untracked (gitignored) | Never staged, never .gitignored |
|---------------------|----------------------|---------------------------------|
| `src/` (package code) | `scripts/` (experiment scripts) | `CLAUDE.md`, `.claude/` |
| `notebooks/` (polished notebooks) | `docs/` (AI context docs) | `.mcp.json`, `.cursor/`, `.copilot/` |
| `environment.yml` | `data/` (all data + outputs) | |
| `pyproject.toml` | `*.log`, `*.db` | |
| `tests/` | | |

**Why AI tool files are neither committed nor gitignored**: listing `.claude/` or `CLAUDE.md` in `.gitignore` is itself a committed signal that you use a specific AI tool — it exposes tooling choices to anyone who clones the repo. The low-profile rule: never stage them, never mention them in committed files. Use `.git/info/exclude` locally if you want the noise suppressed in `git status`.

**Why scripts/ is untracked**: Experiment scripts are rapid, disposable, and often contain hardcoded paths or debug code. The reusable logic lives in `src/`. If a script produces a publishable result, the methodology is captured in `docs/experiments.md` and the polished version becomes a notebook.

---

## CLAUDE.md Structure

The CLAUDE.md is the AI assistant's primary context file. It should be comprehensive but scannable, using tables over prose. Structure it as follows:

```markdown
# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## IMPORTANT

{Critical rules: no AI traces in code/commits, don't add CLAUDE.md to git, etc.}

---

## Project Overview

{1-2 sentence project description. Goal statement.}

**Team**: {Name (role), Name (role), ...}

---

## Environment Setup

{Conda/pip commands to get running. Key dependencies list.}

**Import convention**: {How to import from the package — always explicit submodule imports.}

**Deprecated modules/functions** (do NOT use):
- `{old_module}.{old_func}` → use `{new_module}.{new_func}` instead
- `{removed_module}` — removed in favor of `{replacement}`

{Track deprecated code here so the AI never suggests or uses outdated APIs. Remove entries once all references are cleaned up.}

---

## Quick Reference

### Dataset Summary

| Dimension | Value |
|-----------|-------|
| Samples | {N (breakdown by class)} |
| Features | {N} |
| Class balance | {ratio} |
| ... | ... |

### Key Technical Decisions

1. **{Decision}**: {Rationale}
2. **{Decision}**: {Rationale}

---

## Key Findings

Top 3-5 highest-impact findings only (one line each). Full curated list — including negative/dead-end findings — in [docs/findings.md](docs/findings.md).

- **{Finding}**: {one-line summary with numbers}

---

## Experiments

{N} experiments completed. Index in [docs/experiments/INDEX.md](docs/experiments/INDEX.md) (generated). Per-experiment specs in `docs/experiments/exp_NN_*.md`. Active planning in [docs/progress.md](docs/progress.md).

---

## Conventions

### Output File Naming
- Notebook outputs: `nb{NN}_{description}.{ext}` (e.g., `nb09_clusters.csv`)
- Script outputs: `{NN}_{description}.{ext}` (e.g., `21_feature_importance.pkl`) — matches `scripts/exp_{NN}_*.py`

### Model Save/Load
{Code snippet showing the save/load pattern with hyperparameters embedded in checkpoint.}

### Result CSV Conventions
{What columns to always include, ordering conventions, etc.}

---

## Terminology

### {Concept Category} (disambiguation)
- **{Term A}**: {definition + shape/type if relevant}
- **{Term B}**: {definition}
- Never say just "{ambiguous term}" without specifying which one.

### Key Metrics / Sources Table

| Source | Method | Level | Per-sample? | Output File |
|--------|--------|-------|-------------|-------------|
| ... | ... | ... | ... | ... |

---

## Pipeline Modules

| Module | Purpose | Docs |
|--------|---------|------|
| `data.py` | {purpose} | [api.md](docs/api.md) |
| `models.py` | {purpose} | [api.md](docs/api.md) |
| ... | ... | ... |

---

## Detailed Documentation

| Doc | Contents |
|-----|----------|
| [docs/progress.md](docs/progress.md) | Active sprint planning only (≤200 lines) |
| [docs/findings.md](docs/findings.md) | Curated positive + negative findings (the AI memory of what works and what doesn't) |
| [docs/records/INDEX.md](docs/records/INDEX.md) | Generated index of all records (exp / feat / bug / adr) — produced by `tools/render_index.py` |
| [docs/records/](docs/records/) | Per-record files. AI accesses via `tools/rec.py show <id>` / `list`, not by reading the dir |
| [docs/sessions/INDEX.md](docs/sessions/INDEX.md) | AI session QA aggregates — friction trend, cost trend, by-goal-type quality |
| [docs/sessions/](docs/sessions/) | Per-session telemetry (auto-extracted from Claude transcripts via Stop hook) |
| [docs/ai_log.md](docs/ai_log.md) | Per-event AI calibration log (errors / wins). Reviewed weekly, promoted to CLAUDE.md or memory |
| [docs/ref/](docs/ref/) | Living reference — `architecture.md` (narrative, ADR-triggered) + `*_generated.md` (on-demand from `tools/snapshot.py`) |
| [docs/data.md](docs/data.md) | Output file catalog, source data |
| [docs/api.md](docs/api.md) | Module API reference (or generated via `tools/snapshot.py api`) |
| [docs/kb/](docs/kb/) | Literature, meeting notes, transcripts — vector-indexed (see Knowledge Search section) |
| [docs/archive/](docs/archive/) | Superseded sprints / phases — grep-able, not auto-loaded |
| [docs/setup.md](docs/setup.md) | Environment/infra setup (optional, for complex envs) |

### How the AI accesses these (the navigation surface)

CLAUDE.md should not embed content from these docs — it should tell the AI *how to fetch* what it needs:

- Records lookup: `tools/rec.py show <id>` (5 lines), `tools/rec.py list --kind=exp --recent=10`
- Current schema: `tools/snapshot.py schema && cat docs/ref/schema_generated.md`
- Architecture rationale: `Read docs/ref/architecture.md` (narrative only, small)
- Findings: `Read docs/findings.md`
- Past sessions: `Read docs/sessions/INDEX.md` for aggregates; specific session by date
- Log a mistake: `tools/rec.py log --err "<msg>"` (and the AI does this proactively)

---

## Project Structure

{ASCII tree of the directory layout with inline comments.}
```

---

## Reference Documentation Templates

Each `docs/*.md` file serves a specific purpose. All follow common patterns:
- Single H1 title per file
- Opening line states purpose + cross-references a companion file
- Horizontal rules (`---`) between all H2 sections
- Tables as the primary data structure (minimal prose)
- Bold labels (`**Goal**:`, `**Result**:`) for inline subsections instead of deeper header nesting

### docs/progress.md — Active Sprint Planning

`progress.md` is **planning-only**. The experiment table lives in `docs/experiments/INDEX.md` (generated). When this file exceeds ~200 lines, move completed sprints to `docs/archive/progress_{YYYY-QN}.md`.

```markdown
# Progress & Status

Active planning. Experiment index: [experiments/INDEX.md](experiments/INDEX.md). Findings: [findings.md](findings.md).

---

## Current: {Phase/Sprint Name}

{1-2 sentence summary of where things stand.}

### Next Steps

1. {Next priority}
2. {After that}

---

## Action Items ({context/date})

| # | Item | Owner | Status | Notes |
|---|------|-------|--------|-------|
| A1 | {item} | {person} | Done | {notes} |
| A2 | {item} | {person} | Not started | |

---

## Open Questions

- {Question about approach/data/methods}
- {Unresolved technical decision}

## Timeline

- **{Milestone}**: {date or constraint}

---

## Recent Sprints (last 2-3 only — older ones in archive/)

- **Sprint N**: {Name} ({date}) — {one-line outcome}
```

**Conventions**:
- Action item IDs: `A1`, `A2`, etc.
- Experiment status lives in per-exp frontmatter — never duplicated here.
- Hard cap: ~200 lines. Over the cap → archive completed sprints.

### docs/experiments/ — Per-Experiment Files (replaces monolithic experiments.md)

**Why per-file**: A monolithic `experiments.md` grows unboundedly (a real example at 2,929 lines / 167 KB), forces edits in the same file from every experiment (drift risk), and makes the AI load all of it to look up one experiment. Per-file + frontmatter + generated index removes all three problems.

#### Per-experiment file template

`docs/experiments/exp_{NN}_{description}.md`:

```markdown
---
# --- Identity (always required) ---
exp: 28
title: LightGBM baseline screening
status: done                  # planned | running | done | failed | superseded
date: 2026-03-10

# --- Finding (required when status = done | failed) ---
outcome: improved             # confirmed | refuted | improved | parity | regression | infra | inconclusive
takeaway: "LightGBM on epitope-clean features hits 0.853 AUC — new IBD baseline above MLP (0.871)."

# --- Optional, set only when applicable ---
metric: {auc: 0.853, std: 0.012}    # informational; any shape. Free-form.
track: ibd-classification           # opt-in to "Best by Track" — only set when this exp competes for a leaderboard.

# --- Lineage (W&B-style; gives you a free DAG) ---
parent: 21                          # exp this branched from (experimental lineage)
supersedes: []                      # list of exp numbers this definitively replaces
consumes: [data/processed/scaffolds_v3.pkl]
produces: [data/experiments/exp28_lgbm_screening/model.txt]

tags: [lgbm, baseline, screening]
---

# Exp 28 — LightGBM baseline screening

**Goal**: {What hypothesis is being tested, or what's being measured.}

**Data**: {Input description.}

**Method**: {Numbered steps or brief description.}

**Results**:

| Config | {Metric 1} | {Metric 2} | Notes |
|--------|-----------|-----------|-------|
| A | 0.853 | ... | baseline |
| B | **0.871** | ... | + feature X |

**Takeaway**: {One paragraph elaborating the frontmatter `takeaway:`. Bold best result.}

**Outputs**: see frontmatter `produces:` and [data.md](../data.md).
```

**Schema rules** (enforced by `tools/exp.py`):

- `status: done | failed` requires `outcome:` and `takeaway:`.
- `outcome: improved | parity | regression` requires `track:` and `metric:` (the comparison is meaningless without them).
- `outcome: confirmed | refuted | infra | inconclusive` does NOT require `metric:` — hypothesis-validation, infra, and exploratory experiments are first-class.
- `metric:` is free-form (`{auc: 0.94}`, `{auc_range: [0.51, 0.56]}`, `{phase1: ..., phase2: ...}`, or absent). It's informational; only `track + metric` together gate ranking.
- `parent:` points to the single exp this branched from. `supersedes:` lists exps whose conclusions this overturns (set `status: superseded` on those).
- `consumes:` / `produces:` reference file paths. `tools/exp.py lineage <NN>` walks these to show the full DAG of how a result was built.

**Conventions**:

- One file per experiment number. Never reuse a number.
- File ≤ ~150 lines. If longer, the experiment is actually multiple — split it into a new exp number.
- Frontmatter is the **only source of truth** for status, outcome, lineage, and ranking eligibility.
- Bold best result in result tables: `**0.871**`.
- Feature variant naming: `A) {base}`, `B) {base + extra1}`, `C) {base + extra1 + extra2}`.
- Multi-phase experiments: Phase 1 (exploration), Phase 2 (HPO), Phase 3 (final eval) — sections inside one file.
- **Negative results are first-class.** A refuted hypothesis or a confirmed dead-end is as valuable as a new best score — log them with `outcome: refuted` and a clear `takeaway:`. The most expensive AI is the one that re-tries an approach because no one recorded it failing.

#### docs/experiments/INDEX.md (generated)

DO NOT hand-edit. Produced by `tools/render_index.py` from frontmatter. Multiple auto-derived views from the same data:

```markdown
# Experiment Index

_Generated from `docs/experiments/exp_*.md` frontmatter. Do not edit by hand._

## All Experiments

| # | Title | Status | Outcome | Takeaway | Tags |
|---|-------|--------|---------|----------|------|
| 28 | LightGBM baseline screening | done | improved | LightGBM hits 0.853 AUC — new IBD baseline. | lgbm, baseline |
| 29 | GAT continuous features | done | refuted | GAT fails on PD across all configs. | gnn, pd |

## Best by Track

_Only experiments with both `track:` and `metric:` set._

| Track | Best Exp | Metric |
|-------|----------|--------|
| ibd-classification | 114 | auc=0.941 |
| pd-classification  |  35 | auc=0.651 |

## Refuted Hypotheses (do not re-try)

_`outcome: refuted` — the AI's "do not re-try" register._

| # | Takeaway | Date |
|---|----------|------|
| 7 | GAT fails on 1-dim REAP features regardless of pooling. | 2026-01-12 |
| 29 | GAT fails on PD across all configs. | 2026-02-08 |

## Open / Inconclusive

_`outcome: inconclusive` or `status: running` — candidates for follow-up._

| # | Title | Tags |
|---|-------|------|
| 41 | Per-epitope attribute encoding | lgbm, pd |

## Lineage Roots

_Experiments with no `parent:` — entry points to lineage chains._

| # | Title | Children |
|---|-------|----------|
|  1 | Data pipeline verification | 2, 3, 4, ... |
| 17 | Feature enrichment              | 18, 21, 22, ... |
```

#### tools/render_index.py (reference — ~80 lines)

```python
#!/usr/bin/env python
"""Regenerate docs/experiments/INDEX.md from per-exp frontmatter."""
from pathlib import Path
from collections import defaultdict
import re, yaml

EXP_DIR = Path(__file__).resolve().parent.parent / "docs" / "experiments"
FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

def fmt_metric(m):
    if not m: return ""
    return ", ".join(f"{k}={v}" for k, v in m.items())

# --- Load all frontmatter ---
exps = []
for p in sorted(EXP_DIR.glob("exp_*.md")):
    m = FM_RE.match(p.read_text())
    if not m: continue
    fm = yaml.safe_load(m.group(1)) or {}
    exps.append(fm)
exps.sort(key=lambda r: r["exp"])

# --- Build derived views ---
best_by_track = {}
for e in exps:
    if e.get("track") and e.get("metric") and e.get("outcome") in ("improved", "parity"):
        # Pick first metric value as the rank key (or extend if you have a primary-metric convention)
        v = next(iter(e["metric"].values()), None)
        if v is None: continue
        cur = best_by_track.get(e["track"])
        if cur is None or v > cur[1]:
            best_by_track[e["track"]] = (e, v)

refuted   = [e for e in exps if e.get("outcome") == "refuted"]
open_inc  = [e for e in exps if e.get("status") == "running" or e.get("outcome") == "inconclusive"]
children  = defaultdict(list)
for e in exps:
    if e.get("parent"): children[e["parent"]].append(e["exp"])
roots     = [e for e in exps if not e.get("parent")]

# --- Render ---
out = ["# Experiment Index", "",
       "_Generated from `docs/experiments/exp_*.md` frontmatter. Do not edit by hand._", ""]

out += ["## All Experiments", "",
        "| # | Title | Status | Outcome | Takeaway | Tags |",
        "|---|-------|--------|---------|----------|------|"]
for e in exps:
    out.append(f"| {e['exp']} | {e['title']} | {e.get('status','')} | "
               f"{e.get('outcome','')} | {e.get('takeaway','')} | "
               f"{', '.join(e.get('tags', []))} |")

out += ["", "## Best by Track", "",
        "| Track | Best Exp | Metric |", "|-------|----------|--------|"]
for track, (e, _) in sorted(best_by_track.items()):
    out.append(f"| {track} | {e['exp']} | {fmt_metric(e['metric'])} |")

out += ["", "## Refuted Hypotheses (do not re-try)", "",
        "| # | Takeaway | Date |", "|---|----------|------|"]
for e in refuted:
    out.append(f"| {e['exp']} | {e.get('takeaway','')} | {e.get('date','')} |")

out += ["", "## Open / Inconclusive", "",
        "| # | Title | Tags |", "|---|-------|------|"]
for e in open_inc:
    out.append(f"| {e['exp']} | {e['title']} | {', '.join(e.get('tags', []))} |")

out += ["", "## Lineage Roots", "",
        "| # | Title | Children |", "|---|-------|----------|"]
for e in roots:
    kids = ", ".join(map(str, children.get(e["exp"], []))) or "—"
    out.append(f"| {e['exp']} | {e['title']} | {kids} |")

(EXP_DIR / "INDEX.md").write_text("\n".join(out) + "\n")
print(f"Wrote {EXP_DIR/'INDEX.md'} ({len(exps)} experiments, "
      f"{len(best_by_track)} tracks, {len(refuted)} refuted).")
```

Run after every experiment, or hook into a git pre-commit / Claude Code Stop hook.

#### tools/rec.py — unified record CLI (the *write* path)

The AI should never hand-edit record frontmatter directly. Every status / metric / takeaway / lineage update goes through this CLI. Output is short and structured — token-cheap. The CLI enforces schema invariants so drift becomes impossible.

Subcommand structure: `rec.py <kind> <verb>`. Current kinds: `exp`, `adr`. Adding a new kind (e.g. `feat`) costs one new block — zero changes to existing code.

```bash
# Experiments
$ rec.py exp new "lgbm scaffold split"
Created docs/experiments/exp_42_lgbm_scaffold_split.md (status=planned)

$ rec.py exp update 42 --status=done --outcome=refuted \
    --takeaway="Scaffold splits drop AUC by 0.04; random splits leak."
Updated exp_42 (status: planned → done).

$ rec.py exp update 84 --status=done --outcome=improved \
    --metric=auc=0.938 --track=ibd-classification --parent=78 \
    --takeaway="SHAP top-100 subgraph: 0.938 AUC, +0.02 over MI."
Updated exp_84. Promoted to "Best by Track: ibd-classification".

$ rec.py exp update 13 --status=done --outcome=infra \
    --takeaway="vast.ai 5090 instances stable for 12hr GAT runs."
Updated exp_13.

$ rec.py exp show 84
exp: 84  status: done  outcome: improved  metric: auc=0.938  track: ibd-classification
parent: 78  takeaway: SHAP top-100 subgraph: 0.938 AUC, +0.02 over MI.

$ rec.py exp list --tag=gnn --status=done --outcome=improved
 84  done  improved  auc=0.938  SHAP top-100 subgraph...
114  done  improved  auc=0.941  MI top-100 + ESM2 wins...

$ rec.py exp lineage 114
114 ← 90 ← 84 ← 78 ← 21 ← 17 (root)
consumes: data/processed/scaffolds_v3.pkl, data/experiments/exp84/checkpoint.pt
produces: data/experiments/exp114/{model.txt, predictions.csv, run.log}

$ rec.py exp finding 84 "SHAP feature selection beats MI on subgraph variants."
Appended to docs/findings.md.

$ rec.py exp finding 29 "GAT fails on PD across all configs." --negative
Appended to docs/findings.md.

# ADRs
$ rec.py adr new "task queue selection"
Created docs/adrs/adr_01_task_queue_selection.md (status=proposed)

$ rec.py adr update 1 --status=accepted --decision="Use jobrunner + K3s"
Updated adr_1 (status: proposed → accepted).

$ rec.py adr update 1 --status=superseded --superseded-by=2
Updated adr_1 (status: accepted → superseded).

$ rec.py adr list
  1  superseded  Task queue selection         Use jobrunner + K3s → adr_2
  2  accepted    Worker orchestration         K3s manages worker pods

$ rec.py adr list --status=accepted
  2  accepted    Worker orchestration         K3s manages worker pods
```

**CLI rules** (refuses writes that violate them):

- `rec.py exp update` with `--status=done|failed` requires `--outcome` and `--takeaway`.
- `--outcome=improved | parity | regression` requires `--track` and `--metric`.
- `--track=X` without `--metric` is rejected.
- `--parent=N` rejected if exp N doesn't exist or is `status: superseded`.
- `rec.py adr update --status=superseded` requires `--superseded-by`.
- `--superseded-by=N` rejected if adr N doesn't exist.
- After every successful write, `tools/render_index.py` runs automatically.

The CLI is ~150 lines of Python. It is the API; markdown is just the storage format.

#### tools/check_drift.py — Stop-hook drift detector

Catches the residual drift cheaply rather than trying to prevent it. Runs as a Claude Code Stop hook (or pre-commit). Warns on:

- `findings.md` cites `Exp N` but `exp_N.md` has `status: superseded`
- `CLAUDE.md` top-findings link to a superseded or missing exp
- `INDEX.md` mtime older than any `exp_*.md` or `adr_*.md` (render is stale)
- `consumes:` references a path that doesn't exist on disk
- `parent:` points to a missing or superseded exp
- `adr_N` has `status: superseded` without `superseded_by` set
- `adr_N.superseded_by` points to a non-existent ADR
- **Orphan docs in `docs/` root**: any `docs/*.md` that is not in the standard set (`progress.md`, `findings.md`, `data.md`, `api.md`, `setup.md`, `ai_log.md`) and lacks `kind: domain-doc` frontmatter is flagged. This catches ad-hoc design docs (`reliability_design.md`) that should be ADRs or domain references.

```python
#!/usr/bin/env python
"""Cheap drift detector. Exits non-zero if any issue is found."""
from pathlib import Path
import re, sys, yaml

ROOT = Path(__file__).resolve().parent.parent
EXP_DIR = ROOT / "docs" / "experiments"
FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
EXP_REF = re.compile(r"\bExp\s*(\d+)\b")

issues = []
exps = {}
for p in EXP_DIR.glob("exp_*.md"):
    m = FM_RE.match(p.read_text())
    if m: exps[yaml.safe_load(m.group(1))["exp"]] = (p, yaml.safe_load(m.group(1)))

# 1. INDEX.md staleness
idx = EXP_DIR / "INDEX.md"
if idx.exists():
    idx_mtime = idx.stat().st_mtime
    for p, _ in exps.values():
        if p.stat().st_mtime > idx_mtime:
            issues.append(f"INDEX.md is stale (older than {p.name}). Run render_index.py.")
            break

# 2. Findings.md / CLAUDE.md cite superseded or missing exps
for f in [ROOT / "docs" / "findings.md", ROOT / "CLAUDE.md"]:
    if not f.exists(): continue
    for n in map(int, EXP_REF.findall(f.read_text())):
        if n not in exps:
            issues.append(f"{f.name} references Exp {n} but exp_{n:02d}_*.md does not exist.")
        elif exps[n][1].get("status") == "superseded":
            issues.append(f"{f.name} references Exp {n} which is superseded.")

# 3. Lineage / artifact integrity
for n, (_, fm) in exps.items():
    parent = fm.get("parent")
    if parent and parent not in exps:
        issues.append(f"exp_{n}: parent={parent} does not exist.")
    for path in fm.get("consumes", []) or []:
        if not (ROOT / path).exists():
            issues.append(f"exp_{n}: consumes '{path}' but file is missing.")

if issues:
    print("DRIFT DETECTED:")
    for i in issues: print(f"  - {i}")
    sys.exit(1)
print(f"OK ({len(exps)} experiments, no drift detected).")
```

Hook it into `.claude/settings.json` Stop event (or git pre-commit). Cost: a single `python tools/check_drift.py` run per session. Catches 90% of real-world drift.

### Where experiment logs live (and why)

Experiment logs (training output, optuna progress, training curves) belong **inside the per-exp output directory**, declared in frontmatter `produces:`. They do NOT belong in the project root.

**Convention**: every experiment writes to `data/experiments/exp{NN}_{slug}/`:

```
data/experiments/exp28_lgbm_screening/
├── run.log              # stdout/stderr from the run
├── model.txt            # primary artifact
├── predictions.csv
└── plots/
```

**Launch pattern** (replaces the legacy "log file in project root" pattern):

```bash
# Standard form — log lives next to outputs, not in project root
EXPDIR="data/experiments/exp28_lgbm_screening"
mkdir -p "$EXPDIR"
PYTHONWARNINGS="ignore::UserWarning" python -u scripts/exp_28_lgbm_screening.py \
    > "$EXPDIR/run.log" 2>&1 &

echo "tail -f $EXPDIR/run.log"
```

Then declare it in frontmatter so `tools/exp.py lineage` and `check_drift.py` know about it:

```yaml
produces:
  - data/experiments/exp28_lgbm_screening/model.txt
  - data/experiments/exp28_lgbm_screening/run.log
```

**Why this matters**:

- **Co-located**: log + artifacts + plots travel as one unit. Move/archive/delete the experiment → everything goes together. No orphaned `exp28_out.log` left in project root after the artifact dir is cleaned.
- **Tracked by lineage**: `tools/exp.py lineage 28` shows the log path; `check_drift.py` warns if `produces:` references a missing log (caught a partially-deleted experiment).
- **No name collisions**: previously `exp_28_out.log` and a different project's `exp_28_out.log` would clash if shared via rsync. Now logs are namespaced by their experiment dir.
- **Resumable**: convention `run.log`, `run_resume_2.log`, etc. — all in the same dir.
- **gitignored cleanly**: `data/` is already gitignored; logs need no separate rule.

**Naming inside the dir**:

| File | When |
|------|------|
| `run.log` | Primary stdout/stderr |
| `run_resume_{N}.log` | Resumed runs |
| `optuna.db` | Persistent Optuna study (if any) |
| `tb/` or `csv_logs/` | Training framework logs (TensorBoard, CSVLogger) |

**Migration tip** for existing projects with `exp_NN_out.log` strewn in the root: run

```bash
for f in exp_*_out.log; do
  N=$(echo "$f" | sed 's/exp_\([0-9]*\)_out.log/\1/')
  D=$(ls -d data/experiments/exp${N}_* 2>/dev/null | head -1)
  [ -n "$D" ] && mv "$f" "$D/run.log"
done
```

Then update each experiment's frontmatter to add `produces: [data/experiments/expNN_*/run.log]`.

### docs/data.md — Output File Catalog

```markdown
# Data Catalog

All outputs in `data/experiments/` (per-experiment dirs) or `data/results/` (flat). Cross-ref with [experiments.md](experiments.md).

---

## Source Data

| File | Description |
|------|-------------|
| `data/{filename}` | {what it contains (dimensions)} |

---

## Model Checkpoints

| File | Description |
|------|-------------|
| `data/models/{filename}` | {model type + key config + metric} |

---

## Notebook Outputs (nb prefix)

| File | Description |
|------|-------------|
| `nb{NN}_{name}.csv` | {description (dimensions)} |

---

## Script Outputs (matches exp_XX.py)

| File | Description |
|------|-------------|
| `{NN}_{name}.csv` | {description} |
```

**Conventions**:
- File names in backticks
- One-line descriptions with dimensions in parentheses
- Notebook outputs: `nb{NN}_` prefix; script outputs: `{NN}_` prefix

### docs/api.md — Module API Reference

```markdown
# Module API Reference

Public API for `{package_name}` modules.

---

## {module}.py

```python
from {package}.{module} import (
    function_a,   # Brief description
    function_b,   # Brief description
    CONSTANT_X,
)

# Typical usage
result = function_a(param1, param2)
processed = function_b(result, option=True)
```

**Note**: {Important caveat, default behavior, or common pitfall.}

---

## {next_module}.py

...
```

**Conventions**:
- Code blocks are the documentation — import statement + usage example
- Comments inside code serve as function descriptions
- No formal parameter docs — examples are self-documenting
- Ordered by pipeline stage: data → features → models → training → viz

### docs/findings.md — Curated Findings (positive + negative)

The single curated list of what works and what doesn't. CLAUDE.md links here instead of listing findings inline.

```markdown
# Findings

Curated, append-only. Negative results are equally important — they prevent re-exploring dead ends.

---

## Positive findings (what works)

- **{Finding}**: {one-line summary with numbers} — Exp {N}
- **{Finding}**: {one-line summary} — Exp {N}

---

## Negative findings (what doesn't work)

- **{Dead end}**: {what was tried + why it failed, with numbers} — Exp {N}
- **{Failed approach}**: {description}; {metric showing failure} — Exp {N}

---

## Superseded findings (kept for history)

- ~~**{old finding}**~~ — superseded by {new finding} (Exp {M}).
```

**Rules**:
- Append-only. Findings move to "Superseded" when overturned, never deleted.
- Always link the source experiment number — `Exp 84`. The reader can `rg "exp: 84" docs/experiments/`.
- One line per finding. If you need a paragraph, the detail belongs in the per-exp file, not here.

### docs/adrs/ — Architecture Decision Records

Structured home for design decisions. A decision that would otherwise become a floating `docs/some_design.md` belongs here instead — indexed, supersedable, drift-checked.

**When to create an ADR** (use `/log-adr`):
- Technology or architecture choice (task queue, storage backend, wire protocol)
- Deciding NOT to use something — prevents re-litigating closed decisions
- Any pivot where reversing it would require substantial rework

**When NOT to create an ADR**:
- Experiment results → `rec.py exp` with `outcome: infra` or science outcome
- Sprint plans → `docs/progress.md`
- Bug fixes → commits

#### Per-ADR file template

`docs/adrs/adr_{NN}_{slug}.md`:

```markdown
---
adr: 1
title: Task queue selection
status: accepted        # proposed | accepted | superseded
date: 2026-05-03
superseded_by: null     # set when superseded by another ADR
decision: "Use jobrunner + K3s for distributed task execution"
context: "ssh_jobqueue custom protocol has no lease/redelivery — in-flight jobs lost on worker death (2026-05-02 fleet failure)"
consequences: "peptide becomes a thin jobrunner consumer; ssh_jobqueue removed"
tags: [infra, task-queue]
---

# ADR 1 — Task queue selection

**Context**: ...

**Decision**: ...

**Consequences**: ...
```

**Schema rules**:
- `status: superseded` requires `superseded_by: N` (enforced by `rec.py` and `check_drift.py`)
- `decision:` is a one-line summary — detail goes in the body
- Body sections: **Context**, **Decision**, **Consequences** (≤ 50 lines total)

**CLI** (`tools/rec.py`):

```bash
rec.py adr new "task queue selection"
rec.py adr update 1 --status=accepted --decision="Use jobrunner + K3s"
rec.py adr update 1 --status=superseded --superseded-by=2
rec.py adr show 1
rec.py adr list
rec.py adr list --status=accepted   # active decisions only
```

**Superseding workflow** — when a decision changes:

```bash
rec.py adr new "new approach slug"          # create replacement first
rec.py adr update <new_N> --status=accepted --decision="..."
rec.py adr update <old_N> --status=superseded --superseded-by=<new_N>
```

The old ADR stays in the index (history), the new one is the active decision.

#### docs/adrs/INDEX.md (generated)

```markdown
# ADR Index

## All Decisions
| # | Title | Status | Decision | Tags |
|---|-------|--------|----------|------|
| 1 | Task queue selection | accepted | Use jobrunner + K3s | infra, task-queue |
| 2 | Worker image strategy | accepted | slim python:3.11 base | infra, docker |

## Active Decisions
| # | Title | Decision |
|---|-------|----------|
| 1 | Task queue selection | Use jobrunner + K3s |

## Superseded (history only)
| # | Title | Superseded by |
|---|-------|--------------|
```

---

### docs/kb/meetings.md — Meeting Notes

Lives under `docs/kb/` so it's covered by the vector index (long prose, hard to keyword-search).

```markdown
# Meeting Notes

---

## {Date} — {Attendees or Context}

**Key decisions**:
- {Decision with rationale}

**Action items**:
- [ ] {Person}: {task}
- [x] {Person}: {completed task}

**Discussion**:
- {Topic}: {Summary of discussion}
```

### docs/setup.md — Environment & Infrastructure (optional)

For projects with complex environments (GPU, Docker, compiled deps). Skip for simple pip/conda projects.

```markdown
# Environment Setup

---

## Base Environment

{Conda/pip setup, Python version, key version pins}

---

## GPU / Hardware

{CUDA version, driver requirements, device-specific notes}

---

## Docker Containers

| Container | Purpose | Build |
|-----------|---------|-------|
| `docker/{name}/` | {what it isolates} | `docker build -t {name} docker/{name}` |

---

## Troubleshooting

- **{Issue}**: {Resolution}
```

### Domain-Specific Docs (optional)

Add `docs/{domain}.md` files as your project grows. Common examples:

| Doc | When to add |
|-----|-------------|
| `docking.md` | Molecular docking, pose scoring, site prep |
| `scoring.md` | Post-processing scoring pipelines |
| `preprocessing.md` | Complex data preprocessing/standardization |
| `deployment.md` | Serving, inference, production concerns |

Follow the same formatting patterns: single H1, horizontal rules between H2s, tables over prose.

---

## Knowledge Search (literature, meetings, transcripts)

For long-form prose where exact keywords are hard to predict, run a small vector index over `docs/kb/` only. **Do not index `docs/experiments/`, `findings.md`, or `progress.md`** — those are structured, exact-match-friendly, and embedding-search degrades precision (numeric metrics, exp IDs, table rows don't embed well; `Exp 84` and `Exp 48` are nearly identical in vector space).

### Scope

Index only:
- `docs/kb/literature/**/*.md` and `*.pdf`
- `docs/kb/meetings.md`
- `docs/kb/transcripts/**/*.md`

Skip everything under `docs/experiments/`, `docs/archive/`, `progress.md`, `findings.md`, `data.md`, `api.md`. These respond better to grep / `rg` / direct read.

### Implementation (minimal)

Use `sqlite-vec` or `chroma` — both embed in a single Python file and need no server. Index lives at `.cache/kb_index.sqlite` (gitignored). Re-index on demand or via a Stop hook:

```python
# tools/index_kb.py — sketch
from pathlib import Path
import sqlite_vec, sqlite3
from sentence_transformers import SentenceTransformer

KB = Path(__file__).resolve().parent.parent / "docs" / "kb"
DB = Path(__file__).resolve().parent.parent / ".cache" / "kb_index.sqlite"
model = SentenceTransformer("all-MiniLM-L6-v2")  # local, fast, 384-dim

# walk KB/*.md and KB/**/*.pdf, chunk by H2 (or 800-char windows for PDFs),
# embed, upsert into a sqlite-vec table keyed by (path, chunk_id, mtime).
# Skip files whose mtime hasn't changed since last index.
```

### Querying

Expose as one MCP tool or a `/find-kb <query>` skill that returns top-k `(file:line, snippet)` references. The AI then `Read`s only the matched files. Never returns chunks directly into the prompt — always file paths.

### When NOT to bother

- Project has <5 papers and minimal meeting notes.
- All long-form content is on Notion / Google Drive (use those native search tools instead).
- Solo project with no transcripts/recordings.

---

## /find-exp Skill (experiment search)

A deterministic alternative to RAG for the structured side. Greps `docs/experiments/exp_*.md` frontmatter and result tables, returns matching files. Use this — not the vector index — for "find me experiments about X".

```bash
# tools/find_exp.sh — sketch
# Usage: tools/find_exp.sh <query>
# Examples:
#   tools/find_exp.sh "scaffold split"
#   tools/find_exp.sh "tags: gnn"
#   tools/find_exp.sh "status: superseded"
rg -l --type md "$1" docs/experiments/ \
  | xargs -I{} sh -c 'echo "== {} =="; rg "^(exp|title|status|metric|tags):" {} | head -10'
```

Wrap as a Claude Code skill (`.claude/skills/find-exp/`) so the AI can invoke it without loading every per-exp file.

---

## AI Session & Calibration Logging

Two layers of QA telemetry, modeled on production AI-agent observability stacks (LangSmith, LangFuse, Braintrust, OpenTelemetry GenAI). Goal: turn anecdotes into data so future sessions improve.

| Layer | Granularity | File | Update model | Purpose |
|-------|-------------|------|--------------|---------|
| **Session** (frame) | One per Claude Code conversation | `docs/sessions/{date}-{slug}.md` | Auto-extracted at session end via Stop hook (`tools/session.py end`); user fills 2-3 fields | Longitudinal trends: success rate, friction, cost over time |
| **Event** (point) | One per AI mistake or noteworthy success within a session | `docs/ai_log.md` | Appended in-session via `tools/rec.py log --err / --win` | Catch patterns mid-session; queue items for promotion to CLAUDE.md / memory |

Both feed the **promotion loop**: weekly or sprint-end review → patterns get lifted into CLAUDE.md (project-specific) or `~/.claude/CLAUDE.md` / auto-memory (cross-project). Without the promotion step, this is just clutter — set a calendar reminder.

### docs/ai_log.md — per-event AI calibration log

Plain markdown, no frontmatter. Date-prefixed entries with `❌` (error) or `✅` (win) emoji discriminator for `grep`-ability. ≤200 lines; archive when over.

```markdown
# AI Calibration Log

Append-only. Errors (❌) and wins (✅). Review weekly — promote recurring patterns to CLAUDE.md (project) or auto-memory (cross-project), then prune.

---

## 2026-04-22 14:32 ❌ Hallucinated sklearn parameter

**Context**: tuning RF in exp_42
**What**: Suggested `RandomForestClassifier(min_samples_split_ratio=0.1)` — that param doesn't exist
**Caught by**: type error at runtime
**Fix**: ran sklearn `?` lookup; correct param is `min_samples_split`
**Promote?**: cross-project — AI hallucinates sklearn params often
**Tags**: hallucination, sklearn

---

## 2026-04-23 09:11 ✅ Caught silent test mock leak

**Context**: refactor of PR #128
**What**: Noticed `mock_db` fixture wasn't being torn down between tests; would have caused state pollution in CI
**Saved**: 2-3 hours of debug
**Promote?**: no — situational
**Tags**: testing, fixtures

---

## 2026-04-23 16:45 ❌ Edited markdown directly instead of using rec.py

**Context**: logging exp_44 result
**What**: Used Edit tool on `docs/records/exp_44_*.md` instead of `tools/rec.py update`
**Caught by**: drift checker (INDEX.md became stale)
**Fix**: stricter Stop hook
**Promote?**: project-level — strengthen CLAUDE.md "always use rec.py for record updates"
**Tags**: tooling, bypass
```

**CLI to append** (one Bash call, no file scrolling):

```bash
tools/rec.py log --err "Hallucinated sklearn param in exp_42" --tags=hallucination,sklearn
tools/rec.py log --win "Caught mock fixture leak in PR #128" --tags=testing
tools/rec.py log --err --detail   # opens $EDITOR on a templated entry for full write-up
```

The AI itself should call `--err` whenever it catches itself making a mistake mid-session. Don't silently swallow errors — same-session capture is the only capture that works.

### docs/sessions/ — per-session QA records

One file per Claude Code conversation. Frontmatter is mostly **auto-extracted** from `.claude/projects/{project}/sessions/{id}.jsonl` at session end (Stop hook). Human fills only 2-3 fields.

```yaml
---
# --- Identity (auto) ---
session: 2026-04-22-1432
project: gnn-reap
model: claude-opus-4-7
date: 2026-04-22
duration_min: 47
turns: 12

# --- Telemetry (auto-extracted from transcript) ---
tools_used: {Read: 8, Edit: 5, Bash: 14, "rec.py": 3, TaskCreate: 1}
tokens: {input: 142000, output: 18000, cached: 89000}
files_touched: [src/data.py, tests/test_data.py, docs/records/exp_42_scaffold.md]
records_touched: [exp_42]
errors_logged: 1                  # count of ai_log.md entries written this session
wins_logged: 0
plan_used: true                   # used Plan/TaskCreate?
plan_tasks_completed: 4
plan_tasks_completed_first_try: 2 # didn't need rework
context_size_start_kb: 47
context_size_end_kb: 312

# --- Manual (user fills at session close, or AI proposes) ---
goal: "Add scaffold-split feature to data loader and test"
status: success                   # success | partial | failed | abandoned
user_corrections: 2               # times user said "no, do X instead"
quality: 4                        # 1-5 self-rating (or LLM-judge if you wire one up)
notes: "Scaffold logic correct on first pass. Lost 10 min when AI suggested deprecated `numpy.int`."
---

# Session: scaffold-split feature for data loader

## What happened
{One paragraph. Auto-draft from transcript by `session.py end`, edited by user.}

## Friction points
- {What slowed things down}

## Lessons → promote
- {Promotable observation} → CLAUDE.md / auto-memory / ai_log.md
```

#### Modern metrics, what each one tells you

| Metric | What it diagnoses | Why it matters |
|--------|-------------------|----------------|
| `duration_min` | Total wall-clock | Calibrates "this kind of task takes ~X" estimates |
| `turns` | Conversational round-trips | High turn count for a small change = AI struggling or context unclear |
| `tools_used` distribution | Tool-call profile | Heavy `Read` count → context retrieval problem; heavy `Edit` cycle → AI revising itself a lot |
| `tokens.{input, output, cached}` | Cost signal + cache effectiveness | Low `cached` ratio → CLAUDE.md churning, or long sleep delays evicting cache. Production-grade cost tracking. |
| `user_corrections` | Friction proxy | The single most actionable metric. >3 in a session → CLAUDE.md is missing context, or instructions were ambiguous. |
| `plan_used` + `plan_tasks_completed_first_try` | Plan adherence | If `plan_used` is rarely true on hard tasks, you have a habit problem. If first-try completion is low, plans are being made too coarse. |
| `errors_logged` | In-session error capture rate | Rises early (you're noticing more), should fall over time as patterns get promoted to CLAUDE.md |
| `quality` (1-5) | Subjective rating | Cheap, surprisingly useful for trend lines. Take 5 seconds at end-of-session. |
| `status` (success/partial/failed/abandoned) | Outcome label | Required for any meaningful aggregation |
| `context_size_start_kb` → `_end_kb` | Context growth | Sessions ending at 300+ KB context with low `cached` are the expensive ones |

#### tools/session.py — auto-extraction (Stop hook)

```python
#!/usr/bin/env python
"""
Stop-hook: parse current Claude Code session transcript and write/update
docs/sessions/{date}-{slug}.md with auto-extracted telemetry.

Usage: tools/session.py end [--slug <slug>]
"""
import json, sys, datetime, os, re
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = PROJECT_ROOT / "docs" / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# Resolve session JSONL (Claude Code env vars or fall back to most recent)
session_id = os.environ.get("CLAUDE_SESSION_ID")
proj_dir = Path.home() / ".claude" / "projects" / os.environ.get("CLAUDE_PROJECT_DIR", "")
jsonl = next((p for p in proj_dir.glob("*.jsonl") if session_id and session_id in p.name), None) \
        or max(proj_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, default=None)

if not jsonl:
    sys.exit(0)

events = [json.loads(l) for l in jsonl.read_text().splitlines() if l.strip()]

# --- Aggregate telemetry ---
tools = Counter()
tokens = {"input": 0, "output": 0, "cached": 0}
files_touched, records_touched = set(), set()
turns = 0
start = end = None
plan_used = False
errors = wins = 0

for e in events:
    if e.get("type") == "tool_use":
        name = e.get("name", "")
        tools[name] += 1
        if name in ("Edit", "Write", "Read"):
            p = e.get("input", {}).get("file_path", "")
            if p: files_touched.add(p)
        if name == "Bash":
            cmd = e.get("input", {}).get("command", "")
            if "rec.py log --err" in cmd: errors += 1
            elif "rec.py log --win" in cmd: wins += 1
            for m in re.finditer(r"exp_(\d+)|feat_(\d+)|bug_(\d+)|adr_(\d+)", cmd):
                records_touched.add(next(g for g in m.groups() if g))
        if name == "TaskCreate":
            plan_used = True
    if e.get("role") == "user":
        turns += 1
    if e.get("usage"):
        u = e["usage"]
        tokens["input"]  += u.get("input_tokens", 0)
        tokens["output"] += u.get("output_tokens", 0)
        tokens["cached"] += u.get("cache_read_input_tokens", 0)
    ts = e.get("timestamp")
    if ts:
        start = start or ts
        end = ts

duration_min = round((datetime.datetime.fromisoformat(end) - datetime.datetime.fromisoformat(start)).total_seconds() / 60, 1) if start and end else 0
date = datetime.date.today().isoformat()
slug = sys.argv[sys.argv.index("--slug")+1] if "--slug" in sys.argv else f"session-{datetime.datetime.now().strftime('%H%M')}"
out = SESSIONS_DIR / f"{date}-{slug}.md"

# --- Write file ---
fm = f"""---
session: {date}-{datetime.datetime.now().strftime('%H%M')}
project: {PROJECT_ROOT.name}
date: {date}
duration_min: {duration_min}
turns: {turns}
tools_used: {dict(tools.most_common())}
tokens: {tokens}
files_touched: {sorted(files_touched)}
records_touched: {sorted(records_touched)}
errors_logged: {errors}
wins_logged: {wins}
plan_used: {str(plan_used).lower()}

# Manual fields — fill at session close:
goal: ""
status: ""           # success | partial | failed | abandoned
user_corrections: 0
quality: 0           # 1-5
notes: ""
---

# Session: {slug}

## What happened
<!-- one paragraph -->

## Friction points
- 

## Lessons → promote
- 
"""
out.write_text(fm)
print(f"Wrote {out.relative_to(PROJECT_ROOT)} ({duration_min} min, {turns} turns, {sum(tokens.values())} tok)")
```

Wire it as a Claude Code Stop hook in `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [{"command": "python tools/session.py end"}]
  }
}
```

#### docs/sessions/INDEX.md — aggregate views

Generated. Quarterly trend lines on the metrics that matter:

```markdown
# Sessions Index

_Generated. Last 90 days._

## Outcome distribution (n=42)

| Status      | Count | % |
|-------------|-------|---|
| success     | 28    | 67 |
| partial     | 9     | 21 |
| failed      | 3     | 7 |
| abandoned   | 2     | 5 |

## Friction trend (user_corrections per session, weekly avg)

Week 14: 3.2 → Week 15: 2.8 → Week 16: 1.9 → Week 17: 1.4

## Cost trend (input tokens per session, weekly median)

Week 14: 180k → Week 15: 145k → Week 16: 118k → Week 17: 102k
_(CLAUDE.md was trimmed Week 15; context cache hit ratio improved)_

## By goal type

| Goal kind     | n | Median duration | Median quality | Median corrections |
|---------------|---|-----------------|----------------|--------------------|
| feature       | 18 | 38 min | 4.1 | 1.5 |
| refactor      | 11 | 52 min | 3.7 | 2.4 |
| debug         | 7  | 71 min | 3.0 | 4.1 |
| experiment    | 6  | 95 min | 4.5 | 0.8 |
```

That last table is the gold — it tells you *what kinds of work the AI handles well vs badly* in your projects, which directly informs which workflows to wrap as skills, which sections of CLAUDE.md to harden, and which tasks are still better done manually.

#### The promotion loop (where the value actually lands)

Both `ai_log.md` events and `sessions/` records are *staging areas*. They produce signal only if you periodically review and lift patterns:

1. **Weekly** (15 min): scan `ai_log.md`. For each entry tagged `Promote?: yes`:
   - Project-specific → add to CLAUDE.md "Anti-patterns" / "Conventions"
   - Cross-project → add to `~/.claude/CLAUDE.md` or auto-memory (feedback type)
   - Mark `[✓ promoted]` or delete
2. **Sprint-end** (30 min): scan `sessions/INDEX.md`. Look at:
   - Friction trend (rising or falling?)
   - Goal-type table (which kind regressed?)
   - Cost trend (cache hit rate dropping?)
   - Pick *one* highest-leverage change for next sprint (CLAUDE.md edit, new skill, prompt change)
3. When `ai_log.md` exceeds ~200 lines: archive to `docs/archive/ai_log_{YYYY-QN}.md`, start fresh.

A skill `/promote-ai-log` walks the AI through step 1 interactively — read each unprocessed entry, propose a CLAUDE.md or memory edit, mark promoted on accept.

---

## Skills (Slash Commands)

Two layers of invocation, with different jobs:

| Layer | Where | Invoked by | Use when |
|-------|-------|------------|----------|
| **Tools** (`tools/*.py`) | Project root | AI via `Bash` tool, or human via shell | One-shot deterministic operation. AI runs `tools/rec.py update 42 --status=done` mid-session without ceremony. |
| **Skills** (`.claude/skills/<name>/SKILL.md`) | Per-project (or user-level at `~/.claude/skills/`) | Human via `/<name>` syntax in chat | Multi-step workflow with branching, prompts to user, or post-action follow-ups. |

**Note on syntax**: Claude Code uses `/<name>` for skills/slash commands. `@<path>` references files (pulls into prompt). `#<text>` adds to memory. Tools and skills are invoked via `/`, not `@` or `#`.

### Minimum skill set for the pilot

| Skill | Wraps | Workflow |
|-------|-------|----------|
| `/log-exp <NN>` | `rec.py exp` | Walk through frontmatter fields, compute lineage, update record, run `render_index.py` |
| `/log-adr` | `rec.py adr` | Create or update an ADR; handle superseding workflow; retire orphan design docs |
| `/log-error [msg]` | `tools/rec.py log --err` | Identify mistake, decide promotion scope (project/cross-project/situational), append entry |
| `/log-win [msg]` | `tools/rec.py log --win` | Same shape as error |
| `/sync-records` | `render_index.py` + `check_drift.py` | Regenerate INDEX, run drift detector, surface warnings |
| `/snapshot <kind>` | `tools/snapshot.py` | Generate `ref/{kind}_generated.md` (arch / schema / api) on demand |
| `/promote-ai-log` | reads `ai_log.md` | Walk through each entry, propose CLAUDE.md / memory edit, mark `[✓ promoted]` |

### Example: `.claude/skills/log-error/SKILL.md`

```markdown
---
name: log-error
description: Log an AI mistake to docs/ai_log.md. Use whenever you (the AI) catch yourself making a wrong suggestion, hallucinating an API, breaking the build, or being corrected by the user. Also use when the user types "log this" or "/log-error".
---

# /log-error

When invoked:

1. Identify the mistake from recent context. Be specific:
   - **What** was suggested or done
   - **Why** it was wrong
   - **How** it was caught (user correction / runtime error / drift checker / etc.)

2. Decide promotion scope:
   - **Project-specific** (e.g., uses pattern unique to this codebase) → flag for CLAUDE.md
   - **Cross-project** (e.g., hallucinated common library API) → flag for `~/.claude/CLAUDE.md` or auto-memory
   - **Situational** (one-off) → no promotion

3. Call:
   ```bash
   tools/rec.py log --err "<one-line summary>" --tags=<comma,tags> --detail
   ```
   `--detail` opens $EDITOR on a templated entry. Fill in: Context, What, Caught by, Fix, Promote?, Tags.

4. If `Promote?: yes`, remind the user to run `/promote-ai-log` at session end.

**Critical**: Do NOT silently swallow mistakes. Same-session capture is the only capture that works — by next session you'll have forgotten.
```

### When to write a skill vs just call the tool

- **Just call the tool** if the operation is one CLI call with obvious args.
- **Write a skill** when there's: branching logic, user prompts mid-flow, follow-up actions across multiple tools, or a workflow you find yourself explaining the same way every time.
- Aim for ~5-8 skills total. More than that and you're micro-managing the AI.

---

## Naming Conventions Summary

| Entity | Pattern | Example |
|--------|---------|---------|
| Experiment scripts | `scripts/exp_{NN}_{description}.py` | `exp_28_lgbm_baseline.py` |
| Polished notebooks | `notebooks/{NN}_{description}.ipynb` | `06_feature_importance.ipynb` |
| Experiment output dirs | `data/experiments/exp{NN}_{description}/` | `exp28_lgbm_screening/` |
| Flat notebook outputs | `data/results/nb{NN}_{description}.{ext}` | `nb09_clusters.csv` |
| Flat script outputs | `data/results/{NN}_{description}.{ext}` | `21_node_importance.pkl` |
| Model checkpoints | `data/models/{description}.pt` | `lgbm_baseline_v2.txt` |
| Experiment logs | `data/experiments/exp{NN}_{slug}/run.log` | `data/experiments/exp28_lgbm_screening/run.log` |
| Optuna databases | `data/experiments/exp{NN}_{slug}/optuna.db` | `data/experiments/exp35_lgbm_epitope/optuna.db` |

- Experiment number is the universal ID linking scripts → outputs → logs → docs
- Numbers are sequential and never reused

---

## Cross-Referencing Pattern

The documentation forms a layered system with increasing detail:

```
CLAUDE.md (summary layer — always loaded by AI, target ~60 lines, hard cap 100)
  ├── Quick Reference tables (key numbers at a glance)
  ├── Top 3-5 findings (one line each → link to docs/findings.md for the rest)
  ├── Experiments section (count + link to INDEX.md, NO inline table)
  └── Links to docs/*.md for details
      │
      ├── docs/progress.md             — active sprint planning only (≤200 lines, archive when over)
      ├── docs/findings.md             — curated positive + negative findings (the AI's "what I know")
      ├── docs/experiments/INDEX.md    — generated from per-exp frontmatter
      ├── docs/experiments/exp_NN_*.md — one file per experiment (frontmatter is source of truth)
      ├── docs/data.md                 — file catalog
      ├── docs/api.md                  — how to use the code
      ├── docs/kb/                     — long-form prose, vector-indexed (literature, meetings, transcripts)
      ├── docs/archive/                — superseded sprints / phases (grep-able, not loaded)
      └── docs/{domain}.md             — domain-specific reference as needed
```

**Waterfall for experiment info**: Need status? → frontmatter of `docs/experiments/exp_NN_*.md`. Need to scan all? → `INDEX.md` (generated). Need details? → the per-exp file. **Status lives in exactly one place — the per-exp frontmatter.**

**Information flows upward**: per-exp frontmatter → INDEX.md (rendered) → top findings link in CLAUDE.md. Each layer adds compression and is regenerable, not hand-edited.

**No denormalization**: a fact (status, primary metric, supersedes-relation) lives in exactly one file. Drift becomes structurally impossible because there's nowhere to drift *to*.

---

## Python Package Conventions

- **`__init__.py`**: Version only (`__version__ = "0.1.0"`). No re-exports.
- **Imports**: Always absolute (`from package.module import func`), never relative.
- **Model checkpoints**: Always embed hyperparameters in the saved dict so models are self-describing:
  ```python
  torch.save({
      'model_state_dict': model.state_dict(),
      'param1': value1, 'param2': value2,
  }, path)
  ```

### config.py Template

Central location for paths, constants, and hardware config. Every script imports from here — no hardcoded paths anywhere else.

```python
from pathlib import Path
import os

# --- Paths ---
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent  # src/{pkg}/config.py → project root
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPERIMENTS_DIR = DATA_DIR / "experiments"
MODELS_DIR = DATA_DIR / "models"
RESULTS_DIR = DATA_DIR / "results"       # For flat output layout
PLOTS_DIR = DATA_DIR / "plots"

# --- Hardware ---
import multiprocessing
N_PHYSICAL_CORES = multiprocessing.cpu_count() // 2  # Physical cores (not HT logical)

def limit_threads(n=None):
    """Call BEFORE importing numpy/sklearn/xgboost/lightgbm.
    Prevents thread oversubscription on HT systems."""
    n = n or N_PHYSICAL_CORES
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[var] = str(n)

# --- Device ---
import torch
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
```

**Key rule**: Call `limit_threads()` at the top of every experiment script, **before** importing numpy/sklearn/LightGBM. Thread oversubscription on HT systems causes cache thrashing and degrades performance.

---

## Operational Patterns

Hard-won patterns for running experiments reliably. These prevent common pitfalls like lost results, zombie processes, and thread contention.

### Long-Running Task Execution

Logs live **inside the per-experiment output directory**, not in the project root. This co-locates log + artifacts + plots, makes them gitignored automatically (since `data/` is gitignored), and ties the log into the lineage DAG via frontmatter `produces:`.

```bash
# Standard pattern
EXPDIR="data/experiments/exp28_lgbm_screening"
mkdir -p "$EXPDIR"
PYTHONWARNINGS="ignore::UserWarning" python -u scripts/exp_28_lgbm_screening.py \
    > "$EXPDIR/run.log" 2>&1 &

# If not in the correct conda env
PYTHONWARNINGS="ignore::UserWarning" conda run --no-capture-output -n {env_name} \
    python -u scripts/exp_28_lgbm_screening.py > "$EXPDIR/run.log" 2>&1 &
```

After launching, print the tail command for monitoring:

```bash
tail -f data/experiments/exp28_lgbm_screening/run.log
```

Then declare the log in frontmatter so `tools/exp.py lineage` and `check_drift.py` see it:

```yaml
produces:
  - data/experiments/exp28_lgbm_screening/model.txt
  - data/experiments/exp28_lgbm_screening/run.log
```

**Why each flag matters**:
- `python -u` — unbuffered output; without this, log files appear empty for minutes
- `PYTHONWARNINGS="ignore::UserWarning"` — suppresses sklearn/LightGBM warnings that `warnings.filterwarnings()` and `python -W` miss (they don't reach into C extensions)
- `> "$EXPDIR/run.log" 2>&1` — captures both stdout and stderr inside the per-exp dir
- `&` — background the process

**Anti-pattern** (do not do): writing `exp28_out.log` to the project root. After 30 experiments you have 30+ log files cluttering the repo, no link to their artifacts, and orphans whenever an experiment dir is cleaned up. See real example: `rai/train-admet/` had 80+ root-level `out_*.log` files before adopting this convention.

### Process Safety: Check Before Launch

**Before launching any script**, always check if it's already running:

```bash
ps aux | grep exp_28
```

Never rely on log file contents to determine if a process is running — logs can be stale from a previous run. Only `ps` is authoritative.

### Hyperparameter Optimization (Optuna)

**Always use persistent storage** — never run Optuna in-memory only:

```python
EXPDIR = EXPERIMENTS_DIR / "exp35_lgbm_epitope"
EXPDIR.mkdir(parents=True, exist_ok=True)

study = optuna.create_study(
    study_name="exp35_lgbm_epitope",
    storage=f"sqlite:///{EXPDIR}/optuna.db",   # Persistent, co-located with run.log + artifacts
    load_if_exists=True,                       # Resume interrupted runs
    direction="maximize",
)
```

**Why this matters**: In-memory Optuna studies are lost if the process crashes, the SSH session drops, or you accidentally kill the terminal. With SQLite storage, you can resume from exactly where you left off. One lost overnight HPO run teaches this lesson permanently.

Additional Optuna conventions:
- Use per-trial callbacks to log progress (print trial number + value after each trial)
- DB lives inside the per-exp output dir: `data/experiments/exp{NN}_{slug}/optuna.db` (declare in frontmatter `produces:`)
- Default to 100 trials for tree models (fast enough at ~10-45 sec/trial)
- Use `N_PHYSICAL_CORES` for `n_jobs`, not logical core count

### Conda Environment Management

Check `$CONDA_DEFAULT_ENV` before running commands. If the correct env is already active, run directly. Only use `conda run` when the active env differs:

```bash
# If already in the right env
python -u scripts/exp_28_baseline.py

# If in a different env
conda run --no-capture-output -n {env_name} python -u scripts/exp_28_baseline.py
```

---

## CLAUDE.md Maintenance Rules

1. **Findings are append-only** — they live in `docs/findings.md` (positive + negative). CLAUDE.md only links to it and shows the top 3-5. Never delete; supersede by striking through and linking the replacement.
2. **Log failures as first-class entries** ([Anthropic, *Long-running Claude*](https://www.anthropic.com/research/long-running-Claude)) — "X doesn't work because Y" saves more time than "X works". Every failed approach gets a per-exp file with `outcome: refuted` (or `failed`) and a `takeaway:` that names the dead end. Without these, the AI will repeatedly suggest approaches you've already ruled out, and the loss is *unbounded* — every future session pays the cost. The `INDEX.md § Refuted Hypotheses` view exists for this reason.
3. **Experiment status lives in per-exp frontmatter only** — never in CLAUDE.md, never in `progress.md`. CLAUDE.md links to `docs/experiments/INDEX.md` (generated). `progress.md` is sprint planning only, not a status table.
4. **Terminology section prevents ambiguity** — if two things share a name, define both and mandate qualification. The AI will confuse them otherwise.
5. **Deprecated code must be tracked** — list old functions/modules with their replacements. Remove entries only after all references are cleaned up.
6. **Quick Reference contains the numbers the AI needs most often** — dataset dimensions, class balance, key thresholds.

### Hard size caps (enforce, don't suggest)

| File | Cap | When over |
|------|-----|-----------|
| `CLAUDE.md` | **target ~60, hard cap 100** | HumanLayer's CLAUDE.md is <60 lines — it's a TOC + Quick Reference, not a textbook. Anything over 100 means details that belong in `docs/*.md`. |
| `docs/progress.md` | ~200 lines | Move completed sprints to `docs/archive/progress_{YYYY-QN}.md`. |
| `docs/findings.md` | ~300 lines | Move overturned findings to a `## Superseded findings` section; if that grows too, archive the oldest year. |
| `docs/ai_log.md` | ~200 lines | Promote unprocessed entries via `/promote-ai-log`, archive the rest to `docs/archive/ai_log_{YYYY-QN}.md`. |
| `docs/records/exp_NN_*.md` (any record) | ~150 lines each | If longer, it's actually multiple records — split. |
| `docs/sessions/{date}-*.md` | ~50 lines each | Per-session is short by design. INDEX.md aggregates trends. |
| `docs/{topic}.md` siblings | 3 max | At 3+ siblings (`literature.md`, `literature_a.md`, `literature_b.md`), promote to `docs/{topic}/` directory. |

### Update cadence

7. **After every record write**: `tools/rec.py` runs `render_index.py` automatically. Don't hand-edit INDEX.md — edit the render script if you want a new column.
8. **At session end**: Stop hook runs `tools/session.py end`, writes `docs/sessions/{date}-{slug}.md` with auto-extracted telemetry. Fill in `goal`, `status`, `quality`, `notes` (30 seconds).
9. **In-session error capture**: if you (the AI) catch yourself making a mistake, immediately call `tools/rec.py log --err`. Same-session capture is the only capture that works.
10. **Weekly review** (15 min): `/promote-ai-log` — read each unprocessed `ai_log.md` entry, lift project patterns to CLAUDE.md and cross-project patterns to `~/.claude/CLAUDE.md` or auto-memory.
11. **Sprint-end review** (30 min): read `docs/sessions/INDEX.md` aggregates. Pick **one** highest-leverage change for next sprint based on the trends (CLAUDE.md edit, new skill, prompt change). Don't try to fix everything — pick one.

---

## Per-Project Customization

This template is a starting point. Adapt these areas to your project's needs:

### Sections to Add to CLAUDE.md

| Project type | Consider adding |
|-------------|-----------------|
| Multi-model comparison | **Model Performance** summary table (Model / Features / Metric / Source) |
| Screening / pipeline | **Pipeline Stages** with throughput numbers (9.5B → 10M → 3K → 46) |
| Data engineering | **Schema Reference** with key tables/columns |
| Deployed service | **API Endpoints** and **Deployment** sections |
| Multi-environment | **Environment Matrix** (which env for which task) |

### Docs to Add

Add domain-specific `docs/{topic}.md` files as complexity grows. Examples:

- **Computational chemistry**: `docking.md`, `scoring.md`, `preprocessing.md`
- **NLP/LLM**: `prompts.md`, `evaluation.md`
- **Computer vision**: `augmentation.md`, `annotation.md`
- **Infrastructure-heavy**: `setup.md`, `deployment.md`

### Data Directory

Choose the layout that fits:

- **Flat `data/results/`**: Simple tabular ML projects with single-file outputs per experiment
- **Per-experiment `data/experiments/exp{NN}_*/`**: Projects with multi-file outputs, large artifacts, or complex pipelines (docking, simulation, multi-stage screening)
- **Hybrid**: Use both — `data/results/` for notebook outputs, `data/experiments/` for script outputs

### What to Keep vs. Drop

| Section | Keep if... | Drop if... |
|---------|-----------|------------|
| Terminology | You have ambiguous terms that cause AI mistakes | Domain is simple and unambiguous |
| `findings.md` | Running many experiments iteratively | One-shot analysis or ETL project |
| Per-exp files + INDEX render | >10 experiments | <10 experiments — a single file is fine |
| Pipeline Modules | Package has >3 modules | Simple single-module project |
| Test Conventions | Using pytest markers | No test suite |
| `kb/meetings.md` + vector index | Team project with recurring syncs OR papers/transcripts to search | Solo project with no long-form corpus |
| `setup.md` | Complex env (GPU, Docker, compiled deps) | Simple pip/conda setup |

### Scaling

- **Small project (1-10 experiments)**: CLAUDE.md + a single `docs/experiments.md` may be enough. Skip the per-exp split, skip the render script, skip the vector index. Don't pay for infrastructure you don't need yet.
- **Medium project (10-30 experiments)**: Adopt the full per-exp file layout from day one. `docs/findings.md`, `tools/render_index.py`, archive rule. Skip `docs/kb/` vector index unless you have a real corpus of papers/transcripts.
- **Large project (30+ experiments)**: Everything above + `docs/kb/` vector index for literature/meetings/transcripts + `/find-exp` skill. Aggressively enforce the size caps. CLAUDE.md is a TOC, not a textbook. Periodically re-archive `progress.md` and `findings.md`.

### Migration from monolithic experiments.md

If you have an existing `docs/experiments.md` over ~1000 lines, splitting is a one-time job:

1. Parse the file by `### Experiment N:` headers (or your equivalent).
2. For each block, write `docs/experiments/exp_{NN}_{slug}.md` with frontmatter inferred from the takeaway/results table.
3. Run `tools/render_index.py` to produce `INDEX.md`.
4. Replace `docs/experiments.md` with a single line: `Moved to docs/experiments/. See INDEX.md.` (or delete it).
5. Update CLAUDE.md links.

A 30-line python script handles this. Do it once when the file passes ~1500 lines — don't grind it out at 200 lines.
