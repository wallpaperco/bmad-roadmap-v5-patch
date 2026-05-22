# Phase 5 — Build

**Goal:** Implement every story end-to-end. Visual iteration via `/impeccable live` on the running dev server. **Branch per epic. One PR per epic.**

**Exit:** every story in `sprint-status.yaml` is `shipped` (and thus `done`).

---

## Sub-step A — First-epic-only setup

Runs ONCE before the first story of the first epic. Sets up the test infrastructure every later story uses.

1. **`/bmad-testarch-framework`** — initialize Playwright + test infrastructure (component tests + visual regression baseline). NO E2E suite expansion here — kept minimal per Phase 5 test discipline.
2. **`/bmad-testarch-ci`** — scaffold the CI quality pipeline (`.github/workflows/quality.yml` or equivalent).

Mark `roadmap-progress.yaml: 5-build.first_epic_setup_done: true`.

---

## Sub-step B — Pick next story

1. Read `sprint-status.yaml`.
2. Find the next story with `status: backlog` (respecting topological order).
3. Verify its `depends_on` are all `committed` or `shipped`.
4. Set `roadmap-progress.yaml: 5-build.current_story: "{X.Y}"` and `current_step: 1`.
5. Enter the Story Protocol (see `./story-protocol.md`).

---

## Sub-step C — Story Protocol (9 steps, epic-branched)

Full protocol in `./story-protocol.md`. Summary:

