# Iteration Handoff Prompt — Template

Printed by the orchestrator at Story Protocol Step 4. The user copies it into a fresh chat to iterate visually via `/impeccable live` on the running dev server.

## Placeholders

| Placeholder | Resolved from | Example |
|---|---|---|
| `{project-root}` | working directory | `/Users/abozaid/Desktop/workspace/abozaid/baseir` |
| `{X.Y}` | story ID | `2.7` |
| `{story-title}` | story file frontmatter `title:` | `Mobile + WhatsApp OTP Registration` |
| `{story-file-path}` | absolute path to story md | `_bmad-output/implementation-artifacts/stories/2.7-mobile-otp-registration.md` |
| `{ux-spec-section}` | journey section in UX spec | `§13.2 Journey 1: Authentication & Onboarding` |
| `{port}` | dev server port (from CLAUDE.md port table) | `3015` |
| `{routes}` | list extracted from Saneh's Return block | `/auth/sign-up`, `/auth/otp` |
| `{stack-summary}` | one-line stack description | `NestJS API + Next.js 16 + Tailwind v4 + shadcn/ui` |
| `{design-system-pointer}` | one-line pointer to where tokens live | `src/styles/tokens.css + src/lib/egyptian-native/` |

## Template

```
# /impeccable live — Story {X.Y}: {story-title}

I want to iterate on the screens for this story using /impeccable live on the already-running dev server.

## Project
{project-root}

## What's been built (Saneh just finished)
Story: {X.Y} — {story-title}
Story file: {story-file-path}
UX spec: _bmad-output/planning-artifacts/ux-design-specification.md {ux-spec-section}

Dev server: http://localhost:{port}  (already up — no need to start anything)

Routes built in this story:
{routes — one per line, with one-line purpose each}

## Stack
{stack-summary}
Design system: {design-system-pointer}

## What I want you to do
1. Read the story file (especially the ACs and Edge Cases sections — they define behavior).
2. Read the relevant UX spec journey to understand the broader flow.
3. Open the dev server URL and walk through every route built.
4. Use /impeccable live to iterate on the visuals. Focus on:
   - Visual hierarchy + spacing
   - Component state coverage (default / hover / focus / loading / empty / error / disabled)
   - RTL rendering (Arabic) for every screen with Arabic content
   - Responsive at 375 / 768 / 1440 (mobile / tablet / desktop)
   - Edge cases visible in the UI (e.g. invalid phone, OTP expired, etc.)

## Boundaries — what's a /impeccable change vs. a business change
- ✅ Visual / interaction polish, copy tweaks, accessibility fixes → keep using /impeccable
- 🛑 If you find a missing feature, a logic gap, or a spec change is needed → STOP and tell the user to run /bmad-business-change instead. /impeccable should not change product semantics.

## When you're done
Save changes (the dev server has HMR — they're live). Then go back to the main chat (where Saneh was) and reply with one of:
- `approved` — protocol moves to Simplify → Code Review → PR Review → Verify → Ship (Steps 5–9, fully autonomous)
- `rebuild: <one-line reason>` — Saneh re-runs the build with your note appended
```

## Notes

- The template ends with the user's options for the main chat — `approved`, `rebuild:`, or `/bmad-business-change`. Those signals drive Story Protocol Step 4.
- The orchestrator MUST save a resolved copy of the prompt to `_bmad-output/implementation-artifacts/iteration-prompts/{X.Y}.md` so that if the user opens a different chat and runs `/bmad-roadmap-v5 --resume-story={X.Y}`, the prompt can be re-displayed verbatim.
