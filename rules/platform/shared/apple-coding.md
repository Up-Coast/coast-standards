## Coding (C)

- **C-1** Follow the Swift API Design Guidelines; no abbreviations. [check: review]
- **C-2** Model data as `struct` or `enum`, classes only for identity or lifecycle; protect shared mutable state with actors. [check: review]
- **C-3** No `!`, `try!` or forced casts where failure is possible. [check: swiftlint:force_unwrapping, swiftlint:force_try, swiftlint:force_cast]
- **C-4** Merge only with zero new warnings and a clean SwiftLint run. [check: swiftlint, swiftformat, tool:warnings-as-errors]
- **C-5** Never hardcode outside facts (branch, path, URL, port, tier, external names or limits); get them from their owner or their one configured place, through one shared function. [check: scan:env-literal]
