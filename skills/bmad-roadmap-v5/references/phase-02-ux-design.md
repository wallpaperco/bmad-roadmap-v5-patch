# Phase 2 — UX Design

**Goal:** Produce a single consolidated UX specification document covering all journeys, design system, and component strategy.

**Exit:** `ux-design-specification.md` exists and is approved.

---

## Steps

1. **Run `/bmad-create-ux-design` (BMM-native)** → produces `_bmad-output/planning-artifacts/ux-design-specification.md`.

The workflow walks through 14 steps:
- Discovery + Executive Summary
- Locked Decisions (colors, typography, direction)
- Core User Experience
- Desired Emotional Response
- Inspiration analysis
- Design System Foundation (tokens + components)
- Visual Design Foundation
- Direction Decision (which palette / typography stack wins)
- 18 User Journeys (one per future epic)
- Component Strategy
- Cross-journey UX patterns
- Responsive Design & Accessibility
- PDPL compliance notes (Egyptian projects)

2. **User reviews + approves** the entire document. Discuss any disagreements. Re-run individual steps via `/bmad-create-ux-design --resume-step=N` if needed.

---

## Design system handoff to Phase 5 (Build)

v5 assumes the design system will be wired in code (not in Claude Design). The UX spec must produce enough detail that Story 2.1 (or your first build story) can scaffold:

- `tokens.css` — color / spacing / radius / typography tokens (from §0 Locked Decisions + §9 Design System Foundation)
- Self-hosted fonts in `/public/fonts/` (filenames + `@font-face` declarations)
- Component inventory — list of Tier 2 + Tier 3 components the product needs
- Egyptian-Native wrappers spec (§11.11.4 if Egyptian-market project)

**If the project has an org-level design system repo** (e.g. `github.com/<org>/<project>-design-system`), the UX spec should reference it so Story 2.1 can `git submodule add` or `pnpm add` it instead of rebuilding from scratch.

---

## Phase exit checklist

- [ ] `ux-design-specification.md` exists
- [ ] §0 Locked Decisions section is filled (color / typography / direction)
- [ ] 13.X user-journey sections exist for every planned epic
- [ ] §9 Design System Foundation section is filled (tokens documented)
- [ ] User approved the document

On exit, update `roadmap-progress.yaml`:
```yaml
2-ux-design:
  status: complete
  completed: "{today}"
  artifact: "_bmad-output/planning-artifacts/ux-design-specification.md"
  journeys_count: <int>
```

Advance to Phase 3.
