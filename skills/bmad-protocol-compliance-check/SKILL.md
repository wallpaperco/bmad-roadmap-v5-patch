---
name: bmad-protocol-compliance-check
description: 'Pre-commit gate for the v5 Story Protocol. Reads the active story file, verifies the `## Protocol Audit Trail` section contains all expected entries (Steps 2-8 with the right review-skill bullets), and HALTS the commit if anything is missing. Use only as Step 9.0 inside /commit-story — never standalone unless the user explicitly asks "check protocol compliance for story X.Y".'
---

# Protocol Compliance Check — pre-commit gate

**Why this exists:** when the v5 Story Protocol runs autonomously across an entire epic (via `/goal`), individual review skills can get silently skipped. The Audit Trail convention + this pre-commit gate eliminate the gap — every expected step must produce a verifiable entry in the story file, or no commit happens.

**Where it fits:** Step 9.0 — the FIRST action of `/commit-story`. If the check FAILS, the commit halts and the orchestrator MUST execute the missing step(s) before retrying.

## Inputs

- **Story file path** — resolved from `_bmad-output/roadmap-progress.yaml` (`5-build.epics.{N}.current_story`).
- **Manifest** — the expected Audit Trail bullets per step. Embedded in the script (mirrors the protocol revision in `bmad-roadmap-v5/references/story-protocol.md`).

## EXECUTION

### Step 1: Resolve the active story file

Read `_bmad-output/roadmap-progress.yaml`. Extract:
- `5-build.current_epic` → `{N}`
- `5-build.epics.{N}.current_story` → `{X.Y}`

Find the story file: glob `_bmad-output/implementation-artifacts/stories/{X.Y}-*.md`. If zero or multiple matches → HALT with the resolved glob + match count.

### Step 2: Run the compliance script

```bash
python3 .claude/skills/bmad-protocol-compliance-check/scripts/check.py <story-file-path>
```

The script:
1. Reads the story file
2. Locates the `## Protocol Audit Trail` section (HALT if missing)
3. Parses each `- [x] Step N <name>` and `- [x] <skill-name>` bullet
4. Compares against the manifest of expected entries
5. Exits 0 on PASS, exits 1 with a structured diagnostic on FAIL

### Step 3: Surface the result

**On PASS** — print the one-line summary and end. The caller (`/commit-story`) proceeds to stage files.

```
✅ Protocol Compliance — Story {X.Y} — all 8 expected entries present.
```

**On FAIL** — print the structured diagnostic the script emitted, then HALT (do NOT proceed to staging). The caller must surface the message to the orchestrator unchanged.

```
❌ PROTOCOL COMPLIANCE FAIL — Story {X.Y}
Missing Audit Trail entries (N):
  - Step 5 Simplify > code-quality skill
  - Step 6 Code Review > acceptance skill
  - Step 7 PR Review > silent-failure skill

Required actions before /commit-story can proceed:
  1. Invoke bmad-light-review-code-quality (Step 5)
  2. Invoke bmad-light-review-acceptance (Step 6)
  3. Invoke bmad-light-review-silent-failure (Step 7)
  4. Append the resulting bullets to the story file's ## Protocol Audit Trail
  5. Re-run /commit-story (which re-runs this gate first)
```

## Halt conditions

- **Story file not found** → HALT, surface the resolved glob + match count.
- **Audit Trail section missing entirely** → HALT, instruct the orchestrator to append it now with every step that's been completed so far.
- **Manifest mismatch** (any expected bullet missing) → HALT with the structured FAIL output above.

## Return contract (no-pause)

End with the literal marker:

```
--- end of bmad-protocol-compliance-check ---
```

Do NOT add closing prose. The caller (`/commit-story`) parses exit-code + the structured output to decide whether to proceed.
