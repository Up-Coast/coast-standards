## Keep it DRY (DRY)

DRY comes before every other rule: each piece of knowledge lives in one place.

- **DRY-1** Reuse an existing component or combination before creating one, and state why none fit; a near-duplicate fails review. [check: review]
- **DRY-2** Every colour, font, size, weight and spacing is a token in the one theme file, `Theme.swift`; no second theme file, no styling literal elsewhere. [check: scan:styling-literal, ratchet:spacing-literal, scan:second-theme-file]
- **DRY-3** Strings live in one catalog per locale, `Localizable.xcstrings`; reuse a key before adding a near-duplicate. [check: scan:one-catalog-per-locale]
- **DRY-4** Error messages live in the catalog; never assemble error text where it is thrown or shown. [check: scan:ui-string-literal]
- **DRY-5** Shared behaviour (routing, gestures, animations, formatting, validation, error and after-save paths) lives in one place; one module decides where every screen, overlay and action goes next, Back, Close, Cancel and errors included. [check: tool:jscpd, review]
- **DRY-6** Compute each derived value (total, score, status, rounding) in one place. [check: tool:jscpd, review]
- **DRY-7** One name per thing everywhere; never add a synonym. [check: review]
