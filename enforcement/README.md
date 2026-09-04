# Rules enforcement — the design and the build plan

Filed 2026-09-03 (Fable), at Abbey's request after two weeks of session
agents reporting rules followed that were not followed. Her words: *"these
are not indeterministic checks… I can't protect against some of the rules
that I ask for. And I don't have confidence that an AI agent is gonna catch
them at review time since so far the session agents have shown me that they
decide on their own whether they pay attention or not to the rules."* And the
brief for this document: *"Design a system that would enable Coast to follow
these rules and also others too… Please be the architect and research the
best thing to do here."*

**To start a session on this work, say:** *"Read
`~/Documents/Claude/Code/up-coast-standards/enforcement/README.md` and build
the next enforcement task."* Every decision is taken (section 7) — a session
builds, it never re-asks. Each task's row in section 6 says DONE when it is,
with the commit; the next task is the first row that does not. Coast's own
tasks wait until the scanner is proven on Coast's own code.

This is the ONE home for the design. Coast's own task list for its half
lives in the Coast repo (`the-engine-plans/the-engine/build-plans/rules-enforcement-plan.md`)
and points here; it never restates the design.

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
| Abbey's own app repos (keto-tracker, symptom-tracker, meditation-app) | No CLAUDE.md pointing at this repo, no linter config, no git hooks, no Claude Code hooks. Nothing enforces anything. |
| `~/.claude/settings.json` | No hooks. |

What IS right and is the template for everything below: the native-patterns
checker (a per-platform signature list, a scan of added lines, fails the
push, exceptions only from the approved plan, agents cannot edit it), the
import-matrix checker, the proof verifier, the local gate battery that runs
the shipped scripts before every push and again in CI (one implementation),
the GOVERNING path class agents cannot write, and Coast's own copy guard
test that fails on any bare user-facing literal in a view.

## 2. The principle

