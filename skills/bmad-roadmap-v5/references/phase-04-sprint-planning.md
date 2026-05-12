# Phase 4 — Sprint Planning

**Goal:** Produce a build-order plan that respects story dependencies.

**Exit:** `sprint-status.yaml` exists with stories in a valid topological order.

---

## Steps

1. **Run `/bmad-sprint-planning`** → produces `_bmad-output/implementation-artifacts/sprint-status.yaml`.

   The skill:
   - Reads every story's `dependencies:` frontmatter
   - Builds a dependency DAG
   - Outputs a topological sort (ties broken by story ID ascending)
   - Marks `points` per story (story-points effort estimate)
   - Calls out infrastructure stories that block large groups

2. **User reviews the order.** Adjust manually if business priority should override topological order (e.g. demo timing). Edit `sprint-status.yaml` directly.

---

## Sprint-status schema

```yaml
sprint:
  current_epic: 1
  current_story: "1.1"
  stories:
    - id: "1.1"
      epic: "epic-01-..."
      title: "..."
      status: backlog        # backlog | building | review | shipped | done
      depends_on: []
      points: 3
    - id: "1.2"
      ...
```

---

## v5 specific notes

- The first story of the FIRST EPIC will typically be **platform scaffolding + design-system integration** (Next.js scaffold + tokens.css + fonts + Docker dev env + Egyptian-Native wrappers).
- Sprint planning does NOT trigger any code. It just produces the plan. Code starts in Phase 5.

---

## Phase exit checklist

- [ ] `sprint-status.yaml` exists
- [ ] All buildable stories listed with status `backlog`
- [ ] Topological order valid (no story comes before its `depends_on`)
- [ ] First-epic-first-story is a sensible platform-bootstrap story
- [ ] User approved the order

On exit, update `roadmap-progress.yaml`:
```yaml
4-sprint-planning:
  status: complete
  completed: "{today}"
  artifact: "_bmad-output/implementation-artifacts/sprint-status.yaml"
  stories_ordered: <int>
```

Advance to Phase 5.
