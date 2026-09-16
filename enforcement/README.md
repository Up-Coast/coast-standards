# Rules enforcement: design and build plan

*Last updated: 2026-09-16*

## Summary

The enforcement layer turns the rules in this repo into checks that refuse a change. A rule that lives only in a document is a request, and agents ignore requests. So every rule names the check that holds it, and the checks run before anything leaves the machine.

The parts:

| Part | File(s) | What it does |
|---|---|---|
| Scanner | `enforcement/checks/check_rules.py` | Matches per-platform patterns ("signatures") against the lines a change adds, the staged diff, named files, or the whole tree. |
| Verifier | `enforcement/checks/verify_rules.py` | Checks that every rule names a check that really runs, and prints "rules enforced by a check: N of M". |
| Linter configs | `enforcement/lint/` | SwiftLint, swift-format, ESLint, Prettier, detekt, ktlint, Android Lint, tsconfig, mypy, ruff, with the rules the documents name switched on. |
| Git hooks | `enforcement/hooks/pre-commit`, `commit-msg`, `pre-push` | Run the scanner at commit, check the commit message, and run every check at push. |
| Claude Code session hooks | `enforcement/hooks/claude-hook.py`, `claude-settings.json` | Refuse agent actions the rules forbid (editing check files, chained `cd`, infrastructure commands, force pushes, `--no-verify`, stopping with unpushed work). |
| Installer | `enforcement/adopt.py` | Installs all of the above into a project. Safe to re-run. |

The user manual for what is built is [DEVELOPER-GUIDE.md](DEVELOPER-GUIDE.md). This document is the design and the build plan. Every design decision is taken (section 7): a session builds, it does not re-ask.

**To start a session on this work, say:** *"Read `enforcement/README.md` in the standards repo and build the next enforcement task."* The next task is the first row in section 6 that is not marked DONE. Coast's own task list for its half lives in the Coast repo's plan folder and points here; it never restates the design.

**Contents**

