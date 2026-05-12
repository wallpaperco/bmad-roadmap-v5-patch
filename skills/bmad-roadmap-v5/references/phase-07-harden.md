# Phase 7 — Harden

**Goal:** Make the deployed app production-ready: performance, accessibility, security, observability, reliability, full E2E coverage.

**Exit:** no CRITICAL or HIGH findings unresolved.

---

## Steps

1. **`/bmad-testarch-nfr`** — Non-Functional Requirements audit covering:
   - **Performance:** Lighthouse + bundle size + API p95 latency vs PRD targets
   - **Accessibility:** axe-core scan + manual keyboard nav + screen reader spot-check
   - **Security:** semgrep + dependency audit (`pnpm audit`) + secrets scan
   - **Observability:** Sentry / structured logs / metrics dashboard verified
   - **Reliability:** SLO definition + alerting rules + rollback drill

   Produces `_bmad-output/planning-artifacts/nfr-report-{YYYY-MM-DD}.md` with findings triaged CRITICAL / HIGH / MEDIUM / LOW.

2. **`/bmad-testarch-test-review`** — coverage + test-quality audit:
   - Branch coverage per module
   - Test isolation (no flaky tests)
   - Assertion quality (no `expect(true).toBe(true)` traps)
   - Speed (slowest tests flagged)

3. **`/bmad-qa-generate-e2e-tests`** — one happy-path E2E per journey:
   - Walks every UX journey end-to-end via Playwright
   - Asserts critical state transitions (sign-up → trial active, search → comparison → export, etc.)
   - Locks the journeys in CI

---

## Fix CRITICAL + HIGH findings

For each CRITICAL or HIGH:
- If it's a code issue → open a new story in `sprint-status.yaml` (status `backlog`), reroute through Story Protocol from Phase 5
- If it's a config / infra issue → fix in-place + record the fix in `_bmad-output/planning-artifacts/harden-fixes-{YYYY-MM-DD}.md`
- If it's a process / docs issue → update the relevant doc + record

---

## Phase exit checklist

- [ ] `nfr-report-{YYYY-MM-DD}.md` exists with all CRITICAL and HIGH resolved or explicitly waived
- [ ] Test-review findings addressed
- [ ] Every journey has at least one E2E test in CI
- [ ] CI green on `main`

On exit, update `roadmap-progress.yaml`:
```yaml
7-harden:
  status: complete
  completed: "{today}"
  nfr_status: pass
  e2e_journeys_covered: <N/M>
```

Advance to Phase 8.
