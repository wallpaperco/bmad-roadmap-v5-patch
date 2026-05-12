# Phase 1 — Discover

**Goal:** Produce the four foundational planning artifacts: product brief, PRD, validation report, architecture.

**Exit:** all four exist + are approved by the user.

---

## Steps

1. **Domain research** (optional) — invoke `/bmad-domain-research` if the domain is unfamiliar. Skip if user has deep domain knowledge.
2. **Market research** (optional) — invoke `/bmad-market-research` if competitive landscape matters. Skip for internal tools.
3. **Brainstorming** (optional) — invoke `/bmad-brainstorming` if scope is fuzzy. Skip if user has a clear vision.
4. **Product brief** — invoke `/bmad-product-brief` → produces `_bmad-output/planning-artifacts/product-brief-*.md`. User reviews + approves.
5. **PRD** — invoke `/bmad-create-prd` → produces `_bmad-output/planning-artifacts/prd.md`. User reviews + approves.
6. **Validate PRD** — invoke `/bmad-validate-prd` → produces `_bmad-output/planning-artifacts/validation-report-*.md`. Fix any CRITICAL findings before proceeding.
7. **Architecture** — invoke `/bmad-create-architecture` → produces `_bmad-output/planning-artifacts/architecture.md`. User reviews + approves.

---

## Phase exit checklist

- [ ] `product-brief-*.md` exists and is approved
- [ ] `prd.md` exists and is approved
- [ ] `validation-report-*.md` exists with no CRITICAL unresolved
- [ ] `architecture.md` exists and is approved

On exit, update `roadmap-progress.yaml`:
```yaml
1-discover:
  status: complete
  completed: "{today}"
  artifacts:
    product_brief: "_bmad-output/planning-artifacts/product-brief-<slug>.md"
    prd: "_bmad-output/planning-artifacts/prd.md"
    validation_report: "_bmad-output/planning-artifacts/validation-report-{YYYY-MM-DD}.md"
    architecture: "_bmad-output/planning-artifacts/architecture.md"
```

Advance to Phase 2.
