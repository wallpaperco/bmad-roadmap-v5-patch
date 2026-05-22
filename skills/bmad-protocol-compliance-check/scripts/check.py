#!/usr/bin/env python3
"""
Verify the `## Protocol Audit Trail` section in a v5 story file contains
every expected step + review-skill bullet. Exit 0 on PASS, 1 on FAIL with
a structured diagnostic on stderr.

Usage:
    check.py <story-file-path>

Called by the bmad-protocol-compliance-check skill at Step 9.0 of the
v5 Story Protocol (immediately before /commit-story stages files).

The manifest below mirrors the protocol revision in
.claude/skills/bmad-roadmap-v5/references/story-protocol.md. When the
protocol changes (skill added / removed / renamed), update both.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# Manifest of expected Audit Trail entries.
#
# Each entry is either a top-level step (e.g. "Step 3 AC-Compliance") OR
# a nested skill invocation (e.g. "Step 5 Simplify > code-reuse").
#
# `optional=True` marks entries the orchestrator may skip with explicit
# reason — e.g. the placeholder pre-pause "Step 4 User Review" if the user
# never paused. Today no entries are optional — every step must run.
#
# This list mirrors the v5 protocol AFTER the 2026-05 efficiency-merge +
# pr-tests removal. Update when the protocol changes.
@dataclass(frozen=True)
class ExpectedEntry:
    label: str  # Human-readable for diagnostics
    pattern: str  # Substring or regex (str.lower comparison)
    is_regex: bool = False
    required: bool = True
    parent: str | None = None  # Step bullet that must precede this nested skill

    def matches(self, line: str) -> bool:
        haystack = line.lower()
        if self.is_regex:
            return re.search(self.pattern, haystack) is not None
        return self.pattern.lower() in haystack


MANIFEST: list[ExpectedEntry] = [
    # Top-level step bullets (one per major protocol step).
    # Step 4 (per-story User Review PAUSE) was removed in 2026-05 — visual
    # review moved to post-ship per epic via bmad-epic-flow-demo. The
    # manifest expects 12 entries now (was 13).
    ExpectedEntry("Step 2 Saneh — AC Map", r"step 2 saneh", is_regex=True),
    ExpectedEntry("Step 3 AC-Compliance — PASS", r"step 3 ac.?compliance.*pass", is_regex=True),
    ExpectedEntry("Step 5 Simplify (header)", r"step 5 simplify", is_regex=True),
    ExpectedEntry("Step 6 Code Review (header)", r"step 6 code review", is_regex=True),
    ExpectedEntry("Step 7 PR Review (header)", r"step 7 pr review", is_regex=True),
    ExpectedEntry("Step 8 Verify — PASS", r"step 8 verify.*pass", is_regex=True),
    # Nested skill bullets inside Step 5 (Simplify).
    ExpectedEntry("Step 5 Simplify > code-reuse skill", "code-reuse —", parent="Step 5 Simplify (header)"),
    ExpectedEntry("Step 5 Simplify > code-quality skill", "code-quality —", parent="Step 5 Simplify (header)"),
    # Nested skill bullets inside Step 6 (Code Review).
    ExpectedEntry("Step 6 Code Review > adversarial skill", "adversarial —", parent="Step 6 Code Review (header)"),
    ExpectedEntry("Step 6 Code Review > edge-case-hunter skill", "edge-case-hunter —", parent="Step 6 Code Review (header)"),
    ExpectedEntry("Step 6 Code Review > acceptance skill", "acceptance —", parent="Step 6 Code Review (header)"),
    # Nested skill bullet inside Step 7 (PR Review).
    ExpectedEntry("Step 7 PR Review > silent-failure skill", "silent-failure —", parent="Step 7 PR Review (header)"),
]


@dataclass
class CheckResult:
    pass_: bool
    missing: list[ExpectedEntry] = field(default_factory=list)
    error: str = ""


def load_audit_trail(story_path: Path) -> list[str] | None:
    """Extract the bullet lines under `## Protocol Audit Trail`. Returns
    None if the section is missing entirely."""
    if not story_path.exists():
        return None
    text = story_path.read_text(encoding="utf-8")
    # Match the section heading + its body up to the next ## heading or EOF.
    m = re.search(
        r"(?im)^##\s+protocol\s+audit\s+trail\s*\n(.+?)(?=^##\s|\Z)",
        text,
        re.DOTALL,
    )
    if not m:
        return None
    body = m.group(1)
    # Collect every `- [x]` checked bullet, ignoring unchecked ones.
    bullets = re.findall(r"-\s*\[x\]\s*(.+)", body)
    return [b.strip() for b in bullets]


def check_compliance(story_path: Path) -> CheckResult:
    bullets = load_audit_trail(story_path)
    if bullets is None:
        return CheckResult(
            pass_=False,
            error=(
                "Section `## Protocol Audit Trail` missing from the story file. "
                "Append it with every step completed so far before retrying."
            ),
        )

    missing: list[ExpectedEntry] = []
    matched_labels: set[str] = set()

    for expected in MANIFEST:
        # If parent missing AND we haven't matched any related bullet, we'll
        # report the parent missing — no need to spam nested misses.
        if expected.parent and expected.parent not in matched_labels:
            # Defer evaluation; the parent will be the first surfaced miss.
            continue
        hit = any(expected.matches(line) for line in bullets)
        if hit:
            matched_labels.add(expected.label)
        elif expected.required:
            missing.append(expected)

    # Second pass: for any parent that WAS matched, surface its required
    # children that didn't match.
    for expected in MANIFEST:
        if expected.parent and expected.parent in matched_labels and expected.required:
            hit = any(expected.matches(line) for line in bullets)
            if not hit and expected not in missing:
                missing.append(expected)

    return CheckResult(pass_=len(missing) == 0, missing=missing)


SKILL_BY_LABEL = {
    "Step 5 Simplify > code-reuse skill": "bmad-light-review-code-reuse (Step 5)",
    "Step 5 Simplify > code-quality skill": "bmad-light-review-code-quality (Step 5)",
    "Step 6 Code Review > adversarial skill": "bmad-review-adversarial-general (Step 6)",
    "Step 6 Code Review > edge-case-hunter skill": "bmad-review-edge-case-hunter (Step 6)",
    "Step 6 Code Review > acceptance skill": "bmad-light-review-acceptance (Step 6)",
    "Step 7 PR Review > silent-failure skill": "bmad-light-review-silent-failure (Step 7)",
}


def render_fail_report(story_path: Path, result: CheckResult) -> str:
    story_id = "?"
    m = re.search(r"(\d+\.\d+)", story_path.stem)
    if m:
        story_id = m.group(1)

    lines = [
        f"❌ PROTOCOL COMPLIANCE FAIL — Story {story_id}",
    ]
    if result.error:
        lines.append(f"\n{result.error}")
        return "\n".join(lines)

    lines.append(f"\nMissing Audit Trail entries ({len(result.missing)}):")
    for entry in result.missing:
        lines.append(f"  - {entry.label}")

    # Actionable next-steps list.
    actions = []
    for entry in result.missing:
        if entry.label in SKILL_BY_LABEL:
            actions.append(f"Invoke {SKILL_BY_LABEL[entry.label]}")
        elif "Saneh" in entry.label:
            actions.append("Run Step 2 (Saneh full-stack build)")
        elif "AC-Compliance" in entry.label:
            actions.append("Run Step 3 (AC-Compliance check) — must PASS")
        elif "User Review" in entry.label:
            actions.append("Pause for Step 4 user review; record 'approved' timestamp")
        elif "Verify" in entry.label:
            actions.append("Run Step 8 (typecheck + lint + tests) until PASS")
        elif entry.label.startswith("Step 5 Simplify"):
            actions.append("Complete Step 5 (Simplify) and append its bullets")
        elif entry.label.startswith("Step 6 Code Review"):
            actions.append("Complete Step 6 (Code Review) and append its bullets")
        elif entry.label.startswith("Step 7 PR Review"):
            actions.append("Complete Step 7 (PR Review) and append its bullet")

    if actions:
        lines.append("\nRequired actions before /commit-story can proceed:")
        # Dedupe while preserving order.
        seen: set[str] = set()
        ordered = []
        for a in actions:
            if a not in seen:
                seen.add(a)
                ordered.append(a)
        for i, action in enumerate(ordered, start=1):
            lines.append(f"  {i}. {action}")
        lines.append(
            f"  {len(ordered) + 1}. Append the resulting bullet(s) to "
            "the story file's `## Protocol Audit Trail`"
        )
        lines.append(f"  {len(ordered) + 2}. Re-run /commit-story (gate re-runs first)")

    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check.py <story-file-path>", file=sys.stderr)
        return 2
    story_path = Path(sys.argv[1])
    result = check_compliance(story_path)
    if result.pass_:
        story_id = "?"
        m = re.search(r"(\d+\.\d+)", story_path.stem)
        if m:
            story_id = m.group(1)
        # Count matched entries for the success message.
        bullets = load_audit_trail(story_path) or []
        matched = sum(1 for e in MANIFEST if any(e.matches(b) for b in bullets))
        print(
            f"✅ Protocol Compliance — Story {story_id} — "
            f"{matched}/{len(MANIFEST)} expected entries present."
        )
        return 0
    print(render_fail_report(story_path, result), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
