---
name: bmad-roadmap-v5
description: Orchestrate the BMAD product development lifecycle across 8 phases — lean, implementation-first, no prototyping. Use when the user says 'bmad roadmap v5', 'start v5 roadmap', 'continue v5', 'where am I in v5', 'next phase v5', or asks what to do next on a project using this patch. Tracks progress in _bmad-output/roadmap-progress.yaml so work survives across conversations. Visual iteration uses /impeccable live on a running dev server, not a Claude Design prototype.
---

# BMAD Roadmap v5

## Overview

8-phase lean orchestrator. No prototyping, no Claude Design loop. Visual design iteration happens via `/impeccable live` on a running dev server, in a separate chat.

**Args:** `--status` for progress, `--phase N` to jump, `--resume-story=X.Y` to pick up mid-story, no args to continue.

## Execution Model

- **Phases 1–4 (Discover → UX → Stories → Sprint Planning):** Conversational — each step invokes a skill that produces an artifact. Wait for approval at natural gates.
- **Phase 5 (Build):** Loops per story. Saneh builds, AC-Compliance verifies, the orchestrator prints an iteration prompt for `/impeccable live` in a new chat, the user signals `approved`, then code-review + verify + ship.
- **Phases 6–8 (Deploy / Harden / Evolve):** Task-based. Follow the instructions in each phase file.

## On Activation

1. Load `{project-root}/_bmad-output/roadmap-progress.yaml`. If missing, this is a fresh start.

2. Fresh start:
   - Announce: "No v5 roadmap progress found. Starting fresh at Phase 1: Discover."
   - Copy `references/progress-template.yaml` to `{project-root}/_bmad-output/roadmap-progress.yaml`.
   - **Read it back** to confirm it exists on disk.
   - Set Phase 1 to `in-progress`.
   - Route to Phase 1.

3. Determine intent:
   - **`--status`** → Show current phase, story progress, current branch. Stop.
   - **`--phase N`** → Hard-block enforcement before jumping:
     - Phase 4 requires `3-epics-stories.status == complete`
     - Phase 5 requires `4-sprint-planning.status == complete`
     - Phase 6+ requires `5-build.status == complete`
     - Refuse with a clear message if unmet.
   - **`--resume-story=X.Y`** → Re-enter Phase 5 Story Protocol for that story at the step it was last at.
   - **No args / "continue"** → Resume from where the user left off.

4. Route to the appropriate phase reference file.

## Progress File Structure

### Initial Template (fresh start)

See `references/progress-template.yaml`. Created on activation if missing.

### Mature State Example

```yaml
project_name: "{project-name}"
current_phase: 5
started: "2026-05-20"
updated: "2026-06-04"

phases:
  1-discover:       { status: complete, completed: "2026-05-22" }
  2-ux-design:      { status: complete, completed: "2026-05-24" }
  3-epics-stories:  { status: complete, completed: "2026-05-26", readiness_check: pass }
  4-sprint-planning:{ status: complete, completed: "2026-05-26" }
  5-build:
    status: in-progress
    first_epic_setup_done: true
    current_epic: 2
    current_story: "2.7"
    current_step: 4               # see story-protocol.md
    epics:
      1: { status: complete, stories_total: 4, stories_completed: 4, retro_done: true }
      2: { status: in-progress, stories_total: 5, stories_completed: 2 }
  6-deploy:  { status: pending }
  7-harden:  { status: pending }
  8-evolve:  { status: pending }
```

## Phase Routing

| Phase | Reference File | Summary |
|-------|---------------|---------|
| 1 | `./references/phase-01-discover.md` | Product brief, PRD, validate, architecture |
| 2 | `./references/phase-02-ux-design.md` | `/bmad-create-ux-design` — one consolidated UX doc |
| 3 | `./references/phase-03-epics-stories.md` | `/bmad-create-epics-and-stories-v2` + readiness check |
| 4 | `./references/phase-04-sprint-planning.md` | `/bmad-sprint-planning` |
| 5 | `./references/phase-05-build.md` | Per story: Story Protocol (9 steps). First epic: test-infra. After each epic: retro |
| 6 | `./references/phase-06-deploy.md` | Full-stack deploy |
| 7 | `./references/phase-07-harden.md` | NFR + test review + E2E |
| 8 | `./references/phase-08-evolve.md` | Product evolution |
| — | `./references/story-protocol.md` | Shared sub-workflow for story execution (used by Phase 5) |
| — | `./references/handoff-iteration-prompt.md` | Template the orchestrator prints for `/impeccable live` in a new chat |

Load the reference file for the current phase and follow its instructions.

## Phase Transition Rules

Before moving to the next phase:
1. **Verify completion:** Read the phase reference file's exit condition. Confirm every required step is done.
2. **Update progress file:** Mark the phase `complete` with `completed: "{today}"`.
3. Set the next phase to `status: in-progress` and update `current_phase`.
4. Announce: "Phase N complete. Moving to Phase N+1: [name]."

**Special transitions:**
- **Phase 5 completion** requires every story in `sprint-status.yaml` to be `done`. Per-story completion is tracked inside `5-build.epics[N].stories`.
- **Phase 5 escape (business change)** — if the user runs `/bmad-business-change` mid-story, the affected story's `current_step` is reset to 2 (Saneh re-runs) once the cascade is complete.

## References

- `references/progress-template.yaml` — initial template
- `references/story-protocol.md` — 9-step per-story loop
- `references/handoff-iteration-prompt.md` — template for `/impeccable live`
- `references/phase-*.md` — one per phase
- `scripts/ac-compliance-check.sh` — invoked by story-protocol Step 3
