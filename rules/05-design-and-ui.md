# Design and UI

> **Applies to:** project type A only, apps and frontends. None of this applies to a headless service or pipeline. See `PROJECT-TYPES.md`.

How agents use the owner's designs and build UI. These are the standing rules. Two skills cover the rest:

- Craft (hierarchy, interaction, motion, polish): the BuilderOS `design-better` skill. Install it with `npx skills add BuildGreatProducts/builder-os`.
- Design tokens: the `design-system` skill.

## Tokens and components

The checkable rules, **DES-1 to DES-4** together with **DRY-1 and DRY-2**, are in every app platform rules document (`rules/platform/domain-rules-<platform>.md`, which becomes a project's `docs/domain-rules.md`). Each names the check that enforces it. In short: every visual value is the design's exact token (DES-1); changing the brand means editing one file (DES-2); a new component is justified in writing (DES-3); and when there is a design-system spec, every UI change is checked against it (DES-4). They live there, not here, so a project has one rules document and one count of rules. [check: context]

## Reading design mocks (the owner's drawing conventions)

Read mocks this way by default. The owner can change any of these for a project.

- **A mock draws the thing that changed. Persistent chrome it doesn't redraw is still there.** Designers don't redraw the same frame when it is obvious which feature the UI belongs to. Missing chrome in a mock saves drawing effort; it never means the chrome should be absent. A drill-in mock with a breadcrumb and no outer chrome shows where the screen sits in the navigation. Render it INSIDE that parent. [check: process]
- **If you ever conclude a mock "needs redrawing" before you can build it, STOP and ask**, because that conclusion is much more likely a misreading than a real gap in the design. [check: process]
- **Illustrative numbers are illustrative.** Data volumes and dollar amounts in a mock are placeholders. Confirm the real scale, and design tables that read well at that scale. [check: process]

## Interaction rulings (standing, from the Coast conformance round)

- **Cross-links never navigate away.** When a screen links to docs or details, open them in a modal or in place. Never move the person to another screen this way. [check: review]
- **Detail loads inside the area the user is already in**, not on a new screen, unless the design explicitly shows a new screen. [check: review]
- **A dashboard is not a log.** Event messages belong on the item they are about, not on the landing screen. [check: review]
- **Contextual controls appear only where they apply.** Don't add global rows of buttons to screens they don't belong on. [check: review]
- **Transitions are gradual and in place** where the design says zoom or expand. No abrupt swaps of the whole container. [check: review]

## Accessibility (floor, WCAG 2.2-sourced)

- Text contrast is at least 4.5:1 (3:1 for large text).
- Touch and click targets are at least 44×44 pt (iOS), 48×48 dp (Android), or 24×24 px (web minimum).
- Every interactive element has a screen-reader label that says what it does. On the web, use semantic HTML or correct ARIA roles. Everything can be reached and used with a keyboard.
- Text follows the system text size and 200% zoom without being cut off in a way that loses meaning.
- **Color is never the only signal**. Pair color with text and, ideally, a shape or glyph. Typical problems are red/green confusion and amber next to yellow. [check: review]

## Copy on screens

- Write sentences a support person would say out loud. Use sentence case for body text and deliberate case rules for labels. No jokes in safety text. Never "guarantee". No AI-isms or filler. Don't put commentary that instructs the user into the screens.
- Put all of it in the string catalog, as described in `04-localization.md`.
[check: scan:retired-wording, review]

## Verification

- Verify against the real, running product in live mode. A screenshot of fixture data proves nothing. Check the WHOLE product against the design files, not just the screens you built.
- Real screenshots of finished work are good evidence. Redrawn or mocked "explanatory" UI is never acceptable in place of the design or the build. [check: process]

## Destructive actions

- **A destructive confirm is click-only.** Never bind the default action (the Return key) to a stop, abandon, delete or any other removal confirmation, even when the mock draws it as the primary button. Here, platform guidance wins over the mock's visual emphasis. Escape and Cancel keep their shortcut. Reviews treat a default-action binding on a destructive button as a defect. The user must click, not press Return, to confirm a destructive action. [check: scan:destructive-default-key]

## Status and colour, concretely

- Never show status by colour alone. Pair each colour with a **glyph and a text badge**, using a fixed glyph set such as `■ ▲ ● ○` mapped to the status words. This keeps the meaning readable for colour-blind users, in greyscale print, and at small sizes.
- In a fixed status palette, **a colour means exactly one thing**. Reserve the alarm colour for the highest severity only. Give any demo or placeholder state its own colour that is used nowhere else. [check: review]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
