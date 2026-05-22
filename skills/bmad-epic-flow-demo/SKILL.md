---
name: bmad-epic-flow-demo
description: 'Post-ship visual review cycle for a v5 epic. Runs IMMEDIATELY AFTER /ship-epic completes — opens an epic-{N}-polish branch from main, detects routes/pages the epic added, prints a suggested journey + /impeccable live paste-ready prompt, pauses for the user. On "approved" with polish commits: pushes + opens PR + watches CI + squash-merges + deletes branch + syncs main. On "approved" with no commits: deletes the empty branch and closes the epic. Skips cleanly for infrastructure-only epics (no UI surface). Use as the LAST step of the end-of-epic flow before the orchestrator moves to the next epic.'
---

# /bmad-epic-flow-demo — Post-ship visual review + polish cycle

**Purpose:** Give the user a clean separation between "build the epic autonomously" and "review the result and polish". `/ship-epic` lands the epic on main. This skill picks up from there: opens a fresh `epic-{N}-polish` branch, shows the user what was built, pauses for iteration in a separate chat, then ships the polish work via its own PR.

**When it runs:** Immediately after `/ship-epic` returns success. Called by `bmad-roadmap-v5`'s end-of-epic flow before advancing to the next epic.

**Why post-ship not pre-ship:**
- `/goal Epic N` runs fully autonomous (no per-story pauses) → ships cleanly
- Visual review happens against `main` (production-like), not a transient branch
- Iterations create their own commit history on `epic-{N}-polish` → main stays clean
- CI runs once at the end of polish (when the user signals done), not per-iteration

## Inputs

- `{N}` — epic number (auto-detect from `roadmap-progress.yaml: 5-build.current_epic`)
- `{epic title}` — read from `_bmad-output/planning-artifacts/epics.md` Epic {N} section
- Project root + dev server URL (from `.claude/launch.json` or `apps/web/package.json` dev script)

## Preconditions

1. `/ship-epic` for Epic {N} just completed (verify: `git log -1 main --format=%s` matches `Epic {N}: {title}` or contains `(#<PR num>)` for the merged PR)
2. Current branch is `main` and synced with origin
3. Working tree clean (`git status --porcelain` empty — any leftover changes would land on the polish branch unintentionally)
4. `gh` CLI authenticated

If any fails: HALT with diagnosis. Don't silently create the polish branch in a dirty state.

## Execution

### 1. Detect epic surface area

Compute the diff of files the epic introduced between `main~{commits}..main` (commits = number of commits the ship-epic squashed). Scan for **new UI routes / pages**:

- For Next.js: new files under `apps/web/src/app/**/page.tsx` (or `pages/**/*.tsx` for the legacy router)
- For SPA / Remix / etc: project-specific glob (read from `.claude/launch.json` `flowDemo.routesGlob` if present; default to the Next.js pattern)

Also collect:
- New API routes (`apps/api/src/**/*.controller.ts` for NestJS) — for journey context but not gated
- Components added to a public surface (used by any page added in this epic)

If **zero new pages/routes** → emit the infrastructure-only short path (see § Skip path below) and END. No polish branch is created.

### 2. Create the polish branch

```bash
git checkout -b epic-{N}-polish
```

Push the empty branch so the user (or a future session) can see it exists:

```bash
git push -u origin epic-{N}-polish
```

The branch stays empty at creation — only iteration commits land on it.

### 3. Compose + print the demo prompt

Print this block (replace `{...}` placeholders with resolved values):

```
🎬 Epic {N} — {epic title} — Post-Ship Visual Review

✅ Epic shipped: PR #{ship-pr-num} merged into main ({merge-sha-short})
🌿 Polish branch: epic-{N}-polish (created from main, currently empty)
🌐 Dev server expected at: {dev-url}

────────────────────────────────────────────────────────────────
🧭 Routes added in this epic:
  {route-1}      ({story-id})
  {route-2}      ({story-id})
  ...

🎯 Suggested user journey to try:
  1. {Step 1 — narrative from UX spec §13.X mapping for the epic's journey}
  2. {Step 2 — ...}
  3. {Step 3 — ...}
  Also verify: AR/EN locale switch, light/dark theme on each surface.

📋 PASTE THIS IN A NEW CHAT FOR /impeccable live ITERATION:
════════════════════════════════════════════════════════════════
You're in /impeccable live mode for Epic {N} of {project-name}.

Working branch: epic-{N}-polish (checkout this branch before editing)
Dev server: {dev-url}

Routes to iterate:
{newline-separated list of routes + the story each one belongs to}

Design system context:
- UX spec: _bmad-output/planning-artifacts/ux-design-specification.md (§13.X for this epic's journey)
- Tokens: apps/web/src/app/globals.css + apps/web/src/i18n/config.ts (fontStack)
- Egyptian-Native wrappers under apps/web/src/lib/egyptian-native/ if present
- shadcn/ui primitives under apps/web/src/components/ui/

When you finish a round of edits:
- Commit on epic-{N}-polish (NOT main).
- Return to the orchestrator chat and type `approved`.

Don't push, don't open a PR — the orchestrator handles that on `approved`.
════════════════════════════════════════════════════════════════

📝 When you're done iterating, return here and type:
   `approved`       — close the polish cycle (ship any commits + close epic)
   `skip-polish`    — abandon any commits on the polish branch, close epic
   `iterate <note>` — re-print this demo prompt (e.g. after grabbing a fresh chat)

Waiting for your signal…
```

### 4. PAUSE

