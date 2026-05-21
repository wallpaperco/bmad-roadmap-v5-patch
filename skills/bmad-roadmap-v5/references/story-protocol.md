# Story Protocol — v5 (9 steps, epic-branched)

Per-story workflow invoked by Phase 5 (Build). **Branch per epic, not per story.** Each story produces a single local commit on the epic branch. At end-of-epic the branch is pushed and merged via one PR.

**Inputs (resolved by the orchestrator before entering this protocol):**
- `{X.Y}` — story ID (e.g. `2.7`)
- `{story file path}` — absolute path to the story markdown
- `{epic-slug}` — for branch naming
- `{N}` — epic number

**Stage tracker:** `roadmap-progress.yaml: 5-build.current_step` (1-9). Resumable.

---

## Protocol Audit Trail — append-on-completion (NEW, enforced)

Each story file MUST end with a section titled `## Protocol Audit Trail`. As every step finishes, the orchestrator appends one line confirming the step ran. Step 9 (`/commit-story`) calls `bmad-protocol-compliance-check` BEFORE staging files — if any expected entry is missing, the commit is HALTED until the step is actually executed (not just declared done).

**Why it exists:** when running autonomously across a full epic (via `/goal`), individual review skills can get silently skipped. The audit trail + pre-commit gate eliminates that — a fail-loud, fail-LOCAL check catches the gap at the story that introduced it, not three stories later during a retrospective.

**Format:**

```markdown
## Protocol Audit Trail

- [x] Step 2 Saneh — AC Map (12 ACs mapped, 0 deferred)
- [x] Step 3 AC-Compliance — PASS
- [x] Step 4 User Review — approved at 2026-MM-DDTHH:MM
- [x] Step 5 Simplify
  - [x] code-reuse — 2 findings, 1 fixed, 1 deferred
  - [x] code-quality — 8 findings, 5 fixed, 3 deferred
- [x] Step 6 Code Review
  - [x] adversarial — 12 findings, 4 fixed, 8 deferred
  - [x] edge-case-hunter — 15 findings, 3 fixed, 12 deferred
  - [x] acceptance — 9 findings, 6 fixed, 3 deferred
- [x] Step 7 PR Review
  - [x] silent-failure — 7 findings, 5 fixed, 2 deferred
- [x] Step 8 Verify — typecheck/lint/test PASS
```

**Bullet shape per skill invocation:** `- [x] <skill-name> — <total> findings, <fixed> fixed, <deferred> deferred`. Use `0 findings, 0 fixed, 0 deferred` when the skill returned "No findings". For non-review steps (Saneh, AC-Compliance, User Review, Verify) use the natural one-line description shown above.

The orchestrator appends each line **the same turn** the corresponding step completes — never batched at the end.

---

## Step 1 — Branch

```bash
# First story of the epic:
git checkout main && git pull
git checkout -b epic-{N}

# Subsequent stories of the same epic:
git checkout epic-{N}
```

Branch convention: `epic-{N}` (e.g. `epic-1`, `epic-2`). No story-level branches.

Mark step done; proceed to Step 2 in the same turn.

---

## Step 2 — Saneh — Full-Stack Build

Launch an Agent (subagent_type=general-purpose) with this prompt verbatim:

