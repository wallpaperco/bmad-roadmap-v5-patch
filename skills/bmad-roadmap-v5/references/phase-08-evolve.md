# Phase 8 — Evolve

**Goal:** Post-launch product evolution. Loop back into earlier phases as needed when new requirements or improvements emerge.

**Exit:** open-ended. No fixed exit — this phase continues for the product's lifetime.

---

## Steps

1. **Collect signals** continuously:
   - User feedback (in-app forms, support tickets, qualitative interviews)
   - Analytics (PostHog event funnels, feature adoption, churn cohorts)
   - Operational learnings (Sentry error patterns, performance regressions, on-call incidents)
   - Competitive moves (new entrants, pricing shifts, feature parity gaps)

2. **Prioritize changes** — quarterly or as-needed:
   - Sort by (impact × confidence) / effort
   - Group into themes (Q1 = "convert trial users faster", Q2 = "expand to enterprise", etc.)
   - Communicate prioritization to stakeholders

3. **Loop back** depending on change type:

   | Change type | Re-enter at |
   |---|---|
   | New journey / large feature | Phase 2 (UX) — extend `ux-design-specification.md` with a new §13.X journey, then Phase 3 to add the epic |
   | New story within existing epic | Phase 3 — add story file, re-run readiness check, then Phase 4 sprint planning |
   | Spec-only change (no new stories) | `/bmad-business-change` — cascades PRD/Arch/UX/Stories without re-entering a phase |
   | Tech-debt-only refactor | Open a new story in `sprint-status.yaml`, route through Phase 5 |
   | NFR regression (perf / a11y / security) | Phase 7 — re-run `/bmad-testarch-nfr` for the affected area |

4. **Re-deploy** — every shipped story flows through the same CI/CD pipeline established in Phase 6.

---

## When to retire v5 for this project

Phase 8 may eventually surface fundamental product changes that warrant a fresh roadmap (new domain, new tech stack, new revenue model). At that point, the team typically:
- Creates a v2 product (new repo or major branch)
- Re-runs `/bmad-roadmap-v5` (or whichever roadmap version applies) from Phase 1 for that v2

v5 is designed to support steady product evolution — major rewrites should fork into a new roadmap.

---

## No phase exit

Phase 8 has no exit gate. The product team uses this phase indefinitely. The orchestrator's `--status` command will permanently report Phase 8 once the project lands here.

`roadmap-progress.yaml` is updated each time a `/bmad-business-change` runs or a new evolution story ships:

```yaml
8-evolve:
  status: in-progress
  last_business_change: "{YYYY-MM-DD}"
  last_evolution_story: "<X.Y>"
```
