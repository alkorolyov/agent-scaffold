# Agent Memory Tiers

How the agent should load project state across a session — adapted from the [MemGPT](https://arxiv.org/abs/2310.08560) hierarchical-memory pattern, with operational thresholds drawn from [Long Context vs RAG (2025)](https://arxiv.org/html/2501.01880v1) and [A-MEM (2025)](https://arxiv.org/pdf/2502.12110).

This document tells the agent **what to load when**. Follow it instead of grepping everything every turn.

---

## The three tiers

```
  WORKING        RECALL                  ARCHIVAL
  (always-on)    (load on session start) (load on demand)
  ──────────     ───────────────────     ──────────────────────
  CLAUDE.md      docs/experiments/INDEX  docs/experiments/exp_NN_*.md
  progress.md    docs/adrs/INDEX         docs/kb/literature/<slug>.md
  MEMORY.md      docs/findings.md        docs/kb/literature/raw/<slug>.{pdf,txt}
                                         data/experiments/exp_NN_*/
```

### Working set — loaded every turn

- **CLAUDE.md** (project + parent dirs) — always in context
- **progress.md** — active sprint, current priorities, what's running now
- **MEMORY.md** — auto-memory index (loaded by the runtime)

These are small, hot, and define what "now" means. Keep them under ~200 lines each.

### Recall set — load on session start, keep available

- **`docs/experiments/INDEX.md`** — full table + Best by Track/Benchmark + Refuted + Open + Lineage + Related Networks + External Pointers
- **`docs/adrs/INDEX.md`** — accepted decisions + superseded-by chains
- **`docs/findings.md`** — curated positive + negative findings

These are summaries-of-summaries. They tell the agent *what exists* without spending tokens on full content. INDEX.md is the single most important file the agent loads from this tier — it's how duplicate experiments and refuted hypotheses get caught **before** the agent proposes new work.

### Archival — load only when the recall tier points there

- **`docs/experiments/exp_NN_*.md`** — full per-experiment write-up. Load only when:
  - INDEX flagged a similar prior run (`/log-exp` Step 0)
  - the user asked about a specific experiment by number
  - a write-up is being drafted that cites this experiment
- **`docs/kb/literature/<slug>.md`** — load only when generating a write-up that cites the paper, or when planning an experiment in that paper's domain.
- **`docs/kb/literature/raw/<slug>.{pdf,txt}`** — load only when verifying a quoted number or recipe-level method during a write-up. The `.txt` sidecar is preferred for grep across the corpus.
- **`data/experiments/exp_NN_*/`** — the actual run artifacts. Load when (a) re-verifying a markdown summary against truth, (b) drafting external content per the `write_up.md` protocol.

---

## Why this matters

Loading everything every turn defeats the design. The 1M-token attention window is unreliable past ~32K–64K tokens of dense content (the "lost in the middle" problem); even when nominally fitting, retrieval accuracy drops 10–20 points compared to focused loading. The recall tier is engineered to be small and dense so it stays inside reliable attention range; the archival tier expands lazily and only when a recall pointer justifies it.

---

## When to switch from grep to RAG

The current design uses grep + frontmatter filters across the recall + archival tiers. Heuristics for when to graduate:

| Signal | Threshold | What to switch to |
|---|---|---|
| Total markdown content in `docs/kb/` exceeds reliable attention | ~200 entries × ~4KB ≈ 800KB ≈ 200K tokens | sentence-level vector index over entries (not chunks) |
| Full-text search across PDF sidecars becomes slow / noisy | ~50 PDFs OR ~5 MB of `.txt` | targeted index over `raw/<slug>.txt` |
| Cross-experiment "find similar to this idea" | when `related:` graph density > ~5 edges/exp on average | embed exp takeaways, cluster |

**The trigger is attention reliability, not raw token count.** Long-context models can technically hold 1M tokens; they cannot reliably *use* dense content past ~64K. The 200-entry cutoff is roughly where our recall tier hits this wall.

Until then: grep + frontmatter filters + INDEX.md beat retrieval pipelines on both cost and recall for our scale.

---

## Cross-tier rules

1. **Archival never replaces recall.** If a fact is load-bearing (decision, refuted hypothesis, current best), it must surface in INDEX or findings — not only in a per-experiment file.
2. **Recall summaries must trace to archival truth.** `write_up.md` makes this enforceable at write-up time: re-read source artifacts, fix any drift in markdown, then draft.
3. **External pointers (W&B, MLFlow, DOI, ADR) live in archival but are surfaced in recall** via INDEX's "External Pointers" section. The agent should follow them out-of-tier when the markdown isn't enough.
4. **Working tier is for "today" only.** Don't dump experiment notes there. Move durable facts to archival, leave only active sprint state in `progress.md`.

## Read-time rule (the core defense against error propagation)

When loading a recall-tier entry — any takeaway in INDEX.md, any line in the Refuted Hypotheses table, any Best by Track row — the agent must treat it as a **summary, not verified data**, especially before:

- proposing a new experiment that builds on its conclusion
- citing it in a Confluence / report draft
- rejecting a hypothesis as "already refuted"
- recommending a parameter setting based on a prior best

In each of these cases the agent must re-read the underlying `data/experiments/exp_NN/` artifacts (or `docs/kb/literature/raw/<slug>.{pdf,txt}` for literature) **before** propagating. Check `flags:` for review markers (`single_seed`, `large_unexpected_gain`, `conflicts_prior`, etc.) and `revisions:` for known correction history.

This rule exists because the documented failure mode of agent-maintained KBs is exactly this: agents treat retrieved summaries as ground truth and amplify whatever errors are baked in ([MemoryGraft (2512.16962)](https://arxiv.org/html/2512.16962v1), [Memory Control Flow Attacks (2603.15125)](https://arxiv.org/html/2603.15125v1)). The defense is provenance-checking before propagation ([FAIR R1.2](https://www.go-fair.org/fair-principles/)). The takeaway is an *index*; the data dir is the *truth*.