The orchestrator MUST stop here and wait. No follow-up tool calls until the user types one of the three signals. This is the only PAUSE in the whole post-/goal flow — every other step is autonomous.

### 5. Resume on signal

When the user types `approved`:

#### 5a. Check the polish branch state

```bash
git fetch origin
git checkout epic-{N}-polish
git rebase origin/main  # absorb any drift on main since branch creation
```

If rebase conflicts: HALT — "Conflicts during polish-branch rebase. Resolve manually then retype `approved`."

Count commits ahead of main:

```bash
ahead=$(git rev-list --count origin/main..epic-{N}-polish)
```

#### 5b. Branch with no commits → close cleanly

If `ahead == 0`:

```bash
git checkout main
git push origin --delete epic-{N}-polish
git branch -D epic-{N}-polish
```

Print:
```
✅ Epic {N} fully closed — no polish needed.
   No commits on epic-{N}-polish; branch deleted (local + remote).
```

Update `roadmap-progress.yaml`: mark epic `{N}.polish_status: skipped-no-changes`. Return success. The orchestrator advances to Epic {N+1}.

#### 5c. Branch has commits → ship the polish

Mirror the `/ship-epic` flow on the polish branch:

```bash
# 1. Push (origin/epic-{N}-polish already exists from step 2; just push new commits)
git push origin epic-{N}-polish

# 2. Open PR (squash-merge, same convention as ship-epic)
gh pr create \
  --base main \
  --head epic-{N}-polish \
  --title "Epic {N}: visual polish" \
  --body "$(<polish-pr-body.md)"

# 3. Watch CI (--watch + --interval 15)
gh pr checks {pr-num} --watch --interval 15

# 4. On all-green → squash-merge + delete branch
gh pr merge {pr-num} --squash --delete-branch

# 5. Sync local main
git checkout main
git pull origin main
git branch -D epic-{N}-polish 2>/dev/null || true
```

PR body template (`polish-pr-body.md` composed on the fly):

```markdown
## Summary

Post-ship visual polish for Epic {N} ({epic title}). Iterations applied
in a separate chat via /impeccable live; this PR collects them into one
commit on main.

## Commits ({ahead})

<one bullet per commit on epic-{N}-polish: `{short-sha} {subject}`>

## Test plan

- [ ] CI passes (typecheck + lint + test)
- [ ] No regression on previously shipped epics
```

No AI attribution per global CLAUDE.md rule. No `Co-Authored-By` trailer. No `🤖 Generated with Claude Code` footer.

If CI red:
- Print the failed job logs (`gh run view <run-id> --log-failed | tail -80`)
- HALT — "Polish CI red. Inspect logs above, fix locally, push, retype `approved`."

On success:
```
✅ Epic {N} fully closed — polish PR #{polish-pr-num} merged into main ({merge-sha-short}).
   {ahead} polish commit(s) squashed.
```

Update `roadmap-progress.yaml`: mark epic `{N}.polish_status: shipped`, `{N}.polish_pr_url`, `{N}.polish_merge_sha`.

### 6. `skip-polish` signal — abandon any work

If the user types `skip-polish`:

```bash
git fetch origin
git checkout main
git push origin --delete epic-{N}-polish 2>/dev/null || true
git branch -D epic-{N}-polish 2>/dev/null || true
```

Print:
```
🗑  Polish branch abandoned. Any commits on epic-{N}-polish were discarded.
   Epic {N} closed without polish work.
```

Update `roadmap-progress.yaml`: `{N}.polish_status: skipped-user-abandon`.

### 7. `iterate <note>` signal — reprint demo, keep waiting

If the user types `iterate <note>` (e.g., `iterate I lost the chat tab`):
- Reprint Step 3 verbatim
- Append: `🔁 Iteration note: {note}`
- Continue waiting

## Skip path — infrastructure-only epic

When Step 1 detects zero new pages/routes (Epic 1 in baseir was this), print:

```
ℹ️  Epic {N} — {epic title} — infrastructure-only

Surface area scan:
  New pages/routes: 0
  New API endpoints: {api-count} (not gated for visual review)
  New shared components: {component-count}

No flow to demo. Epic {N} closed without polish cycle.
```

Update `roadmap-progress.yaml`: `{N}.polish_status: skipped-no-ui`. Return success without pausing. The orchestrator advances to Epic {N+1}.

## Resume / re-invocation

If invoked when the polish cycle is already shipped (in progress file):
- Print: "Epic {N} polish already shipped (PR #{num}, merged {date}). Nothing to do."
- HALT cleanly.

If invoked when `/ship-epic` for Epic {N} hasn't run yet:
- HALT with: "Epic {N} hasn't shipped yet. Run /ship-epic first."

## Safety rules

- 🛑 NEVER push directly to main (polish lands via PR like any other change)
- 🛑 NEVER `--force` push
- 🛑 NEVER merge a red CI (no override flag)
- 🛑 NEVER skip the user PAUSE silently — if no UI changes detected, log it explicitly via the skip path; do not pretend the user approved.
- ✅ Always squash-merge (main stays clean)
- ✅ Always delete the polish branch on close (local + remote)

## Return contract (no-pause when invoked autonomously)

The PAUSE in Step 4 is the ONLY interactive checkpoint. Every other path (skip, ship, abandon) ends with the literal marker and nothing after it:

```
--- end of bmad-epic-flow-demo ---
```

The caller (`bmad-roadmap-v5` orchestrator) parses the exit + the marker to decide whether to advance to Epic {N+1} or wait.
