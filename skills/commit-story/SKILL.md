---
name: commit-story
description: 'Commit a v5 story locally on the current epic branch. NO push, NO PR — those happen at end-of-epic via /ship-epic. Use when the user or the v5 orchestrator says "commit-story", "commit this story", or as Step 9 of the v5 Story Protocol. Stages specific files (never git add -A), generates a commit message with AC Implementation Map summary, updates roadmap-progress.yaml.'
---

# /commit-story — Commit current v5 story locally

**Purpose:** Step 9 of the v5 Story Protocol. Commits the story's changes locally on the epic branch. Push + PR + merge happen later via `/ship-epic`.

## Inputs (resolved by caller or interactively)

- `{X.Y}` — story ID (e.g. `2.7`)
- `{story file path}` — absolute path to the story markdown
- `{title}` — story title (read from frontmatter)
- `{N}` — epic number (derived from `X.Y`)

If invoked manually without context, prompt the user for `{X.Y}`.

## Preconditions

- Current branch is `epic-{N}` (verify with `git branch --show-current`)
- Working tree has uncommitted changes from Saneh + reviews (verify with `git status --short`)
- All Step 8 checks passed (typecheck + lint + test) — this should be verified by the orchestrator before invoking

If any precondition fails: HALT with a clear diagnosis. Do not silently push through.

## Execution

### 0. Protocol Compliance Gate (NEW — MANDATORY, no bypass)

**Before staging anything**, invoke `bmad-protocol-compliance-check` via the Skill tool. The check reads the active story file's `## Protocol Audit Trail` section and verifies every expected step entry is present (Saneh → AC-Compliance → User Review → Simplify > 2 skills → Code Review > 3 skills → PR Review > 1 skill → Verify).

If the gate exits with FAIL:
- Print the structured diagnostic verbatim (do NOT summarize).
- HALT — do not proceed to staging.
- The caller (orchestrator) MUST complete the missing step(s), append the resulting bullet(s) to the story file's Audit Trail, then re-invoke `/commit-story`. The gate re-runs first.

There is no `--skip-compliance` flag. The gate is the entire reason this skill exists — bypassing it would silently re-introduce the autonomous-skip class of bugs that prompted its addition.

If the gate exits with PASS, continue to step 1.

### 1. Inspect changes

```bash
git status --short
git diff --stat
```

If output is empty: HALT — "No changes to commit for story {X.Y}."

### 2. Stage specific files (NEVER `git add -A`)

Identify the files Saneh + reviews touched (from `git status --short`). Stage them by explicit path:

```bash
git add <path1> <path2> ...
```

Skip any file that:
- Is in `.env*` or `secrets/*` (sensitive)
- Is a large binary (>1MB) unless explicitly part of the story
- Was modified but not part of this story's scope (warn user, do not stage)

### 3. Compose commit message

Read the AC Implementation Map from the Saneh return block (saved to a tmp file at Step 2). Compose:

**Title (≤72 chars):** `Story {X.Y}: {title}`

**Body:**
```
AC Implementation Map:
- AC-1: <one-line summary>
- AC-2: <one-line summary>
- ...

Files touched: <count>
Tests added: <count>
```

If any AC was deferred or skipped, list it with reason.

**No AI attribution** (per global CLAUDE.md rule):
- Do NOT append `Co-Authored-By: Claude...`
- Do NOT add `🤖 Generated with Claude Code` footer
- Do NOT mention Claude / Anthropic / AI anywhere in the message

### 4. Commit

Use HEREDOC for clean formatting:

```bash
git commit -m "$(cat <<'EOF'
Story {X.Y}: {title}

AC Implementation Map:
- AC-1: <summary>
- AC-2: <summary>
...

Files touched: <N>
Tests added: <M>
EOF
)"
```

If the pre-commit hook fails: fix the issue, re-stage, create a NEW commit (do NOT use `--amend`).

### 5. Capture commit SHA

```bash
COMMIT_SHA=$(git rev-parse HEAD)
COMMIT_SHORT=$(git rev-parse --short HEAD)
```

### 6. Update `roadmap-progress.yaml`

Update the entry for this story:

```yaml
phases:
  5-build:
    epics:
      {N}:
        stories:
          "{X.Y}":
            status: committed
            committed_at: "{ISO timestamp}"
            commit_sha: "{COMMIT_SHA}"
```

Also bump `current_story` to the next pending story in topo order (read from `sprint-status.yaml`).

### 7. Print completion message

```
✅ Story {X.Y} committed locally (sha: {COMMIT_SHORT}).
   Branch: epic-{N}
   Files: <count>

   {if NOT last story in epic}
   Next pending in Epic {N}: Story {X.Y+1} ({next_title})

   {if last story in epic}
   🎯 End-of-epic reached. Next steps:
      1. /bmad-testarch-trace   → AC↔test coverage report
      2. /ship-epic              → push + PR + CI + merge

   To continue: run /bmad-roadmap-v5 in any chat.
```

## Safety rules

- 🛑 NEVER `git push` in this skill
- 🛑 NEVER open a PR in this skill
- 🛑 NEVER `git add -A` — always stage by explicit path
- 🛑 NEVER `git commit --amend` — always create a new commit
- 🛑 NEVER add AI attribution to the commit message
- 🛑 NEVER skip hooks (`--no-verify`) unless user explicitly asks
- ✅ Hook failures → fix root cause + new commit, never bypass

## Resume / re-invocation

If invoked when the story has already been committed (status `committed` in progress file):
- Print: "Story {X.Y} is already committed (sha: <short>). Did you mean to amend? Use git directly or run /ship-epic if epic is done."
- HALT. Do not create a duplicate commit.
