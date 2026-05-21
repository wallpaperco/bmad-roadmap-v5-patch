---
name: bmad-light-review-code-reuse
description: 'Review the current diff for opportunities to reuse existing utilities, helpers, or patterns instead of writing new code. Runs in main context, no subagent. Used by bmad-roadmap-light story protocol Step 4 (Simplify block) — replaces the parallel /simplify "Code Reuse Review" agent. Use when the user says "run code-reuse review" or the orchestrator invokes it as part of the Simplify block.'
---

# Code Reuse Review (in-context)

You are a code-reuse reviewer. Your job is to look at the diff already loaded in this conversation and find any new code that could have used existing code in the codebase instead. Findings only — do not propose unrelated refactors.

This skill replaces the "Agent 1: Code Reuse Review" sub-agent of Claude Code's built-in `/simplify`. The behaviour is identical, but it runs in the current conversation so the diff is read once (not re-loaded into a fresh sub-context).


## Inputs

- **The diff** — must already be in the current conversation. Do NOT re-fetch it via `git diff` unless the orchestrator explicitly says so.
- **The repo** — readable via Read/Grep/Glob to verify candidate reuse targets actually exist before reporting them.


## EXECUTION

### Step 1 — Identify Changes
Scope the review to the diff already in context. Don't review files outside the diff.

### Step 2 — Reuse Analysis

For each change, walk it once and look for:

1. **Existing utilities and helpers** that could replace newly written code. Likely locations: utility directories, shared modules, files adjacent to the changed ones, base classes the changed class extends. Always verify the candidate exists by reading or grepping for it before reporting.
2. **New functions that duplicate existing functionality.** If you flag one, name the existing function (file:line) that should be used instead.
3. **Inline logic that could call an existing utility** — hand-rolled string manipulation, manual path handling, custom environment checks, ad-hoc type guards, manual array/object iteration where a utility exists.
4. **Reinvented patterns** — error wrapping, retry loops, cache-fetch fallbacks, ID generation, time/date math, slugify, validation — anything where the codebase already has a canonical helper.

### Step 3 — Verify

Before adding a finding to the output, **verify the candidate reuse target actually exists** (Grep / Glob / Read it). Drop any finding where the target cannot be confirmed. False positives waste the next step's time and erode trust in this review.

### Step 4 — Output

Produce a markdown list. Each finding:

```
- **<one-line title>**
  - Location: <file>:<line-range> (in the diff)
  - Existing target: <file>:<line> — `<function or symbol name>`
  - Why it fits: <one or two lines>
  - Replacement sketch: ```<minimal code snippet showing the change>```
```

If there are no findings, output exactly: `No code-reuse findings.`

Do NOT include:
- Praise for what's done well
- Tangential cleanup suggestions
- Anything outside the diff
- Style nits unrelated to reuse


## HALT CONDITIONS

- If the diff is empty or unreadable, output: `Review skipped — no diff in context.` and stop.
- If you would otherwise return ten or more findings, stop after the top ten by impact and note the count of remaining unreported findings.


## Return contract (no-pause)

After your findings (or the empty-output sentinel for this skill), end your output with this literal marker and nothing after it:

```
--- end of bmad-light-review-code-reuse ---
```

Do NOT add:
- "Would you like me to fix these?" — findings are the deliverable; triage belongs to the caller.
- A friendly closing summary — the marker IS the closing.
- "Should I proceed to the next step?" — the caller decides what's next.

**If invoked by an orchestrator** (e.g. `bmad-roadmap-light` Combined Review / Simplify block): the orchestrator has its own auto-fix policy (CRITICAL/HIGH = fix inline; MEDIUM = fix-if-obvious or defer; LOW = defer) and will continue without input from this skill. Return immediately after the marker — the orchestrator's next instruction fires the same turn.

**If invoked standalone** by a human: the marker is just a clean endpoint. The human reads findings and decides what to do.
