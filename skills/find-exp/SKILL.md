# /find-exp

Search the experiment index without loading every per-exp file.

## Usage

`/find-exp <query>`

Examples:
- `/find-exp mmgbsa`
- `/find-exp status:done outcome:refuted`
- `/find-exp tags:benchmark`

## Steps

1. Parse the query for filter tokens (`status:`, `outcome:`, `tags:`, `track:`). Remaining words are free-text.
2. Run targeted grep against frontmatter in `docs/experiments/`:
   ```bash
   grep -l "<free-text>" docs/experiments/exp_*.md 2>/dev/null
   ```
   Then for structured filters:
   ```bash
   tools/exp.py list [--status=X] [--outcome=X] [--tag=X]
   ```
3. Return matching experiment numbers and one-line summaries. Offer to show full detail for any:
   ```bash
   tools/exp.py show <N>
   ```
4. If the user wants the full file: `Read docs/experiments/exp_NN_*.md`.

## When to use this over reading INDEX.md

`/find-exp` is faster for filtered queries. Read `docs/experiments/INDEX.md` directly when you need the full table overview.
