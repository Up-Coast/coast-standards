# Rules enforcement — the design and the build plan

*Last updated: 2026-09-07*

Filed 2026-09-03, at the owner's request, after two weeks of session
agents reporting rules followed that were not followed. The owner's point:
these rules are not indeterminate checks, yet nothing protected them, and
an AI agent could not be trusted to catch them at review time when the
session agents had shown they decide on their own whether to pay attention
to a rule. The brief for this document: design a system that lets Coast
follow these rules, and others too; be the architect and research the best
thing to do.

**To start a session on this work, say:** *"Read
`enforcement/README.md` in the standards repo and build the next enforcement
task."* The user-facing manual for what is built is
[DEVELOPER-GUIDE.md](DEVELOPER-GUIDE.md); this document is the design and the plan. Every decision is taken (section 7) — a session
builds, it never re-asks. Each task's row in section 6 says DONE when it is,
with the date; the next task is the first row that does not. Coast's own
tasks wait until the scanner is proven on Coast's own code.

This is the ONE home for the design. Coast's own task list for its half
lives in the Coast repo's plan folder and points here; it never restates
the design.

## 1. The finding that started this (verified 2026-09-03, from the code)

The rules in this repo are enforced by almost nothing, anywhere.

| What was checked | What is true today |
|---|---|
| Coast's shipped iOS rules document (51 rules) | 3 are held by a script or linter (native patterns, SwiftLint standard set, import matrix). |
| The DRY rules — one theme file, one string catalog, one home per fact | In none of the five shipped platform documents. The priority-rules file that holds them never ships into a customer project. |
| Who reads the rules document inside Coast | Only the Domain-rules reviewer, after the work is built. The Coding agent's system prompt contains no rule. The general reviewer never sees the document. |
| The Domain-rules reviewer's prompt | "A diff that touches no rule's territory is a clean pass" — the exemption session agents have been granting themselves, written into the reviewer. |
| Rules that name a deterministic check | iOS C-3 names SwiftLint `force_unwrapping`, which is opt-in and not enabled in the shipped config. Web/RN C-3 names `no-floating-promises`, which needs the type-checked ESLint config; the shipped config is the plain one. Android C-3/C-4 name detekt; no detekt config ships. C-5 on every platform says "deterministic check: review greps the diff" — an instruction to a model, not a script. |
| Coast's own `doc-comments` check | Swift-only, inside the app's build loop; not in the shipped scripts, not in CI, not in the hook. A second kind of mirror. |
| The owner's own app repositories (three iOS apps) | No CLAUDE.md pointing at this repo, no linter config, no git hooks, no Claude Code hooks. Nothing enforces anything. |
| The user-level Claude Code settings | No hooks. |

What IS right and is the template for everything below: the native-patterns
checker (a per-platform signature list, a scan of added lines, fails the
push, exceptions only from the approved plan, agents cannot edit it), the
import-matrix checker, the proof verifier, the local gate battery that runs
the shipped scripts before every push and again in CI (one implementation),
the GOVERNING path class agents cannot write, and Coast's own copy guard
test that fails on any bare user-facing literal in a view.

## 2. The principle

A rule that lives only in a document is a request, and a request loses to
whatever is cheapest for the session in front of the code. The owner's
definition of done (2026-09-01) already says it: a task is done when the
guard that makes its rule unbreakable exists AND a reviewer confirms from
the code. This design applies that to every rule in this repo:

1. **Every rule is sorted into a bin, out loud, next to the rule.**
   - **machine** — a script or linter holds it and fails the push.
   - **ratchet** — a script counts it and fails the push when the count
     goes UP against a committed baseline (how an existing repo adopts a
     rule without a rewrite; the baseline only ever goes down).
   - **review** — only a mind can judge it; the reviewer answers per rule,
     with evidence, and the harness rejects a vacuous answer.
   - **session** — a rule about how the agent works (never chain `cd`,
     never touch infrastructure, push every commit); held by a hook on the
     agent's own tool calls.
2. **The rule and its check have one home, and the check is named in the
   rule.** A rule that names a check nothing runs is a failing test, not a
   footnote.
3. **The builder gets the machine's verdict in seconds, before anything
   leaves the machine.** Every machine and ratchet check runs on the touched
   files as they are edited, on the staged diff at commit, and as the full
   battery at push. CI confirms; it never discovers. Whether the builder
   "paid attention" stops mattering.
4. **Nothing the builder says is an input to any gate.** Only a check's
   output and a reviewer's evidenced rows count.
5. **Every miss grows the machine.** A bug a script could have caught adds a
   signature; a rule review kept catching adds a check. The number of rules
   a machine holds goes up over time, and the founder can see it.

## 3. What was considered, and what was chosen

Researched 2026-09-03 against each tool's own documentation (the research
notes: Claude Code hooks reference and guide; SwiftLint and swift-format
READMEs; ESLint docs and the two JSX-literal plugins; detekt, ktlint and
Android Lint docs; Semgrep docs, CLI reference and licenses; jscpd and PMD
CPD; pre-commit.com; Danger; Apple's build-settings reference; GitHub
rulesets).

| Option | Verdict | Why |
|---|---|---|
| **A stdlib-Python scanner with per-platform signature tables** (the native-patterns shape) | **CHOSEN — the engine for every custom rule** | Already the proven shape in Coast; runs wherever `python3` runs (a Mac with Xcode's command line tools, ubuntu CI); no install step; one implementation and one exception mechanism for all five platforms; one output format the battery already parses (`FAIL <check> <path>:<id>: <words>`). Regex over added lines, scoped by path class, is precise enough for every rule in §5 — the rules are about literals in the wrong file, not about program semantics. |
| **The platform's own linter with a shipped config** | **CHOSEN — for the rules it already holds natively** | SwiftLint (`force_unwrapping` enabled, `type_body_length` advisory), swift-format, ESLint with the type-checked typescript-eslint config (`no-floating-promises`) plus `eslint-plugin-react-hooks`, Prettier, ktlint, detekt (default set; `UnsafeCallOnNullableType` is on by default), Android Lint (`HardcodedText` for layout XML). These are AST-aware, IDE-integrated, and free. Custom rules are NOT written in linter config (SwiftLint `custom_rules`, ESLint virtual plugins) even though both allow it, because that would give one rule three homes across platforms; detekt and ktlint need a compiled JAR for custom rules anyway. |
| **jscpd v5** (MIT; one self-contained binary; Swift, Kotlin, TS/TSX, JS, Python, Dart; `--fail-on-new-clones` against a baseline) | **CHOSEN — for duplicate code** | Duplicate detection is real tokenised work a regex can't do. One extra binary, installed like SwiftLint through Coast's required-programs table. "No NEW clones" is exactly the ratchet shape. |
| **Semgrep** (LGPL-2.1 CLI; own YAML rules unrestricted; Swift/Kotlin/TS/JS/Python; `--baseline-commit`) | **NOT adopted now — filed as a deferred idea** | AST-aware and config-only, which would be the answer for Kotlin custom rules. But it is an install on every founder Mac and every CI runner, its per-language coverage in the free engine is not itemised on a primary source, and nothing in §5 needs an AST today. Revisit when a rule needs one the regex cannot hold. |
| **eslint-plugin-i18next / react/jsx-no-literals** for JSX text | Not adopted | Would give the strings rule a second home on two platforms. The scanner holds JSX text and the known text props. Revisit if precision proves insufficient. |
| **pre-commit framework** | Not adopted | Another runtime dependency; plain `.githooks/` + `core.hooksPath` is what Coast already installs and it needs nothing. |
| **Danger** | Not adopted | PR-time commentary; Coast's reviewer harness already owns that surface, deterministically. |
| **Claude Code hooks** (committed `.claude/settings.json`; `PreToolUse` exit 2 or `permissionDecision: deny` blocks a tool call in every permission mode, even `--dangerously-skip-permissions`; `Stop` can refuse to end the turn; `PostToolUse` shows stderr to the model; hooks can be gated with `"if": "Bash(git commit *)"`) | **CHOSEN — the session layer** | The only mechanism that makes a rule about the agent's own behaviour structural in a Claude Code session. Honoured by every session started at the repo root. Known limit: a user-level `disableAllHooks` turns them off — acceptable, it is the human's own machine. |
| Apple's string-catalog build settings | Not applicable | Verified: they are extraction switches, not warnings. Nothing from Apple warns on an unlocalized Swift literal. The scanner has to hold it. |
| Android Lint for Compose `Text("literal")` | No built-in check found | Lint's `HardcodedText` covers layout XML only. The scanner holds Compose. |

## 4. The architecture

```
coast-standards (this repo) — THE HOME
├── rules/…                       the prose, one rule per line, each with [check: …]
├── enforcement/
│   ├── README.md                 this design
│   ├── checks/
│   │   ├── check_rules.py        the scanner: signatures × path classes × diff
│   │   ├── check_doc_comments.py the doc-comment check (moved out of Coast's Swift)
│   │   ├── verify_rules.py       rule doc ↔ battery parity; the enforced/total number
│   │   ├── rules_signatures.json one row per signature: the shared fields once, each platform's
│   │   │                         globs and regex under platforms (ids match [check: …])
│   │   ├── paths.json            the path-class bindings per platform (theme, strings, UI, tests…)
│   │   └── tests/                one plant per signature (the native_patterns_smoke shape)
│   ├── lint/                     the shipped linter configs (swiftlint.yml with the opt-ins,
│   │                             eslint type-checked, detekt.yml, lint.xml, prettier, swift-format)
│   ├── hooks/
│   │   ├── pre-commit            scanner on the staged diff (seconds)
│   │   ├── pre-push              the full battery for the platform
│   │   ├── claude-settings.json  the Claude Code hooks (session layer)
│   │   └── claude-hook.py        the one entry the Claude hooks call
│   └── adopt.py                  installs all of the above into a project, idempotent
└── CHECKS-VERSION                the corpus + checks version stamp

consumers (each vendors enforcement/ byte-for-byte, pinned, with a parity test)
├── Coast → Templates/…           installs it as GOVERNING into every customer project;
│                                 GateBattery, GateHook and coast-gates.yml run it
├── Coast's own repo              dogfood: the same hooks, the same scanner
└── the adopting app repos        adopt.py, then the same hooks
```

One implementation of every check. The script the hook runs is the script
CI runs is the script Coast's battery runs. No Swift mirrors, no per-platform
re-implementation in linter config.

### 4.1 The rule registry lives in the rule documents

The markdown rule documents stay the founder-facing home (Coast's versioned,
founder-owned, three-way-merged `docs/domain-rules.md` depends on that).
Each rule line's trailing bracket becomes formal:

```
- **L-1** No hardcoded user-facing text … [Coast standard; check: scan:ui-string-literal]
- **C-3** No force-unwraps … [Swift practice; check: swiftlint:force_unwrapping]
- **A-4** No speculative abstraction … [YAGNI; check: review]
- **A-3** A type or module has one job … [SRP; check: ratchet:type-size]
```

`verify_rules.py` parses every rule in the platform documents and this
repo's numbered files and fails when: a rule has no `check:` tag; a tag
names a scanner id, linter rule, or tool that the platform's battery does
not run; a signature exists that no rule names. It prints the number:
`rules enforced by a check / rules total` per document. That test FAILS on
the corpus as it stands today. That is the honest starting line, and making
it pass is the first phase.

**Built (E0.1, 2026-09-04) — what the verifier reads.** The full grammar and
the resolution rules are the docstring of `enforcement/checks/verify_rules.py`,
the one home; this is the shape:

- **What is a rule.** A column-0 bullet that opens in bold (`- **…**`), with
  the leading `PREFIX-n` as its id when there is one and a slug of its bold
  title until E0.2 gives it one; or a leaf section of prose (a heading with
  no bullet rules and no child headings) — the numbered files state many
  rules that way. The H1 and any "Sources" section are not rules. On the
  corpus as of 2026-09-04 this finds 558 rules across the 18 documents
  (51 in the iOS document, matching the count in section 1).
- **The tag.** The last square bracket in the rule that contains `check:`,
  references separated by commas, every one of which must resolve:
  `scan:<id>` / `ratchet:<id>` / `advisory:<id>` (a scanner signature, with
  that severity), `<linter>:<rule>` or a bare `<linter>` (`swiftlint`,
  `swiftformat`, `detekt`, `ktlint`, `androidlint`, `eslint`, `tsc`,
  `prettier`, `ruff`, `mypy`), `tool:<name>`, `session:<id>`, `review`,
  `process`, and `context` for a bullet that explains a rule and is not one
  (left out of the total; it cannot share a tag with a check).
- **What "resolves" means — files on disk, nothing else.** The manifest
  `enforcement/checks/battery.json` names, per platform, the linters and
  their config files, the tools and the runner file that invokes each, the
  scanner, the signatures file and the session-hook files. A scanner id
  must be in the signatures table of EVERY platform the document applies to
  with the severity the tag claims; a linter rule must be named enabled in
  the shipped config (the verifier reads SwiftLint and detekt YAML, ESLint
  flat config, `lint.xml`, `tsconfig`, `mypy.ini` and `ruff.toml`, and does
  NOT know any linter's default set — a config names the rule or the rule
  is not held); a tool's runner must exist and mention it; a session id must
  appear in a hook file. A manifest path that does not exist yet is a gap
  the verifier reports, never a claim it believes.
- **The bins it counts.** `machine` (every reference is a machine check —
  the only bin the headline number counts), `partly` (a machine check and a
  review/process/advisory reference share the rule), `advisory`, `review`,
  `process`, and `open` (any gap). Output is one summary line per document,
  `FAIL verify-rules <path>:<line>:<id>: <words>` per gap, the totals, and
  exit 1 on any gap; `--json` for Coast's Rules tab (E3.7), `--document` +
  `--platform` for one project's copy.
- **This repo's own hook.** `.githooks/pre-commit` (installed per clone with
  `git config core.hooksPath .githooks`) runs the verifier's tests, then the
  verifier against `enforcement/checks/verify-baseline.json` — the ratchet
  of decision 2 applied to this repo's own adoption: the commit is refused
  when the gap count rises, refused when it falls until the baseline is
  lowered in the same commit, and refused on any gap once the 90-day
  deadline (2026-12-03) passes. Proven on the real corpus the day it was
  built: a planted untagged rule was refused; a planted tag was refused
  until the number came down.

