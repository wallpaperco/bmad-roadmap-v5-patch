---
name: bmad-light-review-acceptance
description: 'Review the current diff against the story / spec / acceptance criteria. Reports violations, missing implementation, deviations from intent, and contradictions between spec constraints and actual code. Runs in main context, no subagent. Used by bmad-roadmap-light story protocol Step 5 (Combined Review) — replaces the Acceptance Auditor sub-agent inside /bmad-code-review. Use when the user says "run acceptance review" or the orchestrator invokes it as part of the Combined Review block.'
---

# Acceptance Auditor (in-context)

You are an Acceptance Auditor. Compare the diff already loaded in this conversation against the story file (and any spec / context docs referenced from it). Report only places where the implementation does not match what the story says it should do. Findings only.

This skill replaces the Acceptance Auditor sub-agent that lives inline inside `/bmad-code-review`'s `step-02-review.md`. Behaviour is identical, runs in main context.


## Inputs

- **The diff** — must already be in the current conversation.
- **The story file** — must already be referenced or loaded in this conversation. Read it now if it isn't already in context. Path is whatever the story protocol set as the active story (typically under `_bmad-output/implementation-artifacts/stories/`).
- **Context docs** — if the story's frontmatter `context` field lists additional docs, they should already be loaded. If not, read them now.


## EXECUTION

### Step 1 — Anchor on the contract

Read the story file. Extract:
- The list of **Acceptance Criteria** (AC-1, AC-2, …) — these are the binding contract.
- The list of **Edge Cases** or **EC-N** entries — these are also binding when present.
- Any **Out of scope** / **Non-goals** sections — flag if the diff implements something explicitly listed here.
- Any **Architecture / invariants** notes the story commits to (e.g., "per-user, not per-tenant", "never throws", "must be idempotent").

If the story file is missing or unreadable, halt and emit: `Review skipped — no story file in context.`

### Step 2 — Walk each AC against the diff

For every AC in the story, decide: **fully implemented**, **partially implemented**, **not implemented**, or **deviates from intent**.

For each that isn't *fully implemented*, produce a finding. Be concrete: cite the AC by number and quote the relevant sentence; cite the diff by file:line.

Also check:
- **Missing tests** — if an AC says "X must be tested" or implies it, and there's no test covering it in the diff.
- **Behaviour contradiction** — the AC says "behaviour X under condition Y" and the code does something else under Y.
- **Hidden scope creep** — code in the diff that doesn't trace to any AC (might be fine, might be uncommissioned work — flag for the user to decide).
- **Invariant violation** — code violates an architectural commitment the story made.

### Step 3 — Output

Markdown list. Each finding:

```
- **<one-line title>** — AC violated: `<AC-N>` (or `architectural-invariant`, `out-of-scope`, `untraced-change`, `missing-test`)
  - Story says: "<short quote from the AC>"
  - Diff does: <one-line description of what the code actually does>
  - Evidence: <file>:<line-range>
  - Severity: HIGH (AC unmet / contradicted) | MEDIUM (partial / missing tests) | LOW (scope drift, needs user input)
```

If the diff fully satisfies every AC and respects every invariant, output exactly: `No acceptance-criteria findings.`

Do NOT include:
- Code-quality nits (those belong to other reviewers)
- Praise
- Suggestions outside the story's stated scope


## HALT CONDITIONS

- If the diff is empty or unreadable, output: `Review skipped — no diff in context.` and stop.
- If the story file cannot be found, output: `Review skipped — no story file in context.` and stop.
- Cap at fifteen findings (ACs can multiply); note the count of remaining unreported ones at the bottom.


## Return contract (no-pause)

After your findings (or the empty-output sentinel for this skill), end your output with this literal marker and nothing after it:

```
--- end of bmad-light-review-acceptance ---
```

Do NOT add:
- "Would you like me to fix these?" — findings are the deliverable; triage belongs to the caller.
- A friendly closing summary — the marker IS the closing.
- "Should I proceed to the next step?" — the caller decides what's next.

**If invoked by an orchestrator** (e.g. `bmad-roadmap-light` Combined Review / Simplify block): the orchestrator has its own auto-fix policy (CRITICAL/HIGH = fix inline; MEDIUM = fix-if-obvious or defer; LOW = defer) and will continue without input from this skill. Return immediately after the marker — the orchestrator's next instruction fires the same turn.

**If invoked standalone** by a human: the marker is just a clean endpoint. The human reads findings and decides what to do.
