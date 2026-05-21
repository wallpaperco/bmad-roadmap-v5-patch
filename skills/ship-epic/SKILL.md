---
name: ship-epic
description: 'Ship a completed v5 epic — push the epic-N branch, open a single PR for the whole epic, wait for CI, squash-merge, sync local main. Use when the user says "ship-epic", "ship the epic", or as the End-of-Epic flow in the v5 Story Protocol. Requires that every story in the epic is already in status `committed` per roadmap-progress.yaml.'
---

# /ship-epic — Push, PR, and merge a completed v5 epic

**Purpose:** End-of-epic flow for v5. All stories in the epic have been committed locally via `/commit-story`. This skill handles the remote-side: push, PR, CI, merge.

## Inputs

- `{N}` — epic number (auto-detect from current branch `epic-{N}` if not given)
- `{epic title}` — read from `_bmad-output/planning-artifacts/epics.md`

If invoked from a non-epic branch, HALT with diagnosis.

## Preconditions

Verify all of these before running:

1. Current branch matches `epic-{N}` pattern (`git branch --show-current`)
2. Every story in this epic has status `committed` (or `shipped`) in `roadmap-progress.yaml`
3. Working tree is clean (`git status --porcelain` empty)
4. `gh` CLI is authenticated (`gh auth status`)
5. `/bmad-testarch-trace` was already run for this epic (check for `epic-{N}-trace.md` in planning artifacts)

If preconditions 1-4 fail: HALT. If precondition 5 fails: prompt user to run `/bmad-testarch-trace` first.

## Execution

### 1. Rebase main

```bash
git fetch origin
git rebase origin/main
```

If conflicts: HALT — "Rebase conflicts on epic-{N}. Resolve manually, then re-run /ship-epic."

If clean rebase: continue.

### 2. Push the epic branch

```bash
git push -u origin epic-{N}
```

If push fails (force-required, history rewritten): HALT — investigate. Never `--force` without explicit user consent.

### 3. Compose PR title and body

**Title (≤72 chars):** `Epic {N}: {epic title}`

**Body:**

```markdown
## Summary

<2-3 sentence summary of the epic goal — read from epics.md Epic {N} section>

## Stories shipped

- **{X.Y}**: {story title} ({sha-short})
- **{X.Y+1}**: ...
- ...

## AC coverage trace

See `_bmad-output/planning-artifacts/epic-{N}-trace.md` for full AC ↔ test matrix.

Trace summary:
- Total ACs: {count}
- Fully covered by tests: {count}
- Covered by visual review only (UI ACs): {count}
- Deferred to Phase 7 Harden: {count}

## Test plan

- [ ] CI passes (typecheck + lint + test)
- [ ] Visual review on staging matches design
- [ ] No regression in previously shipped epics

---

Co-built by the team.
```

**No AI attribution** (per global CLAUDE.md rule):
- Do NOT add `🤖 Generated with Claude Code` footer
- Do NOT mention Claude / Anthropic / AI anywhere

### 4. Open PR

```bash
gh pr create \
  --base main \
  --head epic-{N} \
  --title "Epic {N}: {epic title}" \
  --body "$(cat <<'EOF'
<body from step 3>
EOF
)"
```

Capture the PR URL from output.

### 5. Wait for CI

```bash
gh pr checks --watch
```

If CI fails: HALT — "CI red on PR #{num}. Inspect at <URL>. Do not merge red. Fix locally, push, re-run CI watch."

Do NOT auto-merge a failing PR even if the failure looks unrelated.

### 6. Squash-merge

```bash
gh pr merge --squash --delete-branch
```

### 7. Sync local main

```bash
git checkout main
git pull origin main
```

### 8. Update `roadmap-progress.yaml`

For the epic:
```yaml
phases:
  5-build:
    epics:
      {N}:
        status: shipped
        trace_done: true
        shipped_at: "{ISO timestamp}"
        pr_url: "{PR URL}"
        merge_sha: "{merge commit SHA on main}"
```

Mark every story in the epic from `committed` → `shipped` (they were squashed into one merge commit, but we preserve per-story tracking).

Set `current_epic` to {N+1} (or mark phase 5 complete if {N} was the last epic).

### 9. Print completion

```
✅ Epic {N}: {epic title} shipped → PR #{num} merged into main.

   Stories shipped: <count>
   Merge SHA: <short>
   PR URL: {PR URL}

   {if NOT last epic}
   Next: Epic {N+1} starting with Story {first_story_id} ({first_story_title})

   {if last epic}
   🎉 All epics shipped. Phase 5 (Build) complete. Advance to Phase 6 (Deploy).

   To continue: run /bmad-roadmap-v5 in any chat.
```

## Safety rules

- 🛑 NEVER `--force` push to main / master
- 🛑 NEVER merge a red PR (no override)
- 🛑 NEVER skip hooks unless user explicitly asks
- 🛑 NEVER add AI attribution to PR title/body
- ✅ Always rebase main BEFORE pushing the epic branch
- ✅ Always squash-merge (preserves story commits in branch history if user wants to investigate, but main stays clean)
- ✅ Delete branch on merge to keep remote tidy

## Failure recovery

| Failure | Recovery |
|---|---|
| Rebase conflicts | User resolves manually → re-run skill |
| Push rejected (history mismatch) | HALT — never force. Investigate (did someone else push?) |
| CI red | Fix locally → `git commit -am "Fix CI"` → push → CI re-runs → continue from step 5 |
| PR comments require changes | Make changes → commit → push → CI re-runs → re-invoke step 6 (squash-merge) |
| `gh pr merge` fails (e.g., branch protection) | Check branch protection rules, request reviewer if needed, re-invoke |

## Resume / re-invocation

If invoked when the epic is already `shipped` (in progress file):
- Print: "Epic {N} is already shipped (PR #{num}, merged {date}). Nothing to do."
- HALT cleanly.
