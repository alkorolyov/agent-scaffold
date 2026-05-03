# /log-exp

Guide an experiment write-up: create or update an experiment record in `docs/experiments/`.

## Steps

1. Ask the user: experiment title/slug (if creating new), or experiment number (if updating existing).
2. For a **new** experiment: run `tools/exp.py new "<slug>"` to scaffold the file. Open it and help the user fill in Goal, Method, and any initial notes.
3. For a **completed** experiment: prompt for status, outcome, takeaway (and track + metric if outcome is improved/parity/regression). Run:
   ```
   tools/exp.py update <N> --status=<done|failed> --outcome=<...> --takeaway="<...>" [--track=<...>] [--metric=<key=value>]
   ```
4. If the result is worth recording as a finding, offer to run:
   ```
   tools/exp.py finding <N> "<one-line finding text>"
   ```
5. Run `tools/render_index.py` to refresh `docs/experiments/INDEX.md`.

## Outcome vocabulary

| Value | When |
|-------|------|
| `confirmed` | Hypothesis proven correct |
| `refuted` | Hypothesis disproven — log to prevent re-trying |
| `improved` | Metric improved over baseline (requires `--track` + `--metric`) |
| `parity` | Matched baseline (requires `--track` + `--metric`) |
| `regression` | Worse than baseline (requires `--track` + `--metric`) |
| `infra` | Infrastructure/tooling experiment (no scientific outcome) |
| `inconclusive` | Ran but no clear signal |
