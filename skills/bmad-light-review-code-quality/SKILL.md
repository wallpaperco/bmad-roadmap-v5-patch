---
name: bmad-light-review-code-quality
description: 'Review the current diff for hacky patterns, redundant state, parameter sprawl, copy-paste drift, leaky abstractions, stringly-typed code, unnecessary nesting, and unnecessary comments. Runs in main context, no subagent. Used by bmad-roadmap-light story protocol Step 4 (Simplify block) — replaces the parallel /simplify "Code Quality Review" agent. Use when the user says "run code-quality review" or the orchestrator invokes it as part of the Simplify block.'
---

# Code Quality Review (in-context)

You are a code-quality reviewer. Look at the diff already loaded in this conversation and flag hacky patterns and quality issues introduced by the change. Findings only — no praise, no tangents.

This skill replaces the "Agent 2: Code Quality Review" sub-agent of Claude Code's built-in `/simplify`. Behaviour is identical, runs in main context.


## Inputs

- **The diff** — must already be in the current conversation. Do NOT re-fetch via `git diff` unless told to.
- **The repo** — readable via Read/Grep/Glob for cross-checking patterns.


## EXECUTION

### Step 1 — Scope
Review only files in the diff. Touch a file outside the diff only to check whether a pattern (e.g. a stringly-typed value) already has a typed equivalent elsewhere.

### Step 2 — Quality Checklist

Walk the diff once and look for:

1. **Redundant state** — state that duplicates existing state, cached values that could be derived, observers/effects that could be direct calls.
2. **Parameter sprawl** — adding new parameters to a function instead of generalizing or restructuring existing ones.
3. **Copy-paste with slight variation** — near-duplicate code blocks that should be unified with a shared abstraction.
4. **Leaky abstractions** — exposing internal details that should be encapsulated, or breaking existing abstraction boundaries.
5. **Stringly-typed code** — using raw strings where constants, enums (string unions), or branded types already exist in the codebase. Verify the typed equivalent exists before flagging.
6. **Unnecessary JSX nesting** (frontend changes only) — wrapper Boxes/elements that add no layout value. Check whether inner component props (`flexShrink`, `alignItems`, etc.) already provide the needed behaviour.
7. **Unnecessary comments** — comments explaining WHAT the code does (well-named identifiers already do that), narrating the change, or referencing the task/caller. Keep only non-obvious WHY (hidden constraints, subtle invariants, workarounds).
8. **Hacky shortcuts** — `@ts-ignore`, `// eslint-disable`, `any` types in new TS code, broad `catch (e) {}`, `if (process.env...)` smell tests, magic numbers — anything that smells like "we'll fix this later."

### Step 3 — Verify

Confirm each flagged pattern is real by reading the surrounding context. Don't flag a "duplicate" you didn't compare side-by-side.

### Step 4 — Output

Markdown list. Each finding:

```
- **<one-line title>** — category: <one of: redundant-state | parameter-sprawl | copy-paste | leaky-abstraction | stringly-typed | jsx-nesting | unnecessary-comments | hacky-shortcut>
  - Location: <file>:<line-range>
  - What's wrong: <one-two lines>
  - Fix sketch: ```<minimal code snippet>```
```

If no findings, output exactly: `No code-quality findings.`

Do NOT include:
- Praise
- Style preferences unrelated to the categories above
- Findings already covered by `bmad-light-review-code-reuse` (reuse opportunities) — those belong to the other skill


## HALT CONDITIONS

- If the diff is empty or unreadable, output: `Review skipped — no diff in context.` and stop.
- Cap at ten findings; note the count of remaining unreported ones at the bottom.


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
