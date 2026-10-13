# Design and UI

Read this when a task builds or changes UI (project type A). Craft: `design-better` skill (`npx skills add BuildGreatProducts/builder-os`). Tokens: `design-system` skill.

## Tokens and components

**DES-1 to DES-4**, **DRY-1** and **DRY-2** live in `docs/domain-rules.md`. [check: context]

## Reading design mocks (the owner's drawing conventions)

- **A mock draws the thing that changed. Persistent chrome it doesn't redraw is still there.** Render a drill-in mock with a breadcrumb inside its parent. [check: process]
- **If you ever conclude a mock "needs redrawing" before you can build it, STOP and ask**. [check: process]
- **Illustrative numbers are illustrative.** Design tables for the real scale. [check: process]

## Interaction rulings (standing, from the Coast conformance round)

- **Cross-links never navigate away.** Open them in a modal or in place. [check: review]
- **Detail loads inside the area the user is already in**, unless the design shows a new screen. [check: review]
- **A dashboard is not a log.** Events go on their item. [check: review]
- **Contextual controls appear only where they apply.** [check: review]
- **Transitions are gradual and in place** where the design says zoom or expand. [check: review]

## Accessibility (floor, WCAG 2.2-sourced)

- Text contrast is at least 4.5:1 (large text 3:1).
- Targets are at least 44×44 pt (iOS), 48×48 dp (Android) or 24×24 px (web).
- Every control has a screen-reader label (web: semantic HTML or ARIA roles). Everything works by keyboard.
- Text follows system text size and 200% zoom without losing meaning.
- **Color is never the only signal**. Pair each status colour with a text badge and a glyph from a fixed set such as `■ ▲ ● ○`. Each colour means one thing: alarm colour for top severity only, demo states a colour of their own. [check: review]

## Copy on screens

Write what a support person would say aloud, in sentence case (labels follow deliberate case rules). No jokes in safety text, no "guarantee", no AI-isms, no instructional commentary. All copy lives in the string catalog.
[check: scan:retired-wording, review]

## Verification

Check the whole running product in live mode (not fixture data) against the design files. Never offer mocked UI in place of the build. [check: process]

## Destructive actions

- **A destructive confirm is click-only.** Never bind Return to a stop, abandon, delete or removal confirm, even if the mock makes it primary. Escape and Cancel keep their shortcut. [check: scan:destructive-default-key]

---

[← All rules](README.md) · [Documentation](../docs/README.md)
