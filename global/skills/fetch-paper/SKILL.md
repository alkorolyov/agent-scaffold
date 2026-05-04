# /fetch-paper

Fetch a journal paper by DOI and save to the KB raw directory.

**Not for arXiv** — use WebFetch for arXiv preprints.

## Args

`/fetch-paper <DOI> [output_dir]`

- `DOI`: exact DOI string (e.g. `10.1093/nar/gkr431`)
- `output_dir`: optional, defaults to `docs/kb/literature/raw/`

## Steps

1. Extract the DOI: first whitespace-delimited token from args. Do not modify it.

2. Derive slug: take the last `/`-separated component of the DOI, replacing any remaining `/` with `_`.
   - `10.1093/nar/gkr431` → `gkr431`
   - `10.1145/3292500.3330701` → `3292500_3330701`
   - `10.1021/acs.jcim.3c01661` → `acs.jcim.3c01661`

3. Set `output_path = <output_dir>/<slug>` (no extension — CLI adds it).

4. Run the fetch:
   ```bash
   python3 ~/projects/personal/agent-scaffold/global/tools/fetch_paper.py <DOI> --output <output_path> --json
   ```

5. Parse the JSON result. If `file_type` is `abstract_md`, validate the file:
   ```bash
   wc -c <output_path>_abstract.md
   grep -c "not available\|no abstract\|Full PDF" <output_path>_abstract.md
   ```
   - size ≥ 500 bytes AND grep count = 0 → real `abstract_md`
   - size < 500 bytes OR grep count > 0 → stub → report `file_type: unfetchable`

6. Report back: DOI, slug, file_path, file_type (`pdf` | `abstract_md` | `unfetchable`), size_mb, and `text_sidecar` if present.

## Plain-text sidecar (PDFs only)

When `file_type == pdf`, the tool also writes `<slug>.txt` next to `<slug>.pdf` via `pdftotext -layout`. Best-effort: silently skipped if `pdftotext` is missing, the PDF is encrypted, or extraction times out. The `text_sidecar` field in the JSON result holds the path on success, `null` otherwise.

The sidecar lets `grep` reach into full text across the corpus without re-parsing PDFs:

```bash
grep -l "cyclic permeability" docs/kb/literature/raw/*.txt
```

It is **not** an entry source — Phase 3 of the literature_search protocol still treats `raw/<slug>.pdf` as the canonical source. The sidecar exists for retrieval, not for content authoring.