```
You are Saneh, a full-stack builder for BMAD v5 projects. Build Story {X.Y} end-to-end in one pass.

Story file:    {story file path}
UX spec:       {project-root}/_bmad-output/planning-artifacts/ux-design-specification.md
Architecture:  {project-root}/_bmad-output/planning-artifacts/architecture.md
Epic context:  {project-root}/_bmad-output/planning-artifacts/epics.md  (read only the section for {epic-slug})

Do exactly these steps, in order:

1. READ THE STORY FILE COMPLETELY.
   Extract:
   - Every AC (look for "**AC-N:**" headers)
   - Every Edge Case
   - Every Adversarial Finding
   - Every Definition of Done item
   - Components built / used (from frontmatter)
   - Dependencies (from frontmatter — verify they're shipped before continuing)

2. READ THE RELEVANT UX SPEC SECTION.
   Identify which §13.X "Journey" this story belongs to (epic name → journey name).
   Read that journey's full mermaid + failure paths + Egyptian-Native notes.
   Read §0 Locked Decisions (color / typography / direction).
   Read §11.11.4 Egyptian-Native Component Library if the story uses any wrapper.

3. READ RELEVANT ARCHITECTURE SECTIONS.
   Search architecture.md for the modules touched by this story:
   - For auth/identity stories: §AuthService wrapper + §provider abstraction
   - For data stories: §Drizzle schema + §migration discipline
   - For UI stories: §i18n + §design tokens
   Quote any contract / interface that constrains your build.

4. DETECT THE PROJECT STACK.
   Look for:
   - `apps/api/` or `backend/` + `nest-cli.json` → NestJS backend
   - `apps/web/` or `frontend/package.json` → Next.js frontend
   - `pnpm-workspace.yaml` → pnpm monorepo
   - `docker-compose.yml` → Docker dev environment
   Use the detected stack for all commands below.

5. USE THE DESIGN SYSTEM ALREADY WIRED IN THE CODEBASE.
   Look for:
   - `src/styles/tokens.css` or `apps/web/src/styles/tokens.css` → design tokens
   - `src/components/ui/` → shadcn/ui primitives
   - `src/lib/egyptian-native/` → Egyptian-Native wrappers (<InternationalPhone>, <EgyptianPhone>, ...)
   - `tailwind.config.*` → Tailwind theme
   DO NOT introduce new tokens. If a value is missing, reuse the closest existing one or HALT and flag.

6. BUILD FULL-STACK in this order (don't skip layers):
   a. DB migrations (Drizzle) — if the story touches schema
   b. Backend services + API routes — typed contracts with the frontend
   c. Frontend components + routes — use the design system from step 5
   d. Tests — per TEST WRITING DISCIPLINE below
   e. Seeders / fixtures — if the story needs sample data for review

   TEST WRITING DISCIPLINE (READ THIS — over-testing is forbidden):
   - Write tests ONLY for explicit ACs in the story. Not for every function.
   - 1-3 tests per AC maximum. Prefer ONE happy-path + ONE edge case.
   - NO E2E tests in Phase 5 (deferred to Phase 7 Harden). Unit + integration only.
   - If an AC is purely UI (visual styling, color, spacing) — SKIP the test. Visual review in Step 4 handles it.
   - DO NOT write tests for: helper / internal functions, getters/setters, simple wrappers, framework code, third-party library behavior.
   - If you find yourself writing test #4 for the same AC, STOP. You're over-testing.
   - Prefer integration tests over unit tests when both would cover the same AC.

7. START THE DEV SERVER.
   - Backend: `docker compose up -d` (or `pnpm dev:api` if not dockerized)
   - Frontend: `pnpm dev` on the project's assigned port (look up CLAUDE.md port table)
   - Wait for health: `curl -fsS http://localhost:{port}/api/v1/health` should return 200
   - If health check fails, HALT and print the last 40 lines of server logs.

8. PRINT THE AC IMPLEMENTATION MAP (CRITICAL — Step 3 of the protocol will verify this).
   Format every AC in the story file. For each:

   ```
   AC-N (<short title>):
     Files:
       - <relative file path>  (<what it does>)
       - ...
     Tests:
       - <test file path>  (<N cases>)  OR  "Skipped — visual-only AC, covered in Step 4 review"
   ```

   List EVERY AC that exists in the story file. If you couldn't implement one, say so explicitly:

   ```
   AC-N (<short title>):
     STATUS: deferred
     REASON: <one-line reason — e.g. "blocked on WhatsApp BSP credentials">
   ```

9. RETURN A SUMMARY BLOCK with this exact shape:

   ```
   ## Saneh Return — Story {X.Y}

   ### Routes built
   - <method> <path>  → <one-line purpose>
   - ...

   ### Dev server
   URL: http://localhost:{port}
   Health: ✓ 200

   ### AC Implementation Map
   <map from step 8>

   ### Notes for review
   - <anything the human reviewer should know>

   ### Tests run
   - <command>  →  <pass/fail>

   READY for Step 3 (AC-Compliance check).
   ```