### 4.2 The scanner

`check_rules.py <base> <head|WORKTREE|--staged|--files …> --platform <p>`

- Reads `rules_signatures.json`: one row per signature, `{id, severity:
  block|ratchet|advisory, scope, applies_to: [path classes], excludes: [path
  classes], words, rule, platforms: {<p>: {files, pattern, paired?, …}}}`,
  and flattens it (`flatten_signatures`) to one list per platform — each
  entry the row's shared fields with the platform's own laid over them.
  `rule` is the rule id the signature holds, so output and reviews cite the
  same id; a platform whose document numbers it differently says so in its
  entry.
- Reads `paths.json` (Coast: `coast_paths.json` — same file, one home once
  Coast vendors it): the theme file, the strings catalogs, the UI library,
  the feature source, tests, governing, generated, per platform. Coast
  already has every one of these bindings in `PathClasses.swift`; they
  move to the JSON so the scanner and Coast read one table.
- Scans ADDED lines of the diff for `block` signatures (a legacy line
  nobody touched is not this change's fault; on the first push after
  adoption the push hook starts the diff at the adoption commit, so lines
  committed before the checks existed are legacy too — found on Coast, where
  the other lane's commits landed between the measurement and the push); scans the whole tree for
  `ratchet` signatures and compares the count to `.coast/ratchet-baseline.json`
  (GOVERNING; the baseline may be lowered by a human, never raised); prints
  `advisory` counts without failing. The whole-tree pass belongs to the push
  (`--tree` and the diff modes): a commit-time (`--staged`) or editor-time
  (`--files`) scan runs the tree-scope block signatures over the touched
  files only and judges no ratchet — found on Coast's own adoption, where
  every commit and every edit was waiting half a minute for a scan of
  2,400 files, and was refused outright before the baseline existed.
- Exceptions: Coast's plan-approved deviations (the native-patterns
  mechanism, unchanged) and, for repos without a plan, an
  `exceptions` list in the governing rules file — `{id, path, reason,
  who, when}`. Agents cannot write either.
- Output: `FAIL <check> <path>:<line>:<id>: <words> [<rule>]` — the format
  the battery, the hook, CI and Coast's scope router already parse.
- **The warnings baseline (built 2026-09-04 at E2.3/E2.4, decision 2 applied
  to the tools the push gate runs).** The rule is "zero NEW compiler
  warnings" (C-4). A repository that already carries warnings — Coast's own
  build had thousands — cannot be held at zero without a rewrite day, so
  `adopt.py --measure-tools` runs the installed hook's build and format seats
  in counting mode (`pre-push --measure build,format,lint`, which prints
  `MEASURE <id> <count>` instead of judging) and records the build's
  distinct warnings as `build-warnings`, the formatter's findings as
  `format-findings`, the linter's as `lint-findings` and, for an app with
  no test target at all, `tests-missing` (count 1: the tests seat judges
  that entry instead of a test action the project does not have, and runs
  the real tests the day a target exists) in the same
  `.coast/ratchet-baseline.json`, with the same 90-day deadline. From then on the seat runs the tool without its
  strict switch — on a FULL build, since an incremental build prints warnings
  only for what it recompiles (found on a food-tracking app's first push: measured 22,
  rebuilt 0, refused as a fall); SwiftPM drops the package's own targets' build
  products first, xcodebuild runs `clean build` — and hands the count to
  `check_rules.py --ratchet <id> --count <n>`, which judges it as a TOOL ratchet, not a scanner one: above the
  baseline refuses, past the deadline anything above zero refuses, but BELOW
  the baseline passes with a note. A scanner counts a tree deterministically,
  so a fall there must be recorded; a build prints warnings only for what it
  recompiles, so a smaller number is an improvement or a warm build and
  neither is a reason to refuse a push (that app measured 22 and rebuilt
  to 0; Coast measured 270 and rebuilt to 0 while another session held its
  build directory warm — both pushes were refused for nothing). With no entry the seat is
  strict (`-warnings-as-errors`, `swift-format lint --strict`, `swiftlint
  --strict`), so a fresh
  repository is held at zero from its first push; a count of zero at
  adoption writes no entry. Today the Swift seats (SwiftPM and xcodebuild)
  carry it; the Android, web and Python seats stay strict until a repository
  on one of them adopts and needs it — recorded here so it is not mistaken
  for coverage.
- Stdlib only. No network. No model.

### 4.3 The linter configs

Shipped as founder-owned seeds (the existing ownership), but the opt-in
rules the documents name are ON: SwiftLint `force_unwrapping`,
`type_body_length` at 300 (warning), the ESLint config is
`recommended-type-checked` with `parserOptions.projectService`, plus
`react-hooks`; Android gains `detekt.yml` (default set) and a `lint.xml`
with `HardcodedText` as error; the Android toolchain row gains `./gradlew
lint` and detekt beside ktlint. Every claim a rule makes about its linter
must be true in the shipped config — `verify_rules.py` checks the config
file for the named rule.

### 4.4 The session layer (Claude Code hooks)