A rule that lives only in a document is a request, and a request loses to
whatever is cheapest for the session in front of the code. Abbey's
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
up-coast-standards (this repo) — THE HOME
├── rules/…                       the prose, one rule per line, each with [check: …]
├── enforcement/
│   ├── README.md                 this design
│   ├── checks/
│   │   ├── check_rules.py        the scanner: signatures × path classes × diff
│   │   ├── check_doc_comments.py the doc-comment check (moved out of Coast's Swift)
│   │   ├── verify_rules.py       rule doc ↔ battery parity; the enforced/total number
│   │   ├── rules_signatures.json per-platform signature tables (ids match [check: …])
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
└── Abbey's app repos             adopt.py, then the same hooks
```

One implementation of every check. The script the hook runs is the script
CI runs is the script Coast's battery runs. No Swift mirrors, no per-platform
re-implementation in linter config.

### 4.1 The rule registry lives in the rule documents

The markdown rule documents stay the founder-facing home (Coast's versioned,
founder-owned, three-way-merged `docs/domain-rules.md` depends on that).
Each rule line's trailing bracket becomes formal:

```
- **L-1** No hardcoded user-facing text … [Coast D36; check: scan:ui-string-literal]
- **C-3** No force-unwraps … [Swift practice; check: swiftlint:force_unwrapping]
- **A-4** No speculative abstraction … [YAGNI; check: review]
- **A-3** A type or module has one job … [SRP; check: ratchet:type-size]
```

`verify_rules.py` parses every rule in the platform documents and this
repo's numbered files and fails when: a rule has no `check:` tag; a tag
names a scanner id, linter rule, or tool that the platform's battery does
not run; a signature exists that no rule names. It prints the number:
`rules held by a machine / rules total` per document. That test FAILS on
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

- Reads `rules_signatures.json`: per platform, a list of `{id, severity:
  block|ratchet|advisory, applies_to: [path classes], excludes: [path
  classes], pattern, paired?, words, rule}`. `rule` is the rule id the
  signature holds, so output and reviews cite the same id.
- Reads `paths.json` (Coast: `coast_paths.json` — same file, one home once
  Coast vendors it): the theme file, the strings catalogs, the UI library,
  the feature source, tests, governing, generated, per platform. Coast
  already has every one of these bindings in `PathClasses.swift`; they
  move to the JSON so the scanner and Coast read one table.
- Scans ADDED lines of the diff for `block` signatures (a legacy line
  nobody touched is not this change's fault); scans the whole tree for
  `ratchet` signatures and compares the count to `.coast/ratchet-baseline.json`
  (GOVERNING; the baseline may be lowered by a human, never raised); prints
  `advisory` counts without failing.
- Exceptions: Coast's plan-approved deviations (the native-patterns
  mechanism, unchanged) and, for repos without a plan, an
  `exceptions` list in the governing rules file — `{id, path, reason,
  who, when}`. Agents cannot write either.
- Output: `FAIL <check> <path>:<line>:<id>: <words> [<rule>]` — the format
  the battery, the hook, CI and Coast's scope router already parse.
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
| `PreToolUse` | `Edit\|Write\|MultiEdit\|NotebookEdit` | Refuses edits to GOVERNING paths: `Scripts/checks/**`, `.githooks/**`, `.claude/settings.json`, the rules document, the linter configs, `.github/workflows/**`, the ratchet baseline. "Agents never edit the files that define their own checks." | 03 process; Coast D12 |
| `PreToolUse` | `Bash` | Refuses `cd X && …` chains (atomic commands); refuses infrastructure commands (`fly`, `wrangler`, `terraform`, `gh api -X DELETE\|PUT\|POST` on repos/rulesets/secrets, `gh repo delete`, `gh secret set`, DNS tools) with the sentence "ask in one line"; refuses `git push --force*`, `--no-verify`, `git commit --no-verify`. | 10; 00 §2c; 07 |
| `PreToolUse` | `Bash`, `if: Bash(git commit *)` | Runs the scanner on the staged diff; a red scan blocks the commit with the failing lines. (Also installed as the git `pre-commit` hook so a human meets the same refusal.) | 00 §1, §2, §2d |
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
  (Coast's `coast-rules-version` becomes this number). A rules update in
  Coast delivers the new documents, signatures, linter configs, hooks and
  scripts as one founder-clicked change, with the plain-words changes
  line, exactly as today.
- Coast vendors `enforcement/` into `Templates/` pinned by commit and
  SHA-256 (the `skills-lock.json` shape) and a parity test fails the suite
  when the copies drift. This repo's README claim ("byte-for-byte copies
  of the shipped corpus") extends to the checks.
- Abbey's own repos run `adopt.py` once, then take updates by re-running
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
PRs per feature, Abbey's QA gate, RevenueCat always, marketing never
without her go, primary sources first. These stay in the documents with
`[check: process]` so the count is honest about them.

## 6. The build plan

Serial by default, one consolidated review per phase, each task DONE only
with its guard named and a reviewer's confirmation from the code. Sizes: S
under half a day, M a day, L two or more.

### Phase E0 — the honest starting line (this repo)

| Task | What | Size | Guard |
|---|---|---|---|
| E0.1 | **DONE 2026-09-04 (Fable).** `enforcement/checks/verify_rules.py`: parse every rule in `rules/platform/*.md` and the numbered files; require a `check:` tag; resolve each tag against a battery manifest per platform; print enforced/total. Runs in this repo's own CI-less hook. The starting line it measured: **held by a machine 0 of 558**; 540 rules name no check, 18 name one in prose nothing runs (the old "deterministic check: …" brackets on A-7, C-1, C-2, C-3, C-5 and ARCH-8). Convention and resolution rules: §4.1 "Built". | M | 48 tests in `enforcement/checks/tests/` (fixture documents and configs: every grammar form, every config reader, every bin, both ratchet directions, and the real corpus against the committed baseline); it FAILS on today's corpus, and the failure list IS the gap inventory |
| E0.2 | **DONE 2026-09-04 (Fable).** Tag every rule (§5) in the platform documents and the numbered files. No rule content changes yet — only the bin and the check name. Version stamp 8. The 18 legacy "deterministic check: …" brackets became formal tags (A-7's explanation of the approved-deviations mechanism stayed as rule text). After tagging: 551 counted rules (7 explanatory bullets are `context`), 270 reviewer, 89 process, 192 waiting on checks E1/E2 build; gap count 558 → 395, every remaining gap a check that does not exist yet. | M | E0.1 green on tags; rules without a tag: zero — proven: `verify_rules.py` reports no "no check tag" and no "unknown check" |
| E0.3 | **DONE 2026-09-04 (Fable).** Move the DRY block (00 §1), the L rules (04), the token rules (05), and 2d into every platform document as `DRY-*`, `L-*`, `DES-*` sections with checks named. Version 8's plain-words changes line. Done as: DRY-1..7, L-1..12 and DES-1..4 in the five app documents (the Python document keeps its own ARCH-6 and OBS-4; "all" means the app platforms); 2d was already C-5/ARCH-8 in every document; 00 §1, 04 and 05 now point at the ids instead of restating them, so each rule has one home. The gap count rose 395 → 489 because the 92 new rules name checks E1/E2 build — recorded as a move in the baseline file with the reason, never silent. The version-8 plain-words line lives in Coast's `RulesCorpus.changes`. | M | E0.1 green; `tests/test_corpus_sections.py`: every app platform doc carries DRY-1..7, L-1..12, DES-1..4 with checks, the Python doc keeps its equivalents, the numbered files no longer restate them |

### Phase E1 — the scanner (this repo)

| Task | What | Size | Guard |
|---|---|---|---|
| E1.1 | **DONE 2026-09-04 (Fable).** `check_rules.py` runner: diff/worktree/staged/files/tree modes, path classes from `paths.json` (Coast's bindings plus `tests`, `ui`, `config_home`), severity `block/ratchet/advisory`, the ratchet baseline `.coast/ratchet-baseline.json` (`{id, count, deadline, written, by, moves}`; past the deadline a ratchet becomes block; a count above the baseline fails, a count below it fails until the baseline is lowered in the same commit), exceptions (the plan's approved native deviations, unchanged, and `.coast/rules-exceptions.json`), the `FAIL <check> <path>:<line>:<id>: <words> [<rule>]` format. The native-pattern lists are the `native-pattern` group in `rules_signatures.json` (same ids, patterns, paired rule, joined-lines match, Tests/ exemption, governance-only pass); the import matrix is the built-in `import-matrix`, its module `import_matrix.py` absorbed with the judgments unchanged. First rules held: A-2, A-5, A-7 and the numbered files' native/layering rules — **17 of 643**. | L | `tests/test_check_rules.py` (24 tests on a synthetic git repo: every mode, every exception path, the ratchet in both directions and past its deadline, advisory, the built-in) and `tests/plants/<platform>/<id>.{fail,pass}.<ext>` for all 52 folded signatures; Coast's `native_patterns_smoke.py` is re-pointed when Coast vendors `enforcement/` (T248) |
| E1.2 | **IN PROGRESS (2026-09-04, Fable; handed off at the account switch).** Signatures, wave 1: `ui-string-literal` (a built-in — `literals.py` lexes the whole file the way Coast's copy guard does, Swift fully, Kotlin/XML, TSX/JSX, Python message shapes; only added lines count), `styling-literal` (block: colours and font sizes), `spacing-literal` (ratchet: spacing, sizes, radii — the design's "spacing starts as ratchet" as its own id), `second-theme-file` (tree, once per file), `env-literal`, `secret-literal` + `secret-file` (grouped) — all six platforms; the runner gained built-in added-scope checks, `.coast/paths.json` / `--paths-override` (a project's own theme and UI paths), `once`, `files_excluded`; 78 plants; the runner tests cover a view literal vs the same words in a model, added-lines-only, the override, the tree theme check, the .env file vs its example, a secret in a test file. **Built and green, NOT yet tuned:** the first runs (whole tree as if added, `--files`) counted Coast Sources 4,221 hits, keto-tracker 1,824, symptom-tracker 515, meditation-app 353 — nearly all `ui-string-literal`, and the samples show false positives to remove before these become baselines: font names in CoastFonts/CoastType (a `Font.custom`/`static let` context), design-kit literals, `#Preview` names, identifiers like `"receipt-\(x)"`. **Remaining for E1.2:** tune the Swift skip contexts against Coast's copy guard (run both on Sources/CoastAppCore/Views and diff), re-run the four counts, record them here and as `.coast/ratchet-baseline.json` entries at adoption (E2.3/E2.4), mark DONE. | L | plants; run over Coast's own Sources and the three app repos, counts recorded as the first ratchet baselines |
| E1.3 | Signatures, wave 2: security (`plaintext-http`, `raw-html`, `dangerous-eval`, `shell-injection`, `exported-component`, `sql-string-assembly`, `cdn-script`), `blocking-call`, `layer-import`, `destructive-default-key`. | M | plants |
| E1.4 | Signatures, wave 3: localization (`manual-plural`, `ui-string-concat`, `baked-case`, `one-catalog-per-locale`, `english-key`), accessibility (`fixed-text-size`, `fixed-screen-size`), tests (`test-criterion-tag`, `hermetic-test`, `test-weakened`), `pii-in-log`, `inline-comment`, `retired-wording`, `type-size`. | M | plants |
| E1.5 | `check_doc_comments.py` — all platforms; behaviour matches Coast's Swift check on Coast's own tree before the Swift one is deleted. | S | plants; a parity run on Coast |
| E1.6 | Linter configs with the opt-ins (§5.2): swiftlint.yml, eslint (type-checked + react-hooks), detekt.yml, lint.xml, tsconfig seed. `verify_rules.py` reads each config for the rules the documents name. | S | verify_rules green on linter tags |
| E1.7 | jscpd: the pinned version in the toolchain table, `--fail-on-new-clones` in the pre-push and PR battery, baseline on adoption. | S | a plant PR with a copied block fails |

### Phase E2 — the session layer and adoption (this repo, then Abbey's repos)

| Task | What | Size | Guard |
|---|---|---|---|
| E2.1 | `claude-hook.py` + `hooks/claude-settings.json` (§4.4): governing-edit, chained-cd, infra-command, no-verify, force-push, scan-at-commit, scan-on-edit, unpushed-at-stop, rules-at-start. Each hook has a test that feeds it the documented stdin JSON and asserts the exit code and stderr. | M | hook tests; a live check in one session per hook, recorded |
| E2.2 | `.githooks/pre-commit`, `pre-push`, `commit-msg` rendered per platform; `adopt.py` installs everything idempotently (governed files replaced, founder seeds kept, `core.hooksPath` set, CLAUDE.md from the template, first-push secret scan). | M | adopt twice on a fixture repo = no diff the second time |
| E2.3 | Adopt on Coast's own repo (dogfood): the scanner joins its pre-push; ratchet baselines committed; the copy guard retired only after the parity run (§4.5). | M | Coast's suite green; scanner findings on Coast's Views == the copy guard's |
| E2.4 | Adopt on keto-tracker, symptom-tracker, meditation-app (nanny-app when it has code). Baselines committed; the enforced/total printed in each CLAUDE.md. | S each | adopt.py's own verification |
| E2.5 | README, PROJECT-TYPES, TEMPLATE-CLAUDE updated: how adoption works, the bins, the number. The old "reviews grep the diff" sentences replaced by the check names. | S | verify_rules green; no doc names a check that does not run |

### Phase E3 — inside Coast (Coast repo; its task numbers in Coast's plan)

| Task | What | Size |
|---|---|---|
| E3.1 | Vendor `enforcement/` into `Templates/` pinned + parity test; `ShippedChecks` gains the scanner, doc-comments, signatures, paths.json; `PathClasses` reads `paths.json` (one table). | M |
| E3.2 | GateBattery, GateHook, `coast-gates.yml`, the S12 in-loop battery run the scanner (worktree head in the loop) and jscpd on PRs; the Swift `doc-comments` check deleted. | M |
| E3.3 | Prompts: the Coding agent, every specialist, and the Planner receive the rules document split by bin; the general reviewer receives it too. | S |
| E3.4 | Per-rule review rows in `review_agent.py` and the local review: schema, validation (missing rule, vacuous `touched: false`, evidence outside the diff), the "no rule's territory" sentence deleted. Machine-held rules carry the scanner's result instead of a verdict. | M |
| E3.5 | Builder self-reports carry zero weight: a sweep of every reader of `submit_work` prose; any gate or ledger verdict that consumed it now reads check output or reviewer rows. Guard: a test that the coder's report text cannot flip any verdict. | M |
| E3.6 | Fix tickets carry a `guard` field; the done state requires the fix diff to touch the named signature, linter config, or test. | S |
| E3.7 | The Rules tab shows "held by a machine: N of M", each ratchet's count and deadline, and lists the review-only rules; Settings' rules update delivers the checks with the documents (version 8 words). | M |
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

## 7. The decisions (ALL DECIDED 2026-09-04 — build them, don't re-ask)

Every choice this design offered was put to Abbey on 2026-09-04 and taken
as recommended — her words: *"You can record all of your suggestions as the
way we will do things, they sound fine to me."* These are filed decisions,
not proposals. A session does NOT re-ask them; it builds them. Each is
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
   sit on its debt forever. Her question that produced this: *"is there a
   checkpoint at which we can discover they haven't been doing it and
   actually require a rewrite day?"* The baseline file is
   `{id, count, deadline}`; the Rules tab and the session-start context show
   both the count and the date, so the deadline is never a surprise.
   **The default deadline is 90 days from the day a baseline is written**,
   and lowering the count resets nothing — only a human may move a date, and
   moving one is recorded in the baseline file with who and why.
3. **The Claude Code hooks are committed in every repo's
   `.claude/settings.json`** and refuse: edits to the files that define the
   checks, chained `cd` commands, infrastructure commands, `--no-verify`,
   force pushes, and ending a turn with unpushed commits.
4. **This repo is the home; Coast carries a pinned copy.** Plain words:
   Coast keeps its own copy of the check files inside the Coast app, because
   a founder's Mac has no standards repo. That copy is locked to one exact
   version of this repo by checksum, and a Coast test fails if the copy ever
   differs. One home, one verified copy, drift impossible.
5. **The order is E0 → E1 → Coast dogfood (E2.3) → Abbey's own apps (E2.4)
   → Coast's customer-facing half (E3).** Coast does not ship the scanner to
   a customer before it is proven on Coast's own code.
6. **The founder-facing number is shown from day one.** Each project's Rules
   tab shows a line like "rules held by a machine: 12 of 60", with the rest
   listed as rules a reviewer judges. Shown while the number is still low —
   it is the honest version of the promise, and it is the number that should
   visibly climb.
7. **Where each document lives (asked in the same thread).** The design is
   here, in this repo, and it is the only home for it. Coast's numbered task
   list stays in Coast's own plan folder, because that is where a session
   told "do the next Coast task" looks; it points here and restates nothing.

## 8. Limits of this document

Verified from the code and from each tool's own documentation on
2026-09-03: the state in §1, the tool facts in §3, and Coast's current
prompts, battery, hook and scaffold. Not verified: the precision of any
signature on real code (that is what the plants and the ratchet baselines
in E1 exist to measure), and Semgrep's free-engine per-language coverage
(not itemised on a primary source). Built so far: E0.1 (section 6 marks
each row DONE as it lands); everything else here is design.
