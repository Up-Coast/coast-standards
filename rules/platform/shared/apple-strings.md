## Strings and localization (L)

- **L-1** From the first commit, every user-visible string is a catalog key: labels, errors, empty states, loading text, tooltips, accessibility labels, titles, notifications, units. [check: scan:ui-string-literal]
- **L-2** `Localizable.xcstrings` is each locale's only string source (see DRY-3). [check: scan:one-catalog-per-locale]
- **L-3** Keys name the meaning, not the English (`status.doNotDispatch`, not `do_not_dispatch_text`). [check: scan:english-key]
- **L-4** Never join strings into sentences or fill a catalog string with `String(format:)`; use `String(localized:)` with `\(…)` placeholders. [check: scan:ui-string-concat, scan:format-on-catalog-string]
- **L-5** Plurals use catalog plural variants, never `if count == 1`. [check: scan:manual-plural]
- **L-6** Format dates, numbers and currency with `FormatStyle`, never templates. [check: review]
- **L-7** Layouts fit text 30% longer than English without clipping; test German, pseudo-locale and, in scope, right-to-left. [check: review]
- **L-8** Xcode String Catalogs manage the plumbing; write only the text by hand. [check: review]
- **L-9** Safety-critical and client-owned terms use the glossary file's approved translations word for word; never translate them yourself. [check: review]
- **L-10** Database and API text is localized too: per-locale fields, or codes mapped to catalog keys. [check: review]
- **L-11** Users can see and change the language; it applies at once, is saved and never discards typed input. [check: review]
- **L-12** Apply all-caps and letter-spacing at render time (`.textCase(.uppercase)`), never in stored strings. [check: scan:baked-case]
