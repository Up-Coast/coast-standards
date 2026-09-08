<!-- coast-standards: begin (this block is written by enforcement/adopt.py; edit outside it) -->
## Standing rules — enforced by machines where a machine can hold them

This project follows the Coast Standards repo,
`{{STANDARDS_PATH}}` (GitHub: Up-Coast/coast-standards), adopted for
the **{{PLATFORM}}** platform from standards commit `{{STANDARDS_COMMIT}}`.
Read `rules/00-priority-rules.md` there first (DRY is the rule above all
other rules), then `rules/01-working-style.md`, and the others as the work
touches their areas. This project's own checkable rules document is
`{{RULES_DOCUMENT}}`; reviews judge every change against exactly that file.

**Rules enforced by a check: {{ENFORCED}} of {{TOTAL}}** in that document
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

- `.githooks/pre-commit` — the scanner on the staged diff (every added
  line, the doc-comment check among them), in seconds.
- `.githooks/commit-msg` — a subject line under 100 characters; a commit
  from an agent session names the model that did the work
  (`Co-Authored-By: Claude <model> <version> <noreply@anthropic.com>`).
- `.githooks/pre-push` — the full battery: build with warnings as errors,
  tests, lint, format, the scanner on everything added since the remote
  and on the whole tree, the whole-tree doc-comment count (advisory),
  jscpd (no new duplicated code against `.coast/jscpd-baseline.json`),
  and the protected-main ruleset.
- `.coast/ratchet-baseline.json` — the legacy counts the ratchet checks
  may only lower (the scanner's ratchets, and on a repository that came
  with warnings, linter or formatter findings, `build-warnings`,
  `lint-findings`, `format-findings` and, with no test target yet,
  `tests-missing`); each carries a deadline after which the check blocks.
- `.coast/platform`, `.coast/paths.json` (when present), `Scripts/checks/`.

Never `--no-verify`. Never edit the files above. When a check is wrong, say so
in plain words and stop — and say which seat and why, because there is a door
and it is the founder's to open, not yours:

    .coast/rules-exceptions.json
    {"exceptions": [
      {"seat": "build", "reason": "the build needs env vars this checkout has not got",
       "who": "Pat Lee", "when": "2026-09-05", "until": "2026-09-19"}
    ]}

That skips one named seat (`build`, `tests`, `lint`, `format`, `rules-scan`,
`doc-comments`, `jscpd`, `gh-ruleset`) until the date, prints who excused it and
why on every push, and starts refusing again the day it expires. An entry with
no `until` is ignored. The file is GOVERNING, so an agent cannot write it — which
is the point: a wrong check is a founder's call, never a bypass.
<!-- coast-standards: end -->
