## Keep it DRY (DRY) — the rule above every other rule

Every piece of knowledge lives in exactly one place, and everything else uses that place.

- **DRY-1** Design components are built once and reused. Before creating a view, component or helper, check for an existing one, or a combination of existing ones. A near-duplicate of an existing component fails review. Every new component states why nothing existing fit. [Coast standard; check: review]
- **DRY-2** All styling lives in one theme file (`Theme.swift`). Every colour, font, size, weight and spacing value is a token there. Never create a second theme file, and never write a styling literal in a feature file. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal, scan:second-theme-file]
- **DRY-3** Strings live in one catalog per locale (`Localizable.xcstrings`). All new strings go there. Reuse an existing key before adding a near-duplicate. [Coast standard; check: scan:one-catalog-per-locale]
- **DRY-4** Error messages live in one place, like other strings. Never assemble error text where the error is thrown or shown. [Coast standard; check: scan:ui-string-literal]
- **DRY-5** Shared behaviour (gestures, animations, formatting, validation) lives in one place and is called from there. Never re-implement it locally. [Coast standard; check: tool:jscpd, review]
- **DRY-6** Every derived value (a total, a score, a status, a rounding) is computed in one place and reused. Never compute it again, slightly differently, somewhere else. [Coast standard; check: tool:jscpd, review]
- **DRY-7** Each thing has one name everywhere. Choose the vocabulary once, and never introduce a synonym for something that already has a name. [Coast standard; check: review]
