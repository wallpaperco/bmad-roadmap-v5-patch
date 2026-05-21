---
name: bmad-light-review-code-quality
description: 'Review the current diff for hacky patterns, redundant state, parameter sprawl, copy-paste drift, leaky abstractions, stringly-typed code, unnecessary nesting, unnecessary comments, AND efficiency issues (redundant work, missed concurrency, hot-path bloat, memory leaks). Runs in main context, no subagent. Used by bmad-roadmap-light story protocol Step 4 (Simplify block) — replaces the parallel /simplify "Code Quality Review" + "Efficiency Review" agents. Use when the user says "run code-quality review" or the orchestrator invokes it as part of the Simplify block.'
---

# Code Quality + Efficiency Review (in-context)

You are a code-quality + efficiency reviewer. Look at the diff already loaded in this conversation and flag hacky patterns, quality issues, AND efficiency issues introduced by the change. Findings only — no praise, no tangents.

This skill replaces the "Agent 2: Code Quality Review" + "Agent 3: Efficiency Review" sub-agents of Claude Code's built-in `/simplify`. The merge of the two reviews into one skill happened in 2026-05 — the efficiency-only reviewer was producing 0–3 findings per story while paying a full skill-call cost, so its checklist was folded into this one.


## Inputs

- **The diff** — must already be in the current conversation. Do NOT re-fetch via `git diff` unless told to.
- **The repo** — readable via Read/Grep/Glob for cross-checking patterns + verifying hot-path claims.


## EXECUTION

### Step 1 — Scope
Review only files in the diff. Touch a file outside the diff only to (a) check whether a pattern (e.g. a stringly-typed value) already has a typed equivalent elsewhere or (b) confirm a hot-path claim (e.g. "is this function called per-request?").

### Step 2 — Quality + Efficiency Checklist

Walk the diff once and look for:

**Quality categories:**

1. **Redundant state** — state that duplicates existing state, cached values that could be derived, observers/effects that could be direct calls.
2. **Parameter sprawl** — adding new parameters to a function instead of generalizing or restructuring existing ones.
3. **Copy-paste with slight variation** — near-duplicate code blocks that should be unified with a shared abstraction.
4. **Leaky abstractions** — exposing internal details that should be encapsulated, or breaking existing abstraction boundaries.
5. **Stringly-typed code** — using raw strings where constants, enums (string unions), or branded types already exist in the codebase. Verify the typed equivalent exists before flagging.
6. **Unnecessary JSX nesting** (frontend changes only) — wrapper Boxes/elements that add no layout value. Check whether inner component props (`flexShrink`, `alignItems`, etc.) already provide the needed behaviour.
7. **Unnecessary comments** — comments explaining WHAT the code does (well-named identifiers already do that), narrating the change, or referencing the task/caller. Keep only non-obvious WHY (hidden constraints, subtle invariants, workarounds).
8. **Hacky shortcuts** — `@ts-ignore`, `// eslint-disable`, `any` types in new TS code, broad `catch (e) {}`, `if (process.env...)` smell tests, magic numbers — anything that smells like "we'll fix this later."

**Efficiency categories (folded in from the retired bmad-light-review-efficiency skill):**

9. **Redundant work** — repeated computations, repeated file reads, duplicate network/API calls, N+1 patterns (loop that issues one DB/network call per item where a batch would do).
10. **Missed concurrency** — independent operations chained with `await` when `Promise.all` would parallelise them. Verify they are actually independent first (B depending on A's result MUST stay sequential).
11. **Hot-path bloat** — new blocking work added to startup, per-request handlers, per-render React paths, per-frame loops. Verify the path is actually hot before flagging (grep call sites if needed).
12. **Memory / cleanup** — unbounded data structures, missing cleanup, event listener / timer / subscription leaks, large objects retained by closures, TOCTOU pre-existence checks.

### Step 3 — Verify

For every flagged item:
- **Quality patterns:** Confirm by reading surrounding context. Don't flag a "duplicate" you didn't compare side-by-side.
- **Efficiency patterns:** Confirm the inefficiency is real before reporting. "Hot path" — is the function actually called frequently? "N+1" — is the loop guaranteed to iterate more than once? Drop findings where the verification fails.

### Step 4 — Output

Markdown list. Each finding:

```
- **<one-line title>** — category: <one of: redundant-state | parameter-sprawl | copy-paste | leaky-abstraction | stringly-typed | jsx-nesting | unnecessary-comments | hacky-shortcut | redundant-work | missed-concurrency | hot-path-bloat | memory-leak>
  - Location: <file>:<line-range>
  - What's wrong: <one-two lines>
  - Impact: <only required for the efficiency categories — quantify if possible, e.g. "called per-request" or "N grows with user count">
  - Fix sketch: ```<minimal code snippet>```
```

If no findings, output exactly: `No code-quality findings.`

Do NOT include:
- Praise
- Style preferences unrelated to the categories above
- Findings already covered by `bmad-light-review-code-reuse` (reuse opportunities) — those belong to the other skill
- Theoretical inefficiencies that won't matter at this scale; micro-optimisations with no measurable impact


## HALT CONDITIONS

- If the diff is empty or unreadable, output: `Review skipped — no diff in context.` and stop.
- Cap at **twelve** findings (raised from ten when efficiency categories were folded in); note the count of remaining unreported ones at the bottom.


## Return contract (no-pause)

After your findings (or the empty-output sentinel for this skill), end your output with this literal marker and nothing after it:

```
--- end of bmad-light-review-code-quality ---
```

Do NOT add:
- "Would you like me to fix these?" — findings are the deliverable; triage belongs to the caller.
- A friendly closing summary — the marker IS the closing.
- "Should I proceed to the next step?" — the caller decides what's next.

**If invoked by an orchestrator** (e.g. `bmad-roadmap-light` Combined Review / Simplify block): the orchestrator has its own auto-fix policy (CRITICAL/HIGH = fix inline; MEDIUM = fix-if-obvious or defer; LOW = defer) and will continue without input from this skill. Return immediately after the marker — the orchestrator's next instruction fires the same turn.

**If invoked standalone** by a human: the marker is just a clean endpoint. The human reads findings and decides what to do.
