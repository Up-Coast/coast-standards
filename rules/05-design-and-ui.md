# Design and UI

How agents consume Abbey's designs and build UI. The craft layer (hierarchy, interaction,
motion, polish) is covered by the vendored BuilderOS `design-better` skill; token generation
by `design-system`. These are the standing rules on top.

## Tokens and components

- **All visual values come from the design's tokens.** Never invent colors, type sizes, or
  spacing; never inline a near-match — use the exact token value and keep the design's token
  name. When a needed value has no token, request/add the token; never inline a literal.
- **One theme file**, created at project start; a second can never be created. A brand-color
  swap must be a one-file edit.
- **Components are created once and reused.** Check for an existing component (or a
  composition) before creating one; justify any new component by saying why nothing existing
  fit. Builder and approver of a component are different reviews.
- **If the project has a design system spec, every UI change is checked against it** — no
  hardcoded values that bypass tokens. When a needed pattern implies a token the system
  doesn't have, flag it as a new pattern to add — never invent a value inline. [BuilderOS]

## Reading design mocks (Abbey's drawing conventions)

- **A mock draws the thing that changed. Persistent chrome it doesn't redraw is still
  there.** "there is no point in continually drawing the same frame over and over and over
  again when it is OBVIOUS what feature the UI is part of." Absence of chrome in a mock is
  drawing economy, never a specification of absence. A drill-in mock showing a breadcrumb
  and no outer chrome is telling you where it lives in the IA — render it INSIDE that
  parent.
- **If you ever conclude a mock "needs redrawing" before you can build it, STOP and ask** —
  that conclusion is far more likely a misreading than a real gap in the design.
- **Illustrative numbers are illustrative.** Mock data volumes and dollar figures are
  placeholders; confirm the real scale and design tables to read well at it.

## Interaction rulings (standing, from the Coast conformance round)

- **Cross-links never navigate away.** Docs/details surfaced from a screen open in a modal
  or in place — "You should NEVER EVER navigate people this way."
- **Detail loads inside the area the user is already in**, not on a new screen, unless the
  design explicitly draws a new screen.
- **A dashboard is not a log.** Event chatter belongs on the item it concerns, not the
  landing surface.
- **Contextual controls appear only where they apply** — no global button rows stamped onto
  screens they don't belong to.
- **Transitions are gradual and in place** where the design says zoom/expand — no jarring
  container swaps.

## Accessibility (floor, WCAG 2.2-sourced)

- Text contrast ≥ 4.5:1 (3:1 large text).
- Touch/click targets ≥ 44×44 pt (iOS) / 48×48 dp (Android) / 24×24 px floor (web).
- Every interactive element has a screen-reader label saying what it does; web uses
  semantic HTML or correct ARIA roles; keyboard reachable and operable.
- Text respects system text-size / 200% zoom without truncating meaning.
- **Color is never the only signal** — pair color with text and, ideally, shape/glyph.
  Red/green confusion and amber/yellow adjacency are the standing examples.

## Copy on screens

- Sentence a support person would say out loud; sentence case for body, deliberate case
  rules for labels; no jokes in safety copy; no "guarantee"; no AI-isms or filler; no
  instructions-to-the-user commentary baked into screens.
- All of it externalized per `04-localization.md`.

## Verification

- Verify against the real, running product in live mode — a fixture screenshot proves
  nothing. Walk the WHOLE product against the design files, not just the screens you built.
- Real screenshots of finished work are wanted evidence; redrawn/mocked "explanatory" UI is
  never acceptable as a stand-in for the design or the build.
