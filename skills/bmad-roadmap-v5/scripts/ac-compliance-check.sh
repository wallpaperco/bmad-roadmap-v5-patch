#!/bin/bash
# AC-Compliance Check
# Verifies every AC declared in a story file has an entry in Saneh's AC Implementation Map.
#
# Story ACs are detected via the pattern:  **AC-N: <title>**  (markdown bold)
# Map entries are detected via the pattern:  AC-N (<title>):  in Saneh's Return block
#
# Bonus: cited file paths are verified to exist in the repo (catches hallucinations).
#
# Usage:
#   ac-compliance-check.sh --story <story-file> --map-output <map-file> [--repo-root <path>]
#
# Exit codes:
#   0   PASS — all ACs covered, all cited paths exist
#   1   MISSING-AC — at least one story AC has no map entry
#   2   HALLUCINATED-PATH — at least one cited file path doesn't exist
#   3   USAGE / IO error

set -euo pipefail

STORY_FILE=""
MAP_FILE=""
REPO_ROOT="$(pwd)"

while [ $# -gt 0 ]; do
    case "$1" in
        --story)      STORY_FILE="$2"; shift 2 ;;
        --map-output) MAP_FILE="$2"; shift 2 ;;
        --repo-root)  REPO_ROOT="$2"; shift 2 ;;
        *)            echo "Unknown arg: $1" >&2; exit 3 ;;
    esac
done

if [ -z "$STORY_FILE" ] || [ -z "$MAP_FILE" ]; then
    echo "Usage: $0 --story <story-file> --map-output <map-file> [--repo-root <path>]" >&2
    exit 3
fi
[ -f "$STORY_FILE" ] || { echo "Story file not found: $STORY_FILE" >&2; exit 3; }
[ -f "$MAP_FILE" ]   || { echo "Map file not found: $MAP_FILE" >&2; exit 3; }

# ─── Extract story AC IDs ────────────────────────────────────────
# Match: **AC-1: ...** or **AC-1 ...** (case-insensitive)
story_acs=$(grep -oE '\*\*AC-[0-9]+[a-zA-Z]?' "$STORY_FILE" | sed 's/\*\*//g' | sort -u || true)

if [ -z "$story_acs" ]; then
    echo "⚠️  No ACs detected in $STORY_FILE — is this a research story? Skipping."
    exit 0
fi

# ─── Extract map AC IDs ──────────────────────────────────────────
# Match: AC-1 (...) or AC-1: at line start
map_acs=$(grep -oE '^[[:space:]]*AC-[0-9]+[a-zA-Z]?' "$MAP_FILE" | tr -d ' ' | sort -u || true)

# ─── Compare ─────────────────────────────────────────────────────
missing=""
for ac in $story_acs; do
    if ! echo "$map_acs" | grep -qFx "$ac"; then
        missing="$missing $ac"
    fi
done

if [ -n "$missing" ]; then
    echo "❌ MISSING-AC: the following ACs are in the story but absent from Saneh's map:"
    for ac in $missing; do
        echo "   - $ac"
    done
    echo
    echo "Fix:"
    echo "  1. Re-run Saneh with explicit instruction to implement these ACs, OR"
    echo "  2. Amend the story to defer them (with reason in the AC body)"
    exit 1
fi

# ─── Verify cited file paths exist ───────────────────────────────
# Pull anything that looks like a relative path from the map.
# Heuristic: lines starting with " - " followed by a path-ish token before " ("
cited_paths=$(grep -oE '^[[:space:]]+-[[:space:]][^[:space:]]+\.[a-zA-Z]+' "$MAP_FILE" \
              | sed 's/^[[:space:]]*-[[:space:]]*//' || true)

hallucinated=""
for path in $cited_paths; do
    # Strip trailing punctuation
    clean=$(echo "$path" | sed 's/[,.;:]$//')
    if [ ! -e "$REPO_ROOT/$clean" ]; then
        hallucinated="$hallucinated $clean"
    fi
done

if [ -n "$hallucinated" ]; then
    echo "❌ HALLUCINATED-PATH: the following paths are cited in Saneh's map but don't exist:"
    for p in $hallucinated; do
        echo "   - $p"
    done
    echo
    echo "Fix: have Saneh re-check the actual file layout, OR document why the path is forward-looking."
    exit 2
fi

# ─── PASS ────────────────────────────────────────────────────────
ac_count=$(echo "$story_acs" | wc -l | tr -d ' ')
echo "✅ AC-Compliance PASS — all $ac_count ACs addressed in Saneh's map."
exit 0
