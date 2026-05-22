#!/usr/bin/env bash
# Detect routes/pages/components added between two refs.
#
# Usage:
#   detect-routes.sh <base-ref> <head-ref>
#
# Examples:
#   detect-routes.sh main~12 main      # last N commits on main (after a squash)
#   detect-routes.sh epic-1-base main  # everything since the epic branched
#
# Output: tab-separated lines, one per detected surface:
#   route  <url-path>           <story-id-from-filename-or-?>
#   api    <method>:<endpoint>  <controller-file>
#   comp   <component-name>     <component-file>
#
# Exits 0 even when nothing is detected — the caller decides what to do
# with an empty result.
set -euo pipefail

BASE_REF="${1:?usage: detect-routes.sh <base-ref> <head-ref>}"
HEAD_REF="${2:?usage: detect-routes.sh <base-ref> <head-ref>}"

# All files added between the two refs (status A = added).
added_files=$(git diff --name-only --diff-filter=A "$BASE_REF".."$HEAD_REF" 2>/dev/null || true)

if [[ -z "$added_files" ]]; then
    exit 0
fi

# --- Next.js app-router pages (apps/web/src/app/**/page.tsx) ----------------
# Map file path → URL route. Drop `apps/web/src/app`, drop `/page.tsx`,
# strip route groups `(...)`, replace `[param]` with `:param` for human-readable
# display (the framework still resolves via the bracketed form).
while IFS= read -r f; do
    [[ "$f" == apps/web/src/app/*/page.tsx ]] || [[ "$f" == apps/web/src/app/page.tsx ]] || continue
    # Path relative to the app root, without the trailing page filename.
    route=${f#apps/web/src/app}
    route=${route%/page.tsx}
    # Strip route-group segments like `(marketing)/foo` → `/foo`.
    route=$(echo "$route" | sed -E 's#/\([^/]+\)##g')
    # Display dynamic segments as :param instead of [param].
    route=$(echo "$route" | sed -E 's#\[([^/]+)\]#:\1#g')
    [[ -z "$route" ]] && route="/"
    printf 'route\t%s\t%s\n' "$route" "$f"
done <<< "$added_files"

# --- Legacy Next.js pages-router (apps/web/src/pages/**/*.tsx) ---------------
while IFS= read -r f; do
    [[ "$f" == apps/web/src/pages/*.tsx ]] || [[ "$f" == apps/web/src/pages/*/*.tsx ]] || continue
    [[ "$f" == */api/* ]] && continue  # those are API routes, handled below
    route=${f#apps/web/src/pages}
    route=${route%.tsx}
    route=${route%/index}
    route=$(echo "$route" | sed -E 's#\[([^/]+)\]#:\1#g')
    [[ -z "$route" ]] && route="/"
    printf 'route\t%s\t%s\n' "$route" "$f"
done <<< "$added_files"

# --- NestJS controllers (apps/api/src/**/*.controller.ts) --------------------
# We don't parse the @Controller / @Get decorators; just surface the file so
# the caller can list "API endpoints added" without false precision.
while IFS= read -r f; do
    [[ "$f" == apps/api/src/*.controller.ts ]] || [[ "$f" == apps/api/src/**/*.controller.ts ]] || continue
    # Approximate the controller's mount point from the filename:
    # apps/api/src/health/health.controller.ts → /health
    name=$(basename "$f" .controller.ts)
    printf 'api\t/%s\t%s\n' "$name" "$f"
done <<< "$added_files"

# --- Shared components added to apps/web/src/components/ ---------------------
# Skip __tests__/ files. Skip wrapper subdirs we don't treat as surfaces.
while IFS= read -r f; do
    [[ "$f" == apps/web/src/components/*.tsx ]] || [[ "$f" == apps/web/src/components/*/*.tsx ]] || continue
    [[ "$f" == */__tests__/* ]] && continue
    name=$(basename "$f" .tsx)
    printf 'comp\t%s\t%s\n' "$name" "$f"
done <<< "$added_files"
