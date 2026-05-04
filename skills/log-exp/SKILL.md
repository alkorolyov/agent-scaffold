# /log-exp

Guide an experiment write-up: create or update an experiment record in `docs/experiments/`.

## Steps

0. **Check for overlap before scaffolding new.** Read `docs/experiments/INDEX.md` — every section, but especially **Refuted Hypotheses** and **Open / Inconclusive**. Confirm the proposed work does not duplicate or directly re-test a refuted hypothesis. If it overlaps, surface that to the user before scaffolding and ask whether to proceed (e.g. new conditions, different benchmark, lineage child) or abandon. In the new exp's Goal section, note one of: "Similar to exp_NN — extends/varies in <way>" / "No overlap with prior work" / "Re-test of refuted exp_NN under <new condition>".
1. Ask the user: experiment title/slug (if creating new), or experiment number (if updating existing).
2. For a **new** experiment: run `rec.py exp new "<slug>"` to scaffold the file. Open it and help the user fill in Goal, Method, and any initial notes.
3. **Sceptical second pass — MANDATORY before writing any takeaway.** Pure introspective self-critique is empirically weak ([survey on LLM self-correction](https://www.researchgate.net/publication/385650033)); what works is **tool-grounded critique** ([CRITIC, ICLR](https://openreview.net/forum?id=Sx038qxjek)). For each completed experiment:

   a. **Re-read source artifacts** in `data/experiments/exp_NN_*/` (logs, output csvs, checkpoints). Quote at least one verbatim number from a specific file. Do not paraphrase from memory of the run.
   b. **Determine deterministic flags** — these are objective rules, NOT a subjective confidence rating (verbalized confidence is consistently overconfident — [UQ Survey 2503.15850](https://arxiv.org/html/2503.15850), [ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/ef472869c217bf693f2d9bbde66a6b07-Paper-Conference.pdf)):

      | Flag | Set when |
      |------|----------|
      | `single_seed` | Only one seed was run (auto-set if `n_seeds=1`) |
      | `large_unexpected_gain` | Result improves over current INDEX `Best by Track` by more than 3× the prior `metric_sd`, and the magnitude wasn't predicted in the Goal section |
      | `conflicts_prior` | Outcome contradicts an existing Refuted entry, or new refuted contradicts an existing Best-by-Track entry |
      | `setup_unverified` | One or more setup elements (data split, label assignment, env reproducibility) was not independently verified after the run completed |
      | `interpretation_uncertain` | Multiple plausible interpretations of the result remain after artifact re-read |

   c. **Generate the strongest alternative interpretation.** Ask explicitly: *"What's the most likely reading of these artifacts other than the one I am about to write?"* If the alternative is credible, document it in the body's `## Caveats` section AND add `interpretation_uncertain` to flags.
   d. **List source artifacts**. Every quantitative claim in the takeaway must be traceable to at least one path in `--source-artifacts` (FAIR R1.2 provenance — [Wilkinson et al. 2016](https://www.nature.com/articles/sdata201618)). Inline the source for the headline number, e.g. `takeaway: "ESM2 auc=0.940±0.011 across 5 seeds (data/experiments/exp_03/seeds_summary.csv)"`.

4. Now run the update:
   ```
   rec.py exp update <N> --status=<done|failed> --outcome=<...> --takeaway="<...>"
       [--track=<...>] [--benchmark=<...>]
       [--metric="auc=0.84±0.02"]                          # ±SD recommended; aligns with reproducibility lit
       [--n-seeds=N]                                        # auto-flags single_seed if 1
       [--source-artifacts="path,path"]                     # FAIR R1.2 provenance (mandatory if takeaway has numbers)
       [--flags="single_seed,large_unexpected_gain,..."]    # rule-based, not vibes-based
       [--parent=N] [--related="N,M,..."]
       [--wandb=URL] [--mlflow=run_id] [--dois="..."] [--adr=N]
   ```

   Field guidance:
   - `--benchmark`: pass whenever the evaluation setup (dataset version, split scheme, ground-truth source) differs from earlier runs on the same track.
   - `--metric`: prefer `key=val±sd`. Plain `key=val` works but loses variance information.
   - `--n-seeds`: integer count of seeds aggregated into the metric. Setting `1` auto-adds `single_seed` to flags during render.
   - `--source-artifacts`: comma-separated paths the takeaway depends on. When you later find a wrong artifact, grep this field across all experiments to find every claim that depended on it.
   - `--flags`: deterministic flags from Step 3b. INDEX surfaces these in `## Needs Review`.
   - `--parent` vs `--related`: parent = direct child / lineage; related = cross-cutting link.

5. **If you later discover the takeaway was wrong**, do NOT silently edit it. Use `rec.py exp revise`:
   ```
   rec.py exp revise <N> --reason="<why the original was wrong>" --new-takeaway="<corrected>"
   ```
   This appends the correction to a `revisions:` log (FAIR-style errata, [ELN ten simple rules](https://pmc.ncbi.nlm.nih.gov/articles/PMC11189195/)). The original takeaway stays visible — future agent sessions can see how the error happened, which prevents the same failure mode from recurring. Memory poisoning literature ([MemoryGraft 2512.16962](https://arxiv.org/html/2512.16962v1)) frames this as the core defense: agents that treat memories as ground truth without provenance propagate errors at ~87%/4hr in adversarial settings; the same dynamic compounds honest mistakes.

6. If the result is worth recording as a finding, offer to run:
   ```
   rec.py exp finding <N> "<one-line finding text>"            # positive finding (default)
   rec.py exp finding <N> "<one-line finding text>" --negative # negative / dead-end finding
   ```
7. Run `tools/render_index.py` to refresh `docs/experiments/INDEX.md`.

## Read-time rule (when consulting the KB, not writing)

When you load INDEX.md, a per-experiment file, or a refuted-list takeaway and are about to **propagate** the conclusion (use it to motivate a new experiment, cite it in a write-up, or reject a hypothesis as "already refuted"), treat the takeaway as a **summary, not verified data**:

1. Re-read the underlying `data/experiments/exp_NN_*/` artifacts before propagating.
2. Check the entry's `flags:` field — `single_seed`, `large_unexpected_gain`, etc. are direct warnings.
3. Check the entry's `revisions:` field — if the takeaway has been revised, the failure history is informative.
4. If you cannot verify the original artifact (deleted, lost, etc.), explicitly note `setup_unverified` rather than silently assuming the takeaway is correct.

This rule is the single most load-bearing defense against compounding error. The takeaway is an *index entry*; the data dir is the *truth*.

## Why Step 0 matters

The exp KB is agent-maintained state — the user rarely reads it directly. The cost of a duplicate experiment (running again something already refuted, or re-deriving a result already established) is days of compute. The cost of a 30-second INDEX read is trivial. Always pay the read cost.

INDEX.md is the **recall tier** in the agent memory hierarchy — see `protocols/memory_tiers.md` for the full load order across working / recall / archival.

## Outcome vocabulary

| Value | When |
|-------|------|
| `confirmed` | Hypothesis proven correct |
| `refuted` | Hypothesis disproven — log to prevent re-trying |
| `improved` | Metric improved over baseline (requires `--track` + `--metric`) |
| `parity` | Matched baseline (requires `--track` + `--metric`) |
| `regression` | Worse than baseline (requires `--track` + `--metric`) |
| `infra` | Infrastructure or engineering run — fleet test, worker stability, pipeline smoke test |
| `inconclusive` | Ran but no clear signal |

## infra experiments

Use `outcome: infra` for any run whose primary purpose is validating infrastructure rather than testing a scientific hypothesis. Examples: overnight fleet stability test, new worker image smoke test, cost watchdog validation. These are first-class records — log them the same way, with a clear takeaway about what held up or broke.

If the run produced a **design decision** (e.g., "switch to a different task queue"), that decision belongs in an ADR (`/log-adr`), not in the experiment record.
