#!/bin/bash
# BMAD Roadmap v5 patch — installer
#
# Idempotent. Copies (or symlinks with --symlink) the bmad-roadmap-v5 skill
# into the target project's .claude/skills/ directory.
#
# Modes:
#   (default)    Fresh install or update — overwrites managed files.
#   --symlink    Dev mode: symlink instead of copy (for iterating on the patch).
#   --uninstall  Remove the skill from .claude/skills/.
#   --status     Show install state. Read-only.

set -e

PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(pwd)"
CLAUDE_SKILLS_DIR="$PROJECT_DIR/.claude/skills"
SKILL_NAME="bmad-roadmap-v5"
SKILL_SRC="$PATCH_DIR/skills/$SKILL_NAME"
SKILL_DST="$CLAUDE_SKILLS_DIR/$SKILL_NAME"

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
    echo "Skill target:  $SKILL_DST"
    echo
    if [ -L "$SKILL_DST" ]; then
        green "✓ Installed as symlink → $(readlink "$SKILL_DST")"
    elif [ -d "$SKILL_DST" ]; then
        green "✓ Installed as copy"
        if [ -f "$SKILL_DST/.installed_at" ]; then
            echo "  Installed at: $(cat "$SKILL_DST/.installed_at")"
        fi
    else
        yellow "✗ Not installed in this project"
    fi
    echo
    if git -C "$PATCH_DIR" rev-parse HEAD >/dev/null 2>&1; then
        echo "Patch commit:  $(git -C "$PATCH_DIR" rev-parse --short HEAD) — $(git -C "$PATCH_DIR" log -1 --format=%s)"
    fi
    exit 0
fi

# ─── Uninstall mode ──────────────────────────────────────────────
if [ "$MODE" = "uninstall" ]; then
    cyan "═══ Uninstalling bmad-roadmap-v5 ═══"
    if [ -L "$SKILL_DST" ] || [ -d "$SKILL_DST" ]; then
        rm -rf "$SKILL_DST"
        green "✓ Removed $SKILL_DST"
    else
        yellow "Nothing to uninstall — skill not present at $SKILL_DST"
    fi
    exit 0
fi

# ─── Fresh / symlink install ─────────────────────────────────────
mkdir -p "$CLAUDE_SKILLS_DIR"

if [ ! -d "$SKILL_SRC" ]; then
    red "✗ Source skill not found at $SKILL_SRC"
    red "  Make sure you're running this from a clean clone of the patch repo."
    exit 1
fi

# Clean previous install
if [ -L "$SKILL_DST" ] || [ -d "$SKILL_DST" ]; then
    rm -rf "$SKILL_DST"
fi

cyan "═══ Installing bmad-roadmap-v5 ($MODE) ═══"

if [ "$MODE" = "symlink" ]; then
    ln -s "$SKILL_SRC" "$SKILL_DST"
    green "✓ Symlinked $SKILL_DST → $SKILL_SRC"
else
    cp -R "$SKILL_SRC" "$SKILL_DST"
    date -u +%FT%TZ > "$SKILL_DST/.installed_at"
    green "✓ Copied skill into $SKILL_DST"
fi

echo
green "Done. To start: /bmad-roadmap-v5"
echo
yellow "Note: v5 expects the design system to be wired in code (tokens.css + fonts + Egyptian-Native wrappers)."
yellow "      If you don't have one yet, run v2 (Claude Design) first or set up the design system manually."
