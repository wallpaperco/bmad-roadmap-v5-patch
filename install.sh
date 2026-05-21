#!/bin/bash
# BMAD Roadmap v5 patch — installer
#
# Idempotent. Copies (or symlinks with --symlink) the v5 orchestrator skill +
# the 8 in-context review skills it depends on into the target project's
# .claude/skills/ directory.
#
# Modes:
#   (default)    Fresh install or update — overwrites managed files.
#   --symlink    Dev mode: symlink instead of copy (for iterating on the patch).
#   --uninstall  Remove all v5 skills from .claude/skills/.
#   --status     Show install state. Read-only.

set -e

PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(pwd)"
CLAUDE_SKILLS_DIR="$PROJECT_DIR/.claude/skills"

# Skills bundled with this patch. First entry is the orchestrator;
# the rest are in-context review skills invoked by the story protocol.
SKILLS=(
    bmad-roadmap-v5
    bmad-light-review-code-reuse
    bmad-light-review-code-quality
    bmad-review-adversarial-general
    bmad-review-edge-case-hunter
    bmad-light-review-acceptance
    bmad-light-review-silent-failure
    bmad-extract-deferrals
    bmad-protocol-compliance-check
    commit-story
    ship-epic
)

# Skills retired from this revision (will be removed on install if present):
#   bmad-light-review-pr-tests   — removed; was driving over-testing pressure.
#   bmad-light-review-efficiency — merged into bmad-light-review-code-quality
#                                  (2026-05). Efficiency was producing 0-3
#                                  findings/story while paying a full skill-
#                                  call cost; categories overlap heavily with
#                                  quality. Code-quality now covers 12 categories
#                                  with a cap of 12 findings.
RETIRED_SKILLS=(
    bmad-light-review-pr-tests
    bmad-light-review-efficiency
)

MODE="fresh"
for arg in "$@"; do
    case "$arg" in
        --symlink)   MODE="symlink" ;;
        --uninstall) MODE="uninstall" ;;
        --status)    MODE="status" ;;
    esac
done

cyan()   { printf "\033[36m%s\033[0m\n" "$1"; }
green()  { printf "\033[32m%s\033[0m\n" "$1"; }
yellow() { printf "\033[33m%s\033[0m\n" "$1"; }
red()    { printf "\033[31m%s\033[0m\n" "$1"; }

# ─── Validate project root ───────────────────────────────────────
if [ ! -d "$PROJECT_DIR/.claude" ] && [ "$MODE" != "status" ]; then
    yellow "No .claude/ directory found at $PROJECT_DIR"
    yellow "Creating .claude/skills/ now…"
fi

# ─── Status mode ─────────────────────────────────────────────────
if [ "$MODE" = "status" ]; then
    cyan "═══ bmad-roadmap-v5 install status ═══"
    echo "Project:       $PROJECT_DIR"
    echo "Patch source:  $PATCH_DIR"
    echo
    for skill in "${SKILLS[@]}"; do
        dst="$CLAUDE_SKILLS_DIR/$skill"
        if [ -L "$dst" ]; then
            green "✓ $skill (symlink → $(readlink "$dst"))"
        elif [ -d "$dst" ]; then
            if [ -f "$dst/.installed_at" ]; then
                green "✓ $skill (copy, installed $(cat "$dst/.installed_at"))"
            else
                green "✓ $skill (copy)"
            fi
        else
            yellow "✗ $skill (not installed)"
        fi
    done
    echo
    if git -C "$PATCH_DIR" rev-parse HEAD >/dev/null 2>&1; then
        echo "Patch commit:  $(git -C "$PATCH_DIR" rev-parse --short HEAD) — $(git -C "$PATCH_DIR" log -1 --format=%s)"
    fi
    exit 0
fi

# ─── Uninstall mode ──────────────────────────────────────────────
if [ "$MODE" = "uninstall" ]; then
    cyan "═══ Uninstalling bmad-roadmap-v5 (orchestrator + 8 review skills) ═══"
    removed=0
    for skill in "${SKILLS[@]}"; do
        dst="$CLAUDE_SKILLS_DIR/$skill"
        if [ -L "$dst" ] || [ -d "$dst" ]; then
            rm -rf "$dst"
            green "✓ Removed $skill"
            removed=$((removed + 1))
        fi
    done
    if [ "$removed" = "0" ]; then
        yellow "Nothing to uninstall — no v5 skills present at $CLAUDE_SKILLS_DIR"
    else
        echo
        green "Done. Removed $removed skill(s)."
    fi
    exit 0
fi

# ─── Fresh / symlink install ─────────────────────────────────────
mkdir -p "$CLAUDE_SKILLS_DIR"

cyan "═══ Installing bmad-roadmap-v5 patch (${#SKILLS[@]} skills, $MODE) ═══"
echo

# Remove any retired skills from a prior install
retired_removed=0
for skill in "${RETIRED_SKILLS[@]}"; do
    dst="$CLAUDE_SKILLS_DIR/$skill"
    if [ -L "$dst" ] || [ -d "$dst" ]; then
        rm -rf "$dst"
        yellow "✗ Removed retired skill: $skill"
        retired_removed=$((retired_removed + 1))
    fi
done
[ "$retired_removed" -gt 0 ] && echo

installed=0
for skill in "${SKILLS[@]}"; do
    src="$PATCH_DIR/skills/$skill"
    dst="$CLAUDE_SKILLS_DIR/$skill"

    if [ ! -d "$src" ]; then
        red "✗ Source skill not found at $src — skipping"
        continue
    fi

    # Clean previous install (per-skill, so partial state can't linger)
    if [ -L "$dst" ] || [ -d "$dst" ]; then
        rm -rf "$dst"
    fi

    if [ "$MODE" = "symlink" ]; then
        ln -s "$src" "$dst"
        green "✓ Symlinked $skill"
    else
        cp -R "$src" "$dst"
        date -u +%FT%TZ > "$dst/.installed_at"
        green "✓ Copied   $skill"
    fi
    installed=$((installed + 1))
done

echo
green "Done. Installed $installed skill(s)."
echo
green "To start: /bmad-roadmap-v5"
echo
yellow "Note: v5 expects the design system to be wired in code (tokens.css + fonts + Egyptian-Native wrappers)."
yellow "      If you don't have one yet, run v2 (Claude Design) first or set up the design system manually."
echo
yellow "Co-existence: if you also have bmad-figma-patch / bmad-roadmap-light-patch installed,"
yellow "      the review skills are SHARED — re-installing this patch overwrites them with v5's bundled copies."
yellow "      All variants are kept content-identical in source; re-install is safe."
