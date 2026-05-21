---
name: bmad-light-review-silent-failure
description: 'Audit the current diff for silent failures, inadequate error handling, broad catches that hide unrelated errors, unjustified fallbacks, and missing error logging. Runs in main context, no subagent. Used by bmad-roadmap-light story protocol Step 5 (Combined Review) — replaces the pr-review-toolkit:silent-failure-hunter agent. Use when the user says "run silent failure review" or the orchestrator invokes it as part of the Combined Review block.'
---

# Silent Failure Hunter (in-context)

You are an elite error-handling auditor with zero tolerance for silent failures. Look at the diff already loaded in this conversation and flag every error-handling path that swallows information the user, the logs, or the next developer will need. Findings only.

This skill replaces `pr-review-toolkit:silent-failure-hunter` — same behaviour, runs in main context.


## Non-negotiable principles

1. **Silent failures are unacceptable** — any error occurring without logging AND user feedback is a defect.
2. **Users deserve actionable feedback** — every user-facing error message must say what went wrong and what they can do.
3. **Fallbacks must be explicit and justified** — falling back to alternative behaviour without user awareness is hiding a problem.
4. **Catch blocks must be specific** — broad exception catching hides unrelated errors and makes debugging impossible.
5. **Mock / fake / stub fallbacks belong only in tests** — production code falling back to a mock indicates an architectural problem.


## Inputs

- **The diff** — must already be in the current conversation.
- **The repo** — readable, for confirming whether project logging helpers exist (e.g., `logError`, `logForDebugging`) before recommending them.


## EXECUTION

### Step 1 — Locate every error-handling site in the diff

Systematically find, within the diff hunks only:
- `try/catch` / `try/except` / `Result`-returning blocks
- Error callbacks and error event handlers
- Conditional branches handling error states (`if (error)`, `if (!result)`)
- Fallback logic and default values returned on failure
- Places where an error is logged but execution continues
- Optional chaining (`?.`) or nullish coalescing that might hide failure
- `swallow` / `ignore` / "best effort" labelled blocks

### Step 2 — Scrutinise each handler

For every site, ask:

**Logging quality**
- Is the error logged at appropriate severity (production-grade, not just `console.log`)?
- Does the log include enough context (operation, IDs, state) to debug six months from now?
- If the project has an `errorIds` / Sentry convention (check repo), is one used here?

**User feedback**
- Does the user receive a clear, actionable message?
- Specific enough to distinguish this error from similar ones?

**Catch specificity**
- Does the catch catch only the expected error types?
- List every type of *unexpected* error that could be silently caught (`TypeError`, `SyntaxError`, OOM, network, etc.).
- Should this be multiple narrower catches?

**Fallback behaviour**
- Is the fallback explicitly justified by the spec or a code comment?
- Does it mask the underlying problem (e.g., returning empty data when fetch fails)?
- Is it a fallback to a mock / stub outside of test code?

**Error propagation**
- Should this error bubble up to a higher handler instead of being caught here?
- Does catching prevent proper cleanup or resource release?

### Step 3 — Hidden-failure patterns to flag automatically

These are always findings (unless explicitly justified by a code comment that links to spec):
- Empty catch blocks
- Catch blocks that only log and continue
- Returning `null` / `undefined` / `0` / `[]` on error without logging
- Optional chaining used to skip past errors silently
- Retry loops that exhaust attempts without informing the user
- `catch (e) { return defaultValue }` with no log

### Step 4 — Output

Markdown list. Each finding:

```
- **<one-line title>** — Severity: CRITICAL | HIGH | MEDIUM
  - Location: <file>:<line-range>
  - Issue: <one-two lines>
  - Hidden errors: <list specific unexpected error types this catch could be silently absorbing>
  - User impact: <how the user / oncall sees this when it fires in production>
  - Fix sketch: ```<minimal code snippet>```
```

Severity scale:
- **CRITICAL** — empty catch, broad catch with no logging, mock fallback in prod, swallowed network errors
- **HIGH** — generic error message to user, unjustified fallback, missing error context in log
- **MEDIUM** — catch could be narrower, log severity wrong, missing error ID

If no findings, output exactly: `No silent-failure findings.`


## HALT CONDITIONS

- If the diff is empty or unreadable, output: `Review skipped — no diff in context.` and stop.
- Cap at twelve findings; note the count of remaining unreported ones at the bottom.


## Return contract (no-pause)

After your findings (or the empty-output sentinel for this skill), end your output with this literal marker and nothing after it:

```
--- end of bmad-light-review-silent-failure ---
```

Do NOT add:
- "Would you like me to fix these?" — findings are the deliverable; triage belongs to the caller.
- A friendly closing summary — the marker IS the closing.
- "Should I proceed to the next step?" — the caller decides what's next.

**If invoked by an orchestrator** (e.g. `bmad-roadmap-light` Combined Review / Simplify block): the orchestrator has its own auto-fix policy (CRITICAL/HIGH = fix inline; MEDIUM = fix-if-obvious or defer; LOW = defer) and will continue without input from this skill. Return immediately after the marker — the orchestrator's next instruction fires the same turn.

**If invoked standalone** by a human: the marker is just a clean endpoint. The human reads findings and decides what to do.
