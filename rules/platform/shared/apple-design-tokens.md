## Design tokens and components (DES)

How the design's values and components reach the code.

- **DES-1** Every visual value uses the design's exact token, by the design's token name. Never inline a near-match. If the design needs a value that has no token, add a token to the theme instead of writing the value where it is used. [Coast standard; check: scan:styling-literal, ratchet:spacing-literal]
- **DES-2** Changing the brand colour or typeface is a one-file edit. No code outside the theme file (`Theme.swift`) knows a colour, font or spacing value. [Coast standard; check: scan:second-theme-file]
- **DES-3** A new component is justified in writing. The plan or pull request names the existing components that were checked and says why none fit. The person who builds a component and the person who approves it are different reviewers. [Coast standard; check: review]
- **DES-4** If the project has a design-system spec, every UI change is checked against it. No hardcoded value bypasses the tokens. If a pattern needs a token that doesn't exist, add the token instead of inlining a value. [Coast standard; check: review]