CRITICAL RULES:
- NEVER skip the AC Implementation Map — the next step will halt the protocol if it's missing or incomplete.
- If you hit a blocker that prevents finishing a story, HALT with a clear diagnosis. Don't fabricate completion.
- DO NOT commit. The orchestrator handles git in Step 9 via /commit-story.
- DO NOT amend prior commits.
- DO NOT take dev-data destructive actions (e.g. `drop database`) without explicit user approval.
- ALWAYS use the design system tokens. NEVER hand-roll colors / fonts.
- TEST DISCIPLINE: respect the calibrated test rules in step 6. Do not "play it safe" by adding extra tests.
```

When Saneh returns, print its Return block verbatim. **Append to the story file's `## Protocol Audit Trail`:**

```
- [x] Step 2 Saneh — AC Map ({N} ACs mapped, {D} deferred)
```

Mark Step 2 done. Proceed to Step 3 in the same turn.

---

## Step 3 — AC-Compliance Check

Run the AC-Compliance script:

```bash
bash {skill-dir}/scripts/ac-compliance-check.sh \
  --story "{story file path}" \
  --map-output "{path to Saneh's return block saved to a tmp file}"
```

The script:
1. Parses the story file → extracts AC IDs (`AC-1`, `AC-2`, ...)
2. Parses Saneh's AC Implementation Map → extracts which AC IDs were addressed
3. Compares — every story AC must have a map entry (implemented, skipped-visual, OR deferred-with-reason)
4. Bonus: verifies cited file paths exist in the repo (catches hallucinated paths)

Outcomes:
- **PASS** → mark step done, proceed to Step 4. **Append to Audit Trail:** `- [x] Step 3 AC-Compliance — PASS`
- **MISSING-AC** → halt: "AC-X is in the story but absent from Saneh's map. Re-run Saneh with explicit instruction to address AC-X, OR amend the story to defer it (with reason)."
- **HALLUCINATED-PATH** → halt: "Saneh cited <path> for AC-X but the file doesn't exist. Fix or document."

---

## Step 4 — User Review [PAUSE]

The orchestrator prints the iteration prompt (template in `handoff-iteration-prompt.md`) with placeholders filled. Block:

```
✅ Story {X.Y} built. Dev server running at http://localhost:{port}.

📋 PASTE THIS IN A NEW CHAT TO ITERATE WITH /impeccable live:
═══════════════════════════════════════════════════════════════
<contents of handoff-iteration-prompt.md with placeholders resolved>
═══════════════════════════════════════════════════════════════
END — copy everything between the lines above.

Waiting for your "approved" signal in this chat…
```

The orchestrator goes idle. The user iterates in a separate chat — that chat edits files directly. When the user is done, they return and type one of:

- **`approved`** → mark step done, proceed to Step 5. The current file state is what proceeds. **Append to Audit Trail:** `- [x] Step 4 User Review — approved at <ISO timestamp>`
- **`/bmad-business-change ...`** → orchestrator hands off to that skill; on return, Step 2 reruns (the business-change cascade may invalidate the build).

The story state stays at Step 4 until one of those signals lands.

---

## Step 5 — Simplify (sequential review skills, in-context)

Two /simplify review skills run as **skills in the current conversation** — NOT as the `code-simplifier:code-simplifier` Agent. Rationale: the diff is already in this conversation; re-loading it per agent duplicates ~80k tokens per reviewer for no signal gain.

**History:** Step 5 used to run THREE skills (reuse / quality / efficiency). The efficiency skill was merged into code-quality in 2026-05 — efficiency was producing only 0-3 findings per story while paying a full skill-call cost, and the categories overlap heavily with quality (both review hot-path bloat, redundant computation, leaky abstractions). The merged code-quality skill now covers 12 categories with a cap of 12 findings.

Invoke each skill in order via the Skill tool. After each skill produces its findings, **apply the patches inline** before invoking the next.

**CONTINUOUS-FLOW RULE:** Both skill invocations + their fixes happen in **one continuous flow**. Do NOT end the turn between skills. Do NOT summarize findings to the user between skills. Each review skill ends with a `--- end of <skill-id> ---` marker — that marker is your cue to immediately invoke the next skill in the same turn.

