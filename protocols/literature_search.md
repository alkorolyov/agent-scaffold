# Literature Search Protocol

Follow this protocol exactly whenever asked to search for papers on a topic or add papers to the KB.

**Input is always free-text from the user — never DOIs.** The user describes a topic, an intent ("refetch the broken ones", "audit KB"), or a list of paper titles. DOIs and slugs are internal artifacts the protocol must derive; do not ask the user for them.

---

## Phase 0 — Mode selection

Inspect the user's request and pick exactly one mode. If unclear, ask the user a one-line clarifying question — do not guess.

| User says... | Mode | Where to start |
|---|---|---|
| "find papers on X", "add papers about Y", "search for Z" | **topic** | Phase 1 |
| "refetch the broken ones", "retry placeholders", "fix unfetchable entries" | **retry-placeholders** | Phase 0a |
| "audit the KB", "what's missing/wrong", "check for orphans" | **audit** | Phase 0b |
| "fill in entries for raw PDFs without entries", "regenerate missing entries" | **regen-from-raw** | Phase 0c |
| "rewrite \<title\>" or "redo the X paper" | **rewrite-named** | Phase 0d |

The user will not give you a DOI or slug. You derive them by scanning `docs/kb/literature/` and `docs/kb/literature/raw/`.

### Phase 0a — retry-placeholders

```bash
grep -l "^status: placeholder" docs/kb/literature/*.md
```

For each match, extract the DOI from frontmatter (`grep "^doi:"`) and re-run Phase 2 fetch. If the new fetch returns a real PDF or ≥500 B abstract, proceed to Phase 3 to overwrite the placeholder. If it still returns a stub, leave the placeholder unchanged and report which DOIs are persistently unfetchable.

### Phase 0b — audit

Run all four checks and report; do not change files until the user confirms which to fix:

1. **Placeholders awaiting refetch:** `grep -l "^status: placeholder" docs/kb/literature/*.md`
2. **Orphan PDFs (raw exists, no entry):**
   ```bash
   for pdf in docs/kb/literature/raw/*.pdf; do
     slug=$(basename "$pdf" .pdf)
     [ ! -f "docs/kb/literature/$slug.md" ] && echo "ORPHAN: $slug"
   done
   ```
3. **Stub abstracts mislabeled:**
   ```bash
   for abs in docs/kb/literature/raw/*_abstract.md; do
     bytes=$(wc -c < "$abs")
     [ "$bytes" -lt 500 ] && echo "STUB ($bytes B): $abs"
   done
   ```
4. **Frontmatter / disk mismatch:** for each entry, confirm `file_type` matches what's actually in `raw/<slug>*`.

Report findings as a table; let the user pick which to act on.

### Phase 0c — regen-from-raw

Find PDFs in `raw/` without a corresponding entry (Phase 0b check 2). For each, treat the PDF as the source and run Phase 3 directly (skip Phase 1/2 — DOI is the slug, source is on disk).

### Phase 0d — rewrite-named

User gives a paper title or topic phrase. Find the existing entry by title:

```bash
grep -l -i "<phrase from user>" docs/kb/literature/*.md
```

If exactly one match: extract DOI from frontmatter, treat the existing `raw/<slug>*` as source, run Phase 3 to overwrite. If multiple matches or none: ask the user to disambiguate. Never guess.

---

## Phase 1 — Search

1. Use `WebSearch` to find the top papers on the given topic. Queries like:
   - `"<topic>" site:pubmed.ncbi.nlm.nih.gov`
   - `"<topic>" DOI filetype:pdf`
   - `"<topic>" review 2020..2025`
2. For each candidate, resolve the **exact DOI** — verify title + author via CrossRef:
   ```bash
   curl -s "https://api.crossref.org/works/<DOI>" | python3 -c "import json,sys; w=json.load(sys.stdin)['message']; print(w['title'][0], w.get('author',[''])[0])"
   ```
   If CrossRef title does not match your target paper, **discard the DOI and search again**. Never guess DOIs.
3. Check for duplicates before fetching:
   ```bash
   grep -r "<DOI>" docs/kb/literature/*.md
   ```
   Skip any DOI already in the KB.
4. Score each candidate for project relevance — defined in the project's CLAUDE.md under `## Knowledge Base`. Drop papers with no direct relevance.

Target: 5 papers per topic unless user specifies otherwise.

---

## Phase 2 — Fetch

For each confirmed DOI, invoke the fetch-paper skill:

```
/fetch-paper <DOI> docs/kb/literature/raw/
```

The skill handles slug derivation, the fetch, and stub validation — it returns `file_type` directly.

After fetch, verify what was saved:
```bash
ls -lh docs/kb/literature/raw/<slug>*
```

Record the result for each paper as exactly one of:
- `pdf` — a PDF file is present
- `abstract_md` — `*_abstract.md` is present **AND** contains a real abstract (≥500 bytes of prose, not just metadata)
- `unfetchable` — `*_abstract.md` is a stub with no abstract (typically <300 bytes)

### Frontmatter fields: `file_type` vs `status`

`file_type` and `status` are orthogonal. `file_type` describes what is on disk in `raw/`; `status` describes the entry itself.

| `file_type` | `status` | Meaning |
|---|---|---|
| `pdf` | `complete` | Full entry, all sections sourced from PDF and verified |
| `abstract_md` | `abstract_only` | Real abstract retrieved; Method/Key Result are thin or absent (intentional) |
| `unfetchable` | `placeholder` | No usable source; entry is metadata-only awaiting refetch |
| any | `flagged` | Entry has known issues — needs review/rewrite. Add `## Flag` section explaining why |

