---
name: bmad-extract-deferrals
description: 'Extract deferred-work entries from a range of git commit messages and append them to _bmad-output/implementation-artifacts/deferred-work.md. Run at end-of-epic (before /bmad-testarch-trace) to populate the deferrals registry from the 7-skill protocol output that lives in commit message bodies.'
---

# Extract Deferrals — commit messages → deferred-work.md

**Purpose:** The v5 Story Protocol's auto-fix policy (CRITICAL/HIGH = fix inline; MEDIUM/LOW = defer) writes the deferred findings into the **commit message body** of each story. They're meant to also land in `_bmad-output/implementation-artifacts/deferred-work.md` — but in practice, compliance on that step is uneven (Epic 1 stopped updating the file after Story 1.3, leaving ~310 findings only-in-commits).

This skill is the end-of-epic catch-up: it reads all commits in the epic's range, extracts the deferrals, dedupes against the existing file, and appends new entries.

**Where it fits:** Run at end-of-epic, AFTER all per-story commits land, BEFORE `/bmad-testarch-trace` (so the trace report can surface the deferrals it just ingested) and BEFORE `/ship-epic`.

## Inputs

- **Commit range** (optional) — e.g. `main..HEAD` or `682931a..cc917ab`. Defaults to `origin/main..HEAD`.
- **Existing file** — `_bmad-output/implementation-artifacts/deferred-work.md` (read for dedup; appended-to).

## EXECUTION

### Step 1: Resolve commit range

If the user passed a range, use it. Otherwise default to `origin/main..HEAD`. Print the range + commit count.

```bash
git log --reverse <range> --format='%H'
```

If the range is empty, halt with: `No commits in range. Pass an explicit range like 682931a..HEAD if running mid-flight.`

### Step 2: Run the extractor script

```bash
python3 .claude/skills/bmad-extract-deferrals/scripts/extract.py <range>
```

The script reads each commit, parses the body, extracts deferrals, dedupes against the existing file, and appends. It writes a summary line to stdout: `Extracted N deferrals from M commits — K new, D duplicates skipped, U with no owning future story.`

### Step 3: Surface the summary + any red flags

Read the script output. If the count of "no owning future story" entries is greater than zero, list them inline — they're the highest-risk deferrals (no future story owns them, so they're at risk of being permanently forgotten).

### Step 4: Recommend next steps

Always print:
```
Next:
- Review the appended entries in _bmad-output/implementation-artifacts/deferred-work.md.
- Run /bmad-testarch-trace to surface the deferrals in the epic trace report.
```

## Patterns the extractor recognises

These are the structures the v5 reviewers + retroactive runs already produce. Match any of them:

1. **Severity-prefixed headings** in `**bold**`:
   - `**HIGH:** ...`
   - `**MEDIUM (silent-failure): ...`
   - `**LOW: ...`

2. **"Deferred:" section** — bullet list under a heading line like:
   ```
   Deferred (acknowledged in retroactive review):
   - AC-4 per-account sync to users.theme_preference — Story 4.3.
   - AC-6 chart-palette WCAG validation — Epic 6 charts.
   ```

3. **Inline "Defer to" / "deferred to" mentions** in prose:
   - `Defer to Story 4.x — ...`
   - `deferred to Phase 7 Harden`
   - `(Story X.Y owns)`

4. **Skill section headers** (matches the original deferred-work.md convention):
   - `## simplify-v5 (Story X.Y)`
   - `## code-review-v5 (Story X.Y) — non-local MEDIUM + LOW deferrals`

## Output format (matches existing deferred-work.md)

Each entry follows the established H3-per-finding shape:

```markdown
## <source>-v5 (Story X.Y)

### YYYY-MM-DD — <one-line finding title> (<SEVERITY>)

**Source:** <reviewer name>
**Finding:** <verbatim from commit>
**Decision rationale:** <verbatim from commit, or "Defer to <owner>" if no rationale found>
**Reversibility:** High | Medium | Low (inferred — High if the deferral is cosmetic, Low if it touches a contract)
**Owning future story:** <Story X.Y / Phase 7 / "no owner — review">
**Commit:** <short sha>
**Action:** None | Track | Fix in <owner>
```

## Halt conditions

- If `_bmad-output/implementation-artifacts/deferred-work.md` doesn't exist, create it with a minimal header and continue.
- If `python3` isn't available, fall back to inline parsing in this skill (slower but works).
- If the script exits non-zero, surface its stderr and HALT.

## Return contract (no-pause)

End with the literal marker:

```
--- end of bmad-extract-deferrals ---
```

Do NOT prompt the user to confirm or ask "should I run the trace next?" — the orchestrator decides.
