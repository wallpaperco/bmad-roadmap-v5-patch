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
| Story Protocol steps | 9 (with Naqed Compliance + Critique + Audit) | **9** (Naqed → `AC-Compliance` script + `/impeccable live` iteration + sequential in-context review skills — no agents) |
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

The patch is **self-contained** — it bundles the v5 orchestrator + the 8 in-context review skills that the Story Protocol depends on. No external skill dependencies.

```
skills/
├── bmad-roadmap-v5/                      # orchestrator (the one you invoke as /bmad-roadmap-v5)
│   ├── SKILL.md
│   ├── scripts/
│   │   └── ac-compliance-check.sh        # AC-implementation check (Story Protocol Step 3)
│   └── references/
│       ├── progress-template.yaml        # 8 phases, no design-loop tracking
│       ├── story-protocol.md             # 9 steps per story — Saneh + in-context review skills
│       ├── handoff-iteration-prompt.md   # template for /impeccable live (paste in new chat)
│       └── phase-{01..08}-*.md           # one per phase
│
├── bmad-light-review-code-reuse/         # Story Protocol Step 5 (Simplify)
├── bmad-light-review-code-quality/       # Story Protocol Step 5 (includes efficiency cats)
├── bmad-review-adversarial-general/      # Story Protocol Step 6 (Code Review — Blind Hunter)
├── bmad-review-edge-case-hunter/         # Story Protocol Step 6
├── bmad-light-review-acceptance/         # Story Protocol Step 6
├── bmad-light-review-silent-failure/     # Story Protocol Step 7 (PR Review)
├── bmad-extract-deferrals/               # End-of-epic — extract deferrals from commits
├── commit-story/                          # v5 per-story commit helper
└── ship-epic/                             # v5 end-of-epic ship flow
```

**Retired in this revision:**
- `bmad-light-review-efficiency` — merged into `bmad-light-review-code-quality` (2026-05). The efficiency-only skill was producing 0-3 findings per story while paying a full skill-call cost; categories overlap with quality. The merged skill covers 12 categories with a 12-finding cap.
- `bmad-light-review-pr-tests` — removed earlier; was driving over-testing pressure.

**Co-existence with other BMAD roadmap patches:** if you also have `bmad-figma-patch` or `bmad-roadmap-light-patch` installed, the review skills are SHARED — re-installing v5 overwrites them with this patch's bundled copies. The retired skills are removed automatically.
