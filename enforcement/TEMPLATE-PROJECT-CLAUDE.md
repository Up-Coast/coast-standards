<!-- coast-standards: begin (this block is written by enforcement/adopt.py; edit outside it) -->
## Coast Standards — the standing rules, and the checks that enforce them

{{PRODUCT}} follows the Coast Standards repo, `{{STANDARDS_PATH}}` (GitHub: Up-Coast/coast-standards). It was adopted for the **{{PLATFORM}}** platform from standards release `{{STANDARDS_COMMIT}}`.

1. Read `rules/00-priority-rules.md` in that repo first. DRY is the rule above all other rules.
2. Then read `rules/01-working-style.md`.
3. Read the other rules files when the work touches their area.

This project's checkable rules are in `{{RULES_DOCUMENT}}`. Reviews judge every change against exactly that file.

**Rules enforced by a check: {{ENFORCED}} of {{TOTAL}}** in that document{{SWITCHED_OFF}} (partly {{PARTLY}}, advisory {{ADVISORY}}, reviewer {{REVIEW}}, process {{PROCESS}}, switched off {{OFF}}, still open {{OPEN}}).

Each rule is in one of these groups:

| Group | What holds the rule |
|---|---|
| **machine** | A check refuses the change: the rules scanner (`{{CHECKS_DIR}}/check_rules.py`), the platform's linter with the shipped config, a tool the pre-push hook runs (jscpd, warnings-as-errors, the test time limit, gh-ruleset), or a git or Claude Code hook. |
| **partly** | A check and a reviewer share the rule, or one of the rule's checks is switched off in the config. |
| **advisory** | The scanner reports it, but nothing fails. |
| **reviewer** | Only a reviewer can judge it. Every review returns one row per rule, with evidence. |
| **process** | The pipeline or a named person holds it. |
| **switched off** | Every check that held it is off in `{{CONFIG_FILE}}`. Nothing enforces it until a person turns a check back on. |

### What will refuse you

The files below define the checks. They are GOVERNING: you may not edit them.

| File | What it does |
|---|---|
| `{{HOOKS_DIR}}/pre-commit` | Runs the scanner on the staged changes (every added line, including the doc-comment check). Takes seconds. |
| `{{HOOKS_DIR}}/commit-msg` | Requires a subject line under 100 characters. A commit from an agent session must name the model that did the work: `Co-Authored-By: Claude <model> <version> <noreply@anthropic.com>`. |
| `{{HOOKS_DIR}}/pre-push` | Runs the checks on what the push changed (see below). |
| `{{SESSION_HOOK}}` with `{{SETTINGS_FILE}}` | The Claude Code session hooks. They refuse edits to governing files, chained `cd` commands, infrastructure commands, `--no-verify`, force pushes, and a commit while the scan is failing. |
| `{{STATE_DIR}}/ratchet-baseline.json` | The baselines (see below). |
| `{{CONFIG_FILE}}` | The switches and names: which rules, pre-push checks, linters and session hooks are off, and who to ask. It belongs to a person; an agent cannot write it. The number above counts what it switches off. |
| `{{STATE_DIR}}/platform`, `{{STATE_DIR}}/paths.json` (when present), `{{CHECKS_DIR}}/` | The platform, the project's paths, and the checks themselves. |

The pre-push hook runs:

- the build, with warnings treated as errors
- the tests
- the linter and the formatter
- the scanner, on everything added since the remote and on the whole tree
- the whole-tree doc-comment count (advisory only)
- jscpd: no new duplicated code compared with `{{STATE_DIR}}/jscpd-baseline.json`
- the protected-main ruleset check

What runs depends on what the push changed:

- **Documents only:** none of the code checks.
- **Code:** the linter and formatter on the changed files, and the tests of the modules that depend on the change.
- **The checks themselves:** everything.

### Baselines

A baseline is a count of existing problems that may only go down. `{{STATE_DIR}}/ratchet-baseline.json` holds:

- the scanner's baselines
- for a repository that already had problems when it adopted the standards: `build-warnings`, `lint-findings`, `format-findings`, and `tests-missing` if there is no test target yet

Each baseline has a deadline. After its deadline, the check blocks.

**When a count FELL,** the push is refused until the baseline is lowered. Record it yourself:

1. Run `adopt.py <project> --lower-baselines` from the standards repo. It writes only the two baselines (`ratchet-baseline.json` and `jscpd-baseline.json`) and only ever lowers a count.
2. Commit the baseline file together with your change.

Do not hand this to a person. Raising a count or moving a deadline is a person's decision.

### When a check is wrong

- Never use `--no-verify`.
- Never edit the files above.
- Say in plain words that the check is wrong, then stop. Name the check (use its name from the list below) and say why.

There is a way to excuse a check (a door), and it is {{OWNER}}'s to open, not yours. To excuse a check, {{OWNER}} adds an entry to this file:

    {{EXCEPTIONS_FILE}}
    {"exceptions": [
      {"seat": "build", "reason": "the build needs env vars this checkout has not got",
       "who": "{{OWNER}}", "when": "{{TODAY}}", "until": "{{UNTIL}}"}
    ]}

- An entry skips one named check until its `until` date. The seat names are `build`, `tests`, `lint`, `format`, `rules-scan`, `doc-comments`, `jscpd` and `gh-ruleset`.
- Every push prints who excused the check and why.
- The check starts refusing again on the day the entry expires.
- An entry with no `until` is ignored.
- The file is GOVERNING, so an agent cannot write it. A wrong check is {{OWNER}}'s decision, never a reason to bypass it.
<!-- coast-standards: end -->
