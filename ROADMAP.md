# BMAD Roadmap v5 — 8 Phases

> **Interactive workflow:** `/bmad-roadmap-v5`
> Tracks progress in `_bmad-output/roadmap-progress.yaml`. Use `--status` to check, `--phase N` to jump.

Lean implementation-first. No prototyping. No Claude Design loop. Visual iteration via `/impeccable live` on a running dev server, in a separate chat.

---

## Phase 1 — Discover

1. `/bmad-domain-research` · skip if domain is well-known
2. `/bmad-market-research` · skip if not a product
3. `/bmad-brainstorming` · skip if user has clear vision
4. `/bmad-product-brief`
5. `/bmad-create-prd`
6. `/bmad-validate-prd` · fix gaps before moving on
7. `/bmad-create-architecture`

**Exit:** all 4 artifacts (product-brief, prd, validation-report, architecture) approved.

---

## Phase 2 — UX Design

1. `/bmad-create-ux-design` (BMM native) → one consolidated `_bmad-output/planning-artifacts/ux-design-specification.md`

**Exit:** ux-design-specification.md approved.

---

## Phase 3 — Epics & Stories

1. `/bmad-create-epics-and-stories-v2` — generates epics + stories with adversarial + edge-case reviews per story.
2. `/bmad-check-implementation-readiness` — validates PRD/UX/Architecture/Epics consistency.

**Exit:** readiness check returns `pass`.

---

## Phase 4 — Sprint Planning

1. `/bmad-sprint-planning` — produces `sprint-status.yaml` with topologically-sorted stories by `dependencies` field.

**Exit:** sprint-status.yaml shows ordered stories ready to build.

---

## Phase 5 — Build

### First-epic-only setup (runs once before first story)

a. `/bmad-testarch-framework` — initialize Playwright + test infrastructure
b. `/bmad-testarch-ci` — scaffold CI quality pipeline

### Per story — Story Protocol (9 steps)

See [references/story-protocol.md](skills/bmad-roadmap-v5/references/story-protocol.md) for the full prompts.

1. **Branch** — `git checkout -b epic-{N}/story-{N.M}-{slug}`
2. **Saneh** — full-stack build (UI + API + DB + seeder + tests). Starts dev server. Outputs **AC Implementation Map**.
3. **AC-Compliance check** — automated script verifies every AC in the story file has an entry in Saneh's map. Halts on any missing AC.
4. **User Review [PAUSE]** — orchestrator prints `/impeccable live` iteration prompt for a new chat. User iterates visually until satisfied, returns and types `approved`.
5. **`/simplify`** — code-simplifier pass over the story diff.
6. **`/bmad-code-review`** — adversarial code review (Blind Hunter + Edge Case Hunter + Acceptance Auditor).
7. **PR Review (3 agents in parallel)** — pr-review-toolkit (code-reviewer + comment-analyzer + silent-failure-hunter + type-design-analyzer).
8. **Verify** — typecheck + lint + tests.
9. **`/ship`** — commit + push + open PR + wait CI + merge.

### End-of-each-epic

a. `/bmad-retrospective` — extract lessons + assess success
b. `/bmad-testarch-trace` — traceability matrix + quality gate

**Exit:** every story in sprint-status.yaml is `done`.

---

## Phase 6 — Deploy

1. Server setup (clone repo to `/opt/apps/<project>/`)
2. Caddy domain + reverse_proxy
3. `docker-compose.prod.yml` + Dockerfiles + nginx prod.conf
4. GitHub Actions `deploy.yml` + secrets + GHCR
5. Docker proxy network + DNS A record
6. Post-deploy smoke test (health endpoint + every journey)
7. Update global CLAUDE.md "Deployed Apps" table

**Exit:** prod URL returns 200 + every journey walkable end-to-end.

---

## Phase 7 — Harden

1. `/bmad-testarch-nfr` — perf + a11y + security + observability + reliability
2. `/bmad-testarch-test-review` — coverage + quality
3. `/bmad-qa-generate-e2e-tests` — one happy-path E2E per journey

**Exit:** no CRITICAL or HIGH findings unresolved.

---

## Phase 8 — Evolve

1. Collect signals (feedback, analytics, ops learnings)
2. Prioritize changes
3. Loop back into Phase 2 / 3 / 4 as needed (via `/bmad-business-change` for cascading changes)

**Exit:** open-ended; no fixed exit.

---

## Phase transitions — hard rules

- **Phase 5 (Build)** is only enterable when `sprint-status.yaml` exists (Phase 4 complete).
- **Phase 6 (Deploy)** is only enterable when every story is `done`.
- **Phase 5 escape** — if mid-build a business change is needed, the user runs `/bmad-business-change` from any chat. The roadmap tolerates this; the story being built may need to restart from Saneh step.
