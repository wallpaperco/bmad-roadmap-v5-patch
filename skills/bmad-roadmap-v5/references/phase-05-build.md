# Phase 5 — Build

**Goal:** Implement every story end-to-end. Visual iteration via `/impeccable live` on the running dev server. Each story = own branch + PR.

**Exit:** every story in `sprint-status.yaml` is `shipped` (and thus `done`).

---

## Sub-step A — First-epic-only setup

Runs ONCE before the first story of the first epic. Sets up the test infrastructure that every later story will use.

1. **`/bmad-testarch-framework`** — initialize Playwright + test infrastructure (E2E + component tests + visual regression baseline).
2. **`/bmad-testarch-ci`** — scaffold the CI quality pipeline (`.github/workflows/quality.yml` or equivalent).

Mark `roadmap-progress.yaml: 5-build.first_epic_setup_done: true`.

---

## Sub-step B — Pick next story

1. Read `sprint-status.yaml`.
2. Find the next story with `status: backlog` (respecting topological order).
3. Verify its `depends_on` are all `shipped`.
4. Set `roadmap-progress.yaml: 5-build.current_story: "{X.Y}"` and `current_step: 1`.
5. Enter the Story Protocol (see `./story-protocol.md`).

---

## Sub-step C — Story Protocol (9 steps)

Full protocol in `./story-protocol.md`. Summary:

1. **Branch** — `epic-{N}/story-{X.Y}-{slug}`
2. **Saneh — Full-Stack Build** (rewrites the v2 Saneh — reads UX spec + design system from codebase; no Claude Design bundle)
3. **AC-Compliance check** (automated script — verifies every story AC has an entry in Saneh's Implementation Map)
4. **User Review [PAUSE]** — orchestrator prints `/impeccable live` iteration prompt for a new chat; waits for `approved`
5. **`/simplify`** — code-simplifier pass
6. **`/bmad-code-review`** — adversarial code review
7. **PR Review** — pr-review-toolkit (3 agents in parallel)
8. **Verify** — typecheck + lint + tests
9. **`/ship`** — commit + push + PR + merge

After Step 9, the story is marked `shipped` in both `sprint-status.yaml` and `roadmap-progress.yaml`. The orchestrator prints a short notice and STOPS — the user decides when to start the next story.

---

## Sub-step D — End-of-epic

Triggered when the last story of an epic ships. Run:

1. **`/bmad-retrospective`** — extract lessons + assess success metrics
2. **`/bmad-testarch-trace`** — produce traceability matrix (AC ↔ test) + quality-gate decision

Update `roadmap-progress.yaml`:
```yaml
5-build:
  epics:
    {N}:
      retro_done: true
      trace_done: true
      completed: "{today}"
```

Advance to the next epic's first story (Sub-step B) — or, if it was the last epic, mark Phase 5 complete and advance to Phase 6.

---

## Phase 5 escapes

### Mid-story business change

User invokes `/bmad-business-change` mid-story. After the cascade completes:
- Reset the affected story's `current_step` to `2`
- Saneh re-runs with the cascade's diff appended to its prompt
- Story Protocol resumes from Step 2

### Mid-story design-system change

If the user realises the design system needs new tokens or wrappers:
- Pause the story
- Open the design-system repo (or `tokens.css` + wrappers directory)
- Add the missing token / component
- Bump the design-system version (if it's a separate package)
- Resume the story at Step 2 (Saneh re-runs with the new tokens in scope)

### CI failure on `/ship`

If the merged PR triggers a deploy that fails (rare on Phase 5 since Phase 6 is the deploy phase, but possible for projects with continuous-deployment-from-main):
- Revert the merge via `git revert <merge-sha>` + force-push (with user confirmation per CLAUDE.md)
- Reset the story's `current_step` to `8` (Verify) and diagnose

---

## Phase exit checklist

- [ ] Every story in `sprint-status.yaml` has `status: shipped`
- [ ] Every epic's `retro_done: true` and `trace_done: true`
- [ ] No CRITICAL findings from code review or PR review left unresolved
- [ ] `pnpm typecheck && pnpm lint && pnpm test` green on `main`

Advance to Phase 6.