**Auto-fix policy (ZERO user prompts):** CRITICAL + HIGH = always fix. MEDIUM = fix if local/obvious; otherwise defer to `_bmad-output/implementation-artifacts/deferred-work.md` with `source: simplify-v5`. LOW = defer automatically.

**Judgment calls: DECIDE-AND-LOG, never stop-and-ask.** Pick the most-likely-correct interpretation using priority order: (a) PRD ACs for THIS story, (b) UX spec § for this story's journey, (c) architecture doc, (d) prior shipped-story decisions in same area, (e) general principles. Apply the fix. Append entry to the story file's "## Autonomous Decisions" section with: location, options, chosen option, reasoning, reversibility.

1. **Skill:** `bmad-light-review-code-reuse` — apply reuse fixes inline.
2. **Skill:** `bmad-light-review-code-quality` — apply quality + efficiency fixes inline.

If a skill returns "No <X> findings.", move on without changes.

**Append to Audit Trail** (in this order, one bullet per skill):
```
- [x] Step 5 Simplify
  - [x] code-reuse — {total} findings, {fixed} fixed, {deferred} deferred
  - [x] code-quality — {total} findings, {fixed} fixed, {deferred} deferred
```

Mark done → Step 6.

---

## Step 6 — Code Review (sequential review skills, in-context)

Three reviewer skills run sequentially in the current conversation.

**Run Blind Hunter FIRST** — best preservation of blindness available in this architecture.

When invoking each reviewer skill, prefix the input with this **auto-mode preamble**:

> "auto-mode: story-protocol orchestrator (v5) — batch-apply all patches, apply severity gating to decision-needed (stop only on High-impact without spec answer), skip interactive HALTs."

**CONTINUOUS-FLOW RULE:** All three skill invocations happen in **one continuous flow**. Do NOT end the turn between skills. Each review skill ends with a `--- end of <skill-id> ---` marker — your cue to invoke the next skill immediately. Only after ALL three skills have returned do you proceed to triage.

**Collect findings from all three before triaging** — do not fix inline mid-sequence.

1. **Skill:** `bmad-review-adversarial-general` (Blind Hunter — adversarial pass; pass `content = <the diff already in context>`).
2. **Skill:** `bmad-review-edge-case-hunter` (Edge Case Hunter — exhaustive path enumeration; pass `content = <the diff>`).
3. **Skill:** `bmad-light-review-acceptance` (Acceptance Auditor — diff vs the story / acceptance criteria).

### Auto-Fix Findings Policy (ZERO user prompts)

After all three reviewers return, dedupe findings (match file:line + root cause), then triage:

- **CRITICAL** → fix inline immediately. Always.
- **HIGH** → fix inline. Always.
- **MEDIUM** → fix if local/obvious; otherwise defer to `_bmad-output/implementation-artifacts/deferred-work.md` with `source: code-review-v5`.
- **LOW** → defer automatically.
- **Dismissed** → add one-line reason in the story file's "Dismissed Findings" section.

**Judgment calls: DECIDE-AND-LOG, never stop-and-ask.** Same procedure as Step 5.

After fixes applied:
```bash
pnpm typecheck && pnpm lint
```
Fix any regression. **Append to Audit Trail** (one bullet per skill, in invocation order):
```
- [x] Step 6 Code Review
  - [x] adversarial — {total} findings, {fixed} fixed, {deferred} deferred
  - [x] edge-case-hunter — {total} findings, {fixed} fixed, {deferred} deferred
  - [x] acceptance — {total} findings, {fixed} fixed, {deferred} deferred
```
Go to Step 7.

---

## Step 7 — PR Review (in-context)

**One reviewer skill** runs in the current conversation. The previous test-coverage reviewer (`bmad-light-review-pr-tests`) was removed in this protocol revision — its findings were causing over-testing pressure that conflicts with the calibrated Test Writing Discipline in Step 2. Acceptance coverage is already verified by `bmad-light-review-acceptance` in Step 6.

When invoking, prefix the input with the **auto-mode preamble**:

