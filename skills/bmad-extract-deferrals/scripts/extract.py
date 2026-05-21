#!/usr/bin/env python3
"""
Extract deferred-work entries from git commit messages.

Usage:
    extract.py [<commit-range>]

Default range: origin/main..HEAD.

Reads each commit's body, finds deferral patterns (severity-prefixed bullets,
"Deferred:" sections, inline "Defer to" mentions), dedupes against the existing
_bmad-output/implementation-artifacts/deferred-work.md (fuzzy match by finding
text), and appends new entries.

Outputs a one-line summary to stdout.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFERRED_FILE = REPO_ROOT / "_bmad-output" / "implementation-artifacts" / "deferred-work.md"

# How similar two finding titles must be (0..1) to count as the same deferral.
# 0.85 catches "the same finding worded slightly differently" without
# collapsing genuinely different findings that share keywords.
DEDUP_SIMILARITY_THRESHOLD = 0.85

# Severity keywords (in priority order) — first match wins.
SEVERITY_KEYWORDS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

# Reviewer names we recognise from the v5 protocol.
KNOWN_REVIEWERS = {
    "code-reuse": "code-reuse-review",
    "code-quality": "code-quality-review",
    "efficiency": "efficiency-review",
    "adversarial": "adversarial-review",
    "edge-case": "edge-case-hunter",
    "edge case": "edge-case-hunter",
    "acceptance": "acceptance-audit",
    "silent-failure": "silent-failure-hunter",
    "silent failure": "silent-failure-hunter",
    "simplify": "simplify-v5",
    "code review": "code-review-v5",
    "retroactive": "retroactive-protocol",
}


@dataclass
class Deferral:
    """One extracted deferral entry. Many fields are optional — we surface
    whatever the commit message gave us and leave gaps for human review."""

    severity: str  # CRITICAL | HIGH | MEDIUM | LOW (uppercased)
    finding: str  # one-line description
    rationale: str = ""  # "why we deferred" — may be empty
    source: str = "unknown"  # reviewer name
    story: str = ""  # X.Y
    commit_sha: str = ""  # short
    commit_date: str = ""  # YYYY-MM-DD
    owning_future_story: str = ""  # parsed from "Defer to Story X.Y" / "Phase 7"
    raw_excerpt: str = ""  # short verbatim chunk for traceability

    def section_header(self) -> str:
        """The `## simplify-v5 (Story 1.4)` style header for grouping."""
        return f"## {self.source} (Story {self.story})" if self.story else f"## {self.source}"

    def to_markdown(self) -> str:
        """Render in the existing deferred-work.md H3-per-finding shape."""
        reversibility = self._infer_reversibility()
        action = self._infer_action()
        lines = [
            f"### {self.commit_date} — {self._title()} ({self.severity})",
            "",
            f"**Source:** {self.source}",
            f"**Finding:** {self.finding}",
        ]
        if self.rationale:
            lines.append(f"**Decision rationale:** {self.rationale}")
        lines.append(f"**Reversibility:** {reversibility}")
        if self.owning_future_story:
            lines.append(f"**Owning future story:** {self.owning_future_story}")
        else:
            lines.append("**Owning future story:** no owner — review")
        if self.commit_sha:
            lines.append(f"**Commit:** {self.commit_sha}")
        lines.append(f"**Action:** {action}")
        lines.append("")
        return "\n".join(lines)

    def _title(self) -> str:
        # First clause of the finding, capped at 80 chars for the header.
        t = self.finding.split(" — ")[0]
        t = t.split(": ")[-1] if ": " in t else t
        return t[:80].rstrip()

    def _infer_reversibility(self) -> str:
        text = (self.finding + " " + self.rationale).lower()
        if any(kw in text for kw in ["contract", "schema", "migration", "api shape"]):
            return "Low"
        if any(kw in text for kw in ["cosmetic", "refactor", "rename", "comment"]):
            return "High"
        return "Medium"

    def _infer_action(self) -> str:
        if self.owning_future_story:
            return f"Fix in {self.owning_future_story}"
        if self.severity in {"CRITICAL", "HIGH"}:
            return "Track — no owner"
        return "None"


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git"] + args, capture_output=True, text=True, cwd=REPO_ROOT, check=False
    )
    if result.returncode != 0:
        print(f"git {' '.join(args)} failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(2)
    return result.stdout


def list_commits(rev_range: str) -> list[tuple[str, str, str]]:
    """Return (sha, short_sha, date) tuples for commits in the range, oldest-first."""
    out = run_git(["log", "--reverse", rev_range, "--format=%H%x09%h%x09%cs"])
    commits = []
    for line in out.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            commits.append((parts[0], parts[1], parts[2]))
    return commits


def commit_body(sha: str) -> str:
    return run_git(["log", "-1", sha, "--format=%B"])


def normalise_reviewer(s: str) -> str:
    s = s.lower()
    for key, name in KNOWN_REVIEWERS.items():
        if key in s:
            return name
    return "unknown"


_STORY_RE = re.compile(r"Story\s+(\d+\.\d+)", re.IGNORECASE)
_OWNER_RE = re.compile(
    r"(?:Defer(?:red)?\s+to|own[s]?\s+by|owned\s+by)\s+(Story\s+\d+\.\d+|Phase\s+\d+(?:\s+\w+)?|Epic\s+\d+)",
    re.IGNORECASE,
)
_FENCE_RE = re.compile(r"^```", re.MULTILINE)


def extract_from_commit(
    sha: str, short: str, commit_date: str, body: str
) -> list[Deferral]:
    """Parse a commit message body and emit Deferral entries."""
    # Drop fenced code blocks — we don't want to mistake code for prose.
    body_stripped = _FENCE_RE.sub("", body)

    # The story-protocol convention is: title contains "Story X.Y" or
    # the body starts with "Story X.Y:".
    story_match = _STORY_RE.search(body[:200])
    story = story_match.group(1) if story_match else ""

    deferrals: list[Deferral] = []
    seen_in_this_commit: set[str] = set()

    # Pattern 1: severity-prefixed bullets/sections.
    # Examples:
    #   - **HIGH (silent-failure):** flush() requeue without retry-count...
    #   - **MEDIUM:** Some finding text — Defer to Story 4.x.
    severity_pattern = re.compile(
        r"\*\*(CRITICAL|HIGH|MEDIUM|LOW)(?:\s*\(([^)]+)\))?[:\*]?\s*\*?\*?\s*(.+?)(?=\n\s*(?:-\s+\*\*|\Z|\n\n))",
        re.DOTALL | re.IGNORECASE,
    )
    for m in severity_pattern.finditer(body_stripped):
        severity = m.group(1).upper()
        category = (m.group(2) or "").strip()
        text = m.group(3).strip()
        # Take up to first blank line / next bullet as the finding body.
        finding_body = re.split(r"\n\s*-\s+\*\*|\n\s*\n", text, maxsplit=1)[0].strip()
        if len(finding_body) < 10 or len(finding_body) > 2000:
            continue
        finding, rationale = _split_finding(finding_body)
        owner = _extract_owner(finding_body)
        key = _dedup_key(finding)
        if key in seen_in_this_commit:
            continue
        seen_in_this_commit.add(key)
        deferrals.append(
            Deferral(
                severity=severity,
                finding=finding,
                rationale=rationale,
                source=normalise_reviewer(category) if category else "review-fix",
                story=story,
                commit_sha=short,
                commit_date=commit_date,
                owning_future_story=owner,
                raw_excerpt=finding_body[:300],
            )
        )

    # Pattern 2: "Deferred:" section followed by a bullet list. The bullets
    # typically read "- AC-X some finding — Story Y.Z." or "- description (Phase 7)."
    deferred_section = re.search(
        r"(?:^|\n)Deferred(?:\s+\([^)]*\))?:\s*\n((?:\s*-\s+.+\n?)+)",
        body_stripped,
        re.MULTILINE,
    )
    if deferred_section:
        for bullet in re.findall(r"-\s+(.+)", deferred_section.group(1)):
            bullet = bullet.strip()
            if len(bullet) < 10:
                continue
            finding, rationale = _split_finding(bullet)
            owner = _extract_owner(bullet)
            key = _dedup_key(finding)
            if key in seen_in_this_commit:
                continue
            seen_in_this_commit.add(key)
            # Severity isn't always tagged in the bullet — default LOW since
            # the "Deferred:" section is for "acknowledged scope-outs" which
            # are usually low-impact by definition.
            inferred_sev = _infer_severity(bullet)
            deferrals.append(
                Deferral(
                    severity=inferred_sev,
                    finding=finding,
                    rationale=rationale,
                    source="story-protocol",
                    story=story,
                    commit_sha=short,
                    commit_date=commit_date,
                    owning_future_story=owner,
                    raw_excerpt=bullet[:300],
                )
            )

    return deferrals


def _split_finding(text: str) -> tuple[str, str]:
    """Split `<finding> — <rationale>` if an em-dash separates them.
    Otherwise the whole thing is the finding, rationale empty."""
    # Em-dash split (the convention used by the v5 reviewers).
    if " — " in text:
        finding, _, rationale = text.partition(" — ")
        return finding.strip(), rationale.strip()
    return text.strip(), ""


def _extract_owner(text: str) -> str:
    m = _OWNER_RE.search(text)
    if m:
        return m.group(1)
    # Fallback patterns the reviewers use:
    if re.search(r"Phase 7", text, re.IGNORECASE):
        return "Phase 7 Harden"
    if re.search(r"\(Story 4\.x\)", text, re.IGNORECASE):
        return "Story 4.x"
    return ""


def _infer_severity(text: str) -> str:
    """If a deferral bullet doesn't carry an explicit severity, pick the
    most pessimistic plausible severity based on keywords."""
    t = text.lower()
    if any(kw in t for kw in ["security", "leak", "forge", "credential"]):
        return "HIGH"
    if any(kw in t for kw in ["test", "ci ", "lighthouse", "e2e"]):
        return "MEDIUM"
    return "LOW"


def _dedup_key(finding: str) -> str:
    """Normalise a finding string for hashing. Lowercased, whitespace
    collapsed, non-alphanumeric stripped."""
    return re.sub(r"[^a-z0-9]+", " ", finding.lower()).strip()


def load_existing_findings(path: Path) -> list[str]:
    """Extract the normalised finding text from existing deferred-work.md so
    we can dedup. Looks for `**Finding:**` lines."""
    if not path.exists():
        return []
    findings = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\*\*Finding:\*\*\s*(.+)", line)
        if m:
            findings.append(_dedup_key(m.group(1)))
    return findings


def is_duplicate(new_key: str, existing_keys: list[str]) -> bool:
    if new_key in existing_keys:
        return True
    # Fuzzy match — same finding worded slightly differently.
    for existing in existing_keys:
        if SequenceMatcher(None, new_key, existing).ratio() >= DEDUP_SIMILARITY_THRESHOLD:
            return True
    return False


def append_entries(path: Path, deferrals: list[Deferral]) -> None:
    """Append new deferrals, grouped by section header. If the same section
    header already exists in the file, append entries under it; otherwise
    create the section."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# Deferred Work — Baseir MVP-1\n\n"
            "Findings deferred during story protocol execution. Each entry "
            "includes source, severity, story, and decision rationale.\n\n---\n\n",
            encoding="utf-8",
        )
    current = path.read_text(encoding="utf-8")

    # Group new deferrals by section header.
    by_section: dict[str, list[Deferral]] = {}
    for d in deferrals:
        by_section.setdefault(d.section_header(), []).append(d)

    to_append: list[str] = []
    for section, entries in by_section.items():
        if section in current:
            # Section already exists — find it and append entries just below
            # the header. To keep this script idempotent + simple, we just
            # append the new entries at the END of the file under a fresh
            # subsection header so we never rewrite existing content.
            to_append.append(f"\n{section} — appended {date.today().isoformat()}\n")
        else:
            to_append.append(f"\n{section}\n")
        for entry in entries:
            to_append.append("\n" + entry.to_markdown())

    path.write_text(current + "".join(to_append), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("range", nargs="?", default="origin/main..HEAD")
    args = parser.parse_args()

    commits = list_commits(args.range)
    if not commits:
        print(
            f"No commits in range {args.range}. Pass an explicit range like "
            "682931a..HEAD if running mid-flight."
        )
        return 1

    existing_keys = load_existing_findings(DEFERRED_FILE)

    all_deferrals: list[Deferral] = []
    for sha, short, dt in commits:
        body = commit_body(sha)
        all_deferrals.extend(extract_from_commit(sha, short, dt, body))

    new_deferrals: list[Deferral] = []
    dup_count = 0
    seen_in_batch: set[str] = set()
    for d in all_deferrals:
        key = _dedup_key(d.finding)
        if is_duplicate(key, existing_keys) or key in seen_in_batch:
            dup_count += 1
            continue
        seen_in_batch.add(key)
        new_deferrals.append(d)

    if new_deferrals:
        append_entries(DEFERRED_FILE, new_deferrals)

    no_owner = [d for d in new_deferrals if not d.owning_future_story]

    print(
        f"Extracted {len(all_deferrals)} deferrals from {len(commits)} commit(s) — "
        f"{len(new_deferrals)} new, {dup_count} duplicates skipped, "
        f"{len(no_owner)} with no owning future story."
    )
    if no_owner:
        print("\nNo-owner deferrals (highest review priority):")
        for d in no_owner[:10]:
            print(f"  [{d.severity}] {d._title()[:90]}  (Story {d.story}, {d.commit_sha})")
        if len(no_owner) > 10:
            print(f"  ... and {len(no_owner) - 10} more in {DEFERRED_FILE.name}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
