---
name: log-adr
description: Create or update an Architecture Decision Record in docs/adrs/. Use when a significant design choice is made — technology selection, protocol change, architectural pivot — especially choices that rule out alternatives or can be superseded later.
---

# /log-adr

Guide an Architecture Decision Record write-up.

## When to create an ADR

- Choosing a technology or architecture (task queue, storage backend, wire protocol)
- Deciding NOT to use something and why — prevents re-litigating closed decisions
- Any pivot significant enough that reversing it would require substantial rework
- **Not** for experiment results (use `rec.py exp`) or sprint plans (use `docs/progress.md`)

## Steps

### Creating a new ADR

1. Run:
   ```
   rec.py adr new "<slug>"
   ```
2. Open the created file. Help the user fill in:
   - **Context**: what situation or failure triggered this decision
   - **Decision**: the choice, stated in one clear sentence
   - **Consequences**: what this enables, what it closes off, what must happen next
3. Accept the ADR:
   ```
   rec.py adr update <N> --status=accepted --decision="<one-line summary>"
   ```
4. Run `tools/render_index.py` to refresh `docs/adrs/INDEX.md`.

### Superseding an existing ADR

When a prior decision is overturned:

1. Create the replacement ADR first (steps above).
2. Mark the old one superseded:
   ```
   rec.py adr update <old_N> --status=superseded --superseded-by=<new_N>
   ```

### Retiring a stale standalone doc

If a floating `docs/*.md` is really a design decision (e.g., `reliability_design.md`):

1. Create the ADR: `rec.py adr new "<slug>"`
2. Fill in context/decision/consequences from the old doc.
3. Delete the old doc.
4. If the decision is already superseded, immediately mark it so (step above).

## Outcome vocabulary

| Status | When |
|--------|------|
| `proposed` | Decision drafted, not yet committed |
| `accepted` | Decision is active and governing |
| `superseded` | Replaced by a newer ADR (requires `--superseded-by`) |
