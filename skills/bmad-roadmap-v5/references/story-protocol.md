# Story Protocol — v5 (9 steps)

Per-story workflow invoked by Phase 5 (Build). Each story = its own branch + PR. The user typically runs each story in a fresh chat for clean context.

**Inputs (resolved by the orchestrator before entering this protocol):**
- `{X.Y}` — story ID (e.g. `2.7`)
- `{story file path}` — absolute path to the story markdown
- `{epic-slug}` — for branch naming
- `{slug}` — short URL-safe slug derived from story title

**Stage tracker:** `roadmap-progress.yaml: 5-build.current_step` (1-9). Resumable.

---

## Step 1 — Branch

```bash
git checkout -b epic-{N}/story-{X.Y}-{slug}
```

Convention: `epic-2/story-2.7-mobile-otp-registration`. If the branch already exists (resuming a story), check it out instead. Mark step done; proceed to Step 2 in the same turn.

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
   d. Tests — unit (Vitest) + integration where required by DoD
   e. Seeders / fixtures — if the story needs sample data for review

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
       - <test file path>  (<N cases>)
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
   - <anything the human reviewer should know — e.g. "Tier B/C consent deferred to Settings per FR-NEW-UT11 clarification">

   ### Tests run
   - <command>  →  <pass/fail>

   READY for Step 3 (AC-Compliance check).
   ```

CRITICAL RULES:
- NEVER skip the AC Implementation Map — the next step will halt the protocol if it's missing or incomplete.
- If you hit a blocker that prevents finishing a story, HALT with a clear diagnosis. Don't fabricate completion.
- DO NOT commit. The orchestrator handles git in Step 9.
- DO NOT amend prior commits.
- DO NOT take dev-data destructive actions (e.g. `drop database`) without explicit user approval.
- ALWAYS use the design system tokens. NEVER hand-roll colors / fonts.
```

When Saneh returns, print its Return block verbatim. Mark Step 2 done. Proceed to Step 3 in the same turn.

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
3. Compares — every story AC must have a map entry (implemented OR deferred-with-reason)
4. Bonus: verifies cited file paths exist in the repo (catches hallucinated paths)

Outcomes:
- **PASS** → mark step done, proceed to Step 4
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

Then the orchestrator goes idle in the main chat. The user iterates in a separate chat via `/impeccable live`. When done, the user returns and types one of:

- **`approved`** → mark step done, proceed to Step 5
- **`rebuild: <reason>`** → reset Step 2; Saneh runs again with the user's note appended to its prompt
- **`/bmad-business-change ...`** → orchestrator hands off to that skill; on return, Step 2 reruns

The story state stays at Step 4 until one of those signals lands.

---

## Step 5 — `/simplify`

Invoke the `code-simplifier` (`code-simplifier:code-simplifier`) Agent over the story diff:

```
Skill: code-simplifier
Args: focus on the diff for branch epic-{N}/story-{X.Y}-{slug}
```

Wait for it to complete. Review changes; if unsure, ask the user. Mark done, proceed.

---

## Step 6 — `/bmad-code-review`

Invoke `/bmad-code-review` (already part of BMAD). Three layers run in parallel:
- Blind Hunter (logic + correctness)
- Edge Case Hunter (boundary conditions)
- Acceptance Auditor (AC verification — overlaps with Step 3 but covers behavior, not just file presence)

Findings get triaged into: CRITICAL / HIGH / MEDIUM / LOW. CRITICAL / HIGH must be addressed before Step 7.

---

## Step 7 — PR Review (3 agents in parallel)

Launch three agents in one message (parallel):
1. `pr-review-toolkit:code-reviewer` — style + project conventions
2. `pr-review-toolkit:silent-failure-hunter` — empty catches, inappropriate fallbacks
3. `pr-review-toolkit:type-design-analyzer` — type design quality for any new types

(Optional 4th: `pr-review-toolkit:comment-analyzer` if many new comments were added.)

CRITICAL findings must be addressed before Step 8.

---

## Step 8 — Verify

Run from project root:

```bash
pnpm typecheck && pnpm lint && pnpm test
```

(Or the project-specific equivalents.) If any fail → halt + diagnose. Mark done when all green.

---

## Step 9 — `/ship`

Invoke `/ship`:
- Generates a commit message (concise, ≤72 chars title; body lists AC Implementation Map summary)
- Stages specific files (not `git add -A`)
- Commits
- Pushes to remote
- Opens PR via `gh pr create`
- Waits for CI to pass
- Merges (squash-merge by default)

On success: update `roadmap-progress.yaml` for the story:

```yaml
phases:
  5-build:
    epics:
      {N}:
        stories:
          "{X.Y}":
            status: shipped
            shipped_at: "{ISO timestamp}"
            pr_url: "<PR URL>"
            commit_sha: "<sha>"
        current_story: "<next pending story ID>"
```

Then print:

```
✅ Story {X.Y} shipped → PR merged.
   Next pending in Epic {N}: Story {X.Y+1} (<title>)

   To continue: run /bmad-roadmap-v5 in any chat (this one or a fresh one — your call).
```

The protocol ends. The orchestrator does NOT auto-start the next story. The user decides when and where (main chat vs. fresh chat).

---

## End of Epic — Retro + Trace

After the LAST story of an epic is shipped (i.e., `epic.stories_completed == epic.stories_total`):

a. Run `/bmad-retrospective` for that epic
b. Run `/bmad-testarch-trace` for that epic

Update `roadmap-progress.yaml`:
```yaml
epics:
  {N}:
    retro_done: true
    trace_done: true
    completed: "{today}"
```

Then move to the next epic's first story (or, if it was the last epic, mark Phase 5 complete and advance to Phase 6).

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
