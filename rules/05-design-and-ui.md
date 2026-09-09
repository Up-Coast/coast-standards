# Design and UI

> **Applies to:** project type A only — apps and frontends. Nothing here applies to a
> headless service or pipeline. See `PROJECT-TYPES.md`.

How agents consume the owner's designs and build UI. The craft layer (hierarchy, interaction,
motion, polish) is covered by the BuilderOS `design-better` skill (install it with
`npx skills add BuildGreatProducts/builder-os`); token generation
by `design-system`. These are the standing rules on top.

## Tokens and components

The checkable rules — **DES-1 to DES-4**, beside **DRY-1 and DRY-2** — live in every app
platform rules document (`rules/platform/domain-rules-<platform>.md`, a project's
`docs/domain-rules.md`), each with the check that holds it named: every visual value is the
design's exact token (DES-1), a brand swap is a one-file edit (DES-2), a new component is
justified in writing (DES-3), and every UI change is checked against the design-system spec
when there is one (DES-4). They live there, not here, so a project has exactly one rules
document and one counted number. [check: context]

## Reading design mocks (the owner's drawing conventions)

These are the defaults for reading a mock. The owner may override any of them for a
project; until then, read mocks this way.

- **A mock draws the thing that changed. Persistent chrome it doesn't redraw is still
  there.** There is no point in redrawing the same frame when it is obvious what feature
  the UI is part of. Absence of chrome in a mock is
  drawing economy, never a specification of absence. A drill-in mock showing a breadcrumb
  and no outer chrome is telling you where it lives in the IA — render it INSIDE that
  parent. [check: process]
- **If you ever conclude a mock "needs redrawing" before you can build it, STOP and ask** —
  that conclusion is far more likely a misreading than a real gap in the design.
  [check: process]
- **Illustrative numbers are illustrative.** Mock data volumes and dollar figures are
  placeholders; confirm the real scale and design tables to read well at it.
  [check: process]

## Interaction rulings (standing, from the Coast conformance round)

- **Cross-links never navigate away.** Docs/details surfaced from a screen open in a modal
  or in place — never navigate people away this way.
  [check: review]
- **Detail loads inside the area the user is already in**, not on a new screen, unless the
  design explicitly draws a new screen. [check: review]
- **A dashboard is not a log.** Event chatter belongs on the item it concerns, not the
  landing surface. [check: review]
- **Contextual controls appear only where they apply** — no global button rows stamped onto
  screens they don't belong to. [check: review]
- **Transitions are gradual and in place** where the design says zoom/expand — no jarring
  container swaps. [check: review]

## Accessibility (floor, WCAG 2.2-sourced)

- Text contrast ≥ 4.5:1 (3:1 large text).
- Touch/click targets ≥ 44×44 pt (iOS) / 48×48 dp (Android) / 24×24 px floor (web).
- Every interactive element has a screen-reader label saying what it does; web uses
  semantic HTML or correct ARIA roles; keyboard reachable and operable.
- Text respects system text-size / 200% zoom without truncating meaning.
- **Color is never the only signal** — pair color with text and, ideally, shape/glyph.
  Red/green confusion and amber/yellow adjacency are the standing examples.
  [check: review]

## Copy on screens

- Sentence a support person would say out loud; sentence case for body, deliberate case
  rules for labels; no jokes in safety copy; no "guarantee"; no AI-isms or filler; no
  instructions-to-the-user commentary baked into screens.
- All of it externalized per `04-localization.md`.
[check: scan:retired-wording, review]

## Verification

- Verify against the real, running product in live mode — a fixture screenshot proves
  nothing. Walk the WHOLE product against the design files, not just the screens you built.
- Real screenshots of finished work are wanted evidence; redrawn/mocked "explanatory" UI is
  never acceptable as a stand-in for the design or the build. [check: process]

## Destructive actions

- **A destructive confirm is click-only.** Never attach the default-action / Return key
  binding to stop, abandon, delete, or any removal-class confirm — even when the mock draws
  it as the visual primary. Platform guidance wins over the mock's visual weight here;
  Escape/cancel keeps its shortcut. Reviews treat a default-action binding on a destructive
  button as a defect. The user must click, not hit Return, for destructive actions.
  [check: scan:destructive-default-key]

## Status and colour, concretely

- Status is never colour alone: pair a **glyph and a text badge** with it (a fixed glyph set
  such as `■ ▲ ● ○` mapped to the status words), so meaning survives colour-blindness,
  greyscale printing, and small sizes.
- In a fixed status palette, **a colour means exactly one thing** — reserve the alarm colour
  for the top severity only, and give any demo/placeholder state its own colour used nowhere
  else. [check: review]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
