<!-- up-coast-standards: begin (this block is written by enforcement/adopt.py; edit outside it) -->
## Standing rules — enforced by machines where a machine can hold them

This project follows the Up Coast standards repo,
`{{STANDARDS_PATH}}` (GitHub: Up-Coast/up-coast-standards), adopted for
the **{{PLATFORM}}** platform from standards commit `{{STANDARDS_COMMIT}}`.
Read `rules/00-priority-rules.md` there first (DRY is the rule above all
other rules), then `rules/01-working-style.md`, and the others as the work
touches their areas. This project's own checkable rules document is
`{{RULES_DOCUMENT}}`; reviews judge every change against exactly that file.

**Rules held by a machine: {{ENFORCED}} of {{TOTAL}}** in that document
(partly {{PARTLY}}, advisory {{ADVISORY}}, reviewer {{REVIEW}}, process {{PROCESS}},
still open {{OPEN}}). A rule is in one of these bins:

- **machine** — a check refuses the change: the rules scanner
  (`Scripts/checks/check_rules.py`), the platform's linter with the shipped
  config, a tool the pre-push battery runs (jscpd, warnings-as-errors,
  gh-ruleset), or a hook (git and Claude Code).
- **partly** — a machine check and a reviewer share the rule.
- **advisory** — the scanner reports it; nothing fails.
- **reviewer** — only a mind can judge it; every review returns a row per
  rule with evidence.
- **process** — held by the pipeline or by a person, named as such.

What will refuse you, and where it lives — all GOVERNING, none of it is
yours to edit:

- `.githooks/pre-commit` — the scanner on the staged diff and the
  doc-comment check, in seconds.
- `.githooks/commit-msg` — a subject line under 100 characters; a commit
  from an agent session names the model that did the work
  (`Co-Authored-By: Claude <model> <version> <noreply@anthropic.com>`).
- `.githooks/pre-push` — the full battery: build with warnings as errors,
  tests, lint, format, the scanner on everything added since the remote
  and on the whole tree, doc-comments, jscpd (no new duplicated code
  against `.coast/jscpd-baseline.json`), and the protected-main ruleset.
- `.coast/ratchet-baseline.json` — the legacy counts the ratchet checks
  may only lower; each carries a deadline after which the check blocks.
- `.coast/platform`, `.coast/paths.json` (when present), `Scripts/checks/`.

Never `--no-verify`. Never edit the files above. When a check is wrong,
say so in plain words and stop; the founder changes the standards repo.
<!-- up-coast-standards: end -->
