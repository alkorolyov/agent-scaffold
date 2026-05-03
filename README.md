# agent-scaffold

Reusable protocols, tools, and skills for AI-assisted research and ML projects with Claude Code.

Clone once per machine. Reference protocols by path. Copy local tools per project.

---

## What's included

| Path | Type | Purpose |
|------|------|---------|
| `protocols/literature_search.md` | Protocol | Phase-by-phase literature search, fetch, and KB entry writing |
| `tools/exp.py` | Local tool | Experiment record management (new / update / list / show) |
| `tools/render_index.py` | Local tool | Regenerate `docs/experiments/INDEX.md` from frontmatter |
| `tools/check_drift.py` | Local tool | Stop-hook drift detector for docs/ consistency |
| `global/tools/fetch_paper.py` | Global tool | Fetch papers by DOI (Sci-Hub / OpenAlex / CrossRef fallback) |
| `global/skills/fetch-paper/` | Global skill | Agentic wrapper: slug derivation + fetch + stub validation |
| `skills/log-exp/` | Local skill | `/log-exp` — guided experiment write-up |
| `skills/find-exp/` | Local skill | `/find-exp` — search experiment index |
| `skills/find-kb/` | Local skill | `/find-kb` — search knowledge base |
| `design.md` | Reference | Full design rationale, template structures, architecture decisions |

---

## Install (once per machine)

```bash
git clone <repo-url> ~/agent-scaffold
bash ~/agent-scaffold/install.sh
```

`install.sh` copies global skills to `~/.claude/skills/`. Global tools are called by direct path — no install needed.

---

## Use in a new project

**1. Copy local tools:**
```bash
cp ~/agent-scaffold/tools/*.py <project>/tools/
```

**2. Copy local skills:**
```bash
cp -r ~/agent-scaffold/skills/* <project>/.claude/skills/
```

**3. Reference protocols in `CLAUDE.md`:**
```markdown
**Literature search**: follow `~/agent-scaffold/protocols/literature_search.md`
```

**4. Add project-specific relevance topics** to CLAUDE.md under `## Knowledge Base` — the literature search protocol uses this to score paper candidates.

---

## Update

```bash
cd ~/agent-scaffold && git pull
bash ~/agent-scaffold/install.sh   # re-copy updated global skills
```

Local tool copies in projects are not auto-updated — re-copy manually when needed.

---

## Contributing back

Protocols improve through real failures across projects. When a new rule is added to any project's protocol copy, update the canonical file here and commit.

See [design.md](design.md) for full architecture rationale, document templates, and scaling guidance.