1. **Branch** — `epic-{N}` (created on first story of the epic; subsequent stories check out the same branch)
2. **Saneh — Full-Stack Build** — reads UX spec + design system from codebase. Test Writing Discipline enforced (1-3 tests per AC, no E2E, skip visual-only ACs).
3. **AC-Compliance check** (automated script — verifies every story AC has an entry in Saneh's Implementation Map)
4. **(removed — per-story User Review PAUSE)** — visual review now happens post-ship per epic via `bmad-epic-flow-demo` (see § Post-ship review below). Saneh's output flows directly into Step 5 without a pause. The whole story protocol is now autonomous under `/goal`.
5. **Simplify** — sequential in-context skills (code-reuse + code-quality, efficiency merged into code-quality in 2026-05) — autonomous, no user prompts
6. **Code Review** — sequential in-context skills (adversarial-general / Blind Hunter + edge-case-hunter + light-review-acceptance) — autonomous, no user prompts
7. **PR Review** — single in-context skill (light-review-silent-failure). pr-tests reviewer retired in this revision to avoid over-testing pressure.
8. **Verify** — typecheck + lint + tests
9. **`/commit-story`** — local commit on `epic-{N}` branch. **Step 9.0 invokes `bmad-protocol-compliance-check`** which verifies the story file's `## Protocol Audit Trail` section has every expected entry — halts the commit if any step's bullet is missing. **NO push, NO PR.** Push + PR happen once at end-of-epic.

Steps 5–7 use the DECIDE-AND-LOG pattern (any judgment call is recorded in the story file's "## Autonomous Decisions" section instead of pausing for user input). The user reviews these decisions at post-ship visual review time (end-of-epic).

After Step 9, the story is marked `committed` in both `sprint-status.yaml` and `roadmap-progress.yaml`. Under `/goal` the orchestrator advances to the next story in the same epic without stopping; without `/goal` it prints a short notice and stops.

---

## Sub-step D — End-of-epic

Triggered when the last story of an epic is `committed`. Run in order:

1. **`/bmad-extract-deferrals`** — walk the epic's commit messages, extract deferred findings into `_bmad-output/implementation-artifacts/deferred-work.md`. Catches the LOW/MEDIUM findings the per-story protocol punted via the auto-fix policy.
2. **`/bmad-testarch-trace`** — produce traceability matrix (AC ↔ test) + quality-gate decision for the entire epic. Reads `deferred-work.md` and surfaces a Deferrals Registry section.
3. **`/ship-epic`** — rebase main → push `epic-{N}` → open one PR for the whole epic → wait for CI → squash-merge → sync local main.
4. **`/bmad-epic-flow-demo`** — post-ship visual review cycle (NEW — replaces the per-story Step 4 PAUSE that was removed in this revision). See § Post-ship review below.

`/ship-epic` updates `roadmap-progress.yaml`:
```yaml
5-build:
  epics:
    {N}:
      status: shipped
      trace_done: true
      shipped_at: "{today}"
      pr_url: "<PR URL>"
```

It also flips every story in the epic from `committed` → `shipped`. Then `bmad-epic-flow-demo` adds `polish_status` (`shipped` / `skipped-no-ui` / `skipped-no-changes` / `skipped-user-abandon`) and `polish_pr_url` / `polish_merge_sha` when applicable.

Advance to the next epic's first story (Sub-step B) — or, if it was the last epic, mark Phase 5 complete and advance to Phase 6.

**Retrospective is intentionally NOT part of this flow** — removed in this revision to keep end-of-epic lean. If you want a retro for a specific epic, invoke `/bmad-retrospective` manually before `/ship-epic`.

---

## Post-ship review (Sub-step D, step 4)

`bmad-epic-flow-demo` runs IMMEDIATELY after `/ship-epic` returns success. It's the only PAUSE in the whole epic flow — every other step (per-story protocol + extract-deferrals + trace + ship) runs autonomously under `/goal`.

**What it does:**
1. Detects the epic's UI surface area (new pages/routes between the merge base and main).
2. If zero new routes (pure-infra epic like `Epic 1: Platform Foundation`) → emits a one-line summary and ends. No polish branch, no PAUSE. The orchestrator advances to Epic {N+1} immediately.
3. Otherwise:
   - Creates `epic-{N}-polish` branch from main (empty)
   - Pushes the empty branch
   - Prints: routes added + suggested journey + `/impeccable live` paste-ready prompt
   - PAUSES waiting for the user signal
4. User iterates in a separate chat against `epic-{N}-polish`. The orchestrator goes idle in this chat.
5. User returns and signals:
   - `approved` → if the polish branch has commits: push + open PR + watch CI + squash-merge + delete branch + sync main. If no commits: delete the empty branch and close the epic.
   - `skip-polish` → abandon any commits, delete the branch, close the epic.
   - `iterate <note>` → reprint the demo prompt (e.g., after losing the iteration chat).

**Why post-ship rather than per-story:**
- `/goal Epic N` runs end-to-end autonomously through merge — no per-story pause, no `/goal` interruption.
- Visual review happens against `main` (production-like), not a transient branch.
- Iterations create their own commit history on `epic-{N}-polish` → main stays clean.
- CI runs once at the end of polish, not per-iteration commit.
- Pure-infra epics (no UI surface) skip the PAUSE entirely.

**Branch / PR convention:**
- Branch name: `epic-{N}-polish`
- PR title: `Epic {N}: visual polish`
- Merge: squash (mirrors `/ship-epic` convention; main stays clean)

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

### CI failure on `/ship-epic`

If `/ship-epic` hits a CI failure on the epic PR:
- `/ship-epic` HALTs at "Wait for CI" — does not merge red
- Fix locally on `epic-{N}` branch
- Push the fix
- CI re-runs
- Continue `/ship-epic` from the wait step

If CI continues to fail and you need to investigate a single story without unwinding the entire epic:
- `git log --oneline` on `epic-{N}` to find the culprit commit
- Drop into a hotfix workflow OR revert specific commits (with care — the epic is locally committed but not pushed yet, so `git reset` is safe)

### Branch needs rebase mid-epic

If main moves while you're building epic-{N} (someone else merges another epic):
- `git fetch origin && git rebase origin/main` at any point during the epic
- Resolve conflicts locally
- Continue building stories on the rebased branch

---

## Phase exit checklist

- [ ] Every story in `sprint-status.yaml` has `status: shipped`
- [ ] Every epic's `trace_done: true` and `status: shipped`
- [ ] No CRITICAL findings from code review left unresolved
- [ ] `pnpm typecheck && pnpm lint && pnpm test` green on `main`

Advance to Phase 6.
