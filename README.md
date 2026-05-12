# BMAD Roadmap v5 Patch

**Lean implementation-first roadmap.** 8 phases. No prototyping. No Claude Design loop. Visual iteration happens on a running dev server via `/impeccable live`.

## When to use

- **New projects** that already have a design system in code (tokens.css + fonts + Egyptian-Native wrappers) and want to skip the Claude Design prototyping phase entirely.
- You're comfortable iterating on UI on a running dev server (not on a static prototype).
- You want the shortest path from PRD to shipped code.

## When NOT to use

- You need a clickable prototype for stakeholder approval BEFORE writing code → use [v2 (Claude Design)](../bmad-claude-design-patch/ROADMAP.md).
- You have no design system yet → still use v2, run the Phase 4 Claude Design loop, then come back here for future projects.
- Legacy projects on WDS + per-screen specs → use [v1](../bmad-figma-patch/ROADMAP.md).

## What's different from v2

| | v2 (Claude Design) | v5 (this patch) |
|---|---|---|
| Phases | 9 | **8** |
| Phase 4 Claude Design loop | per-epic, manual browser work | **REMOVED** |
| Phase 5 Sprint Planning | separate phase | **separate (renumbered to 4)** |
| Story Protocol steps | 9 (with Naqed Compliance + Critique + Audit) | **9** (Naqed → `AC-Compliance` script + `/impeccable live` iteration + automated PR-review-toolkit) |
| Saneh prompt | reads Design Reference block + WebFetches bundle | reads UX spec §journey + uses design system already wired in codebase |
| Visual iteration | inside Claude Design (manual) | `/impeccable live` on the running dev server (in a new chat — orchestrator prints a paste-ready prompt) |
| `design-progress.yaml` | required | **not used** |

## Install

```bash
cd /path/to/project
bash ~/Desktop/workspace/abozaid/bmad-roadmap-v5-patch/install.sh
```

The installer is idempotent — re-run anytime. It copies (or symlinks with `--symlink`) the `bmad-roadmap-v5` skill into `.claude/skills/`.

## Roadmap overview

See [ROADMAP.md](ROADMAP.md) for the 8-phase summary.

## Migration from v2

Both `bmad-roadmap-v2` and `bmad-roadmap-v5` coexist as separate skills — install both, use whichever applies. **A project in mid-flight on v2 must manually edit `_bmad-output/roadmap-progress.yaml`** to switch (drop v2's `4-claude-design-loop` phase, renumber 5-9 → 4-8). The installer does NOT auto-migrate.

## Patch contents

```
skills/bmad-roadmap-v5/
├── SKILL.md                              # orchestrator — reads progress, routes to phase
├── scripts/
│   └── ac-compliance-check.sh            # lightweight grep-based AC-implementation check
└── references/
    ├── progress-template.yaml            # 8 phases, no design-loop tracking
    ├── story-protocol.md                 # 9 steps per story — Saneh rewritten for code-first
    ├── handoff-iteration-prompt.md       # template for /impeccable live (paste in new chat)
    ├── phase-01-discover.md
    ├── phase-02-ux-design.md
    ├── phase-03-epics-stories.md
    ├── phase-04-sprint-planning.md
    ├── phase-05-build.md
    ├── phase-06-deploy.md
    ├── phase-07-harden.md
    └── phase-08-evolve.md
```