Committed `.claude/settings.json`, one entry point (`claude-hook.py`, reads
the hook's stdin JSON, exits 2 with the reason on stderr to block):

| Hook | Matcher | What it holds | Rule |
|---|---|---|---|
| `PreToolUse` | `Edit\|Write\|MultiEdit\|NotebookEdit` | Refuses edits to GOVERNING paths: `Scripts/checks/**`, `.githooks/**`, `.claude/settings.json`, the rules document, the linter configs, `.github/workflows/**`, the ratchet baseline. "Agents never edit the files that define their own checks." | 03 process; (Coast decision) |
| `PreToolUse` | `Bash` | Refuses `cd X && …` chains (atomic commands); refuses infrastructure commands (`fly`, `wrangler`, `terraform`, `gh api -X DELETE\|PUT\|POST` on repos/rulesets/secrets, `gh repo delete`, `gh secret set`, DNS tools) with the sentence "ask in one line"; refuses `git push --force*`, `--no-verify`, `git commit --no-verify`. | 10; 00 §2c; 07 |
| `PreToolUse` | `Bash` (the hook reads the command itself; Anthropic's `if` filter is a best-effort prefix match and would miss `git -C <dir> commit`) | Runs the scanner on the staged diff; a red scan blocks the commit with the failing lines. (Also installed as the git `pre-commit` hook so a human meets the same refusal.) | 00 §1, §2, §2d |
| `PostToolUse` | `Edit\|Write\|MultiEdit` | Runs the scanner on the touched file; findings go to the model's stderr immediately. Cannot block (the edit already happened) — it is the seconds-later feedback. | all machine rules |
| `Stop` | — | Refuses to end the turn while the branch has commits not on the remote, or a dirty working tree that includes source changes, with "push before finishing". Honours `stop_hook_active` to avoid a loop. | 00 §7; 07 |
| `SessionStart` | — | Prints, as context: project type and platform, the enforced/total number, the review-only rules in one list, the ratchet counts. The session starts knowing what will refuse it. | 01 |

Git hooks beside them: `.githooks/pre-commit` (scanner on staged) and
`.githooks/pre-push` (build → tests → lint → format → scanner → jscpd new
clones → the other shipped checks), `core.hooksPath` set by `adopt.py`.
Both refuse in the checks' own lines. A human and an agent meet the same
wall.

### 4.5 Inside Coast

- **The Coding agent and every specialist receive the rules document**,
  split: the machine and ratchet rules as one paragraph ("these checks will
  refuse your push: …"), the review rules in full for their role. The
  Planner receives the same, so plan items name their tokens, keys and
  components (the plan already names native features for A-7).
- **The in-loop battery** (S12) runs the scanner on the working tree after
  every build-and-test request, so the coder sees the failing lines in the
  same turn — the local battery already has the `WORKTREE` head for this.
- **Review becomes per-rule rows.** Every reviewer pass returns
  `rules: [{id, touched, verdict, evidence: {file, line}}]` for the rules in
  its bin. The harness rejects: a missing rule; `touched: false` for a
  rule whose `applies_to` path classes intersect the diff's paths; a
  `fail` with no evidence; evidence naming a file not in the diff (the
  existing citation check, extended). Machine-held rules are not sent for
  a verdict — the scanner's result is attached instead, which is cheaper
  and spends judgment where it matters. The "touches no rule's territory
  is a clean pass" sentence is deleted.
- **The general reviewer reads the rules document too** (today only the
  Domain-rules pass does).
- **Builder self-reports carry zero weight.** No gate, ledger verdict, or
  dashboard row reads the coder's `submit_work` prose as evidence; only
  check output and reviewer rows do. Written into the harness, not the
  prompt.
- **Every fix ticket names its guard.** A bug-fix ticket's done state
  requires a `guard` field naming the scanner signature, linter rule, or
  test that now prevents the class; the fix diff must touch it. The
  native-patterns feedback loop, made mandatory.
- **The founder sees the number.** The Rules tab shows "rules held by a
  machine: N of M" per project, with the review-only rules listed
  honestly. This is the marketing sentence once N is high; until then it
  is the truth.
- **The `doc-comments` check moves to `check_doc_comments.py`**, shipped,
  in CI and the hook — the Swift implementation is deleted (one
  implementation per check).
- **Coast's own repo adopts the same layer**: its pre-push hook runs the
  scanner; its copy guard test is retired only after the scanner's Swift
  `ui-string-literal` signature reproduces every one of its findings on
  Coast's own Views (run both, compare, then delete the Swift one).

### 4.6 Versioning and delivery

- `CHECKS-VERSION` in this repo stamps the corpus AND the checks together
  (Coast's `coast-rules-version` becomes this number). It is the release
  number: every release is this number, the git tag `v<number>`, and an
  entry in the root `CHANGELOG.md`, and each project records the release it
  carries in `.coast/standards-version`. A rules update in
  Coast delivers the new documents, signatures, linter configs, hooks and
  scripts as one founder-clicked change, with the plain-words changes
  line, exactly as today.
- Coast vendors `enforcement/` into `Templates/` pinned by commit and
  SHA-256 (the `skills-lock.json` shape) and a parity test fails the suite
  when the copies drift. This repo's README claim ("byte-for-byte copies
  of the shipped corpus") extends to the checks.
- The owner's own repos run `adopt.py` once, then take updates by re-running
  it (idempotent; refuses to overwrite a founder-edited seed, replaces a
  governed file, prints what changed).

## 5. Every rule, its bin, its check

The ids below are the shipped platform documents' ids where one exists. The
DRY, L and DES rules got theirs in E0.3 (they live in the platform documents
now); the numbered files' remaining rules are named by the parser's slug of
their bold title (E0.1 convention) — ids such as `GIT-`, `ENV-`, `SES-` are
not needed for the count and are not planned. "all" means every app platform;
platform-specific notes follow the id. Severity `block` unless marked
`ratchet` or `advisory`.

### 5.1 Machine — the scanner (`scan:<id>`)

| Signature id | Rule(s) | What it matches (per-platform patterns live in `rules_signatures.json`) | Scope |
|---|---|---|---|
| `ui-string-literal` | 00 §2, L-1 | Swift: a letters-and-spaces literal in `Text(`, `Label(`, `Button(`, `.navigationTitle(`, `.alert(`, `Toggle(`, `TextField(` placeholders, `accessibilityLabel(`, and any bare literal in a Views/Screens path outside the skip contexts (SF Symbol names, identifiers, URLs, comparisons — Coast's copy-guard list). Kotlin/Compose: `Text("…")`, `text = "…"`, `contentDescription = "…"`, `title = "…"`, `label = "…"`; XML `android:text="literal"` (Android Lint also holds this one). TSX/JSX: text between tags, and `title=`, `placeholder=`, `aria-label=`, `alt=`, `label=` string props. Python services: literal user-facing strings in response bodies outside the messages module (OBS-4). | added lines; UI/feature paths; excludes strings catalogs, tests, generated |
| `styling-literal` | 00 §1 (one theme file), 05 tokens | Swift: `Color(red:`, `Color(hex`, `Color(.sRGB`, `#RRGGBB`, `.font(.system(size:`, `.fontWeight(` with a literal outside the theme, `.frame(width: <n>` at page scale. Kotlin: `Color(0x…`, `.sp`/`.dp` literals outside theme, `fontSize = <n>`. TS/TSX/RN: hex colours, `fontSize: <n>`, `color: "…"`, `padding: <n>` in styles outside the tokens file, raw CSS colour literals in `.css` outside the theme sheet. | added lines; everything but the theme file and tests. Spacing literals start as `ratchet`, colours and font sizes `block`. |
| `second-theme-file` | 00 §1, 05 | A second file matching the theme shape (`*Theme.swift`, `theme.ts`, `tokens.*`, `Color+*.swift`, `Colors.kt`) outside the bound theme path. | whole tree |
| `env-literal` | 00 §2d, C-5 / ARCH-8 | `"main"`/`"master"`/`origin/main` as a ref, absolute `/Users/`/`/home/` paths, `localhost:<port>`, hardcoded hosts (`https://api.` etc. outside the config home), plan or tier names, `Bundle.main.path` fallbacks. Allowlist in the governing exceptions. | added lines; all source; excludes the configured config home, tests |
| `secret-literal` | SEC-4, ENG-6/SEC-7, 00 §4 | `sk-ant-`, `AKIA…`, `ghp_`, `xox[bp]-`, `-----BEGIN … PRIVATE KEY`, `password = "`, `apiKey = "`, `.env` files, `*.p8`/`*.p12`/`*.pem`, and data-shaped files (`*.csv` over a size, `*.sqlite`) added to the tree. | added lines and added files; whole tree at push |
| `plaintext-http` | SEC-1 | `http://` literal that is not `localhost`/`127.0.0.1`; Android `usesCleartextTraffic="true"`; iOS `NSAllowsArbitraryLoads` true. | added lines |
| `raw-html` | Web/RN SEC-3 | `innerHTML =`, `dangerouslySetInnerHTML`, `document.write(`. | added lines |
| `dangerous-eval` | Web SEC, Python SEC-5 | `eval(`, `new Function(`, `exec(`, `pickle.load`, `yaml.load(` without `SafeLoader`. | added lines |
| `shell-injection` | Python SEC-4 | `shell=True`, `os.system(`, `os.popen(`. | added lines |
| `exported-component` | Android SEC-6 | `android:exported="true"` without `android:permission`. | added lines in manifests |
| `sql-string-assembly` | SEC-2 / SEC-3 | `"SELECT … " +`, f-strings/interpolation feeding `execute(`/`rawQuery(`/`query(`. | added lines |
| `cdn-script` | 03 supply chain | `<script src="https://cdn…` / `unpkg` / `jsdelivr` in HTML or TSX. | added lines |
| `blocking-call` | ENG-3, ASYNC-1 | Swift: `sleep(`, `usleep(`, `Thread.sleep`, `DispatchSemaphore(…).wait`, `.wait()` on the main actor, `RunLoop.run`. Kotlin: `Thread.sleep`, `runBlocking` in UI, `.get()` on a future. JS: busy `while (Date.now()`, `Atomics.wait`. Python: `time.sleep`/`requests.` inside `async def`. | added lines; UI/feature paths |
| `fixed-text-size` | ACC-4 | Swift `.font(.system(size:` (also styling); Kotlin `fontSize = <n>.dp` (dp, not sp); RN `allowFontScaling={false}`; CSS `font-size: <n>px` on body text. | added lines |
| `fixed-screen-size` | ENG-2 | Swift `.frame(width: <big>, height: <big>)` at page scale; RN `Dimensions.get` used as a fixed layout; CSS `width: <n>px` on page containers. `advisory` first, `block` once tuned. | added lines |
| `manual-plural` | L-5 | `count == 1 ?`, `== 1 ? "`, `if (n === 1)` adjacent to a string. | added lines; UI paths |
| `ui-string-concat` | L-4 | `"…" + <ident> + "…"` in UI paths; Swift interpolation inside a `LocalizedStringKey`. | added lines; UI paths |
| `baked-case` | L-12 | `.uppercased()`, `.toUpperCase()`, `.uppercase()` applied to display strings in UI paths. | added lines; UI paths |
| `one-catalog-per-locale` | L-2 | More than one strings catalog per locale outside the bound strings paths. | whole tree |
| `english-key` | L-3 | A catalog key that is a sentence (spaces, capital first letter) instead of a semantic path. | added lines in catalogs |
| `layer-import` | A-1 | A Views/Screens/components path importing a data framework (`CoreData`, `SwiftData`, `GRDB`, `Room`, `prisma`, `supabase-js`) or the Data module directly; a ViewModel importing UI frameworks. (The import matrix holds the module layer; this holds the file layer.) | added lines |
| `destructive-default-key` | MAC-6, 05 | `.keyboardShortcut(.defaultAction)` or `defaultAction` within a destructive-role button's block. | added lines |
| `pii-in-log` | PRIV-3 | `print(`/`console.log(`/`Log.d(`/`logger.` whose line names `email`, `password`, `token`, `phone`, `address`, `ssn`. `ratchet`. | added lines |
| `test-criterion-tag` | TEST-1 | A test in a changed test file with no acceptance-criterion reference (`AC-<n>` / `criterion:` in the test's name or first comment). | added lines in tests |
| `hermetic-test` | TEST-2 | `https://`, `URLSession.shared`, `fetch(`, `requests.get(` in a merge-gating test file without a `LIVE_TESTS` guard. | added lines in tests |
| `test-weakened` | 06 test changes | Assertions removed from a test file in the diff without `test-change:` in the commit message (sessions) or the plan's test-change item (Coast). | diff of test files |
| `native-pattern` | A-5, A-7 | The existing checker, unchanged — folded under the same runner. | added lines |
| `import-matrix` | A-2 | The existing checker, unchanged. | whole tree |
| `doc-comments` | DOC-1 | Every `public`/`open`/`export`/top-level `def` declaration preceded by a doc comment. Moves from Coast's Swift to a shipped script, all platforms. `ratchet` on adoption of an existing repo, `block` on a new one. | whole tree |
| `type-size` | A-3, 02 granularity | Types over 300 lines, initializers with more than 7 injected dependencies. `advisory` — the rules say advisory, never a failure. | whole tree |
| `inline-comment` | 02 naming | `//` comments that are not doc comments, `ratchet`. | added lines |
| `spacing-literal` | DRY-2, DES-1 | The spacing half of `styling-literal` as its own id so it can carry its own severity: `.padding(<n>)`, `.frame(width: <n>`, `spacing: <n>`, `cornerRadius(<n>)`; Kotlin `<n>.dp`; TS/CSS `padding: <n>`, `margin`, `gap`, `borderRadius`. `ratchet`. | added lines; everything but the theme file and tests |
| `secret-file` | SEC-4, 00 §4 | Grouped under `secret-literal`: a secret- or data-shaped FILE added to the tree (`.env*` except `.env.example`, `*.p8`, `*.p12`, `*.pem`, `*.key`, `*.sqlite`, `*.db`, `*.mobileprovision`, `*.jks`, `*.keystore`); once per file. | added files |
| `money-float` | PAY-1, Python DATA-3 | A binary floating-point type (`Double`, `Float`, `number`, `float`) declared or annotated next to an identifier naming money (`price`, `amount`, `total`, `cost`, `fee`, `balance`). `advisory` only — the reviewer judges (§5.5). Named in E0.2's tags. | added lines |
| `retired-wording` | 01 truth | A configurable list of retired words (`guarantee`, an old product name) in copy, docs and catalogs. Coast's own guard tests for demo wording become signatures here. | added lines |

### 5.2 Machine — the platform's linter (`swiftlint:<rule>`, `eslint:<rule>`, `detekt:<rule>`, `androidlint:<id>`, `tsc:strict`)

| Rule | Check | Shipped-config change needed |
|---|---|---|
| C-3 iOS/macOS | `swiftlint:force_unwrapping`, `force_try`, `force_cast` | enable `force_unwrapping` (opt-in) |
| C-4 iOS/macOS | `swiftlint:*` strict, `swift-format lint --strict` | none; format seat already there |
| C-3 Android | `detekt:UnsafeCallOnNullableType` | ship `detekt.yml`; add detekt to the toolchain row |
| C-4 Android | `ktlint`, `detekt`, `androidlint:*` | add `./gradlew lint` |
| ACC/strings XML Android | `androidlint:HardcodedText` (error) | ship `lint.xml` |
| C-1 Web/RN | `tsc:strict` (`strict: true`, `noImplicitAny`) | verify in shipped `tsconfig` seed |
| C-2 RN/Web | `eslint:react-hooks/rules-of-hooks`, `exhaustive-deps` | add `eslint-plugin-react-hooks` |
| C-3 Web/RN | `eslint:@typescript-eslint/no-floating-promises` | switch to `recommended-type-checked` + `projectService` |
| A-3 (advisory) | `swiftlint:type_body_length` 300 warning, `file_length`; detekt `LargeClass`; eslint `max-lines` warn | set thresholds |
| STYLE-1 Python | `ruff`, `mypy --strict` on public boundaries | Python toolchain row (this repo only; Coast has no Python target) |

### 5.3 Machine — a tool (`tool:<name>`)

| Rule | Check |
|---|---|
| 00 §1 duplicated logic, 02 DRY mechanics, PAY-3 recomputation | `tool:jscpd` — `--fail-on-new-clones` against the base branch, `--min-tokens 50`, on PRs and in the pre-push hook. |
| 00 §4 data never in VCS, 07 secret-scan before first push | `scan:secret-literal` on every push; a full-history scan on the first push (adopt.py runs it). |
| 07 protected main | `tool:gh-ruleset` — `verify_rules.py --remote` reads the ruleset and fails when the required checks, PR requirement, or empty bypass list are missing (Coast's ruleset step already writes them). |
| 02 zero new warnings, C-4 | `tool:warnings-as-errors` — build with warnings as errors in CI and the battery (`SWIFT_TREAT_WARNINGS_AS_ERRORS`, `-Werror`/`allWarningsAsErrors`, `tsc` errors); the pre-push battery names it. |

### 5.4 Session (`session:<id>`) — the Claude Code hooks and git hooks in §4.4

`governing-edit`, `chained-cd`, `infra-command`, `no-verify`, `force-push`,
`scan-at-commit`, `scan-on-edit`, `unpushed-at-stop`, `rules-at-start`,
`attribution-trailer` (a `commit-msg` hook: the model trailer 09 requires).

### 5.5 Review (`review`) — per-rule rows with evidence, nothing else

A-4 speculative abstraction · A-6 role-honest naming · PAY-1/2 (heuristic
scan for `Double` next to `price|amount` is `advisory` only) · PAY-3
one computation site (jscpd catches the copy; the reviewer judges the
"slightly different" recomputation) · AUTH-1..4 · PRIV-1/2/4/5 · SEC-5/8
error wording · UGC-1 · ACC-1 contrast (mechanical later: compute from the
theme tokens) · ACC-2 target size · ACC-3/5 · ENG-1 reactive state · ENG-4
lifetimes · ENG-5 typed errors · TEST-3 assertion strength · TEST-4/5
fixtures · DOC-2 doc matches code · 00 §1 components created once and
cross-cutting one home (the scanner surfaces a near-duplicate component
name; the reviewer judges) · 00 §2b simple and elegant · 00 §5 never invent
domain logic · 05 reading mocks, copy voice, status colour · 02 layering
semantics beyond imports · Python ARCH/API/OBS/DATA rules that are about
design.

Every one of these gets a row per review with `touched`, `verdict`,
`evidence`. The harness rejects `touched: false` when the rule's
`applies_to` classes intersect the diff. This is what turns "I checked" into
a claim that can be false.

### 5.6 Process — held by Coast's pipeline or by a human, named as such

Tests-first (Coast's S9 ordering; a session's git hook can only warn), two
PRs per feature, the owner as the final QA gate on every release, one
subscription layer for every app decided once and never reopened per
project, marketing and content published only on the owner's explicit go,
primary sources first. These stay in the documents with
`[check: process]` so the count is honest about them.

## 6. The build plan

Serial by default, one consolidated review per phase, each task DONE only
with its guard named and a reviewer's confirmation from the code. Sizes: S
under half a day, M a day, L two or more.

**The order from 2026-09-07 (the owner's brief: finish the remaining work, fix what the review
found, wrap every rule in a config):** E2.7 → E2.8 … E2.12 → E5.1 … E5.7 → E6 (once
the name is chosen) → E7. Phase E3 is Coast's own half and runs in Coast's repo on
its own clock; E4 stays filed.

### Phase E0 — the honest starting line (this repo)

| Task | What | Size | Guard |
|---|---|---|---|
| E0.1 | **DONE 2026-09-04.** `enforcement/checks/verify_rules.py`: parse every rule in `rules/platform/*.md` and the numbered files; require a `check:` tag; resolve each tag against a battery manifest per platform; print enforced/total. Runs in this repo's own CI-less hook. The starting line it measured: **enforced by a check 0 of 558**; 540 rules name no check, 18 name one in prose nothing runs (the old "deterministic check: …" brackets on A-7, C-1, C-2, C-3, C-5 and ARCH-8). Convention and resolution rules: §4.1 "Built". | M | 48 tests in `enforcement/checks/tests/` (fixture documents and configs: every grammar form, every config reader, every bin, both ratchet directions, and the real corpus against the committed baseline); it FAILS on today's corpus, and the failure list IS the gap inventory |
| E0.2 | **DONE 2026-09-04.** Tag every rule (§5) in the platform documents and the numbered files. No rule content changes yet — only the bin and the check name. Version stamp 8. The 18 legacy "deterministic check: …" brackets became formal tags (A-7's explanation of the approved-deviations mechanism stayed as rule text). After tagging: 551 counted rules (7 explanatory bullets are `context`), 270 reviewer, 89 process, 192 waiting on checks E1/E2 build; gap count 558 → 395, every remaining gap a check that does not exist yet. | M | E0.1 green on tags; rules without a tag: zero — proven: `verify_rules.py` reports no "no check tag" and no "unknown check" |
| E0.3 | **DONE 2026-09-04.** Move the DRY block (00 §1), the L rules (04), the token rules (05), and 2d into every platform document as `DRY-*`, `L-*`, `DES-*` sections with checks named. Version 8's plain-words changes line. Done as: DRY-1..7, L-1..12 and DES-1..4 in the five app documents (the Python document keeps its own ARCH-6 and OBS-4; "all" means the app platforms); 2d was already C-5/ARCH-8 in every document; 00 §1, 04 and 05 now point at the ids instead of restating them, so each rule has one home. The gap count rose 395 → 489 because the 92 new rules name checks E1/E2 build — recorded as a move in the baseline file with the reason, never silent. The version-8 plain-words line lives in Coast's `RulesCorpus.changes`. | M | E0.1 green; `tests/test_corpus_sections.py`: every app platform doc carries DRY-1..7, L-1..12, DES-1..4 with checks, the Python doc keeps its equivalents, the numbered files no longer restate them |

### Phase E1 — the scanner (this repo)

| Task | What | Size | Guard |
|---|---|---|---|
| E1.1 | **DONE 2026-09-04.** `check_rules.py` runner: diff/worktree/staged/files/tree modes, path classes from `paths.json` (Coast's bindings plus `tests`, `ui`, `config_home`), severity `block/ratchet/advisory`, the ratchet baseline `.coast/ratchet-baseline.json` (`{id, count, deadline, written, by, moves}`; past the deadline a ratchet becomes block; a count above the baseline fails, a count below it fails until the baseline is lowered in the same commit), exceptions (the plan's approved native deviations, unchanged, and `.coast/rules-exceptions.json`), the `FAIL <check> <path>:<line>:<id>: <words> [<rule>]` format. The native-pattern lists are the `native-pattern` group in `rules_signatures.json` (same ids, patterns, paired rule, joined-lines match, Tests/ exemption, governance-only pass); the import matrix is the built-in `import-matrix`, its module `import_matrix.py` absorbed with the judgments unchanged. First rules held: A-2, A-5, A-7 and the numbered files' native/layering rules — **17 of 643**. | L | `tests/test_check_rules.py` (24 tests on a synthetic git repo: every mode, every exception path, the ratchet in both directions and past its deadline, advisory, the built-in) and `tests/plants/<platform>/<id>.{fail,pass}.<ext>` for all 52 folded signatures; Coast's `native_patterns_smoke.py` is re-pointed when Coast vendors `enforcement/` (E3.1) |
| E1.2 | **DONE 2026-09-04.** Signatures, wave 1: `ui-string-literal` (a built-in — `literals.py` lexes the whole file the way Coast's copy guard does, Swift fully, Kotlin/XML, TSX/JSX, Python message shapes; only added lines count), `styling-literal` (block: colours and font sizes), `spacing-literal` (ratchet: spacing, sizes, radii — the design's "spacing starts as ratchet" as its own id), `second-theme-file` (tree, once per file), `env-literal`, `secret-literal` + `secret-file` (grouped) — all six platforms; the runner gained built-in added-scope checks, `.coast/paths.json` / `--paths-override` (a project's own theme and UI paths), `once`, `files_excluded`; 78 plants. **Tuned against Coast's copy guard:** the scanner and `CoastCopyGuardTests` both report ZERO on the guard's own scan roots (`Sources/CoastAppCore/Views` and `ViewModels`), so the Swift skip contexts are the guard's list exactly; the one false positive found on Coast's wider tree — SQL statements in a store file — is now excluded by shape (`looks_like_text` refuses a SQL statement), and the iOS/macOS pass plant carries every guard context so the parity cannot regress. The earlier 4,221 "Coast Sources" number was every literal in every file treated as UI; the signature applies to the `ui`/`ui_lib` path classes only, and on those Coast is clean. **The counts (2026-09-04, by path class as the scanner classifies each repo with the platform's default bindings):** `ui-string-literal` on UI-class files — Coast (macOS table) 0 · the food-tracking app 273 (14 UI files) · the symptom-diary app 241 (21) · the meditation app 136 (12); every sampled app hit is real bare copy, none a false positive. `spacing-literal` (the ratchet) on the whole tree — Coast 2,814 · the food-tracking app 842 · the symptom-diary app 67 · the meditation app 73. `second-theme-file`: the food-tracking and meditation apps each carry a `DesignSystem/Theme.swift` outside the default theme path (their own `.coast/paths.json` binds it at adoption). These become the `.coast/ratchet-baseline.json` entries at E2.3/E2.4; `ui-string-literal` is `block` on added lines, so legacy copy needs no baseline — only new lines are refused. | L | plants; run over Coast's own Sources and the three app repos, counts recorded above as the first ratchet baselines
| E1.3 | **DONE 2026-09-04.** Signatures, wave 2, on every platform the rules demand: `plaintext-http` (the literal, `usesCleartextTraffic`, `NSAllowsArbitraryLoads`; local hosts and XML namespaces excused), `raw-html` (web: `dangerouslySetInnerHTML`/`innerHTML`/`document.write`/`v-html`; iOS/macOS: `loadHTMLString`, HTML attributed strings; Android: `Html.fromHtml`, `loadData`; RN: a `WebView` fed a variable as `html:`; Python: `mark_safe`, `Markup`, `|safe`, `render_template_string`), `dangerous-eval` and `shell-injection` (Python), `exported-component` (Android manifests — an exported component with no permission, the launcher activity excused by the pattern itself), `sql-string-assembly` (interpolation or concatenation inside a SQL string, per language), `cdn-script` (a `<script src="https://…">` anywhere, including inside a code string), `blocking-call` (Swift semaphores/sleeps/`RunLoop.run`; Kotlin `runBlocking`/`Thread.sleep`/`CountDownLatch`; JS busy waits, sync XHR and — on the web — `alert`/`confirm`/`prompt`; Python is a built-in, `async_blocking.py`, that walks indentation and counts a blocking call only inside `async def`), `layer-import` (a data framework imported into view code; a second member, `viewmodel-ui-import`, a UI toolkit imported into a `*ViewModel`; Python: database imports or `.execute(` inside routes/handlers), `destructive-default-key` (SwiftUI `role: .destructive` wired to `.defaultAction`; Compose `onDone`, RN `onSubmitEditing` and web `onSubmit`/`autoFocus` firing a delete). Also a Python `native-pattern` group (`hand-rolled-password-hash`, `hand-rolled-query-parse`, `hand-rolled-arg-parse`) so the priority file's native-first rule holds on the sixth platform. One built-in dispatch (`check_rules.builtin_hits`) serves the scanner and the plant test. **Enforced by a check 84 of 643** (gaps 325 → 246). | M | 141 plants, every one proven in both directions; the scanner tests green |
| E1.4 | **DONE 2026-09-04.** Signatures, wave 3: localization — `manual-plural` (a `count == 1` choosing words), `ui-string-concat` (a string with a space concatenated to a value), `baked-case` (`uppercased`/`capitalized`/`toUpperCase`/CSS `text-transform` on display text; comparisons and sorts excused), `one-catalog-per-locale` (tree: a catalog outside the bound strings home or beside the platform's one — iOS only `Localizable`/`InfoPlist`/`AppShortcuts` catalogs and no legacy `.lproj` tables; Android one `strings.xml` per `values*`; web/RN one file per locale folder), `english-key` (a key with a space or sentence punctuation; dotted keys are semantic); accessibility — `fixed-text-size` (fixed point/dp/px sizes, RN `allowFontScaling={false}`), `fixed-screen-size` (advisory; three-digit `width`/`height`, `Dimensions.get`, page-scale CSS); tests — `test-criterion-tag` (a built-in, `test_criteria.py`: every test declaration in every test language, reported when neither it, the three lines above it nor its first body line names `AC-<n>` or the word criterion), `hermetic-test` (a live host, `URLSession.shared`, `fetch("http`, `requests.get`, `OkHttpClient()`, `axios` in a test file without a `LIVE_TESTS` guard on the line), `test-weakened` (skips, disables, `.only`, vacuous assertions, wide tolerances); `pii-in-log` (ratchet: a log call naming email, password, token, phone, address, card…), `inline-comment` (ratchet: a comment trailing code on its line; URLs in strings excused), `retired-wording` (the word "guarantee" in any source, catalog, markdown or template), `type-size` (advisory built-in, `type_size.py`: a Swift/Kotlin/Python type past 300 lines or any file past 400, reported once at the first added line inside it), and `money-float` (advisory; a money-named field typed `Double`/`Float`/`number`/`float`, names in cents or minor units excused). **Enforced by a check 138 of 643**, advisory 22 (gaps 246 → 87; every gap left is E1.5–E2.1's). | M | 225 plants, every one proven in both directions; the scanner tests green |
| E1.5 | **DONE 2026-09-04 — parity run recorded below.** `enforcement/checks/check_doc_comments.py`: Coast's `DocsGeneration.docCommentCheck` and the scanners under it ported line for line — the sanitizer (ordinary comments and string contents removed, `///` and `/** */` kept), the container stack, the Swift scanner (public by modifier, by public-protocol or public-extension membership, or as a case of a public enum; members of public types scanned; extensions folded into their type per module under the `Sources/<Target>` and `Modules/<M>/Sources` layouts, an extension of a type from elsewhere read through its members; cases, associated types and extensions need no doc), the Kotlin/Java scanner (Kotlin public by default, Java only when it says so, a Java interface's members implicitly public; nested members and accessors not read — the scanner's stated limit), plus TypeScript (exported declarations and the non-private members of exported classes and interfaces, a `/** */` block directly above) and Python (PEP 257: public module-level defs and classes, public methods and `__init__`, a docstring as the first statement). `--files` reads a Swift file's whole module so the fold matches; `--all` walks the tree; output in the FAIL line format. It is also the `doc-comments` built-in signature in every platform table (DOC-1 / Python STYLE-4), so the scanner runs it on added lines and the plant test proves it in both directions. **Enforced by a check 156 of 643** (gaps 58 → 46). **Parity on Coast's own tree:** `Tests/CoastOrchestratorTests/DocCommentParityTests.swift` in the Coast repo runs Coast's Swift scanner over every file under `Sources/`, folds per module, mirrors the check's verdict, runs this script over the same tree and requires the two offender sets to be identical — the result of its first run is recorded in the next row. | S | 12 plants; the Coast parity test |
| E1.5 parity | **DONE 2026-09-04.** The parity test passed twice: in a clean worktree and on Coast `main` at the commit that lands the test (18.6 s of testing after the build). The two checks name the same offender set on Coast's own tree: **8,801 public declarations without a doc comment**, from both, and not one name only one of them reports. The Swift implementation can be deleted at E3.2 as designed; until then the parity test keeps the two equal. | — | `DocCommentParityTests` (committed on Coast main) |
| E1.6 | **DONE 2026-09-04.** Linter configs with the opt-ins (§5.2), under `enforcement/lint/` at the paths `battery.json` names: `swiftlint.yml` (Coast's seed plus `force_unwrapping` opt-in at error, `force_cast`/`force_try` named at error, `type_body_length` 300 and `file_length` 400 as warnings only), `swift-format.json`, `eslint.config.mjs` (`recommendedTypeChecked` with `projectService`, `react-hooks/rules-of-hooks` and `exhaustive-deps`, `@typescript-eslint/no-floating-promises`, `max-lines` warn), `.prettierrc.json`, `detekt.yml` (layered on the default set with `--build-upon-default-config`; `UnsafeCallOnNullableType` and `LargeClass` 300 active), ktlint's `.editorconfig`, `lint.xml` (`HardcodedText` error), `tsconfig.seed.json` (`strict`, `noImplicitAny`), `mypy.ini` (`strict = True`), `ruff.toml` (`B` selected, so `B006`). Every `<linter>:<rule>` and bare `<linter>` tag in the corpus resolves; every config shape was checked against the linter's own documentation. **Enforced by a check 149 of 643** (gaps 87 → 58: 12 name the doc-comment check E1.5 builds, 39 name tools whose pre-push runner E1.7 and E2.2 write, 7 name session hooks E2.1 writes). | S | verify_rules green on linter tags; `tests/test_lint_configs.py`: every config `battery.json` names exists, and for every linter tag the verifier's parser finds in the corpus, `config_enables` is true against the shipped config on every platform the document applies to — a future edit cannot silently turn one off. Also fixed on the way: `tests/test_check_rules.py`'s throwaway-repo fixture now drops the `GIT_DIR`/`GIT_INDEX_FILE` a git hook exports (always, in a linked worktree) — before the fix, committing from a worktree made the hook's test run commit its fixtures onto the branch being committed |
| E1.7 | **DONE 2026-09-04.** jscpd **5.1.2** pinned in `enforcement/TOOLCHAIN.md` (new; the repo had no toolchain table) with its flags quoted from the binary's own `--help` and the repository's `docs/rust.md`: the pre-push seat runs `jscpd . --min-tokens 50 --baseline .coast/jscpd-baseline.json --fail-on-new-clones` (the flag exists in 5.x and needs `--baseline` or `--baseline-from-ref`), refusing in its own FAIL line; past the baseline's deadline it runs `--exit-code` so any clone refuses (decision 2). `adopt.py` writes the baseline from jscpd's `--update-baseline` fingerprints plus the clone count, `written`, `by`, `deadline` (90 days) and `moves` in one file (jscpd tolerates the extra keys on read; a rewrite would drop them, so adopt.py owns the write); without jscpd it records `"clones": null` and the seat refuses until it is written. Coast's PR battery picks the same seat up at E3.2. | S | `tests/test_hooks_and_adopt.py`: a copied 24-line block fails the jscpd seat, the clean tree passes; the test FAILS out loud when jscpd is not installed (JSCPD_BIN or PATH), never skips |

### Phase E2 — the session layer and adoption (this repo, then the owner's repos)

| Task | What | Size | Guard |
|---|---|---|---|
| E2.1 | **DONE 2026-09-04.** `enforcement/hooks/claude-hook.py` (one entry point, stdlib only, `claude-hook.py <hook-id>`, the event JSON on stdin, exit 2 with the reason on stderr) and `enforcement/hooks/claude-settings.json` (the committed `.claude/settings.json`, every hook wired with the documented schema; the commands name `Scripts/hooks/claude-hook.py`, the path `adopt.py` installs it at). The hooks: `governing-edit` (PreToolUse Edit|Write|MultiEdit|NotebookEdit; the platform's GOVERNING class read from `paths.json` through the scanner's own `PathClasses` — one table — plus `.claude/settings.json`; every platform's table when the platform is unknown), `chained-cd` (`cd X && …`, `cd X; …`, a `cd` line followed by more; a bare `cd` passes), `infra-command` (fly/flyctl/wrangler/cloudflared/terraform/tofu/pulumi/doctl/aws/gcloud/az/nsupdate, `gh repo delete`, `gh secret|variable|ruleset …`, a mutating `gh api` on a repo/ruleset/secret/variable/hook/key/environment/deployment/protection endpoint — `dig`/`nslookup` only read and pass — with the sentence "this changes infrastructure — ask the founder in one line first"), `no-verify` (`--no-verify`, `git commit -n`, `-c core.hooksPath=`), `force-push` (`--force`, `-f`, `--force-with-lease`, `--force-if-includes`, `+refspec`), `scan-at-commit` (`if: Bash(git commit *)` — a documented field — and the hook also checks the command itself; `check_rules.py --staged --platform <p>` from the repo root, the FAIL lines on stderr; platform from `.coast/platform` — a one-line file, `ios A` = platform and project type — or `COAST_PLATFORM`), `scan-on-edit` (PostToolUse; `check_rules.py --files <path>`; it exits **2** with the findings because Anthropic's reference says stderr on exit 0 is never shown to the model and to "exit 2 instead so Claude sees the stderr even though the tool already ran" — nothing is blocked, the edit already happened), `unpushed-at-stop` (Stop; `git log @{upstream}..HEAD` non-empty or uncommitted product-source changes → "push before finishing"; `stop_hook_active: true` → 0; no upstream → 0 with a note), `rules-at-start` (SessionStart, stdout as context, always 0: platform and type, the enforced/total number from `verify_rules.py --document docs/domain-rules.md --platform <p> --json` — else the corpus TOTAL — the review-only rules in one list, the ratchet counts). Every behaviour verified against Anthropic's Claude Code hooks reference, https://code.claude.com/docs/en/hooks (the docs.anthropic.com address redirects there), quoted in the docstring; the settings file uses only documented fields (`matcher`, `if`, `type`, `command`, `timeout`, `statusMessage`). `paths.json` gained `.swift-format` beside `.swiftformat` in the ios/macos governing class (the shipped config is Apple's swift-format). Tests: `enforcement/checks/tests/test_claude_hooks.py`, 36 tests — every hook fed the documented stdin JSON through a subprocess in a fixture repo with a bare origin (a planted `ui-string-literal` in a staged view blocks the commit; `.githooks/pre-push` refused and `Sources/App/HomeView.swift` allowed; the Stop block, the pass after pushing, the pass on `stop_hook_active`; the installed `Scripts/checks/` layout), and the settings file proven to name every `session:<id>` the corpus demands except `attribution-trailer` (E2.2's `commit-msg`). **Enforced by a check 162 of 643** (gaps 46 → 40 on top of E1.5; the six `session:` gaps this layer owned are closed; `attribution-trailer` waits on E2.2). **The live check, partly done 2026-09-04:** the adopting session installed this settings file into Coast mid-session and Claude Code picked it up immediately, so four hooks were exercised for real, not in a fixture. `chained-cd` refused two `cd X && …` commands and the session used `git -C` and absolute paths instead. `scan-at-commit` refused the adoption commit with the scanner's own FAIL lines (the whole tree's ratchets, before the baselines existed — the refusal that produced the staged-scope fix) and then passed every later commit with `PASS rules`. `unpushed-at-stop` refused to let the session end with eight commits off the remote, naming them. The git `pre-commit` hook ran on every commit in all four repositories. **Still owed:** `governing-edit`, `scan-on-edit`, `no-verify`, `force-push` and `rules-at-start` have their fixture tests but were not met by a live session (nothing tried to edit a governing file or force-push, and the session predated the SessionStart hook's installation). | M | hook tests (done); the live check, four of nine hooks recorded above |
| E2.2 | **DONE 2026-09-04.** `enforcement/hooks/pre-commit` (the scanner on the staged diff, `check_doc_comments.py --files` on the staged product files once E1.5 ships it — until then the seat says so out loud), `commit-msg` (a subject that exists and fits 100 characters; `session:attribution-trailer` — a commit from an agent session, which Claude Code marks with `CLAUDECODE` in its shell, must name the model in its `Co-Authored-By` trailer, and any Claude trailer must name a model, never a bare "Claude Code"), and `pre-push` — ONE script with a per-platform switch (ios/macos: `swift build -Xswiftc -warnings-as-errors`, `swift test`, `swiftlint --strict`, `swift-format lint`; android: `gradlew build test lint` with `allWarningsAsErrors` required in the build files, detekt, ktlint; react-native/web: `tsc --noEmit` under `strict`, `npm run build`, `npm test`, `eslint --max-warnings 0`, `prettier --check`; python: the tests under `PYTHONWARNINGS=error`, ruff, mypy), then the scanner on the lines added since the remote and on the whole tree, doc-comments, the jscpd seat (E1.7) and `gh-ruleset` (read-only through `gh api`: an active ruleset on the default branch with `pull_request`, `deletion`, `non_fast_forward` and no bypass actors — a plain-words note when gh is absent or offline). Every seat prints `gate: <name>` and refuses in its own lines, Coast's hook shape; a missing battery member is a refusal with its install line, never a silent pass. `enforcement/adopt.py` installs it all into a project idempotently: `Scripts/checks/` (governed, replaced), `.githooks/` (governed), the platform's lint seeds from `enforcement/lint/` (founder-owned: written when absent, replaced only while still equal to a shipped seed by the checksum in `.coast/seeds.json`, kept with a note when edited), `docs/domain-rules.md` (a seed never replaced, a Coast decision), `.coast/platform`, `.coast/standards-version`, `.coast/ratchet-baseline.json` from `check_rules.py --tree` (deadline 90 days, `by` the adopter; a re-run lowers a count that fell and never raises one), `.coast/jscpd-baseline.json`, the marked block in `CLAUDE.md` from `enforcement/TEMPLATE-PROJECT-CLAUDE.md` (the bins and the enforced/total number from `verify_rules.py` on the project's own rules document — 21 of 74 for a fresh iOS copy today), `git config core.hooksPath .githooks`, and the first-adoption secret scan (`secret-literal` over every tracked file; findings exit 1). `--dry-run` writes nothing. **Enforced by a check 141 of 643** (gaps 87 → 47; every gap left is E1.5, E1.6 or E2.1's). Known: the 100-character subject limit will refuse this repo's own long commit subjects if Coast or this repo adopts the hook as is. | M | `tests/test_hooks_and_adopt.py` (11 tests): adopt twice = no diff the second time, `--dry-run` writes nothing, founder text outside the CLAUDE.md block survives, an edited lint seed is kept while an unedited one takes the new shipped version, the rules-document seed is never replaced, the secret scan reports a planted key, pre-commit refuses a staged `ui-string-literal` and passes a clean file (run as the installed hook, no `__pycache__` left behind), commit-msg refuses an empty subject, a long one, a bare "Claude Code" trailer and an agent commit with no model, the jscpd plant, the rules-scan seat, and every tool the manifest claims is named in pre-push |
| E2.3 | **DONE 2026-09-04 — Coast adopted, committed on Coast main.** `adopt.py <coast> --platform macos --measure-tools` installed `Scripts/checks/`, the three git hooks (Coast's own `.githooks/pre-push` replaced by the shipped one — the same build, test and `swiftlint --strict` seats CoastOwnGateTests demands, plus the rules scan on the lines added since the remote and on the tree, the whole-tree doc-comment count as an advisory, jscpd against the committed clone baseline, and the warnings baseline), `Scripts/hooks/claude-hook.py` + `.claude/settings.json` (the session hooks — the adopting session picked them up mid-session and met them: the chained-cd refusal, the commit scan, the unpushed-at-stop wall), `docs/domain-rules.md` for Coast itself, `.swift-format`; `.swiftlint.yml` kept (founder-edited, its own THE RATCHET block). Written at adoption, all GOVERNING: `.coast/module-kinds.json` — Coast's library targets are shared layers, CoastApp and CoastCLI the app targets (the import matrix read every `Sources/<Target>` as a customer feature module and refused 711 imports; Coast's own layering stays with `H54ModuleBoundaryTests`); `.coast/paths.json` — CoastDesignKit is the theme home, the plan folder, `spikes/`, `benchmark-results/` and `dist/` are not product source, the `ui` class adds `**/ViewModels/**` and the two scaffold-text files the copy guard scanned; `.coast/rules-exceptions.json` (11) — the spike's scaffold `Theme.swift` fixture, eight test files whose key-shaped fixtures (fake `sk-ant` keys, PEM markers, placeholder passwords) the secret scan reads as secrets, one transcript that quotes them, and the four PlatformRefusal strings the copy guard's allowlist carried. **The baselines** (`.coast/ratchet-baseline.json`, deadline 2026-12-03): build-warnings 244 (distinct; Coast's build prints them thousands of times over), format-findings 46,777, spacing-literal 2,840, inline-comment 574, pii-in-log 10; lint-findings 0 so the lint seat stays strict; jscpd 4,037 clones. **The copy guard is retired:** the scanner's `ui-string-literal` reports zero on every root `CoastCopyGuardTests` scanned once those roots are `ui` and the allowlist is the exceptions file — the guard is deleted, CLAUDE.md and CoastCopy.swift point at the scanner. **Found on the way and fixed in the standards repo:** the first-push secret scan took most of an hour on 2,400 tracked files (`--only`), read `emailPassword = "email-password"`, error text quoting the PEM marker and `"your-api-key"` as secrets (the pattern now wants a value that looks like one), and found one real GitHub token in a July 17 raw transcript (redacted in the file; the owner's call: tokens get refreshed at launch); commit-time and edit-time scans judged the whole tree's ratchets (35 s per commit and per edit, refused outright before the baseline existed — now the touched files only); a `git -C <other repo> commit` was scanned by Coast's hook (now routed to that repository). Coast's own rules document: **enforced by a check 25 of 81**. | M | Coast's suite green through the new gate (the adoption push); scanner findings on the guard's roots == the guard's (0 == 0, allowlist carried) |
| E2.4 | **DONE 2026-09-04.** All three of the owner's iOS app repositories adopted with `adopt.py <app> --platform ios --measure-tools`, each committed and pushed through its own new gate. **The food-tracking app** (three commits): 24 of 74; theme bound at its `DesignSystem/Theme.swift` (its folder becomes the UI library); baselines build-warnings 22, format-findings 1,462, lint-findings 330, tests-missing 1, spacing-literal 839, inline-comment 74, jscpd 105; secret scan clean; the whole gate green on the first push. **The meditation app** (two commits): 24 of 74; theme bound at its `Core/DesignSystem/Theme.swift`; baselines build-warnings 3, format-findings 177, lint-findings 47, tests-missing 1, spacing-literal 73, inline-comment 43; the secret scan's two findings were `env(…)` references in `supabase/config.toml`, which taught the signature that an environment reference is not a secret; green on the first push. **The symptom-diary app** (two commits): 24 of 74; no theme-shaped file to bind; baselines build-warnings 2, format-findings 1,640, lint-findings 364, spacing-literal 67, inline-comment 29 — and no `tests-missing` entry, because it has a test target and the seat runs the real tests. **What the three taught the layer, all fixed in this repo:** an app with no test target at all (two of the three) needs the `tests-missing` baseline rather than a push refused forever; the iOS tests seat must pick the iPhone on the newest installed runtime by id (it asked for an iOS 18 device for an iOS 26 app) and, when xcodebuild can see no concrete simulator at all, fall back to the Mac's Designed-for-iPad destination; the warnings count is comparable only on a full build; a linter seed that fails on legacy code is answered by the `lint-findings` baseline, so no app needed a rules-doc edit or a `--no-verify`. | S each | adopt.py's own verification; each app's first push through its installed gate |
| E2.5 | **DONE 2026-09-04.** The repo README's `enforcement/` row says what is built and where; step 6 of "How to adopt" runs `adopt.py --measure-tools` and says what it installs; a new "How enforcement works, in one screen" section gives the bins, the number (170 of 643 on 2026-09-04, each project's own from its `docs/domain-rules.md`), what refuses where, and the baselines with their deadline. `PROJECT-TYPES.md` gains "The checks travel with the rules". `TEMPLATE-CLAUDE.md` points at the block `adopt.py` writes and keeps. The one "reviews grep the diff" sentence (00 §2c) now names `env-literal`, the scanner and the hooks; its `[check: scan:env-literal]` tag is unchanged. | S | verify_rules green; no doc names a check that does not run |

### Phase E2 — the review (2026-09-07, at the owner's request)

Three reviewers read every line of the scanner, the hooks and the installer against this
document and against Anthropic's hooks reference, and confirmed each finding with a
probe before reporting it. What was fixed is fixed with a test; what was not is a row
below, ranked, and the next session builds the first row that does not say DONE.

| Task | What | Size | Guard |
|---|---|---|---|
| E2.6 | **DONE 2026-09-07.** The small, unambiguous defects, each with a test: `verify_rules.py --document` reported every signature the one document did not name as a gap (198 false FAILs and exit 1 on a clean iOS document — the unnamed-signature check now runs only over the whole manifest); `rules-at-start` said "unknown" in every adopted repository because the verifier is not shipped (it now reads the number `adopt.py` wrote into the CLAUDE.md block); `if: Bash(git commit *)` on `scan-at-commit` is a best-effort prefix match per Anthropic's page, so `git -C <dir> commit` never reached the hook and the routing written for Coast's incident was dead (the field is gone; the hook reads the command); a `-C` target that did not exist raised a traceback; `no-verify` missed `core.hookspath` in any case, `--no-verif` (git takes unique prefixes) and `git config core.hooksPath …`; the push lock's start-time file left a window in which a second push read "no start time", called the live lock stale and took it too (the age is now the directory's own mtime), and Ctrl-C released the lock but kept the gate running (a signal now exits); the moved-remote check always fetched `origin`; `commit-msg` counted bytes under a C locale (a 98-character subject with two em dashes refused as 102); the scanner skipped an added line beginning `++` without counting it, shifting every later line number in the hunk; the whitespace-joined fallback ran over a WHOLE file in tree and `--files` scope, so `print(` on one line and `address` hundreds of lines later was one `pii-in-log` hit — and a ratchet count (the join is now a window of 8 lines); `ui-string-concat` backtracked cubically on a long line with one unmatched quote (a 12 KB line never finished; lookaheads now); `manual-plural` matched every identifier ending in `n` (`version == 1`, `column == 1`, `position === 1`); a malformed baseline file crashed with a traceback instead of a FAIL line; a negative tool count passed; git quoted non-ASCII paths so every mode silently skipped `CaféView.swift`; `adopt.py` crashed on a Mac without `npx` after files were written; a project folder that case-folds to `Scripts/` (a web project's `scripts/`) is now said out loud in the report. Two stale clone paths fixed. `enforcement/DEVELOPER-GUIDE.md` written: the manual. | M | 155 tests green; verify-rules 170 of 643, open 0 |
| E2.7 | **Re-adopt the four repositories.** Coast and the three iOS apps carry a standards version five commits behind this review, and more after it: they lack the seat exceptions (§4.7b), the previous-hooks chaining (§4.8), the tsconfig parser, and everything in E2.6. Each also has an uncommitted CLAUDE.md edit (the standards clone moved on the owner's machine) that `adopt.py` will rewrite anyway. Run `adopt.py <repo>` (no `--measure-tools`; the counts stand), commit, push through the gate. Note the `pii-in-log` and `spacing-literal` counts may FALL after E2.6's join-window fix — `adopt.py` lowers them. | S each | each repo's `.coast/standards-version` at head; its first push green |
| E2.8 | **DONE 2026-09-07.** **The Bash-rule bypasses, and the permission layer the docs recommend.** Probed and passing today: `sh -c "git push --force"`, a `\`-newline split before `--force`, `A=1 B=2 git push -f` (only the first `VAR=` is skipped), `env -i …`, `xargs git push -f`, `{ fly deploy; }`, `$(fly deploy)`, `npx wrangler deploy`; `chained-cd` misses `if cd X; then`, `pushd`, `builtin cd`; `infra-command` refuses `fly status`, `aws s3 ls`, `terraform plan` while its own sentence says read-only checks are fine. Fix: join `\`-newlines before splitting; skip every leading `VAR=` and wrapper; scan `$(…)` and backtick bodies and the string argument of `sh|bash|zsh -c`; treat `npx`, `pnpm dlx`, `bunx`, `xargs` as wrappers; a per-program read-only allowlist. And add `permissions.deny` rules to the committed settings (`Bash(git push --force*)`, `Bash(fly *)`, …) — Anthropic's page says outright to use the permission system, not a hook, for a hard deny; the hook stays as the explanation. Also `"disableAllHooks": false` in the committed settings (a project `false` overrides a user `true`) and `.claude/settings.local.json` in `ALWAYS_GOVERNING`. Shipped: `claude-hook.py` reads every command through one `commands()` walk (continuations joined; split outside quotes; `$(…)`, backticks, `(…)`, `{ …; }`, `sh -c "…"`, `eval`, `find -exec` bodies read too; every `VAR=`, wrapper, runner and shell keyword skipped; `cd`/`pushd` refused unless last), `infra-command` passes the read-only forms by verb, `claude-settings.json` carries `permissions.deny` (the mutating forms per program and the fixed governing paths, never a whole program — the permissions page says a deny rule cannot carry exceptions) and `"disableAllHooks": false`, `adopt.py` merges both keys keeping the founder's `allow`/`ask` — proved by `test_claude_hooks.py` (`BashBypasses`, the `ChainedCd` and `InfraCommand` additions, `SettingsFile.test_the_permission_layer_uses_the_documented_syntax`) and `test_hooks_and_adopt.py` (`…merges_the_deny_rules_in_front…`). | M | `test_claude_hooks.py`: every bypass above refused |
| E2.9 | **DONE 2026-09-07.** **The doc-comment scanners for TypeScript and Python were written fresh, not ported, and both miss.** TS: a multi-line decorator (`@Component({` … `})`) drives brace depth negative and silences the rest of the file — every Angular/NestJS file is exempt; single-quoted and template strings are not sanitized, so a `"` inside one eats source to the next `"`; a `/** */` followed by blank lines still documents the next declaration. Python: a trailing `# comment` on a `def` line skips the next declaration; a nested function inside a method is reported as a public member. Fix Python with `ast` (stdlib: exact public defs, docstrings, nesting, `@overload`); fix TS by counting braces on decorator lines and a JS-aware string sanitizer. Shipped: the Python side reads `ast` (nesting, `@overload`, setters, trailing comments), the TS side joins a decorator until its brackets balance, sanitizes `'…'`/`"…"`/`` `…` `` strings with `sanitize_js`, and a blank line now breaks a doc; every shape sits in `plants/web/doc-comments.*.tsx` and `plants/python/doc-comments.*.py`, proven line by line in `tests/test_doc_comments.py`. | M | plants for each shape, both directions |
| E2.10 | **DONE 2026-09-07.** **Scanner correctness on the push path.** (1) `secret-file` is added-scope with a `[\s\S]` pattern, so a binary `.p12`/`.sqlite`/`.jks` produces no `+` lines and is never caught in `<base> HEAD` or `--staged` — judge it from `--name-status` A/R/C paths. (2) A `git mv` re-judges every legacy line as new (`-- path` defeats rename detection) — pass both paths or parse one `-M` diff. (3) Built-ins lex the WORKTREE file but filter by index/commit line numbers, so partial staging moves or hides hits — read `:path` / `<head>:path` through `git show`. (4) `plaintext-http`'s plist toggle and `exported-component` need key and value in one hunk; flipping `<false/>` to `<true/>` under an existing key adds one line and misses — make them built-ins that read the file with context. (5) The tree+ratchet pass runs twice per push (`main` runs `scan_tree` in diff mode, then the hook runs `--tree`) — Coast's half-minute scan doubled. (6) A baseline entry with no `deadline` is accepted silently as permanent; decision 2 says every baseline carries one — refuse it. Shipped: `secret-file`, `plaintext-http` and `exported-component` are built-ins in `check_rules.py` (the first judged from the `--name-status` letter, the other two reading the whole file); every diff is asked for with `-M` under both paths of a rename; a built-in reads the index or commit blob through `git show`; the tree+ratchet pass is `--tree` alone; an undated baseline entry is a `FAIL ratchet` line — `PushPathCorrectnessTests` (six tests) in `test_check_rules.py`, plus the renamed `secret-file` plants, the ios plist-toggle plants and the multi-line manifest plants. | M | `test_check_rules.py` for each |
| E2.11 | **DONE 2026-09-07.** **Web precision before the first web project adopts.** `literals.py` on TSX flags each line of a multi-line named import (`  Button,`) and any comparison with `>` and `<` on one line (`if (a > 0 && b < max)`) as bare copy — block severity on every `.tsx` in the `ui` class, so a web adoption would refuse ordinary code at commit. `one-catalog-per-locale` blocks every legacy `.lproj/Localizable.strings` pair and every flat `locales/en.json`, and binding the `strings` class changes nothing (the exemption §5.1 describes was never wired). `import_matrix` misses a multi-line `import {\n…\n} from` (prettier's default), so the web/RN matrix is mostly blind. `eslint.config.mjs` imports `eslint-plugin-react-hooks` unconditionally, so a non-React web project's lint seat fails on import; `tsconfig.seed.json` is installed AS `tsconfig.json` with no `include` while its own comment calls it a base to extend. Run the scanner over the web project's tree and tune until the sampled hits are all real, the way E1.2 did for Swift. **Shipped:** `literals.py` on TSX refuses a comparison, an arrow, a generic close and one name per line of a named import as copy, and reads bare JSX text on its own line (the web and RN plants carry every shape; `test_check_rules.WebPrecisionTests` runs them through the runner); `one-catalog-per-locale` on web/RN excludes the bound `strings` class and drops its hand-listed exemptions, so the class binding is the one truth (a test rebinds it and watches the verdict move to `locales/en.json`); `import_matrix.typescript_imports` joins a named list broken over lines (a runner test on a `Modules/<M>/src` layout); `eslint.config.mjs` requires the hooks plugin inside a `try` and names its two rules only when it is there (`test_lint_configs` loads the config under node with and without a stub plugin); `tsconfig.seed.json` is a complete starter with `include`, still landing as `tsconfig.json` only when the project has none — the push gate reads `strict` from `tsconfig.json` and does not follow `extends`, so a base file the project extends would have refused every adoption. **The counts (2026-09-07, one adopting web project, every `.tsx` read as new lines):** `ui-string-literal` 128 → 50 over all `.tsx` files; on the `ui`/`ui_lib` classes the signature applies to, 110 → 40, and all 40 sampled are real bare copy (38 in one component-gallery page, an `aria-label`, an iframe `title`). The 70 removed were `Promise` after `=>`, `= Extract` after a generic close, `= startMs && now` between `>=` and `<=`, and one name per line of named imports. Tree mode on the same project: `inline-comment` 104, `spacing-literal` 62, `second-theme-file` 3, `pii-in-log` 1 — the baselines it adopts with; no catalog files, so `one-catalog-per-locale` is proved by the tests alone. Not done here: the iOS/macOS tables still block a legacy `<locale>.lproj/Localizable.strings` pair (add `**/Localizable.strings` to their `files_excluded`; those entries were another agent's this session). | M | web plants; a dry-run on the web project whose hits are sampled and recorded here |
| E2.12 | **DONE 2026-09-07.** **The installer's edges.** The CLAUDE.md marker rewrite appends a block on every run when an end marker precedes the begin, and a second run after an orphaned begin deletes founder text between the orphan and the appended block — find the last begin, the first end after it, refuse on inconsistent markers. Hooks living in `.git/hooks/` (pre-commit-framework, lefthook, old husky) are dropped silently — §4.8 promises they are not; also record `$(git rev-parse --git-path hooks)` when it holds executables. Previous hooks are forced through `sh` (a Python or bash-ism hook breaks) — exec when executable. `pre-push` scans HEAD, not the pushed sha (`git push origin feature` from main scans the wrong range). `commit-msg` strips a `#123 …` subject as a comment and refuses every agent `git merge`/`revert` default message. The `Scripts/`-vs-`scripts/` collision is noted, not solved: the layout constants live in at least six files (`adopt.py`, the three hooks, `claude-settings.json`, `claude-hook.py`, every `paths.json` governing class) — one home for them is the fix, and the same change is the first step of E5. Stale governed files are never removed when a module is renamed upstream. `detect_platform` returns None for an `.xcodeproj`-only project (all three apps) — read the pbxproj. Shipped: the marker rewrite refuses any arrangement but one pair before writing anything, git's own hooks directory is recorded as the previous hooks and an executable previous hook runs as itself, `pre-push` scans each pushed sha from its stdin ref lines, `commit-msg` keeps a `#123 …` subject and accepts git's own merge and revert messages, `.coast/installed.json` lets a later run remove a governed file a release stopped shipping, and `detect_platform` reads the pbxproj — six tests in `test_hooks_and_adopt.py` (`…markers_in_a_wrong_arrangement…`, `…gits_own_hooks_dir…`, `…no_longer_ships_is_removed`, `…reads_the_pbxproj…`, `…issue_number_subject…`, `…pushed_sha_from_stdin…`); the layout collision stays with E5.1. | M | `test_hooks_and_adopt.py` for each |

### Phase E3 — inside Coast (Coast repo; its task numbers in Coast's plan)

| Task | What | Size |
|---|---|---|
| E3.1 | Vendor `enforcement/` into `Templates/` pinned + parity test; `ShippedChecks` gains the scanner, doc-comments, signatures, paths.json; `PathClasses` reads `paths.json` (one table). | M |
| E3.2 | GateBattery, GateHook, `coast-gates.yml`, the S12 in-loop battery run the scanner (worktree head in the loop) and jscpd on PRs; the Swift `doc-comments` check deleted. | M |
| E3.3 | Prompts: the Coding agent, every specialist, and the Planner receive the rules document split by bin; the general reviewer receives it too. | S |
| E3.4 | Per-rule review rows in `review_agent.py` and the local review: schema, validation (missing rule, vacuous `touched: false`, evidence outside the diff), the "no rule's territory" sentence deleted. Machine-held rules carry the scanner's result instead of a verdict. | M |
| E3.5 | Builder self-reports carry zero weight: a sweep of every reader of `submit_work` prose; any gate or ledger verdict that consumed it now reads check output or reviewer rows. Guard: a test that the coder's report text cannot flip any verdict. | M |
| E3.6 | Fix tickets carry a `guard` field; the done state requires the fix diff to touch the named signature, linter config, or test. | S |
| E3.7 | The Rules tab shows "enforced by a check: N of M", each ratchet's count and deadline, and lists the review-only rules; Settings' rules update delivers the checks with the documents (version 8 words). | M |
| E3.8 | Android and Web toolchain rows: detekt, `gradlew lint`, the type-checked ESLint run, jscpd — installed through the required-programs table. | M |
| E3.9 | The domain-rules reviewer's own catches feed signatures: a review `fail` on a machine-able rule files a "make this a signature" task automatically (the native-patterns loop, generalized). | S |

### Phase E4 — later, filed so it is not lost

- ACC-1 contrast computed from the theme tokens (mechanical once tokens
  are the only colour source).
- Semgrep, if a rule ever needs an AST (deferred idea, §3).
- A reviewer-outcome log per rule id, so a reviewer that is consistently
  wrong on one rule can be found (07 already asks for it).
- Compose `Text("literal")` as an Android Lint custom check if the scanner's
  Kotlin precision proves insufficient.

### Phase E5 — the config: every rule, seat and hook behind a switch, and the names out of the code (2026-09-07)

The owner's brief, 2026-09-07: make a detailed plan to finish all of the remaining
work, fix the things the review found wrong, and wrap all of the rules in a config. The
config lets a user put their own name and app name in, and when they do not, the
text is general — except that "Coast" may stay, because these are Coast's standards.
E2.7–E2.12 come first (a third party meets every one of those edges on day one), then
E5 in the order below. Sizes: S under half a day, M a day, L two or more.

**What the review found that shapes this** (§ Phase E2 review): nothing is
configurable today — every signature, seat, session hook and lint opt-in is on for the
platform, and the only switches are the two dated exception shapes. The signature table
is six near-copies, so any per-project override must key on `(platform, id)`. The
layout (`Scripts/checks`, `Scripts/hooks`, `.githooks`, `.coast/`, `docs/domain-rules.md`)
is a literal in at least six files. The owner's name, the company name and "Coast" appear in refusal
text, the CLAUDE.md template, every lint seed's header and the temp-file names. And the
one design constraint on any switch: **a rule switched off must show in "held by a
machine N of M"**, or the number becomes a lie — the thing this whole design exists to
prevent.

| Task | What | Size | Guard |
|---|---|---|---|
| E5.1 | **One home for the layout.** Every path the layer names lives in one table, `enforcement/checks/layout.json`: `checks_dir`, `hooks_dir` (git), `session_hook`, `settings_file`, `state_dir`, `rules_document`, `ai_rules_document`, `lock_name`, `temp_prefix`, the env-variable prefix. `adopt.py`, the three git hooks, `claude-hook.py`, `claude-settings.json` (rendered at adoption, not copied), `paths.json`'s governing classes and the jscpd ignore list read it — the hooks through a generated `.coast/layout.sh` the installer writes beside the platform file, so a `sh` hook sources one line instead of carrying literals. **Decision offered with this row:** move the checks and the session hook under the state directory (`.coast/checks/`, `.coast/hooks/`) so a project has ONE folder that is the layer's and the `Scripts/`-vs-`scripts/` case-fold collision cannot happen; recommended. | M | a test greps every shipped file for the old literals and fails on any; the case-fold test from E2.6 passes on a project with `scripts/` |
| E5.2 | **DONE 2026-09-07.** **One row per signature.** `rules_signatures.json` becomes `{"signatures": [{id, rule, severity, scope, applies_to, excludes, words, platforms: {ios: {files, pattern}, web: {…}}}]}` — the shared fields once, the per-platform `files`/`pattern`/`paired` under `platforms`, a signature absent from a platform simply not listed there. `load_tables` flattens it back to the per-platform shape the scanner already uses, so nothing downstream changes; the plants and `verify_rules.py` read the same loader. The retired-words list, the test reference words and the tool-ratchet ids move from Python constants into the table. Shipped: the file is 66 rows (237 platform entries, 3,191 lines where the six copies were 5,714), `check_rules.flatten_signatures` / `load_signature_tables` are the one reader (the scanner, the plants, `verify_rules.py` and the session hook go through them), the one-off parity script found every platform's entries byte-equal by id and one order change — React Native's `scrim-modal` now precedes its three native-pattern ids, because Android and React Native ordered that pair oppositely and one row list holds one order — and `SignatureTableShapeTests` in `test_check_rules.py` pins each platform's ids in order, the fields every flattened entry carries, the overlay, and that no platform entry repeats the row; not moved: the retired words already live in the table as `retired-wording`'s pattern, and `TOOL_RATCHETS` (the ratchet verdict) and the test reference words (`test_criteria.py`) sit outside the loader this row changed — they move with E5.3's config, which is what reads a project's own list. | M | every plant still proves both directions; the flattened tables are byte-equal to today's per-platform tables on the day of the change (a one-off parity test, then deleted) |
| E5.3 | **The config file.** `.coast/config.json`, GOVERNING (an agent cannot switch a rule off), written by `adopt.py` from `enforcement/config.default.json` on first adoption, merged over the defaults on every read — one loader (`config.py`) used by the scanner, the verifier, the hooks (through the same generated `layout.sh`) and the installer: <br>`{"version": 1,`<br>` "owner": {"name": "", "product": "", "org": ""},`<br>` "rules": {"off": [ids], "severity": {id: "block"\|"ratchet"\|"advisory"}, "retired_words": [...]},`<br>` "seats": {"off": [names]},`<br>` "session_hooks": {"off": [ids]},`<br>` "linters": {"off": [names]},`<br>` "ratchet_days": 90,`<br>` "layout": {…overrides of E5.1's table…}}`<br>An `off` entry is the whole switch: the scanner skips the id, the hook skips the seat or hook, the verifier reports it (E5.4). Severity may only move DOWN (block → ratchet → advisory) in the config; moving up is the table's job. `rules-exceptions.json` stays as it is — an exception is dated and per-path, a switch is neither. | M | `test_config.py`: an `off` signature produces no hit on its fail plant; an `off` seat prints `gate: <name> OFF (config)` and runs nothing; an `off` session hook exits 0 with a one-line note; a severity raised in the config is refused with a sentence |
| E5.4 | **The verifier tells the truth about switches.** A new bin, `off`, in `verify_rules.py` and in every place the number is printed (the CLAUDE.md block, `rules-at-start`, `--json`): a rule whose every machine reference is switched off is `off`, not `machine`; a rule with one of several references off is `partly`. `--config <file>` (default the project's) so `adopt.py` computes the project's number with its switches applied. The headline reads "rules enforced by a check 21 of 74 (3 switched off)". | S | `test_verify_rules.py`: the bins with a config; the number falls by exactly the rules switched off |
| E5.5 | **The names out of the code.** Every sentence that says the owner's name, the company name or a product name reads `owner.name` / `owner.product` from the config and falls back to general words: "ask the founder in one line first" (not a person's name), "this project" (not the app's name), "the standards" (not a company's standards). "Coast" stays where it names the product: the `.coast/` directory, the `coast-rules-version` stamp, "Coast standards" in the CLAUDE.md block title. The lint seeds' headers, `TEMPLATE-PROJECT-CLAUDE.md`, `claude-hook.py`'s refusals, the verifier baseline's `by`, the temp-file names and the exception examples are the list; `adopt.py --owner "Pat Lee" --product "Example App"` (or the config) fills them in. | S | a test greps every shipped file and template for the configured names and fails on any |
| E5.6 | **Ask once.** `adopt.py --init` (or a first adoption with no config) asks the founder the on/off questions once, in plain words, one screen per group (rules with a sentence each, seats, session hooks), writes `.coast/config.json`, and never asks again; `--yes` takes every default. Every question's default is "on". | S | a scripted answer file drives the prompt in a test; `--yes` writes the default config byte-for-byte |
| E5.7 | **Docs.** `DEVELOPER-GUIDE.md` gains "Configuration" (the schema, the merge order, what `off` does to the number) and the layout table changes; this document's §4 architecture tree and §4.2 gain the config; `README.md` "How to adopt" gains the one question screen. | S | verify_rules green; no doc names a path the layout table does not |

### Phase E6 — the name: **Coast Standards** (2026-09-07)

The owner was unsure whether to brand this with the company name or with Coast,
leaned to Coast, and noted that the repository name and product name would have to
change with it. Decided the same day: **Coast Standards**. The product name is in every
title and template already (2026-09-07); the rows below are the repository rename, which
waited for the owner's go-ahead because it changes GitHub and every clone path.

| Task | What | Size | Guard |
|---|---|---|---|
| E6.1 | **DONE 2026-09-07.** `gh repo rename coast-standards` (GitHub's docs, read first: every clone, fetch and push to the old name redirects; never create a new repo under the old name or the redirect dies) and the local clone moved to a folder of the new name; the GitHub organisation stays. | S | `git fetch` from the new remote; `gh repo view` on the new name |
| E6.2 | **DONE 2026-09-07.** 22 files rewritten: this repo, the owner's global Claude instructions and memory files, the four adopted repos' CLAUDE.md (uncommitted there until E2.7 re-adopts and commits), Coast's plan documents and `.coast/paths.json`, and the docs of two web projects. Left on purpose: transcripts, agent worktree copies, and the CLAUDE.md block markers `<!-- up-coast-standards: begin/end -->`, which are `adopt.py`'s identifier and change with E5.1 (the installer must recognise both spellings for one release). | S | a grep for the old name over the owner's Claude configuration and every project folder finds only history, transcripts and the markers |
| E6.3 | The corpus stamp and the block title carry the product name (`coast-rules-version` already does). | S | verify_rules green |

### Phase E7 — releases, per-repo copies, and one thin skill (after E5; decided 2026-09-07)

Not a plugin. The owner's decision, 2026-09-07: a plugin would sit in the context of
every chat a person has, and every project carries different rules, so the standards
are delivered like any other library — **each repository holds its own copy at a
pinned release**, and nothing global carries the instructions. The only global piece
is a thin skill that says where to fetch from and how to run the installer. (This
replaces the earlier plugin shape.)

| Task | What | Size | Guard |
|---|---|---|---|
| E7.1 | **DONE 2026-09-07 (release 1.0.0).** **Releases.** Semantic versions: `CHECKS-VERSION` (§4.6) holds the number, every release is a git tag `vN.N.N` on `main` plus a plain-words entry in `CHANGELOG.md` (what changed for a project that upgrades: rules added or retired, checks that now refuse more, new switches). CI refuses a tag whose number differs from the file. `adopt.py` records the release it installed from in `.coast/standards-version` (the tag, falling back to the commit only for an unreleased clone) and prints "installed Coast Standards 1.2.0" so the number is legible. | S | a tag builds a GitHub release with the changelog entry; the installed project's version file holds the tag |
| E7.2 | **DONE 2026-09-07 (release 1.0.0).** **Fetch by release, not by clone.** The installer can be run without a maintained clone: `adopt.py` fetches the release tarball for a named version (`--version 1.2.0`, default latest) into a cache and installs from it, so "upgrade this project to 1.3.0" is one command and no developer keeps a checkout of this repo. A clone still works for contributors. | M | a project adopts from a tarball with no clone present; re-running with a newer version upgrades and keeps edits |
| E7.3 | **DONE 2026-09-07 (release 1.0.0).** **The thin skill.** One `SKILL.md` a person may install globally or per project, holding only: where the releases are, the one command to adopt or upgrade, and the instruction to run the dry run first and put the few real questions (platform, theme file, owner name, any check the project cannot run yet) to the user before writing. No rules, no checks, nothing else in it; the instructions live in the project's own copy. | S | the skill's steps run end to end on a fixture from an empty machine |
| E7.4 | **DONE 2026-09-07 (release 1.0.0).** **Docs.** The quickstart says "install release N" instead of "clone"; the options page shows the version file; the developer guide gains a release checklist (bump, changelog, tag, the four re-adoptions). | S | a fresh Mac follows the README from nothing to a first green push |

## 7. The decisions (ALL DECIDED 2026-09-04 — build them, don't re-ask)

Every choice this design offered was put to the owner on 2026-09-04 and
taken as recommended: every suggestion was accepted as the way the work will
be done. These are filed decisions, not proposals. A session does NOT re-ask them; it builds them. Each is
restated in plain words so nobody has to reconstruct what was agreed.

1. **The scanner is plain Python with per-platform signature tables.**
   Semgrep is not adopted now. Every rule a machine holds today is a literal
   in the wrong file, which line matching scoped by file kind holds
   precisely, with nothing to install on any Mac or CI runner. Semgrep
   becomes the answer only when a rule genuinely needs code structure; §3
   names that revisit point and it stays a deferred idea until then.
2. **Existing repos adopt with ratchet baselines, and every baseline
   carries a deadline.** No rewrite day on adoption; the count may only fall
   or stay flat. When a baseline's deadline passes, that check flips from
   ratchet to block — the forced rewrite day, so a repo can never quietly
   sit on its debt forever. The owner's question that produced this was
   whether there is a checkpoint at which a repo that has not been paying
   its debt down is found out and made to hold a rewrite day. The baseline file is
   `{id, count, deadline}`; the Rules tab and the session-start context show
   both the count and the date, so the deadline is never a surprise.
   **The default deadline is 90 days from the day a baseline is written**,
   and lowering the count resets nothing — only a human may move a date, and
   moving one is recorded in the baseline file with who and why.
3. **The Claude Code hooks are committed in every repo's
   `.claude/settings.json`** and refuse: edits to the files that define the
   checks, chained `cd` commands, infrastructure commands, `--no-verify`,
   force pushes, and ending a turn with unpushed commits. Beside them the
   same file carries `permissions.deny` rules for the mutating forms and
   `"disableAllHooks": false` (E2.8).
4. **This repo is the home; Coast carries a pinned copy.** Plain words:
   Coast keeps its own copy of the check files inside the Coast app, because
   a founder's Mac has no standards repo. That copy is locked to one exact
   version of this repo by checksum, and a Coast test fails if the copy ever
   differs. One home, one verified copy, drift impossible.
5. **The order is E0 → E1 → Coast dogfood (E2.3) → the owner's own apps (E2.4)
   → Coast's customer-facing half (E3).** Coast does not ship the scanner to
   a customer before it is proven on Coast's own code.
6. **The founder-facing number is shown from day one.** Each project's Rules
   tab shows a line like "rules enforced by a check: 12 of 60", with the rest
   listed as rules a reviewer judges. Shown while the number is still low —
   it is the honest version of the promise, and it is the number that should
   visibly climb.
7. **Where each document lives (asked in the same thread).** The design is
   here, in this repo, and it is the only home for it. Coast's numbered task
   list stays in Coast's own plan folder, because that is where a session
   told "do the next Coast task" looks; it points here and restates nothing.

### 4.7 What adopting an existing repository must not ask the founder

Four things were offered to the owner as decisions on 2026-09-05 and were not
decisions at all — they were defects in `adopt.py`, and the answer was to fix
them. Recorded because the pattern will recur: **if adoption produces a
question whose answer is always the same, the answer belongs in the code.**

- **Measuring is not optional.** An existing repository has warnings, linter
  and formatter findings already. A first adoption now measures them and
  writes their baselines without being asked; `--measure-tools` only forces a
  re-measure later.
- **A rules document at an older corpus version is not a founder's edit.** It
  is last year's rule book, and keeping it means the project's rules name
  checks that do not exist (a web project sat at version 7 with three check
  tags, so its number read "0 of 54"). An older version stamp is upgraded and
  the copy it replaced is written beside it as `docs/domain-rules.v<N>.md`, so
  nothing a founder wrote is lost. A document at the CURRENT version that
  differs is a founder's edit and is left alone.
- **The theme is the design-token home, not whichever path sorts first.**
  Candidates are ranked by where token files actually live (`styles/`,
  `theme/`, `design-system/`, `tokens/`) and by name, and every token file in
  the winning folder is bound — `tokens.css` and `tokens.ts` side by side are
  one token set in two formats, not a second theme.
- **An obvious test fake is not a secret.** A value beginning `test-`, `fake_`,
  `dummy.`, `sample-`, `stub-` and the like is excused. A value shaped like a
  real credential (`sk-ant-…`, `ghp_…`, `AKIA…`, a PEM header) is still
  reported wherever it appears, including in tests, because that shape is
  worth a human's glance every time.

### 4.7b A wrong check is a founder's call, not a dead end

Raised by a web project's session on 2026-09-05, from the other side of the
tsconfig bug: combined with a false-positive check, an adopted repo could hard-block
every push with no sanctioned way out. That session had done exactly what its
CLAUDE.md block told it to — verified the check was wrong, refused to bypass, and
stopped with an unpushed commit. The instruction was right and the design left it
nowhere to go.

A seat can now be excused by a person, in `.coast/rules-exceptions.json`, beside the
signature exceptions that were already there:

```json
{"exceptions": [
  {"seat": "build", "reason": "the build needs env vars this checkout has not got",
   "who": "Pat Lee", "when": "2026-09-05", "until": "2026-09-19"}
]}
```

It skips one named seat (`build`, `tests`, `lint`, `format`, `rules-scan`,
`doc-comments`, `jscpd`, `gh-ruleset`), prints who excused it and why on every push,
and refuses again the day it expires. An entry with no `until` is ignored — a
permanent skip is how enforcement quietly dies. The file is GOVERNING, so the session
hooks refuse an agent writing it: the door exists, and only a human can open it.
`--no-verify` stays forbidden, because it turns everything off at once and leaves no
record of who did it or why.

### 4.8 A project's own hooks are never switched off

Adopting used to point `core.hooksPath` at `.githooks` and say nothing about what was
there before. One web project's own `scripts/git-hooks/pre-push` ran `gitleaks` — a real
secret scanner this layer does not have — and adoption silently turned it off. A check a
founder chose is never dropped on the floor.

`adopt.py` now records the path it found in `.coast/previous-hooks-path`, and each shipped
hook runs the project's own hook of the same name after its own checks pass, with the same
arguments and the same ref lines on stdin. It also names the npm script that would undo the
adoption: a `prepare` step running `git config core.hooksPath scripts/git-hooks` puts the
old path back on the next install, so the report says which script and which word to change.

### 4.9 One gate at a time per checkout

Two sessions sharing one working tree ran their gates concurrently and hurt
each other twice: their incremental builds crossed, so a warning count read
zero because the other build had just made everything current, and the slower
push spent twenty-five minutes only to be rejected by a ref lock the faster
one had taken. `pre-push` now serialises on a lock directory in the common git
dir (`mkdir` is atomic; the lock's age is the directory's own mtime, and a lock
older than an hour is broken). After the wait it re-fetches: if the remote moved and this branch does
not already contain it, the hook says so in seconds instead of building for
half an hour and losing the race again. A `--seat` or `--measure` run takes no
lock, so the tests are unaffected.

## 8. Limits of this document

Verified from the code and from each tool's own documentation on
2026-09-03: the state in §1, the tool facts in §3, and Coast's current
prompts, battery, hook and scaffold. Not verified: the precision of any
signature on real code (that is what the plants and the ratchet baselines
in E1 exist to measure), and Semgrep's free-engine per-language coverage
(not itemised on a primary source). Built so far: **the whole of phases E0, E1 and E2** — E0.1 through E2.5, every
row DONE, and reviewed line by line on 2026-09-07 (E2.6 fixed, E2.7–E2.12 ranked), with what each one found on the way recorded in it. The layer is
installed and proven on four real repositories (the reference
implementation's own repository and three iOS apps that adopted it): each
one adopted, committed
and pushed through its own gate, and every refusal along the way was a defect
in this repo that the row records and the tests now hold. Phase E3 — Coast's
customer-facing half, where Coast vendors this layer and ships it to a
founder's project — and phase E4 are design until their rows say otherwise.