`status: complete` requires `file_type: pdf`. `status: abstract_only` requires `file_type: abstract_md` (real, ≥500 B). `status: placeholder` requires `file_type: unfetchable`.

---

## Phase 3 — Write KB Entry

### Single-source rule (read this first)

**The ONLY source for entry content is the file in `docs/kb/literature/raw/<slug>*`.** Nothing else. Specifically forbidden during entry writing:

- ❌ `WebFetch` to PMC, PubMed, bioRxiv, ACS, publisher pages, ResearchGate, etc.
- ❌ `WebSearch` to find numbers, abstracts, or method details
- ❌ Reading other entries in `docs/kb/literature/` and reusing their content
- ❌ Training memory / general knowledge about the paper
- ❌ Inferred or "likely" content based on the title

If a number, method, or claim is not present in the raw file, **it does not go in the entry.** Period.

### MANDATORY: Read before writing

Before writing a single word of content for a paper:
- If `pdf`: `Read` the PDF file. Read at least the abstract + methods + results sections. Note the page numbers of key claims.
- If `abstract_md`: `Read` the abstract stub. It contains CrossRef abstract only — no full text. Method/Result sections must be very thin or absent.
- If `unfetchable`: do **not** write a content entry. Either skip the paper entirely, or — only if the user explicitly wants a placeholder — write a metadata-only stub (see below).

**Never write content from training data or memory.**

### Unfetchable handling

Entry must contain ONLY:
- Frontmatter (with `file_type: unfetchable`)
- Title, Authors, Year, DOI header
- `## Status`: `Source not retrieved. Only DOI metadata available — no abstract, no full text. Re-attempt fetch later or remove from KB.`

No Abstract, no Method, no Key Result, no Relevance, no Takeaway, no Limitations.

### Entry file

Save to: `docs/kb/literature/<slug>.md`

```markdown
---
doi: <doi>
title: "<exact title from source>"
authors: "<First Author, Second Author et al.>"
year: <year>
tags: [tag1, tag2, ...]
file_type: pdf | abstract_md | unfetchable
status: complete | abstract_only | placeholder | flagged
---

# <Title>

**Authors**: <authors>
**Year**: <year>
**DOI**: <doi>

## Abstract

<Extract verbatim or closely paraphrased from source page 1.>

## Method

<Sourced from paper. Cite page in parentheses where useful, e.g. "(p. 3)".>

## Key Result

<Quantitative results with exact numbers from the paper. Never round or extrapolate.>

## Relevance

<How this paper relates to this project specifically — see project CLAUDE.md for domain context.>

## Takeaway

<One or two sentences: the single most actionable conclusion for this project.>

## Limitations

<Limitations stated in the paper or directly observable from the methods. Do not invent.>
```

### Rules that prevented failures before

| Rule | Violation that caused it |
|---|---|
| `file_type` must match `ls raw/<slug>*` output | Two entries had `abstract_md` despite PDFs being present |
| Abstract must come from page 1 of source | Four entries used boilerplate "not available" |
| Benchmark numbers must be exact from paper | Optuna entry had invented "hundreds of workers", "3–5× pruning" not in paper |
| Samplers/features only from the paper's year | Optuna 2019 entry included NSGA-II which appeared in Optuna later |
| If abstract_md only: write "from abstract only" and avoid specific numbers not present | CycPeptMPDB had fabricated dataset stats |
| Stub `_abstract.md` (<500 B / "PDF not available") = `unfetchable`, not `abstract_md` | Multi_CycGT and Fromer 2023 had empty 218–342 B stubs labeled `abstract_md` and filled with fabricated content |
| No WebFetch / WebSearch / external scrape during entry writing | Agent WebFetched PMC + PubMed to scrape numbers and wrote them as if from the abstract |
| `(from abstract only)` prefix is reserved for content actually IN the abstract | Used as camouflage while content was scraped from PubMed/PMC summary pages |
| No biographical claims about authors unless in source | Relevance asserted "same research group, Tokyo Institute of Technology" — not in the source |

**Cross-reference escape hatch.** If a cross-paper link is genuinely useful, state it with an explicit provenance tag: `(cross-ref: <slug>)`. Without the tag, the claim must be in the source or removed.

---

## Phase 4 — Verify

After writing each entry:
1. Pick the 3 most specific quantitative claims. For each, locate it in the source with a concrete pointer (page number for PDF, line number for `abstract_md`).
2. If any claim cannot be found in the source: remove it.
3. Confirm `file_type` in frontmatter matches what `ls raw/` shows.
4. For `unfetchable` entries: confirm only Status + frontmatter — no Method, Key Result, etc.
5. Grep the authoring trail: any `WebFetch` / `WebSearch` after Phase 2 is a red flag — re-audit the entry.
6. Scan Relevance / Takeaway / Limitations for biographical claims. For each, either find it in `raw/<slug>*` or replace with `(cross-ref: <slug>)`. If neither, delete it.

---

## Phase 5 — Cleanup

- Delete any stale `*_abstract.md` stub in `raw/` if a PDF for the same paper is present.

---

## Entry Quality Checklist

- [ ] `file_type` matches disk AND respects the stub rule
- [ ] `status` matches `file_type` per the combination table
- [ ] Abstract is from source (not boilerplate)
- [ ] No fabricated numbers — every stat traceable to a page/line in `raw/<slug>*`
- [ ] Relevance section mentions a specific component of this project
- [ ] `raw/` contains the source file used (and only that file was used)
- [ ] No `WebFetch` / `WebSearch` / external scrape was run between Phase 2 and Phase 4
- [ ] `placeholder` entries contain only Status + frontmatter, no fabricated sections
- [ ] No biographical claims unless in source OR carrying an explicit `(cross-ref: <slug>)` tag
