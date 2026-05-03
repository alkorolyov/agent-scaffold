# /find-kb

Search the knowledge base (literature, meeting notes) in `docs/kb/`.

## Current state: grep-based (vector index not yet set up)

Until `tools/index_kb.py` is implemented and the index is built, use ripgrep:

```bash
grep -r --include="*.md" -l "<query>" docs/kb/
grep -r --include="*.md" -n "<query>" docs/kb/ | head -30
```

## When the vector index is available

Run `tools/index_kb.py search "<query>"` to return top-k `(file:line, snippet)` references, then `Read` matched files. Never embed chunks directly — always read the source file.

## Scope

Index covers only:
- `docs/kb/literature/**/*.md`
- `docs/kb/meetings.md`
- `docs/kb/transcripts/` (if present)

For experiments, use `/find-exp`. For structured data (findings, progress), read those files directly.
