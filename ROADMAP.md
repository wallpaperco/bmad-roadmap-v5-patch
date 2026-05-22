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
4. **(removed)** — per-story User Review PAUSE removed in 2026-05. Visual review now happens once per epic, post-ship, via `bmad-epic-flow-demo` (see End-of-each-epic step `d`). Saneh's output flows directly into Step 5.
5. **Simplify (in-context skills)** — sequential `bmad-light-review-code-reuse` + `bmad-light-review-code-quality` (2 skills, not 3 — efficiency was merged into code-quality in 2026-05). Autonomous (no user prompts). Findings auto-applied per severity policy; judgment calls logged to story file's `## Autonomous Decisions` section instead of pausing.
6. **Code Review (in-context skills)** — sequential `bmad-review-adversarial-general` (Blind Hunter, capped at 12 findings) + `bmad-review-edge-case-hunter` + `bmad-light-review-acceptance`. Autonomous, same DECIDE-AND-LOG pattern.
7. **PR Review (in-context skills)** — `bmad-light-review-silent-failure`. Autonomous, same pattern. (`bmad-light-review-pr-tests` retired earlier — was driving over-testing pressure. Legacy `pr-review-toolkit` agents intentionally dropped; invoke manually if a specific story needs them.)
8. **Verify** — typecheck + lint + tests.
9. **`/commit-story`** — local commit on the epic branch. **Step 9.0 calls `bmad-protocol-compliance-check`** which reads the story file's `## Protocol Audit Trail` section and HALTS the commit if any expected step entry is missing. No `--skip-compliance` flag — the gate is mandatory because it's the entire defence against autonomous-skip bugs in `/goal` mode. No push, no PR (those happen at end-of-epic via `/ship-epic`).

**Audit Trail discipline:** every story file ends with a `## Protocol Audit Trail` section. The orchestrator appends one `- [x] Step N <name>` bullet the same turn each step finishes. The compliance check at Step 9.0 grep's this section and verifies the 12-entry manifest (Saneh + AC-Compliance + Simplify×2 + Code Review×3 + PR Review×1 + Verify + 4 step headers). When a skill is silently skipped, the missing bullet trips the gate at the LOCAL story — not three stories later in a retrospective.

### End-of-each-epic

a. `/bmad-extract-deferrals` — walk the epic's commit messages, extract `**MEDIUM/LOW:**` + `Deferred:` sections, append to `_bmad-output/implementation-artifacts/deferred-work.md`. Catches up the registry from protocol output that lived in commit message bodies.
b. `/bmad-testarch-trace` — traceability matrix + quality gate. Reads `deferred-work.md` and surfaces a Deferrals Registry section (by source / severity / owning future story + red-flag for no-owner entries).
c. `/ship-epic` — rebase main, push the epic branch, open + merge the PR, sync local main.
d. **`bmad-epic-flow-demo`** — post-ship visual review (replaces the per-story Step 4 PAUSE). Detects new routes added in the epic; opens `epic-{N}-polish` branch from main; prints routes + suggested journey + `/impeccable live` paste-ready prompt; pauses for the user. On `approved` with polish commits: ships them via their own squash-merge PR. On `approved` with no commits: deletes the empty branch. Pure-infra epics (no UI surface) skip the pause and end immediately. **This is the ONLY user pause in the autonomous `/goal` flow.**

**Exit:** every story in sprint-status.yaml is `done` AND every epic's `polish_status` is recorded in roadmap-progress.yaml.

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
