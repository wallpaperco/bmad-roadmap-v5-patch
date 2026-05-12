# Phase 3 — Epics & Stories

**Goal:** Decompose the PRD/UX into epics and stories, each story with adversarial + edge-case reviews. Validate implementation readiness.

**Exit:** readiness check returns `pass`.

---

## Steps

1. **Run `/bmad-create-epics-and-stories-v2`** → generates:
   - `_bmad-output/planning-artifacts/epics.md` (epic list + coverage tables)
   - `_bmad-output/implementation-artifacts/stories/<N.M>-<slug>.md` (one file per story)
   - Each story includes adversarial + edge-case reviews (no Kateb pass needed afterwards)

2. **Run `/bmad-check-implementation-readiness`** → produces `_bmad-output/planning-artifacts/implementation-readiness-report-{YYYY-MM-DD}.md`.

   Looks for:
   - PRD ↔ epics FR coverage (every PRD FR must map to ≥1 epic)
   - UX journey ↔ epic mapping (every journey covered by an epic)
   - Architecture coverage (every ARCH item touched by ≥1 story)
   - Story quality (every story has ACs, edge cases, DoD, frontmatter)

   Outcomes:
   - **PASS** — proceed to Phase 4
   - **FAIL** — fix gaps (re-run `/bmad-create-epics-and-stories-v2` for the gaps, or amend PRD/UX if scope is wrong)

---

## What v5 explicitly doesn't add to stories

- No `Design Reference` block (no Claude Design bundle URLs)
- No screen-specific mockup pointers (no per-screen specs)
- Saneh (Phase 5) reads the UX spec § for visual intent at build time

---

## Phase exit checklist

- [ ] `epics.md` exists with epic list + FR coverage table
- [ ] Every story has its own `<N.M>-<slug>.md` file in `stories/`
- [ ] Every story passes adversarial + edge-case reviews
- [ ] `implementation-readiness-report-{YYYY-MM-DD}.md` reports `pass`
- [ ] User approved the readiness report

On exit, update `roadmap-progress.yaml`:
```yaml
3-epics-stories:
  status: complete
  completed: "{today}"
  epics_count: <int>
  stories_count: <int>
  buildable_stories: <int>
  research_stories: <int>
  fr_coverage: "{N/M} ({X}%)"
  readiness_check: pass
  artifacts:
    epics: "_bmad-output/planning-artifacts/epics.md"
    stories: "_bmad-output/implementation-artifacts/stories/"
    readiness_report: "_bmad-output/planning-artifacts/implementation-readiness-report-{YYYY-MM-DD}.md"
```

Advance to Phase 4.