> "auto-mode: story-protocol orchestrator (v5) — batch-apply all patches, apply severity gating to decision-needed (stop only on High-impact without spec answer), skip interactive HALTs."

1. **Skill:** `bmad-light-review-silent-failure` (Silent Failure Hunter — error-handling audit).

### Auto-Fix Findings Policy (ZERO user prompts)

After the reviewer returns, dedupe against Step 6 findings, then triage with the same policy as Steps 5 + 6.

**Judgment calls: DECIDE-AND-LOG, never stop-and-ask.**

After fixes applied:
```bash
pnpm typecheck && pnpm lint && pnpm test
```
Fix any regression. **Append to Audit Trail:**
```
- [x] Step 7 PR Review
  - [x] silent-failure — {total} findings, {fixed} fixed, {deferred} deferred
```
Go to Step 8.

---

## Step 8 — Verify

Run from project root:

```bash
pnpm typecheck && pnpm lint && pnpm test
```

(Or project-specific equivalents.) If any fail → halt + diagnose. **Append to Audit Trail** when all green:
```
- [x] Step 8 Verify — typecheck/lint/test PASS
```
Mark done.

---

## Step 9 — `/commit-story` (local commit, no push)

Invoke `/commit-story` skill. **As its FIRST action it calls `bmad-protocol-compliance-check`** — that skill reads the story file's `## Protocol Audit Trail` section, verifies every expected entry (Steps 2-8) is present, HALTS the commit if anything's missing. The orchestrator MUST complete the missing step before retrying — no bypass flag, no manual override.

Once the gate passes, the skill:
- Stages specific files Saneh + reviews touched (NEVER `git add -A`)
- Creates a commit message: `Story {X.Y}: <title>` + body listing the AC Implementation Map summary
- Commits locally on the `epic-{N}` branch
- **Does NOT push.** Does NOT open a PR. Both happen at end-of-epic.
- Updates `roadmap-progress.yaml` for the story:

```yaml
phases:
  5-build:
    epics:
      {N}:
        stories:
          "{X.Y}":
            status: committed
            committed_at: "{ISO timestamp}"
            commit_sha: "<sha>"
        current_story: "<next pending story ID>"
```

Then print:

```
✅ Story {X.Y} committed locally (sha: <short>).
   {if NOT last story in epic} Next pending in Epic {N}: Story {X.Y+1} (<title>)
   {if last story in epic} End-of-epic reached. Run `/ship-epic` when ready to merge.

   To continue: run /bmad-roadmap-v5 in any chat.
```

The protocol ends for this story. The orchestrator does NOT auto-start the next story.

---

## End of Epic — Trace + Ship

After the LAST story of an epic is committed (i.e., `epic.stories_committed == epic.stories_total`):

1. **Trace coverage:** Run `/bmad-testarch-trace` for this epic. Produces `epic-{N}-trace.md` (AC ↔ tests matrix). If gaps flagged: review with user (add tests, defer to Phase 7, or accept).
2. **Ship:** Run `/ship-epic`. It handles rebase + push + PR + CI wait + squash-merge + sync.

Update `roadmap-progress.yaml` (the `/ship-epic` skill does this):
```yaml
epics:
  {N}:
    status: shipped
    trace_done: true
    shipped_at: "{today}"
    pr_url: "<PR URL>"
```

Move to the next epic's first story (or, if it was the last epic, mark Phase 5 complete and advance to Phase 6).

---

## Resume contract

If the user opens a fresh chat and runs `/bmad-roadmap-v5 --resume-story={X.Y}`:
1. Read `roadmap-progress.yaml: 5-build.epics[N].stories[X.Y].current_step` (or the implicit step from `5-build.current_step` if X.Y matches `current_story`)
2. Re-enter the protocol at that step
3. If at Step 4 (User Review pause) — read the iteration prompt from disk (we save it next to the story for replay) and re-display it

For Step 4 replay, the orchestrator saves the iteration prompt to:
```
{project-root}/_bmad-output/implementation-artifacts/iteration-prompts/{X.Y}.md
```
This file is auto-deleted on Step 9 success.
