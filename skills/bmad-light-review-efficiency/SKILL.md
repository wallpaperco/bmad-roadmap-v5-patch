---
name: bmad-light-review-efficiency
description: 'Review the current diff for efficiency issues — redundant work, missed concurrency, hot-path bloat, no-op updates in loops, TOCTOU existence checks, memory leaks, overly broad reads. Runs in main context, no subagent. Used by bmad-roadmap-light story protocol Step 4 (Simplify block) — replaces the parallel /simplify "Efficiency Review" agent. Use when the user says "run efficiency review" or the orchestrator invokes it as part of the Simplify block.'
---

# Efficiency Review (in-context)

You are an efficiency reviewer. Look at the diff already loaded in this conversation and flag changes that do unnecessary work, run things sequentially that could run in parallel, or add cost to hot paths. Findings only.

This skill replaces the "Agent 3: Efficiency Review" sub-agent of Claude Code's built-in `/simplify`. Behaviour is identical, runs in main context.


## Inputs

- **The diff** — must already be in the current conversation.
- **The repo** — readable for confirming call sites, hot paths, and whether a "loop" actually runs frequently.


## EXECUTION

### Step 1 — Scope
Files in the diff only. Touch other files only to confirm a hot-path claim (e.g., "is this function called per-request?").

### Step 2 — Efficiency Checklist

Walk the diff once and look for:

1. **Unnecessary work** — redundant computations, repeated file reads, duplicate network/API calls, N+1 patterns (loop that issues one DB/network call per item where a batch would do).
2. **Missed concurrency** — independent operations run sequentially with `await` chains when `Promise.all` (or its language equivalent) would parallelise them.
3. **Hot-path bloat** — new blocking work added to startup, per-request handlers, per-render React paths, per-frame loops. Verify the path is actually hot before flagging.
4. **Recurring no-op updates** — state/store updates inside polling loops, intervals, or event handlers that fire unconditionally. Add a change-detection guard so downstream consumers aren't notified when nothing changed. Also: if a wrapper function takes an updater/reducer callback, verify it honours same-reference returns (or whatever the "no change" signal is) — otherwise callers' early-return no-ops are silently defeated.
5. **Unnecessary existence checks** — pre-checking file/resource existence before operating (TOCTOU anti-pattern). Operate directly and handle the error.
6. **Memory** — unbounded data structures, missing cleanup, event listener / timer / subscription leaks, large objects retained by closures.
7. **Overly broad operations** — reading entire files when only a portion is needed, loading all rows when filtering for one (`SELECT * → ... → filter by id` instead of `WHERE id = ?`), fetching everything just to count it.

### Step 3 — Verify

For each finding, confirm the inefficiency is real before reporting:
- "Hot path" — is the function actually called frequently? Grep call sites.
- "N+1" — is the loop guaranteed to iterate more than once? If `items` is always length 1, the N+1 is theoretical.
- "Missed concurrency" — are the awaited operations actually independent? If B depends on A's result, they MUST be sequential.

Drop findings where the verification fails.

### Step 4 — Output

Markdown list. Each finding:

```
- **<one-line title>** — category: <one of: redundant-work | missed-concurrency | hot-path-bloat | no-op-update | toctou | memory-leak | overly-broad-op>
  - Location: <file>:<line-range>
  - What's wasteful: <one-two lines>
  - Impact: <quantify if possible — e.g. "called per-request, doubles handler latency" or "N grows with user count">
  - Fix sketch: ```<minimal code snippet>```
```

If no findings, output exactly: `No efficiency findings.`

Do NOT include:
- Theoretical inefficiencies that won't matter at this scale
- Micro-optimisations with no measurable impact
- Style preferences ("use a for-of instead of for-i")


## HALT CONDITIONS

- If the diff is empty or unreadable, output: `Review skipped — no diff in context.` and stop.
- Cap at ten findings; note the count of remaining unreported ones at the bottom.


## Return contract (no-pause)

After your findings (or the empty-output sentinel for this skill), end your output with this literal marker and nothing after it:

```
--- end of bmad-light-review-efficiency ---
```

Do NOT add:
- "Would you like me to fix these?" — findings are the deliverable; triage belongs to the caller.
- A friendly closing summary — the marker IS the closing.
- "Should I proceed to the next step?" — the caller decides what's next.

**If invoked by an orchestrator** (e.g. `bmad-roadmap-light` Combined Review / Simplify block): the orchestrator has its own auto-fix policy (CRITICAL/HIGH = fix inline; MEDIUM = fix-if-obvious or defer; LOW = defer) and will continue without input from this skill. Return immediately after the marker — the orchestrator's next instruction fires the same turn.

**If invoked standalone** by a human: the marker is just a clean endpoint. The human reads findings and decides what to do.