1. [The problem this solves](#1-the-problem-this-solves)
2. [The principle](#2-the-principle)
3. [Tools considered](#3-tools-considered)
4. [The architecture](#4-the-architecture): 4.1 rule registry, 4.2 scanner, 4.3 linter configs, 4.4 session hooks, 4.5 inside Coast, 4.6 versioning, 4.7 adoption defaults, 4.7b excusing a check, 4.8 a project's own hooks, 4.9 one push at a time
5. [Every rule, its bin, its check](#5-every-rule-its-bin-its-check)
6. [The build plan](#6-the-build-plan)
7. [The decisions](#7-the-decisions)
8. [Limits of this document](#8-limits-of-this-document)

## 1. The problem this solves

Session agents reported rules as followed when they were not. The rules are not matters of judgment, yet nothing checked them, and a review agent cannot be trusted to catch what the builder agent skipped.

What was true on 2026-09-03, checked in the code, before this layer existed:

- Of the 51 rules in Coast's shipped iOS rules document, 3 were held by a script or linter.
- The DRY rules (one theme file, one string catalog, one place per fact) were in none of the shipped platform documents.
- Inside Coast, only the domain-rules reviewer read the rules document, after the work was built. The coding agent's prompt held no rule. That reviewer's prompt said a diff touching no rule's area is a clean pass.
- Several rules named checks that did not run: SwiftLint `force_unwrapping` (opt-in, not enabled), ESLint `no-floating-promises` (needs the type-checked config, which was not shipped), detekt (no config shipped), and "review greps the diff" (an instruction to a model, not a script).
- Coast's `doc-comments` check was Swift-only and ran only inside Coast's build loop.
- The owner's three iOS app repos and the user-level Claude Code settings had no linter config, no git hooks and no Claude Code hooks.

What already worked, and is the template for this design: Coast's native-patterns checker (a per-platform pattern list, run on added lines, fails the push, exceptions only from the approved plan, agents cannot edit it), the import-matrix checker, the proof verifier, a local check run that is the same scripts as CI, a class of files agents cannot write, and Coast's copy guard test for bare user-facing text in views.

## 2. The principle

A task is done when the check that makes its rule unbreakable exists and a reviewer confirms it from the code. This design applies that to every rule:

1. **Every rule is sorted into a bin, written next to the rule.**
   - **machine**: a script or linter holds it and fails the push.
   - **ratchet**: a script counts existing problems and fails the push when the count goes up against a committed baseline. The baseline may only go down. This is how an existing repo adopts a rule without a rewrite.
   - **review**: only a person or reviewer model can judge it. The reviewer answers per rule, with evidence, and an empty answer is rejected.
   - **session**: a rule about how the agent works (never chain `cd`, never touch infrastructure, push every commit). A hook on the agent's own tool calls holds it.
2. **The rule names its check.** A rule that names a check nothing runs is a failure, not a footnote.
3. **The builder gets the verdict in seconds, locally.** Checks run on files as they are edited, on the staged diff at commit, and in full at push. CI confirms; it never discovers.
4. **Nothing the builder says counts.** Only check output and a reviewer's evidenced rows feed a verdict.
5. **Every miss adds a check.** A bug a script could have caught adds a signature. The number of rules enforced by a check goes up, and the owner can see it.

## 3. Tools considered

Researched on 2026-09-03 against each tool's own documentation.

| Option | Verdict | Why |
|---|---|---|
| **Stdlib Python scanner with per-platform signature tables** | **Chosen, for every custom rule** | Proven in Coast. Runs wherever `python3` runs, with nothing to install. One implementation, one exception mechanism and one output format for all platforms. The rules are about literals in the wrong file, so regex over added lines, scoped by path class, is precise enough. |
| **The platform's own linter with a shipped config** | **Chosen, for rules linters already hold** | SwiftLint, swift-format, ESLint (type-checked config, `react-hooks`), Prettier, ktlint, detekt, Android Lint. They understand syntax and are free. Custom rules are not written in linter config: that would give one rule a home per platform, and detekt/ktlint need a compiled JAR anyway. |
| **jscpd v5** (MIT, one binary) | **Chosen, for duplicate code** | Real token-based clone detection a regex can't do. `--fail-on-new-clones` against a baseline is exactly the ratchet shape. |
| **Semgrep** (LGPL-2.1 CLI) | Deferred | Understands syntax and needs only config. But it is an install on every Mac and CI runner, its free per-language coverage is not listed on a primary source, and no rule needs syntax awareness yet. Revisit when one does. |
| `eslint-plugin-i18next` / `react/jsx-no-literals` | Not adopted | Would give the strings rule a second home. The scanner holds JSX text. |
| pre-commit framework | Not adopted | Another dependency. Plain `.githooks/` with `core.hooksPath` needs nothing. |
| Danger | Not adopted | PR-time comments; Coast's reviewer already covers that. |
| **Claude Code hooks** (committed `.claude/settings.json`) | **Chosen, for session rules** | The only way to make a rule about the agent's own actions structural. A `PreToolUse` hook that exits 2 (or returns `permissionDecision: deny`) blocks the call in every permission mode. `Stop` can refuse to end the turn. Limit: a user-level `disableAllHooks` turns them off; that is the person's own machine. |
| Apple's string-catalog build settings | Not applicable | They switch extraction on; they do not warn on an unlocalized literal. The scanner holds it. |
| Android Lint for Compose `Text("literal")` | No built-in check | `HardcodedText` covers layout XML only. The scanner holds Compose. |

## 4. The architecture

```
coast-standards (this repo): the one home
├── rules/…                       the rules, each with a [check: …] tag
├── enforcement/
│   ├── README.md                 this design
│   ├── DEVELOPER-GUIDE.md        the manual
│   ├── TOOLCHAIN.md              pinned tool versions (jscpd)
│   ├── adopt.py                  the installer (idempotent)
│   ├── checks/
│   │   ├── check_rules.py        the scanner: signatures × path classes × diff
│   │   ├── scope.py              what a push changed: none / files / all, and the affected modules
│   │   ├── check_doc_comments.py the doc-comment check
│   │   ├── verify_rules.py       rule documents ↔ checks; the enforced/total number
│   │   ├── battery.json          per platform: linters, configs, tools, scanner, hook files
│   │   ├── rules_signatures.json one row per signature; each platform's files and pattern under "platforms"
│   │   ├── paths.json            the path classes per platform (theme, strings, ui, tests…)
│   │   ├── layout.json/.py       every path the layer uses inside a project
│   │   ├── config.default.json   the project config's defaults; config.py is its one loader
│   │   ├── verify-baseline.json  this repo's own gap-count baseline
│   │   └── tests/                tests and plants (a failing and a passing sample per signature)
│   ├── lint/                     the shipped linter configs
│   └── hooks/
│       ├── pre-commit            scanner on the staged diff (seconds)
│       ├── commit-msg            subject length and the model attribution trailer
│       ├── pre-push              every check for the platform, on what the push changed
│       ├── claude-settings.json  the Claude Code hooks and deny rules
│       └── claude-hook.py        the one script every Claude Code hook calls
└── CHECKS-VERSION                the release number (rules and checks together)

consumers (each carries a pinned copy)
├── Coast → Templates/…           installs it into every customer project; its gate runner and CI run it
├── Coast's own repo              uses the same hooks and scanner
└── adopting app repos            adopt.py, then the same hooks
```

Inside a project, `adopt.py` installs to the paths in `layout.json`:

| Key | Default path |
|---|---|
| `state_dir` | `.coast` |
| `checks_dir` | `.coast/checks` |
| `session_hook` | `.coast/hooks/claude-hook.py` |
| `hooks_dir` (git) | `.githooks` |
| `settings_file` | `.claude/settings.json` |
| `rules_document` | `docs/domain-rules.md` |
| `ai_rules_document` | `docs/ai-features-rules.md` |
| `context_file` | `CLAUDE.md` |
| `lock_name` | `coast-push.lock` |
| `temp_prefix` / `env_prefix` | `coast-` / `COAST_` |

A project overrides any key except `state_dir` under `layout` in `.coast/config.json`.

There is one implementation of every check. The script the hook runs is the script CI runs and the script Coast runs. No Swift copies, no per-platform re-implementation in linter config.

### 4.1 The rule registry lives in the rule documents

The Markdown rule documents stay the owner-facing home. Coast's `docs/domain-rules.md` (versioned, owner-editable, three-way-merged) depends on that. Each rule ends with a formal tag:

```
- **L-1** No hardcoded user-facing text … [Coast standard; check: scan:ui-string-literal]
- **C-3** No force-unwraps … [Swift practice; check: swiftlint:force_unwrapping]
- **A-4** No speculative abstraction … [YAGNI; check: review]
- **A-3** A type or module has one job … [SRP; check: ratchet:type-size]
```

`verify_rules.py` parses every rule in `rules/platform/*.md` and the numbered files. It fails when a rule has no `check:` tag, when a tag names a check the platform does not run, or when a signature exists that no rule names. The full grammar is the docstring of `verify_rules.py`. The shape:

**What counts as a rule**

- A column-0 bullet that opens in bold (`- **…**`). Its id is the leading `PREFIX-n`, or a slug of the bold title when it has none.
- Or a leaf section written as prose: a heading with no bold bullets and no child headings.
- The H1 and any "Sources" section are not rules.

**The tag** is the last square bracket in the rule that contains `check:`. It holds comma-separated references, and every one must resolve:

| Reference | Meaning |
|---|---|
| `scan:<id>`, `ratchet:<id>`, `advisory:<id>` | A scanner signature with that severity |
| `<linter>:<rule>` or bare `<linter>` | `swiftlint`, `swiftformat`, `detekt`, `ktlint`, `androidlint`, `eslint`, `tsc`, `prettier`, `ruff`, `mypy` |
| `tool:<name>` | A tool the pre-push hook runs (jscpd, gh-ruleset, warnings-as-errors) |
| `session:<id>` | A session or git hook |
| `review` | A reviewer judges it |
| `process` | Held by a pipeline or a person |
| `context` | The bullet explains a rule and is not one. Not counted. Cannot share a tag with a check. |

**What "resolves" means: files on disk, nothing else.** `enforcement/checks/battery.json` names, per platform, the linters and their config files, each tool and the runner file that invokes it, the scanner, the signatures file and the session-hook files.

- A scanner id must be in the signatures table of every platform the document applies to, with the severity the tag claims.
- A linter rule must be enabled by name in the shipped config. The verifier reads SwiftLint and detekt YAML, ESLint flat config, `lint.xml`, `tsconfig`, `mypy.ini` and `ruff.toml`. It does not know any linter's default set: if the config does not name the rule, the rule is not held.
- A tool's runner file must exist and mention the tool.
- A session id must appear in a hook file.
- A manifest path that does not exist is reported as a gap.

**The bins it counts**

| Bin | Meaning |
|---|---|
| `machine` | Every reference is a machine check. The only bin the headline number counts. |
| `partly` | A machine check shares the rule with a review, process or advisory reference, or one of several machine references is switched off. |
| `advisory` | Reported, never fails. |
| `review` | A reviewer judges it. |
| `process` | A pipeline or a person holds it. |
| `off` | Every machine reference is switched off in the project config. |
| `open` | Any gap. |

**Output and exit codes**

- One summary line per document, then `FAIL verify-rules <path>:<line>:<id>: <words>` per gap, then totals.
- Exit 1 on any gap, 0 otherwise.

| Flag | Use |
|---|---|
| `--json` | Machine-readable output (Coast's Rules tab) |
| `--document <file> --platform <p>` | Check one project's copy |
| `--config <file>` | Apply a project's switches (default: the state dir's `config.json`, else the shipped defaults) |
| `--baseline <file>` | Pass only while the gap count equals this file's count |
| `--summary` | Print the per-document lines and totals only |
| `--root <dir>`, `--battery <file>` | The repo root and the manifest (default `enforcement/checks/battery.json`) |

**This repo's own hook.** `.githooks/pre-commit` (install per clone with `git config core.hooksPath .githooks`) runs the verifier's tests, then the verifier against `enforcement/checks/verify-baseline.json`. The commit is refused when the gap count rises. It is also refused when the count falls until the baseline is lowered in the same commit. After the deadline (2026-12-03) any gap is refused.

### 4.2 The scanner

```
check_rules.py <base> <head> --platform <p>        # lines added between two commits (pre-push)
check_rules.py <base> WORKTREE --platform <p>      # tracked changes since base, plus untracked files
check_rules.py --staged --platform <p>             # the index (pre-commit)
check_rules.py --files a b c --platform <p>        # whole files; every line counts as new (edit hook)
check_rules.py --tree --platform <p>               # whole tree: tree-scope and ratchet signatures only
check_rules.py --ratchet <id> --count <n> --platform <p>
check_rules.py --ratchet <id> --log <log> [--measured <listing>] --platform <p>
check_rules.py --measure <id> --log <log>
check_rules.py --has-baseline <id> [--per-file]
… --only <id>[,<id>]                               # run only these signatures
```

Run it from the repository root. The platform can also come from `COAST_PLATFORM` (`<env_prefix>PLATFORM`). Stdlib only, no network, no model.

**Inputs**

- **`rules_signatures.json`**: one row per signature, `{id, severity, scope, applies_to, excludes, words, rule, platforms: {<p>: {files, pattern, paired?, …}}}`. `severity` is `block`, `ratchet` or `advisory`. `rule` is the rule id the signature holds, so output and reviews cite the same id. `flatten_signatures` turns the table into one list per platform, laying each platform's fields over the shared ones. A signature a platform lacks is simply not listed under it.
- **The project config** (`.coast/config.json`, read through `config.py`): a signature in `rules.off` does not run; `rules.severity` may lower a severity but never raise it; `rules.retired_words` extend the `retired-wording` pattern.
- **`paths.json`**: the path classes per platform. Classes include `git`, `governing`, `plans`, `generated`, `schema`, `theme`, `ui_lib`, `strings`, `manifest`, `docs`, `design_bundle`, `tests`, `ui`, `config_home` and `gallery`. A project's own bindings live in `.coast/paths.json` (or `--paths-override`). Coast reads the same table.

**What each mode judges**

- Every mode except `--tree` judges the change: `block` signatures with scope `added` on the added lines, and `block` signatures with scope `tree` on the changed files. No ratchets. This keeps commit-time and edit-time scans to seconds.
- `--tree` runs the tree-scope signatures and the ratchets over the whole tree. A push runs it once.
- Only added lines are judged, because an untouched legacy line is not this change's fault. On the first push after adoption, the push hook starts the diff at the adoption commit, so earlier commits count as legacy too.
- A diff that touches only governing or git paths passes.

**Severities**

| Severity | Behaviour |
|---|---|
| `block` | Any hit fails, unless an exception covers it. |
| `ratchet` | Counted over the whole tree and compared with `.coast/ratchet-baseline.json`. Above the baseline fails. Below it fails until the baseline is lowered in the same commit (the message gives the number). No entry means a baseline of 0. After the deadline the signature is `block`. An entry with no deadline is a `FAIL ratchet` line. |
| `advisory` | Printed as `ADVISORY` lines. Never fails. |

**The ratchet baseline file** is `.coast/ratchet-baseline.json`: `{"baselines": [{id, count, deadline, written, by, moves}]}`. Tool entries may also carry a per-file map, `files` (section 6, phase E8). It is a file that defines the checks, so agents may not edit it. Lower a count that fell with `adopt.py <project> --lower-baselines`; any session may run this because it can only lower counts. Only a person raises a count or moves a deadline. The scanner never writes the file.

**Tool ratchets (the warnings baseline).** Rule C-4 says "zero new compiler warnings". A repo that already has warnings cannot meet that without a rewrite, so:

1. `adopt.py --measure-tools` runs the installed pre-push hook in counting mode: `pre-push --measure build,format,lint`. Each step prints `MEASURE <id> <count>` instead of judging.
2. It records the counts in `.coast/ratchet-baseline.json` with the usual 90-day deadline:

   | Entry | What it counts |
   |---|---|
   | `build-warnings` | Distinct build warnings |
   | `format-findings` | Formatter findings |
   | `lint-findings` | Linter findings |
   | `tests-missing` | Count 1, for an app with no test target. The test step judges this entry instead of running tests, until a test target exists. |

   A count of zero writes no entry.
3. From then on, the step runs the tool without its strict switch and hands the count to `check_rules.py --ratchet <id> --count <n>` (or `--log`).
   - The build is a full build, because an incremental build prints warnings only for what it recompiles. SwiftPM drops the package's own build products first; xcodebuild runs `clean build`.
   - Above the baseline refuses. After the deadline, anything above zero refuses.
   - Below the baseline passes with a note. (A scanner count is deterministic, so a fall there must be recorded. A build's count can fall because the build was warm, which is no reason to refuse.)
4. With no entry, the step is strict (`-warnings-as-errors`, `swift-format lint --strict`, `swiftlint --strict`), so a new repo is held at zero from its first push.

Today the Swift steps (SwiftPM and xcodebuild) support tool ratchets. The Android, web and Python steps stay strict until a repo on those platforms needs a baseline.

**Exceptions** (agents cannot write either):

- Coast's plan-approved native deviations: the last plan verdict in `plans/<feature>/proof.json` carries `approved_native_deviations: [{file, signatures: [ids]}]`.
- `.coast/rules-exceptions.json`, for repos without a plan: `{"exceptions": [{id, path, reason, who, when}]}`. `path` is an exact path or a `dir/**` glob. The same file excuses a whole pre-push step (section 4.7b).

**Output**

- A failure: `FAIL <check> <path>:<line>:<id>: <words> [<rule>]`. The hooks, CI and Coast parse this format.
- Advisory hits: `ADVISORY` lines.
- `--measure`: `MEASURE <id> <total>` and `MEASURE-FILE <id> <count> <path>`.
- The last line is a JSON summary: `{"result": "pass"|"fail", ...}`.
- Exit 0 on pass, 1 on any failure. `--has-baseline` exits 0 when the entry exists.

### 4.3 The linter configs

The linter configs are starter files the project owner may edit (`adopt.py` tracks them in `.coast/seeds.json`, section 6, E2.2). The opt-in rules the documents name are switched on:

- SwiftLint: `force_unwrapping` (error), `force_cast` and `force_try` (error), `type_body_length` 300 and `file_length` 400 (warnings only).
- ESLint: `recommended-type-checked` with `parserOptions.projectService`, `@typescript-eslint/no-floating-promises`, `react-hooks` rules (only when the plugin is installed), `max-lines` warning.
- Android: `detekt.yml` on the default set (`UnsafeCallOnNullableType`, `LargeClass` 300) and `lint.xml` with `HardcodedText` as an error. The Android toolchain runs `./gradlew lint` and detekt beside ktlint.

Every claim a rule makes about its linter must be true in the shipped config. `verify_rules.py` checks the config file for the named rule.

### 4.4 The Claude Code session hooks

The committed `.claude/settings.json` wires every hook to one script, `claude-hook.py <hook-id>`. The script reads the hook's JSON on stdin and exits 2 with the reason on stderr to block.

| Hook id | Event and matcher | What it does | Rules |
|---|---|---|---|
| `governing-edit` | `PreToolUse`, `Edit\|Write\|MultiEdit\|NotebookEdit` | Refuses edits to files that define the checks (agents may not edit these): the `governing` path class (`.github/**`, `.coast/**`, `.githooks/**`, the rules documents, the linter configs), plus `.claude/settings.json` and `.claude/settings.local.json`. | 03 process |
| `chained-cd` | `PreToolUse`, `Bash` | Refuses `cd X && …`, `cd X; …`, `pushd`, and a `cd` followed by more commands. A bare `cd` passes. | 10 |
| `infra-command` | `PreToolUse`, `Bash` | Refuses commands that change infrastructure (`fly`, `wrangler`, `terraform`, `aws`, `gcloud`, mutating `gh api` calls on repos, rulesets and secrets, `gh repo delete`, `gh secret set`, DNS tools) with "ask in one line first". Read-only forms (`fly status`, `terraform plan`, `dig`) pass. | 00 §2c |
| `no-verify` | `PreToolUse`, `Bash` | Refuses `--no-verify` (and its prefixes), `git commit -n`, and changing `core.hooksPath`. | 07 |
| `force-push` | `PreToolUse`, `Bash` | Refuses `--force`, `-f`, `--force-with-lease`, `--force-if-includes`, and `+refspec`. | 07 |
| `scan-at-commit` | `PreToolUse`, `Bash` | On `git commit` (including `git -C <dir> commit`, routed to that repo), runs `check_rules.py --staged`. A failing scan blocks the commit with the FAIL lines. The hook reads the command itself, because the settings `if` filter is only a best-effort prefix match. | 00 §1, §2, §2d |
| `scan-on-edit` | `PostToolUse`, `Edit\|Write\|MultiEdit` | Runs `check_rules.py --files <path>`. Findings exit 2 so the model sees them (stderr on exit 0 is not shown). Nothing is blocked; the edit already happened. | all machine rules |
| `unpushed-at-stop` | `Stop` | Refuses to end the turn with commits not on the remote, or uncommitted source changes: "push before finishing". Passes when `stop_hook_active` is true, or when there is no upstream (with a note). | 00 §7, 07 |
| `rules-at-start` | `SessionStart` | Prints as context: platform and project type, the enforced/total number (read from the CLAUDE.md block `adopt.py` wrote), the review-only rules, and the ratchet counts. Always exits 0. | 01 |

How the hook finds its inputs:

- The platform comes from `.coast/platform` (one line, for example `ios A` for platform and project type) or `COAST_PLATFORM`.
- Every Bash command is split into its parts before judging: line continuations are joined; `$(…)`, backticks, `(…)`, `{ …; }`, `sh -c "…"`, `eval` and `find -exec` bodies are read too; leading `VAR=` assignments, wrappers (`env`, `xargs`, `npx`, `pnpm dlx`, `bunx`) and shell keywords are skipped.
- A hook listed in the config's `session_hooks.off` exits 0 with a one-line note.

The settings file uses only documented fields (`matcher`, `if`, `type`, `command`, `timeout`, `statusMessage`). It also carries:

- `permissions.deny` rules for the mutating forms of each command and the fixed governing paths. Anthropic's docs recommend the permission system for a hard deny; the hook explains the refusal. A deny rule cannot carry exceptions, so no rule denies a whole program.
- `"disableAllHooks": false`, which overrides a user-level `true`.

`adopt.py` merges both keys into an existing settings file and keeps the owner's `allow` and `ask` rules. Hook behaviour was verified against Anthropic's Claude Code hooks reference, https://code.claude.com/docs/en/hooks.

**Git hooks beside them** (`core.hooksPath` set by `adopt.py`):

- `.githooks/pre-commit`: the scanner on the staged diff.
- `.githooks/commit-msg`: the subject must exist and be at most 100 characters. A commit from an agent session (Claude Code sets `CLAUDECODE` in its shell) must name the model in its `Co-Authored-By` trailer; any Claude trailer must name a model, never a bare "Claude Code". Git's own merge and revert messages, and subjects starting `#123`, are accepted. This is `session:attribution-trailer`.
- `.githooks/pre-push`: build, tests, lint, format, the scanner, jscpd new clones and the other shipped checks, each on what the push changed (section 6, phase E8).

A person and an agent get the same refusal, in the checks' own output lines.

### 4.5 Inside Coast

Coast's half of the design (phase E3):

- **The coding agent, every specialist and the planner receive the rules document**, split by bin: the machine and ratchet rules as one paragraph ("these checks will refuse your push: …"), and the review rules in full for their role. Plans then name their tokens, keys and components.
- **The in-loop check run** runs the scanner on the working tree (`WORKTREE` mode) after every build-and-test request, so the coder sees failures in the same turn.
- **Review returns one row per rule**: `rules: [{id, touched, verdict, evidence: {file, line}}]`. The harness rejects a missing rule, `touched: false` when the rule's `applies_to` classes intersect the diff, a `fail` with no evidence, and evidence naming a file outside the diff. Machine-held rules get the scanner's result attached instead of a verdict. The "touches no rule's area is a clean pass" sentence is deleted.
- **The general reviewer reads the rules document too.**
- **Builder self-reports count for nothing.** No gate, ledger verdict or dashboard row reads the coder's `submit_work` text as evidence. This is enforced in the harness, not the prompt.
- **Every fix ticket names its guard.** A bug-fix ticket needs a `guard` field naming the signature, linter rule or test that now prevents the problem, and the fix diff must touch it.
- **The owner sees the number.** The Rules tab shows "rules enforced by a check: N of M" per project and lists the review-only rules.
- **The `doc-comments` check is `check_doc_comments.py`**, shipped and run in CI and the hook. The Swift implementation is deleted.
- **Coast's own repo uses the same layer.** Its copy guard test was retired once the scanner's `ui-string-literal` reproduced every one of its findings.

### 4.6 Versioning and delivery

- `CHECKS-VERSION` holds one release number for the rules and the checks together. The platform rule documents carry the same kind of number on their first line, `<!-- coast-standards-release: X.Y.Z -->`: the release in which their text last changed. `tools/build_rules.py` keeps it right, and there is no separate rules version. Every release is that number, a git tag `v<number>` on `main`, and an entry in the root `CHANGELOG.md`. CI refuses a tag that differs from the file.
- Each project records the release it carries in `.coast/standards-version` (the tag, or the commit for an unreleased clone).
- A rules update in Coast delivers the documents, signatures, linter configs, hooks and scripts as one owner-approved change, with a plain-words list of changes.
- Coast carries `enforcement/` in `Templates/`, pinned by commit and SHA-256. A parity test fails Coast's suite if the copy drifts.
- Other repos run `adopt.py` once, then re-run it to update. It can fetch a release tarball instead of using a clone. A re-run replaces the check files, keeps a starter file the owner edited, and prints what changed.

### 4.7 What adopting an existing repository does without asking

If adoption produces a question whose answer is always the same, the answer belongs in the code. `adopt.py` handles these on its own:

- **It measures existing problems.** A first adoption measures warnings, linter findings and formatter findings and writes their baselines. `--measure-tools` only forces a re-measure later.
- **It upgrades an old rules document.** A `docs/domain-rules.md` stamped with an older release (or with an old `coast-rules-version: N` number) is replaced. An edited copy is saved as `docs/domain-rules.v<release>.md`. A copy from the current release that differs is the owner's edit and is left alone.
- **It binds the real theme.** Theme candidates are ranked by folder (`styles/`, `theme/`, `design-system/`, `tokens/`) and by name. Every token file in the winning folder is bound, so `tokens.css` and `tokens.ts` count as one theme.
- **It ignores obvious test fakes.** A value starting `test-`, `fake_`, `dummy.`, `sample-`, `stub-` and similar is not a secret. A value shaped like a real credential (`sk-ant-…`, `ghp_…`, `AKIA…`, a PEM header) is always reported, including in tests.

### 4.7b A wrong check is a founder's call, not a dead end

A false-positive check could block every push with no allowed way out. So a person can excuse one step of the pre-push hook in `.coast/rules-exceptions.json`, beside the signature exceptions:

```json
{"exceptions": [
  {"seat": "build", "reason": "the build needs env vars this checkout has not got",
   "who": "Pat Lee", "when": "2026-09-05", "until": "2026-09-19"}
]}
```

- `seat` is one of `build`, `tests`, `lint`, `format`, `rules-scan`, `doc-comments`, `jscpd`, `gh-ruleset`.
- The hook skips that step, printing who excused it and why on every push.
- The step refuses again on the `until` date. An entry with no `until` is ignored, so no skip is permanent.
- Agents cannot write the file; only a person can grant an exception.
- `--no-verify` stays forbidden: it turns everything off and records nothing.

### 4.8 A project's own hooks are never switched off

Pointing `core.hooksPath` at `.githooks` would silently disable hooks a project already had (for example a `gitleaks` secret scan). So:

- `adopt.py` records the previous hooks path in `.coast/previous-hooks-path`. If git's own hooks directory (`git rev-parse --git-path hooks`) holds executables, that is recorded.
- Each shipped hook runs the project's hook of the same name after its own checks pass, with the same arguments and the same stdin. An executable hook runs as itself.
- The report names any npm `prepare` script that would reset `core.hooksPath` on the next install, and which word to change.

### 4.9 One gate at a time per checkout

Two pushes running in the same working tree interfere: their builds cross, and the slower push loses the ref race after a long run. So `pre-push`:

- Takes a lock directory named `coast-push.lock` in the common git dir. `mkdir` is atomic. The lock's age is the directory's own mtime, and a lock older than an hour is broken.
- Prints `gate: another push is running in this checkout — waiting for it to finish` while it waits.
- After waiting, re-fetches. If the remote moved and the branch does not contain it, it says so at once instead of building.
- Releases the lock on exit, including Ctrl-C.
- Takes no lock for a `--seat` or `--measure` run.

## 5. Every rule, its bin, its check

Ids are the platform documents' ids where one exists. DRY, L and DES rules have ids in the platform documents. Other rules in the numbered files are named by a slug of their bold title. "all" means every app platform. Severity is `block` unless marked `ratchet` or `advisory`.

### 5.1 Machine — the scanner (`scan:<id>`)

Per-platform patterns live in `rules_signatures.json`. This table summarises them.

| Signature id | Rule(s) | What it matches | Scope |
|---|---|---|---|
| `ui-string-literal` | 00 §2, L-1 | Swift: a text literal in `Text(`, `Label(`, `Button(`, `.navigationTitle(`, `.alert(`, `Toggle(`, `TextField(`, `accessibilityLabel(`, and bare literals in view paths, skipping SF Symbol names, identifiers, URLs and comparisons. Kotlin/Compose: `Text("…")`, `text =`, `contentDescription =`, `title =`, `label =`; XML `android:text`. TSX/JSX: text between tags and `title=`, `placeholder=`, `aria-label=`, `alt=`, `label=`. Python: user-facing strings in responses outside the messages module (OBS-4). Built-in (`literals.py`). | Added lines; `ui`/`ui_lib` classes; excludes strings, tests, generated |
| `styling-literal` | 00 §1, 05 tokens | Swift: `Color(red:`, `Color(hex`, `Color(.sRGB`, `#RRGGBB`, `.font(.system(size:`, literal `.fontWeight(`. Kotlin: `Color(0x…`, `fontSize = <n>`. TS/CSS: hex colours, `fontSize: <n>`, `color: "…"`, raw CSS colours outside the theme. Colours and font sizes. | Added lines; all but the theme file and tests |
| `spacing-literal` | DRY-2, DES-1 | The spacing half of styling: `.padding(<n>)`, `.frame(width: <n>`, `spacing: <n>`, `cornerRadius(<n>)`; Kotlin `<n>.dp`; TS/CSS `padding`, `margin`, `gap`, `borderRadius`. `ratchet`. | Added lines; all but the theme file and tests |
| `second-theme-file` | 00 §1, 05 | A theme-shaped file (`*Theme.swift`, `theme.ts`, `tokens.*`, `Color+*.swift`, `Colors.kt`) outside the bound theme path. Once per file. | Whole tree |
| `env-literal` | 00 §2d, C-5 / ARCH-8 | `"main"`/`"master"`/`origin/main` as a ref, `/Users/` or `/home/` paths, `localhost:<port>`, hardcoded hosts outside the config home, plan or tier names, `Bundle.main.path` fallbacks. | Added lines; excludes `config_home`, tests |
| `secret-literal` | SEC-4, ENG-6/SEC-7, 00 §4 | `sk-ant-`, `AKIA…`, `ghp_`, `xox[bp]-`, `-----BEGIN … PRIVATE KEY`, `password = "`, `apiKey = "` with a real-looking value. Environment references are not secrets. | Added lines; whole tree at first adoption |
| `secret-file` | SEC-4, 00 §4 | Grouped with `secret-literal`. An added file shaped like a secret or data: `.env*` (except `.env.example`), `*.p8`, `*.p12`, `*.pem`, `*.key`, `*.sqlite`, `*.db`, `*.mobileprovision`, `*.jks`, `*.keystore`. Built-in, judged from git's added/renamed/copied status, so binary files are caught. | Added files |
| `plaintext-http` | SEC-1 | `http://` not to `localhost`/`127.0.0.1` (XML namespaces excused); Android `usesCleartextTraffic="true"`; iOS `NSAllowsArbitraryLoads` true. Built-in; reads the whole file so a flipped plist value is caught. | Added lines |
| `raw-html` | SEC-3 | Web: `innerHTML`, `dangerouslySetInnerHTML`, `document.write`, `v-html`. iOS/macOS: `loadHTMLString`, HTML attributed strings. Android: `Html.fromHtml`, `loadData`. RN: a `WebView` given a variable as `html:`. Python: `mark_safe`, `Markup`, `\|safe`, `render_template_string`. | Added lines |
| `dangerous-eval` | Web SEC, Python SEC-5 | `eval(`, `new Function(`, `exec(`, `pickle.load`, `yaml.load(` without `SafeLoader`. | Added lines |
| `shell-injection` | Python SEC-4 | `shell=True`, `os.system(`, `os.popen(`. | Added lines |
| `exported-component` | Android SEC-6 | `android:exported="true"` without `android:permission`; the launcher activity is excused. Built-in; reads the whole manifest. | Added lines in manifests |
| `sql-string-assembly` | SEC-2 / SEC-3 | Interpolation or concatenation inside a SQL string, per language. | Added lines |
| `cdn-script` | 03 supply chain | `<script src="https://…">` anywhere, including inside a code string. | Added lines |
| `blocking-call` | ENG-3, ASYNC-1 | Swift: semaphores, `sleep`, `Thread.sleep`, `RunLoop.run`. Kotlin: `runBlocking`, `Thread.sleep`, `CountDownLatch`. JS: busy waits, sync XHR, and on the web `alert`/`confirm`/`prompt`. Python: a blocking call inside `async def` (built-in, `async_blocking.py`). | Added lines; UI/feature paths |
| `layer-import` | A-1 | A data framework (`CoreData`, `SwiftData`, `GRDB`, `Room`, `prisma`, `supabase-js`) imported into view code. Member `viewmodel-ui-import`: a UI toolkit imported into a `*ViewModel`. Python: database imports or `.execute(` in routes/handlers. | Added lines |
| `destructive-default-key` | MAC-6, 05 | SwiftUI `role: .destructive` wired to `.defaultAction`; Compose `onDone`, RN `onSubmitEditing`, web `onSubmit`/`autoFocus` firing a delete. | Added lines |
| `manual-plural` | L-5 | A `count == 1` check choosing words. | Added lines; UI paths |
| `ui-string-concat` | L-4 | A string with a space concatenated with a value; Swift interpolation in a `LocalizedStringKey`. | Added lines; UI paths |
| `baked-case` | L-12 | `uppercased`, `capitalized`, `toUpperCase`, CSS `text-transform` on display text. Comparisons and sorts excused. | Added lines; UI paths |
| `one-catalog-per-locale` | L-2 | A catalog outside the bound `strings` class or beside the platform's one. iOS: only `Localizable`, `InfoPlist`, `AppShortcuts` catalogs, no legacy `.lproj` tables. Android: one `strings.xml` per `values*`. Web/RN: one file per locale folder. | Whole tree |
| `english-key` | L-3 | A catalog key with a space or sentence punctuation. Dotted keys are fine. | Added lines in catalogs |
| `fixed-text-size` | ACC-4 | Fixed point, dp or px text sizes; RN `allowFontScaling={false}`. | Added lines |
| `fixed-screen-size` | ENG-2 | Three-digit `width`/`height`, `Dimensions.get` as fixed layout, page-scale CSS widths. `advisory`. | Added lines |
| `pii-in-log` | PRIV-3 | A log call (`print(`, `console.log(`, `Log.d(`, `logger.`) naming email, password, token, phone, address, card, and similar. Matches within a window of 8 lines. `ratchet`. | Added lines |
| `test-criterion-tag` | TEST-1 | A test whose declaration, the three lines above it, and its first body line name neither `AC-<n>` nor "criterion". Built-in (`test_criteria.py`), every test language. | Added lines in tests |
| `hermetic-test` | TEST-2 | A live host, `URLSession.shared`, `fetch("http`, `requests.get`, `OkHttpClient()`, `axios` in a test file without a `LIVE_TESTS` guard on the line. | Added lines in tests |
| `test-weakened` | 06 test changes | Skips, disables, `.only`, empty assertions, wide tolerances. | Added lines in tests |
| `native-pattern` | A-5, A-7 | Coast's native-patterns lists, folded in unchanged (same ids, patterns, paired rule, `Tests/` exemption). Python adds `hand-rolled-password-hash`, `hand-rolled-query-parse`, `hand-rolled-arg-parse`. | Added lines |
| `import-matrix` | A-2 | Built-in (`import_matrix.py`): module-layer import rules, including multi-line TypeScript imports. Project module kinds in `.coast/module-kinds.json`. | Whole tree |
| `doc-comments` | DOC-1, Python STYLE-4 | Every public declaration has a doc comment (section 6, E1.5). Built-in (`check_doc_comments.py`). | Added lines; whole-tree count is advisory at push |
| `type-size` | A-3, 02 granularity | A Swift, Kotlin or Python type over 300 lines, or any file over 400, reported once at the first added line inside it. Built-in (`type_size.py`). `advisory`. | Added lines |
| `inline-comment` | 02 naming | A comment trailing code on the same line (URLs in strings excused). `ratchet`. | Added lines |
| `money-float` | PAY-1, Python DATA-3 | A money-named field (`price`, `amount`, `total`, `cost`, `fee`, `balance`) typed `Double`, `Float`, `number` or `float`. Names in cents or minor units excused. `advisory`; the reviewer judges. | Added lines |
| `retired-wording` | 01 truth | Retired words (by default "guarantee"; the config adds more) in source, catalogs, Markdown and templates. | Added lines |
| `unreached-view` | 08 | Built-in (`unreached_views.py`): a public view or component type with no construction site on a shipping route. Debug galleries, previews and tests (the `gallery` class) do not count. A view deliberately not mounted yet is declared in code with a doc-comment tag, e.g. `/// not-mounted-yet: <task>`. | See `unreached_views.py` |

### 5.2 Machine — the platform's linter (`swiftlint:<rule>`, `eslint:<rule>`, `detekt:<rule>`, `androidlint:<id>`, `tsc:strict`)

| Rule | Check | Config |
|---|---|---|
| C-3 iOS/macOS | `swiftlint:force_unwrapping`, `force_try`, `force_cast` | `force_unwrapping` opted in |
| C-4 iOS/macOS | SwiftLint strict, `swift-format lint --strict` | — |
| C-3 Android | `detekt:UnsafeCallOnNullableType` | `detekt.yml` shipped |
| C-4 Android | `ktlint`, `detekt`, `androidlint` | `./gradlew lint` in the toolchain |
| Strings in Android XML | `androidlint:HardcodedText` (error) | `lint.xml` shipped |
| C-1 Web/RN | `tsc:strict` (`strict: true`, `noImplicitAny`) | `tsconfig.seed.json` |
| C-2 Web/RN | `eslint:react-hooks/rules-of-hooks`, `exhaustive-deps` | `eslint-plugin-react-hooks` |
| C-3 Web/RN | `eslint:@typescript-eslint/no-floating-promises` | `recommended-type-checked` + `projectService` |
| A-3 (advisory) | `swiftlint:type_body_length` 300, `file_length`; detekt `LargeClass`; ESLint `max-lines` | Warnings only |
| STYLE-1 Python | `ruff`, `mypy --strict` | `ruff.toml`, `mypy.ini` |

### 5.3 Machine — a tool (`tool:<name>`)

| Rule | Check |
|---|---|
| 00 §1 duplicated logic, 02 DRY, PAY-3 recomputation | `tool:jscpd`: `jscpd . --min-tokens 50 --baseline .coast/jscpd-baseline.json --fail-on-new-clones` in the pre-push hook. After the baseline's deadline it runs with `--exit-code`, so any clone refuses. |
| 00 §4 data never in version control, 07 secret scan before first push | `scan:secret-literal` on every push; a full scan of tracked files at first adoption (`adopt.py`). |
| 07 protected main | `tool:gh-ruleset`: read-only through `gh api`. Requires an active ruleset on the default branch with `pull_request`, `deletion`, `non_fast_forward` and no bypass actors. Prints a note when `gh` is absent or offline. |
| 02 zero new warnings, C-4 | `tool:warnings-as-errors`: build with warnings as errors (`-warnings-as-errors`, `allWarningsAsErrors`, `tsc` errors), or the tool ratchet (section 4.2). |

### 5.4 Session (`session:<id>`) — the Claude Code hooks and git hooks in §4.4

`governing-edit`, `chained-cd`, `infra-command`, `no-verify`, `force-push`, `scan-at-commit`, `scan-on-edit`, `unpushed-at-stop`, `rules-at-start`, and `attribution-trailer` (the `commit-msg` hook's model trailer, required by rules/09).

### 5.5 Review (`review`) — per-rule rows with evidence, nothing else

These rules need judgment:

- A-4 speculative abstraction; A-6 honest naming.
- PAY-1/2 (the `money-float` scan is advisory only); PAY-3 one computation site (jscpd catches copies; the reviewer judges near-copies).
- AUTH-1..4; PRIV-1/2/4/5; SEC-5/8 error wording; UGC-1.
- ACC-1 contrast (could later be computed from theme tokens); ACC-2 target size; ACC-3/5.
- ENG-1 reactive state; ENG-4 lifetimes; ENG-5 typed errors.
- TEST-3 assertion strength; TEST-4/5 fixtures; DOC-2 docs match code.
- 00 §1 components created once, cross-cutting code in one place; 00 §2b simple and elegant; 00 §5 never invent domain logic.
- 05 reading mocks, copy voice, status colour; 02 layering beyond imports.
- Python ARCH/API/OBS/DATA rules about design.

Each review returns a row per rule with `touched`, `verdict` and `evidence`. The harness rejects `touched: false` when the rule's `applies_to` classes intersect the diff. That makes "I checked" a claim that can be proven false.

### 5.6 Process — held by Coast's pipeline or by a human, named as such

Tests first (Coast orders it; a git hook can only warn), two PRs per feature, the owner as the final QA gate on every release, one subscription layer for every app, marketing published only on the owner's go, primary sources first. These carry `[check: process]` so the count includes them.

## 6. The build plan

This section is the build history and the remaining work. Each task is DONE only with its guard named and a reviewer's confirmation from the code. Sizes: S under half a day, M a day, L two or more.

Order from 2026-09-07: E2.7 → E2.8 … E2.12 → E5.1 … E5.7 → E6 → E7. Phase E3 is Coast's half and runs in Coast's repo. E4 is filed for later.

### Phase E0 — the honest starting line (this repo)

| Task | What | Size | Guard |
|---|---|---|---|
| E0.1 | **DONE 2026-09-04.** `verify_rules.py`: parses every rule, requires a `check:` tag, resolves tags against `battery.json`, prints enforced/total. Starting point: 0 of 558 rules enforced. | M | 48 tests in `enforcement/checks/tests/` (every grammar form, config reader and bin; the real corpus against the baseline) |
| E0.2 | **DONE 2026-09-04.** Tagged every rule in the platform documents and numbered files with its bin and check (version stamp 8). Rule content unchanged. | M | The verifier reports no untagged rule and no unknown check |
| E0.3 | **DONE 2026-09-04.** Moved the DRY, localization and design-token rules into every app platform document as DRY-1..7, L-1..12 and DES-1..4. 00 §1, 04 and 05 now point at those ids. | M | `tests/test_corpus_sections.py` |

### Phase E1 — the scanner (this repo)

| Task | What | Size | Guard |
|---|---|---|---|
| E1.1 | **DONE 2026-09-04.** `check_rules.py`: all modes, path classes, severities, the ratchet baseline, both exception files, the FAIL output format. Folded in Coast's native-patterns lists and import matrix unchanged. | L | `tests/test_check_rules.py` (a synthetic git repo: every mode, exception and ratchet direction); plants in `tests/plants/<platform>/<id>.{fail,pass}.<ext>` |
| E1.2 | **DONE 2026-09-04.** Signatures wave 1: `ui-string-literal`, `styling-literal`, `spacing-literal`, `second-theme-file`, `env-literal`, `secret-literal`/`secret-file`, on all six platforms. Added `.coast/paths.json` and `--paths-override`. `ui-string-literal` matches Coast's copy guard exactly (zero on the guard's own folders). | L | Plants; counts on Coast and three app repos became the first baselines |
| E1.3 | **DONE 2026-09-04.** Signatures wave 2: `plaintext-http`, `raw-html`, `dangerous-eval`, `shell-injection`, `exported-component`, `sql-string-assembly`, `cdn-script`, `blocking-call`, `layer-import`, `destructive-default-key`, and the Python native-pattern group. 84 of 643 enforced. | M | 141 plants, both directions |
| E1.4 | **DONE 2026-09-04.** Signatures wave 3: localization, accessibility, test, logging, comment, wording, type-size and money signatures (section 5.1). 138 of 643 enforced. | M | 225 plants, both directions |
| E1.5 | **DONE 2026-09-04.** `check_doc_comments.py`: Coast's Swift doc-comment scanner ported line for line (public by modifier, protocol or extension membership; extensions folded per module; `--files` reads the whole module), plus Kotlin/Java, TypeScript and Python. Also the `doc-comments` built-in signature. 156 of 643 enforced. | S | 12 plants; Coast's parity test |
| E1.5 parity | **DONE 2026-09-04.** `DocCommentParityTests` in Coast confirmed both implementations report the same 8,801 undocumented declarations on Coast's tree. | — | `DocCommentParityTests` (Coast) |
| E1.6 | **DONE 2026-09-04.** The linter configs in `enforcement/lint/` with the opt-ins in section 5.2, each checked against the linter's own docs. | S | `tests/test_lint_configs.py`: every config `battery.json` names exists, and every linter tag in the corpus is enabled in the shipped config |
| E1.7 | **DONE 2026-09-04.** jscpd 5.1.2 pinned in `enforcement/TOOLCHAIN.md`; the jscpd step of the pre-push hook (section 5.3). `adopt.py` writes `.coast/jscpd-baseline.json` (fingerprints plus clone count, `written`, `by`, `deadline`, `moves`); without jscpd it records `"clones": null` and the step refuses. | S | `tests/test_hooks_and_adopt.py`: a copied block fails, a clean tree passes; the test fails if jscpd is not installed (`JSCPD_BIN` or PATH) |

### Phase E2 — the session layer and adoption (this repo, then the owner's repos)

| Task | What | Size | Guard |
|---|---|---|---|
| E2.1 | **DONE 2026-09-04.** `claude-hook.py` and `claude-settings.json` with the nine hooks in section 4.4. Four hooks were met by a live session (`chained-cd`, `scan-at-commit`, `unpushed-at-stop`, and the git pre-commit hook); the rest are proven by fixture tests only. | M | `tests/test_claude_hooks.py` (every hook fed the documented stdin JSON in a fixture repo) |
| E2.2 | **DONE 2026-09-04.** The git hooks (`pre-commit`, `commit-msg`, `pre-push` with one switch per platform) and `adopt.py`. Every pre-push step prints `gate: <name>`; a missing tool is a refusal with its install line. `adopt.py` installs the checks and hooks (replaced on re-run), the lint starter files (kept once the owner edits them, tracked by checksum in `.coast/seeds.json`), `docs/domain-rules.md` (never replaced at the same version), `.coast/platform`, `.coast/standards-version`, both baselines, the marked block in `CLAUDE.md` from `TEMPLATE-PROJECT-CLAUDE.md`, `core.hooksPath`, and the first-adoption secret scan (findings exit 1). `--dry-run` writes nothing. | M | `tests/test_hooks_and_adopt.py`: adopting twice changes nothing, `--dry-run` writes nothing, owner text outside the block survives, edited seeds are kept, each hook refuses its cases |
| E2.3 | **DONE 2026-09-04.** Coast adopted (macOS), with project files for module kinds, path bindings and 11 exceptions. Coast's copy guard test was retired. Coast's own rules document: 25 of 81 enforced. | M | Coast's suite green through the new gate; scanner and guard both report zero on the guard's folders |
| E2.4 | **DONE 2026-09-04.** The owner's three iOS apps adopted, each pushed green through its own gate (24 of 74 each). This added the `tests-missing` baseline, newest-runtime simulator selection with a Designed-for-iPad fallback, and full-build warning counts. | S each | Each app's first push through its gate |
| E2.5 | **DONE 2026-09-04.** The repo README, `PROJECT-TYPES.md` and `TEMPLATE-CLAUDE.md` describe the layer and the adoption step. | S | verify_rules green; no doc names a check that does not run |

### Phase E2 — the review (2026-09-07, at the owner's request)

Three reviewers read the scanner, hooks and installer against this document and Anthropic's hooks reference. Each fix below has a test.

| Task | What | Size | Guard |
|---|---|---|---|
| E2.6 | **DONE 2026-09-07.** Fixed a list of defects: `--document` false gaps; `rules-at-start` reading the number from the CLAUDE.md block; the `if` prefix filter removed from `scan-at-commit`; more `no-verify` forms; push-lock age and Ctrl-C; commit-msg counting characters, not bytes; line numbering after `++` lines; the `pii-in-log` join window (8 lines); regex backtracking in `ui-string-concat`; `manual-plural` false hits; malformed baselines and negative counts as FAIL lines; non-ASCII paths; `adopt.py` without `npx`; a `scripts/` case-fold warning. Wrote `DEVELOPER-GUIDE.md`. | M | 155 tests green; verify-rules 170 of 643, open 0 |
| E2.7 | **DONE for three of four (release 1.1.0).** The three iOS apps were re-adopted with `adopt.py <repo> --release 1.1.0 --yes` and pushed green. Coast's re-adoption is committed locally, but its jscpd step refuses four clones in `Templates/throwaway/Scripts/checks/` that the old ignore list hid. **Waiting on the owner:** extract the shared code, add the folder to `layout.jscpd_ignore` in the project config, or excuse the `jscpd` step with a date. | S each | Each repo's `.coast/standards-version` at head; its first push green |
| E2.8 | **DONE 2026-09-07.** Closed Bash bypasses of the session hooks (`sh -c`, line continuations, `VAR=` prefixes, `env`/`xargs`/`npx` wrappers, `$(…)`, `pushd`, `if cd`). `infra-command` allows read-only forms. Settings gained `permissions.deny` and `"disableAllHooks": false`; `adopt.py` merges them. `.claude/settings.local.json` is always governing. | M | `test_claude_hooks.py` (`BashBypasses`, `ChainedCd`, `InfraCommand`, `SettingsFile`); `test_hooks_and_adopt.py` (deny-rule merge) |
| E2.9 | **DONE 2026-09-07.** Doc-comment scanners fixed: Python now uses `ast` (nesting, `@overload`, setters, trailing comments); TypeScript handles multi-line decorators, all string quote styles, and a blank line breaks a doc comment. | M | `plants/web/doc-comments.*.tsx`, `plants/python/doc-comments.*.py`, `tests/test_doc_comments.py` |
| E2.10 | **DONE 2026-09-07.** Push-path correctness: `secret-file`, `plaintext-http` and `exported-component` became built-ins; diffs use `-M` so renames are not re-judged; built-ins read the index or commit blob via `git show`; the tree pass runs once per push; an undated baseline entry fails. | M | `PushPathCorrectnessTests` in `test_check_rules.py`; the related plants |
| E2.11 | **DONE 2026-09-07.** Web precision: `literals.py` no longer flags comparisons, arrows, generic closes or named-import lines in TSX; `one-catalog-per-locale` on web/RN respects the `strings` class; the import matrix reads multi-line imports; the ESLint config loads the hooks plugin only if installed; `tsconfig.seed.json` is a complete starter (installed as `tsconfig.json` only when none exists; the push hook reads `strict` from `tsconfig.json` and does not follow `extends`). On a real web project, all 40 remaining `ui-string-literal` hits were real. Open: iOS/macOS still block a legacy `<locale>.lproj/Localizable.strings` pair (add `**/Localizable.strings` to their `files_excluded`). | M | `test_check_rules.WebPrecisionTests`; web plants; `test_lint_configs` |
| E2.12 | **DONE 2026-09-07.** Installer edges: the CLAUDE.md marker rewrite refuses anything but one begin/end pair; git's own hooks directory is recorded as previous hooks; executable previous hooks run as themselves; `pre-push` scans each pushed sha from stdin; commit-msg accepts `#123` subjects and git's merge/revert messages; `.coast/installed.json` lets a re-run remove files a release stopped shipping; `detect_platform` reads `.pbxproj`. | M | Six tests in `test_hooks_and_adopt.py` |

### Phase E3 — inside Coast (Coast repo; its task numbers in Coast's plan)

| Task | What | Size |
|---|---|---|
| E3.1 | Carry `enforcement/` in `Templates/`, pinned, with a parity test. Coast's shipped checks gain the scanner, doc-comments, signatures and `paths.json`; Coast's path classes read `paths.json`. | M |
| E3.2 | Coast's gate runner, git hook, `coast-gates.yml` and in-loop check run the scanner (worktree mode in the loop) and jscpd on PRs. Delete the Swift `doc-comments` check. | M |
| E3.3 | The coding agent, every specialist and the planner receive the rules document split by bin; the general reviewer receives it too. | S |
| E3.4 | Per-rule review rows in `review_agent.py` and the local review: schema and validation (section 4.5). Machine-held rules carry the scanner's result. | M |
| E3.5 | Builder self-reports carry no weight: every reader of `submit_work` text now reads check output or reviewer rows. Guard: a test that the coder's report cannot change any verdict. | M |
| E3.6 | Fix tickets carry a `guard` field; done requires the fix diff to touch it. | S |
| E3.7 | The Rules tab shows "enforced by a check: N of M", each ratchet's count and deadline, and the review-only rules. Settings' rules update delivers the checks with the documents. | M |
| E3.8 | Android and web toolchain rows: detekt, `gradlew lint`, type-checked ESLint, jscpd, installed through Coast's required-programs table. | M |
| E3.9 | A review `fail` on a rule a machine could hold files a "make this a signature" task automatically. | S |

### Phase E4 — later, filed so it is not lost

- ACC-1 contrast computed from the theme tokens.
- Semgrep, if a rule ever needs syntax awareness (section 3).
- A reviewer-outcome log per rule id, to find a reviewer that is consistently wrong on one rule (rules/07 asks for it).
- Compose `Text("literal")` as an Android Lint custom check, if the scanner's Kotlin precision is not enough.
- **E4.5 — DONE 2026-09-15 (release 1.4.0).** The unreached-view check (section 5.1): `unreached_views.py`, the `gallery` path class and rules/08's new section, with 13 tests. A feature flag counts as a route when the flag is declared and its off state is named.

### Phase E5 — the config: every rule, seat and hook behind a switch, and the names out of the code (2026-09-07)

Goal: every signature, pre-push step, session hook and linter can be switched off per project, and owner and product names come from config. One constraint: a rule switched off must show in the "N of M" number, or the number is false.

| Task | What | Size | Guard |
|---|---|---|---|
| E5.1 | **DONE 2026-09-08 (release 1.1.0).** One table for the layout, `enforcement/checks/layout.json` (section 4). The checks and session hook moved under `.coast/`, which removes the `Scripts/`-vs-`scripts/` case-fold clash. `adopt.py` renders `.coast/layout.sh` for the shell hooks and renders `claude-settings.json` from `{key}` placeholders. A re-adopt moves an older project's files. | M | A test greps every shipped file for the old literals; the case-fold test passes on a project with `scripts/` |
| E5.2 | **DONE 2026-09-07.** `rules_signatures.json` is one row per signature with per-platform fields under `platforms` (66 rows, 237 platform entries). `flatten_signatures` / `load_signature_tables` are the one reader. | M | `SignatureTableShapeTests` in `test_check_rules.py`; every plant still passes both directions |
| E5.3 | **DONE 2026-09-08 (release 1.1.0).** The project config (below). `adopt.py` writes it from `config.default.json`; `config.py` merges it over the defaults on every read and is used by the scanner, verifier, installer and hooks (the git hooks run `config.py --sh` on every run, so edits apply without re-installing). | M | `test_config.py`: an `off` signature produces no hit; an `off` step prints `gate: <name> OFF (config)` and runs nothing; an `off` session hook exits 0 with a note; a raised severity is refused |
| E5.4 | **DONE 2026-09-08 (release 1.1.0).** The `off` bin in `verify_rules.py` and everywhere the number is printed; `--config <file>`. The headline reads, for example, "rules enforced by a check 21 of 74 (3 switched off)". | S | `test_verify_rules.py`: the number falls by exactly the rules switched off |
| E5.5 | **DONE 2026-09-08 (release 1.1.0).** Refusal text, templates, lint headers, temp-file names and examples read `owner.name` / `owner.product` from the config and fall back to general words ("the founder", "this project", "the standards"). "Coast" stays where it names the product (`.coast/`, `coast-standards-release`, the CLAUDE.md block title). `adopt.py --owner "Pat Lee" --product "Example App"` fills them in. | S | A test greps every shipped file for the configured names |
| E5.6 | **DONE 2026-09-08 (release 1.1.0).** `adopt.py --init` (or a first adoption with no config) asks the on/off questions once, one screen per group, and writes `.coast/config.json`. `--yes` takes every default; every default is on. | S | A scripted answer file drives the prompt; `--yes` writes the default config exactly |
| E5.7 | **DONE 2026-09-08 (release 1.1.0).** Docs: `DEVELOPER-GUIDE.md` "Configuration", this document's section 4, and the README's adoption question screen. | S | verify_rules green; no doc names a path the layout table does not |

**The project config**, `.coast/config.json`. Agents may not edit it, so an agent cannot switch a rule off.

```
{"version": 1,
 "owner": {"name": "", "product": "", "org": ""},
 "rules": {"off": [ids], "severity": {id: "block"|"ratchet"|"advisory"}, "retired_words": [...]},
 "seats": {"off": [names]},
 "session_hooks": {"off": [ids]},
 "linters": {"off": [names]},
 "ratchet_days": 90,
 "layout": {…overrides of layout.json…}}
```

- An `off` entry is the whole switch: the scanner skips the signature, the hook skips the step or session hook, and the verifier counts the rule as `off`.
- Severity may only move down (block → ratchet → advisory). Raising it is the signature table's job.
- `rules-exceptions.json` is separate: an exception is dated and per path; a switch is neither.

### Phase E6 — the name: **Coast Standards** (2026-09-07)

| Task | What | Size | Guard |
|---|---|---|---|
| E6.1 | **DONE 2026-09-07.** Repo renamed to `coast-standards` with `gh repo rename` (GitHub redirects the old name; never create a repo under the old name). Local clone moved; the organisation is unchanged. | S | `git fetch` from the new remote; `gh repo view` on the new name |
| E6.2 | **DONE 2026-09-07.** The old name replaced in 22 files across this repo, the owner's config and the adopted repos. Transcripts, worktree copies and the old CLAUDE.md block markers were left; the installer recognised both marker spellings for one release. | S | A grep for the old name finds only history, transcripts and the markers |
| E6.3 | **DONE 2026-09-08 (release 1.1.0).** The CLAUDE.md block title reads "Coast Standards — the standing rules, enforced by machines where a machine can hold them". | S | verify_rules green |

### Phase E7 — releases, per-repo copies, and one thin skill (after E5; decided 2026-09-07)

Not a plugin: a plugin would sit in every chat, and every project has different rules. Each repository holds its own copy at a pinned release. The only global piece is a thin skill that says where to fetch from and how to run the installer.

| Task | What | Size | Guard |
|---|---|---|---|
| E7.1 | **DONE 2026-09-07 (release 1.0.0).** Semantic versions and releases (section 4.6). `adopt.py` records the release in `.coast/standards-version` and prints "installed Coast Standards <version>". | S | A tag builds a GitHub release with the changelog entry; the project's version file holds the tag |
| E7.2 | **DONE 2026-09-07 (release 1.0.0).** `adopt.py` fetches a named release tarball into a cache and installs from it (`--release <version>` or `--release latest`), so no clone is needed. A clone still works. | M | A project adopts from a tarball with no clone; a newer version upgrades and keeps edits |
| E7.3 | **DONE 2026-09-07 (release 1.0.0).** One `SKILL.md`: where the releases are, the command to adopt or upgrade, and the instruction to run the dry run first and ask the user the few real questions (platform, theme file, owner name, any check the project cannot run yet). Nothing else. | S | The skill's steps run end to end on a fixture from an empty machine |
| E7.4 | **DONE 2026-09-07 (release 1.0.0).** Docs: the quickstart installs a release; the options page shows the version file; the developer guide has a release checklist. | S | A fresh Mac follows the README to a first green push |

### Phase E8 — the battery runs on what changed (2026-09-09, at the owner's request)

Checks run only when code changes, and only on the changed code and what depends on it. The pre-push hook first works out what the push changed, then each step runs on nothing, the changed files, the affected modules, or everything.

**What changed** (`enforcement/checks/scope.py`): the paths in every pushed range, classified with `paths.json` (including the project's own bindings).

| Kind | When | What runs |
|---|---|---|
| `none` | Every path is in a `not_code_classes` class (`docs`, `plans`, `design_bundle`, `generated`, `git`) or has a `prose_extensions` extension (`.md`, `.txt`, …) | Every code step prints `gate: <name> SKIPPED — no code changed (…)`. Only the diff scan, `gh-ruleset` and the project's own hooks run. |
| `files` | Code changed | File-list steps run on the changed files; module steps on the affected modules. |
| `all` | A `full_run_classes` path changed (`governing`, `manifest`: a check, config, linter starter, baseline or package manifest), a code file no module owns, or `COAST_SCOPE=all` (`<env_prefix>SCOPE`) is set | Everything. |

**How each step is scoped**

- **Tests (SwiftPM):** `swift package describe` maps each changed file to its target. The affected set is those targets and every target that depends on them. The test step runs their test targets (`swift test --filter`) and says so when none depends on the change. An Xcode-project app has no readable graph, so its build and tests run whole when code changed.
- **Build:** rebuilds only the affected targets under the warnings ratchet. The baseline entry carries a per-file map, `files` (written by `adopt.py --measure-tools`), and the count over the rebuilt files may not rise against those files' baseline. `lint-findings` and `format-findings` are judged the same way. An entry without the map runs the step whole and prints the re-measure command that enables scoping.
- **Lint and format:** run on the changed files (`swiftlint --force-exclude` keeps the config's excludes). Xcode projects are file-scoped too.
- **jscpd, the whole-tree scan and the doc-comment count:** run whenever code changed (a clone can pair a changed file with an unchanged one), and not otherwise.
- **`gh-ruleset`:** about the repository, so it runs on every push.
- **Other platforms:** Gradle modules, npm workspaces and Python's import graph limit build and tests; eslint, prettier, ruff and ktlint read the changed files; jest and vitest run the tests related to the changed files.

| Task | What | Size | Guard |
|---|---|---|---|
| E8.1 | **DONE 2026-09-09 (release 1.2.0).** `scope.py`: changed paths, the three kinds, the SwiftPM graph and affected set, the test filter. Prints shell assignments the hook `eval`s and writes the file lists the steps take. `paths.json` gains `prose_extensions`. | M | `tests/test_scope.py`: docs-only is `none`; a source file is `files` with its dependents; a manifest, governing or unowned file is `all`; the environment variable forces `all`; a synthetic graph proves the closure |
| E8.2 | **DONE 2026-09-09 (release 1.2.0).** `pre-push`: ranges computed once; every code step gated by the kind; the Swift build rebuilds affected targets; tests filtered; lint and format on changed files. | M | `test_hooks_and_adopt.py`: a docs-only push skips code steps; a scoped push judges only its files; a new warning in a changed file refuses while old warnings elsewhere do not |
| E8.3 | **DONE 2026-09-09 (release 1.2.0).** `check_rules.py`: one reader for tools' `file:line:col: warning\|error:` lines; `--ratchet ID --log <log> [--measured <listing>]`; `--measure ID --log <log>` (prints `MEASURE` and `MEASURE-FILE`); `--has-baseline ID --per-file`. | S | `test_check_rules.py`: the per-file judgment both ways; a file missing from the map counts as zero; no map means no scoped judgment |
| E8.4 | **DONE 2026-09-09 (release 1.2.0).** `adopt.py --measure-tools` writes the per-file map. A lower or equal total replaces the map; a rise leaves the entry unchanged. | S | `test_hooks_and_adopt.py` |
| E8.5 | **DONE 2026-09-09 (release 1.2.0).** Docs: rules/07, the README, the project `CLAUDE.md` template, how-it-works, options (`SCOPE`, the `files` map), the developer guide, CHANGELOG 1.2.0. | S | verify_rules green; the site builds |
| E8.6 | **DONE 2026-09-09 (release 1.3.0).** Module graphs for Gradle (`settings.gradle[.kts]`, `project(':x')`; `:m:build`, `:m:test`), npm workspaces (`npm test -w`) and Python (imports resolved to files; `pytest`/`unittest` on the reached test files). `jest --findRelatedTests` and `vitest related` on changed files; ktlint on changed files. | M | `test_scope.py` (each graph); `test_hooks_and_adopt.py` (Android, web and Python scoped pushes) |

## 7. The decisions

All decided on 2026-09-04, as recommended. A session builds these; it does not re-ask them.

1. **The scanner is plain Python with per-platform signature tables.** Every rule a machine holds today is a literal in the wrong file, which line matching scoped by file kind holds precisely, with nothing to install. Semgrep is deferred until a rule needs syntax awareness (section 3).
2. **Existing repos adopt with ratchet baselines, and every baseline has a deadline.** No rewrite on adoption; counts may only fall or stay flat. When the deadline passes, the check changes from ratchet to block, so no repo can sit on its debt forever. The default deadline is 90 days after the baseline is written (`ratchet_days` in the config). Lowering a count does not reset it. Only a person moves a date, and the move is recorded in the baseline file with who and why. The Rules tab and the session-start context show both the count and the date.
3. **The Claude Code hooks are committed in every repo's `.claude/settings.json`.** They refuse edits to check files, chained `cd`, infrastructure commands, `--no-verify`, force pushes, and ending a turn with unpushed commits. The same file carries `permissions.deny` rules and `"disableAllHooks": false`.
4. **This repo is the one home; Coast carries a pinned copy.** A founder's Mac has no standards repo, so Coast ships its own copy, locked to one version by checksum. A Coast test fails if the copy differs.
5. **The build order is E0 → E1 → Coast's own adoption (E2.3) → the owner's apps (E2.4) → Coast's customer-facing half (E3).** Coast does not ship the scanner to customers before it is proven on Coast's own code.
6. **The enforced number is shown from day one.** Each project's Rules tab shows "rules enforced by a check: N of M" and lists the rest as reviewer-judged, even while N is low.
7. **The design lives here only.** Coast's task list stays in Coast's plan folder, points here, and restates nothing.

## 8. Limits of this document

- **Verified** from the code and each tool's documentation on 2026-09-03: the state in section 1, the tool facts in section 3, and Coast's prompts, gate runner, hook and scaffold at that date.
- **Not verified:** Semgrep's free per-language coverage (not listed on a primary source). Signature precision on real code is measured by the plants and the ratchet baselines, not asserted here.
- **Built:** phases E0, E1, E2 (reviewed line by line on 2026-09-07), E5, E6, E7, E8 and E4.5. The layer is installed and proven on four real repositories: Coast's own repo and three iOS apps, each adopted and pushed through its own gate.
- **Not built:** phase E3 (Coast's customer-facing half) and the rest of E4 are design until their rows say DONE.
