# Coast Standards Enforcement — Developer Guide

*Last updated: 2026-09-16*

The technical reference for developers who adopt or maintain the enforcement layer: the scanner, the hooks and the installer. The current release number is in the root `CHECKS-VERSION`. The design and build plan are in [README.md](README.md).

For installing the standards into a product, start with the public docs in [docs/](../docs/README.md). Every installer flag and settings key is listed in [docs/options.md](../docs/options.md).

## Contents

1. [What it is](#1-what-it-is)
2. [Concepts](#2-concepts)
3. [Quick start](#3-quick-start)
4. [The rule documents and the check tag](#4-the-rule-documents-and-the-check-tag)
5. [The scanner — `check_rules.py`](#5-the-scanner--check_rulespy)
6. [The doc-comment check — `check_doc_comments.py`](#6-the-doc-comment-check--check_doc_commentspy)
7. [The verifier — `verify_rules.py`](#7-the-verifier--verify_rulespy)
8. [The git hooks](#8-the-git-hooks)
9. [The Claude Code session hooks](#9-the-claude-code-session-hooks)
10. [The installer — `adopt.py`](#10-the-installer--adoptpy)
11. [The linter configs](#11-the-linter-configs)
12. [Versioning](#12-versioning)
13. [Troubleshooting](#13-troubleshooting)
14. [Extending](#14-extending)
15. [Tests](#15-tests)
16. [Limits, stated plainly](#16-limits-stated-plainly)

---

## 1. What it is

Every rule in `rules/` names the check that enforces it. The enforcement layer runs those checks in any git repository.

| Part | File | What it does |
|---|---|---|
| Scanner | `check_rules.py` | Runs regex patterns over added lines, scoped by file type. |
| Doc-comment check | `check_doc_comments.py` | Finds public declarations with no doc comment. |
| Verifier | `verify_rules.py` | Confirms every rule names a real check, and prints "enforced by a check N of M". |
| Linter configs | `lint/` | Linter settings with the rules the documents cite switched on. |
| Git hooks | `hooks/` | `pre-commit`, `commit-msg`, `pre-push`. |
| Session hooks | `hooks/claude-hook.py` | Claude Code hooks that refuse actions an agent must not take. |
| Installer | `adopt.py` | Installs everything into a project, and writes baselines so existing code can adopt. |

It is Python 3 (standard library only) and POSIX `sh`, with no network and no AI model. It also needs the platform's toolchain and `jscpd`.

---

## 2. Concepts

| Term | Meaning |
|---|---|
| **Rule** | A bold bullet or a leaf prose section in a rule document, ending in a `[…; check: …]` tag. |
| **Check tag** | The last square bracket in a rule that contains `check:` (§4). |
| **Bin** | How a rule is enforced: `machine`, `partly`, `advisory`, `review`, `process`, or `open` (a gap). Only `machine` counts in the number. |
| **Signature** | One row in `rules_signatures.json`: an id, a severity, the path classes it covers, a message, and a regex per platform. |
| **Path class** | A named set of globs in `paths.json`, such as `theme`, `ui`, `tests`, `governing`. |
| **Severity** | `block` fails on any hit. `ratchet` fails if the count rises. `advisory` only prints. |
| **Ratchet** | A count of existing problems that may only go down. |
| **Baseline** | The committed count for a ratchet, with a deadline. |
| **Seat** | One check in the pre-push hook: `build`, `tests`, `lint`, `format`, `rules-scan`, `doc-comments`, `jscpd`, `gh-ruleset`. |
| **Scope** | What a push changed: `none` (prose only), `files` (code), or `all` (the checks themselves). |
| **Governing file** | A file that defines the checks. The installer replaces it, and agents may not edit it. |
| **Seed** | A file the installer writes once; the owner controls it afterwards. |
| **Exception** | A person's entry in `.coast/rules-exceptions.json` that excuses a signature on a path, or a seat until a date. |
| **The number** | "Rules enforced by a check N of M", shown in `CLAUDE.md`, the verifier output, the session-start context and Coast's Rules tab. |

The number's wording lives in `enforcement/checks/vocabulary.json`. To rename it, change `label`, add the old wording to `retired`, and run the tests. `test_vocabulary.py` lists every page still using the old wording.

---

## 3. Quick start

### 3.1 Requirements

| Platform | Needs |
|---|---|
| all | `python3` 3.10+, `git`, `jscpd` 5.1.2 (`npm install -g jscpd@5.1.2`); `gh` optional |
| ios, macos | Xcode command line tools, `swiftlint`, `swift-format` |
| android | a Gradle wrapper, `ktlint`; detekt through the Gradle plugin |
| react-native, web | `node`, `npm`; `typescript`, `eslint`, `prettier` in `node_modules` |
| python | `ruff`, `mypy`, `pytest` (or unittest) |

Pinned versions are in [TOOLCHAIN.md](TOOLCHAIN.md).

### 3.2 Adopt a project

1. Preview the changes (nothing is written):

   ```bash
   python3 enforcement/adopt.py /path/to/project --platform ios --dry-run
   ```

2. Run it. Leave out `--platform` if the manifest makes it obvious (§10.2). Add `--yes` to skip the on/off questions.

   ```bash
   python3 enforcement/adopt.py /path/to/project --platform ios
   ```

3. Commit what it wrote, and push. The first push runs every check.

A first adoption:

1. Copies the checks to `.coast/checks/` and the git hooks to `.githooks/`.
2. Installs the session hook and its keys in `.claude/settings.json`.
3. Writes `.coast/config.json` and `.coast/layout.sh`.
4. Writes linter configs and `docs/domain-rules.md` if missing.
5. Records the theme file in `.coast/paths.json`.
6. Measures existing problems and writes `.coast/ratchet-baseline.json`, with a deadline `ratchet_days` (default 90) away.
7. Writes `.coast/jscpd-baseline.json`.
8. Rewrites the marked block in `CLAUDE.md`.
9. Sets `core.hooksPath` to `.githooks`, remembering any previous hooks path.
10. Scans tracked files for secrets, and exits 1 if it finds any.

The scanner starts from the adoption commit. Older problems are counted in the baselines.

### 3.3 Take a newer version

```bash
python3 <copy>/enforcement/adopt.py /path/to/project --release 1.1.0    # or: latest
```

A re-run replaces governing files, keeps seeds you edited, lowers baselines whose count fell, and changes nothing otherwise.

| Flag | Use |
|---|---|
| `--measure-tools [format,lint]` | Re-measure the tool baselines (a list without `build` skips the build). |
| `--lower-baselines` | Write only the two baselines, lowering counts that fell. Installs nothing; an agent may run it. |

### 3.4 Run the checks by hand

From the project root:

```bash
python3 .coast/checks/check_rules.py --tree --platform ios
python3 .coast/checks/check_rules.py --staged --platform ios
python3 .coast/checks/check_rules.py origin/main HEAD --platform ios
python3 .coast/checks/check_rules.py --files Sources/App/HomeView.swift --platform ios
sh .githooks/pre-push --seat lint
sh .githooks/pre-push --seat build,tests
```

The number, from the standards repo, with the project's switches:

```bash
python3 enforcement/checks/verify_rules.py --document /path/to/project/docs/domain-rules.md --platform ios --config /path/to/project/.coast/config.json
```

---

## 4. The rule documents and the check tag

### 4.1 What is a rule

- **A column-0 bullet that opens in bold**, such as `- **L-1 — No hardcoded user-facing text** … [check: …]`. The id is the leading `PREFIX-n` in the bold, or else a slug of the title. Indented lines belong to it; a blank or unindented line ends it.
- **A leaf prose section**: a heading with no bullet rules and no sub-headings. If it has several tags, the last one counts.

The H1 and any "Sources" section are not rules.

### 4.2 The tag grammar

```
[Coast standard; check: scan:ui-string-literal]
[Swift practice; check: swiftlint:force_unwrapping, swiftlint:force_try]
[SRP; check: advisory:type-size, review]
```

| Reference | Meaning | Bin |
|---|---|---|
| `scan:<id>` | a `block` signature | machine |
| `ratchet:<id>` | a `ratchet` signature | machine |
| `advisory:<id>` | a signature that never fails | advisory |
| `<linter>:<rule>` | a rule the shipped config enables, such as `swiftlint:force_unwrapping`, `eslint:react-hooks/rules-of-hooks`, `detekt:UnsafeCallOnNullableType`, `androidlint:HardcodedText`, `tsc:strict`, `ruff:E501`, `mypy:strict` | machine |
| `<linter>` | a whole linter: `prettier`, `ktlint`, `swiftformat` | machine |
| `tool:<name>` | a tool the pre-push hook runs: `tool:jscpd`, `tool:gh-ruleset`, `tool:warnings-as-errors`, `tool:tests-deadline` | machine |
| `session:<id>` | a Claude Code or git hook, such as `session:chained-cd` | machine |
| `review` | a reviewer judges it | review |
| `process` | the pipeline or a person enforces it | process |
| `context` | explains a rule; not counted, and cannot be combined | — |

A rule whose references are all machine checks is `machine`. A machine check combined with `review`, `process` or `advisory` is `partly`.

### 4.3 How a reference resolves

| Reference | Present when |
|---|---|
| `scan`, `ratchet`, `advisory` | The id is in the signatures for **every** platform the document covers, with the claimed severity. |
| `<linter>:<rule>` | `battery.json` lists the linter, its config exists, and the config **names** the rule. Linter defaults do not count. |
| `tool:<name>` | The manifest's runner file mentions the tool. |
| `session:<id>` | A session-hook file in the manifest mentions the id. |

A signature that no rule names is also a gap.

### 4.4 Which documents apply to which platform

`battery.json` lists each document's platforms. `rules/0x-*.md` apply to all (04 and 05 to app platforms only). `rules/platform/domain-rules-<p>.md` applies to its platform. `rules/platform/ai-features.md` applies to all. A project carries its platform document as `docs/domain-rules.md`, and its number comes from that file.

---

## 5. The scanner — `check_rules.py`

### 5.1 Modes

```
check_rules.py <base> <head> --platform <p>     lines added between two commits
check_rules.py <base> WORKTREE --platform <p>   tracked changes since base + untracked files
check_rules.py --staged --platform <p>          the index (pre-commit); no ratchets
check_rules.py --files a b c --platform <p>     whole files; every line counts as added
check_rules.py --tree --platform <p>            tree-scope signatures and ratchets only
check_rules.py --ratchet <id> --count <n>       judge a tool's count (§5.5)
check_rules.py --ratchet <id> --log <log> [--measured <listing>]
                                                count a tool's log and judge it
check_rules.py --measure <id> --log <log>       print MEASURE / MEASURE-FILE lines
check_rules.py --has-baseline <id> [--per-file] exit 0 if the baseline has an entry
```

| Option | What it does |
|---|---|
| `--only id[,id]` | Runs only these signatures (used by the secret scan). |
| `--paths-override <file>` | The project's path-class file; default `.coast/paths.json`. |
| `COAST_PLATFORM` | Sets the platform instead of `--platform`. |

Run it from the repository root. It applies the project's config on every run, and refuses a config that raises a severity.

Only `--tree` counts ratchets, and a push runs it once. Other modes check only the change, so they take seconds.

- Renames are detected, so a `git mv` adds nothing.
- A new file named like a secret (`.env`, `.p12`, `.sqlite`, `.jks`, …) hits `secret-file` without its content being read.
- Built-ins read the file version the diff saw, so partial staging cannot hide a hit.
- A diff that touches only governing or git files passes.

### 5.2 Output

```
FAIL <check> <path>:<line>:<id>: <words> [<rule>]
ADVISORY <check> <path>:<line>:<id>: <words> [<rule>]
OK ratchet <id>: <n> in the tree, equal to the baseline; deadline <date> [<rule>]
PASS rules
{"result": "pass", "advisories": 0}
```

Exit 0 on pass, 1 on any `FAIL`. The last line is a JSON summary. Hooks, CI and Coast parse the `FAIL` line, so keep its format stable.

### 5.3 The signature table — `rules_signatures.json`

Shared fields sit on the row. Each platform the signature runs on has an entry under `platforms` with its own globs, regex and any overrides.

```json
{
  "signatures": [
    {
      "id": "money-float",
      "rule": "PAY-1",
      "severity": "advisory",
      "scope": "added",
      "applies_to": ["*"],
      "excludes": ["tests", "docs"],
      "words": "a money field typed as binary floating point — money is a decimal",
      "platforms": {
        "ios": {
          "files": ["**/*.swift"],
          "pattern": "(price|amount|total)\\w*\\s*:\\s*(Double|Float)\\b"
        },
        "python": {
          "rule": "DATA-3",
          "files": ["**/*.py"],
          "pattern": "(price|amount|total)\\w*\\s*:\\s*float\\b"
        }
      }
    }
  ]
}
```

`check_rules.flatten_signatures` merges each platform entry over the row. A platform value equal to the row's is refused by `test_check_rules.py`.

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | The name a `scan:<id>` tag uses. |
| `rule` | yes | The rule id printed on each hit; a platform may override it. |
| `severity` | yes | `block`, `ratchet` or `advisory`. |
| `scope` | yes | `added` (added lines) or `tree` (every file, at push). |
| `applies_to` | for regex | Path classes it runs on; `["*"]` for all. |
| `excludes` | no | Path classes it skips. |
| `kind` | no | `builtin` for a check written in code (§5.4). |
| `group` | no | A label grouping related ids. |
| `once` | no | `true` to report a file once, not per line. |
| `words` | yes | The message: what is wrong and where it belongs. |
| `files` | no | Platform file globs that narrow it. |
| `files_excluded` | no | Platform file globs it skips. |
| `pattern` | for regex | A Python `re` pattern matched per line. |
| `paired` | no | A second pattern that must match in the same window of lines. |

Each signature needs fixtures in `checks/tests/plants/<platform>/`: `<id>.fail.<ext>` must hit and `<id>.pass.<ext>` must not.

### 5.4 Built-ins

| Built-in | Module | Finds |
|---|---|---|
| `ui-string-literal` | `literals.py` | User-facing text written inline (Swift, Kotlin/XML, TSX/JSX, Python). |
| `doc-comments` | `check_doc_comments.py` | Public declarations with no doc comment (§6). |
| `import-matrix` | `import_matrix.py` | Imports that break the app / feature / shared layers in `.coast/module-kinds.json`. |
| `blocking-call` (python) | `async_blocking.py` | Blocking calls inside `async def`. |
| `test-criterion-tag` | `test_criteria.py` | Tests with no `AC-<n>` or "criterion" in the name, the three lines above, or the first body line. |
| `type-size` | `type_size.py` | Types over 300 lines or files over 400 (advisory). |
| `unreached-view` | `unreached_views.py` | Public views or components no route constructs. Previews, galleries and tests do not count as routes. A `not-mounted-yet: <task>` comment above the declaration passes. |
| `secret-file` | `check_rules.py` | New, renamed or copied files named like secrets. |
| `plaintext-http` | `check_rules.py` | `http://` URLs, `usesCleartextTraffic="true"`, and `NSAllowsArbitraryLoads` set to `<true/>`. |
| `exported-component` (android) | `check_rules.py` | Manifest components exported with no permission and no LAUNCHER category. |

Added-scope built-ins read the whole file but report only added lines.

### 5.5 Ratchets and baselines

`.coast/ratchet-baseline.json`:

```json
{
  "baselines": [
    {"id": "spacing-literal", "count": 839, "deadline": "2026-12-03",
     "written": "2026-09-04", "by": "the owner", "moves": []},
    {"id": "build-warnings",  "count": 22,  "deadline": "2026-12-03",
     "written": "2026-09-04", "by": "the owner", "moves": []}
  ]
}
```

| | Scanner ratchets | Tool ratchets |
|---|---|---|
| Ids | `spacing-literal`, `inline-comment`, `pii-in-log` | `build-warnings`, `format-findings`, `lint-findings`, `tests-missing` |
| Count rises | fails | fails |
| Count falls | fails until the baseline is lowered in the same commit | passes with a note |
| No entry | baseline is 0 | the check runs strict |

**Per-file map.** `adopt.py --measure-tools` also stores per-file counts for tool ratchets. A scoped push then judges only the changed files, and a rise names the file. Without the map, the check runs on the whole tree and prints the command to add it.

**Deadlines.**

- After the deadline, the ratchet blocks any count above zero.
- An entry with no `deadline` is refused.
- Lowering a count never moves the deadline.
- Only a person moves a deadline, recorded under `moves`.
- Nothing raises a count.

### 5.6 Path classes — `paths.json` and `.coast/paths.json`

Each platform has `extensions` (source file types), `order` (which class wins) and `classes` (name → globs). A file belongs to the first matching class in `order`.

Shipped classes: `git`, `governing`, `plans`, `generated`, `schema`, `theme`, `ui_lib`, `strings`, `manifest`, `docs`, `design_bundle`, `tests`, `gallery`, `ui`, `config_home`. Anything else is product source.

- `gallery` holds previews and component catalogues. They are not routes, and the string-literal check ignores them.
- `strings` is the only allowed home for string catalogs (`one-catalog-per-locale`).

A project overrides classes in `.coast/paths.json`. A named class replaces the shipped globs for that class:

```json
{
  "platforms": {
    "ios": {
      "classes": {
        "theme": ["App/DesignSystem/Theme.swift"],
        "ui_lib": ["App/DesignSystem/**"],
        "plans": ["plans/**", "docs/handoff/**"]
      }
    }
  }
}
```

The installer writes it first when it finds a theme file outside the default path. After that it is governing.

### 5.7 Exceptions

`.coast/rules-exceptions.json` excuses one signature on one path (exact path or `dir/**`):

```json
{
  "exceptions": [
    {"id": "secret-literal", "path": "Tests/AuthTests/FixtureKeys.swift",
     "reason": "a fake sk-ant key read by the code under test",
     "who": "the owner", "when": "2026-09-04"}
  ]
}
```

The file is governing, so agents cannot write it. It also holds seat exceptions (§8.6). Coast projects also honour `approved_native_deviations` in `plans/<feature>/proof.json`.

---

## 6. The doc-comment check — `check_doc_comments.py`

```
check_doc_comments.py --files a b c --platform <p>   named files
check_doc_comments.py --all --platform <p>           the whole tree
```

It prints `FAIL doc-comments <path>:<line>:<name>: …` for each undocumented public declaration.

| Language | Public | Doc comment |
|---|---|---|
| Swift | `public`/`open`, and members of public extensions, protocols and enums; extensions fold into their type per module | `///` or `/** */` |
| Kotlin / Java | Kotlin by default; Java when declared, plus interface members | `/** */` |
| TypeScript | exports, and non-private members of exported classes and interfaces | `/** */` directly above; decorators and `//` may sit between, a blank line may not |
| Python | PEP 257 public functions, classes, methods and `__init__` (read with `ast`); `@overload` and property setters are exempt | a docstring |

A Python file that does not parse reports nothing. The scanner also runs this as the `doc-comments` built-in on added lines. The pre-push hook prints the whole-tree count as advisory.

---

## 7. The verifier — `verify_rules.py`

```
verify_rules.py                                   the whole corpus, from the standards repo root
verify_rules.py --summary                         per-document lines and totals
verify_rules.py --document <file> --platform <p>  one project's copy (repeatable)
verify_rules.py --json                            machine-readable report
verify_rules.py --baseline <file>                 pass only while the gap count equals the file's
verify_rules.py --config <file>                   apply a project's switches
```

It prints a line per document, a `FAIL verify-rules` line per gap, and totals, and exits 1 on any gap. The standards repo's pre-commit hook runs it against `checks/verify-baseline.json` (0 gaps), then runs the test suite.

The verifier and `battery.json` are not installed into projects. The installer runs the verifier at adoption to write the number into `CLAUDE.md`.

---

## 8. The git hooks

The three hooks are POSIX `sh` in `.githooks/`. Each one:

- reads `.coast/layout.sh` and the config (a switched-off check prints `gate: <name> OFF (config)`);
- prints refusals as `FAIL` lines on stderr;
- clears git's `GIT_DIR` variables and sets `PYTHONDONTWRITEBYTECODE=1`.

### 8.1 `pre-commit`

Runs the scanner on the staged changes, including the doc-comment check. Takes seconds.

### 8.2 `commit-msg`

Refuses:

- a missing subject, or one over 100 characters;
- `session:attribution-trailer`: an agent commit (`CLAUDECODE` is set) without `Co-Authored-By: Claude <Model> <version> <email>`. Any Claude trailer must name a model.

Git's own merge and revert messages are exempt, and the hook prints a `gate:` line saying so.

### 8.3 `pre-push` — the battery

First, `scope.py` decides the scope from the pushed ranges and prints `gate: scope <kind> — <reason>`:

| Scope | When | What runs |
|---|---|---|
| `none` | Only docs, plans, design, generated, git or prose files changed. | The diff scan, `gh-ruleset`, and the project's own hooks. |
| `files` | Code changed. | `lint` and `format` on changed files; `build` and `tests` on the affected targets and their dependants; everything else whole. |
| `all` | Governing or manifest files changed, a code file has no target, `--measure` was passed, or `COAST_SCOPE=all` is set. | Everything. |

Affected targets come from `swift package describe`, Gradle `project(':x')` edges, npm workspaces (with `--findRelatedTests` / `vitest related` for jest or vitest), or Python imports. Xcode builds, `tsc`, `mypy`, `npm run build` and `detekt` always run whole.

Then the checks run in this order, and any failure stops the push:

| Check | ios / macos | android | react-native / web | python |
|---|---|---|---|---|
| `build` | `swift build -Xswiftc -warnings-as-errors`, or `xcodebuild build` with `SWIFT_TREAT_WARNINGS_AS_ERRORS=YES` (or the warnings ratchet) | requires `allWarningsAsErrors`; `gradlew build test lint` | requires `strict: true`; `tsc --noEmit`; `npm run build` if present | — |
| `tests` | `swift test`, or `xcodebuild test` on the newest iPhone simulator; or the `tests-missing` ratchet | part of `build` | `npm test` | `pytest -q` with `PYTHONWARNINGS=error` |
| `lint` | `swiftlint --strict` (or ratchet) | `gradlew detekt` | `eslint . --max-warnings 0` | `ruff check .`, `mypy .` |
| `format` | `swift-format lint --strict` (or ratchet) | `ktlint` | `prettier --check .` | `ruff format --check .` |
| `rules-scan` | the scanner on the pushed lines, then `--tree` once | same | same | same |
| `doc-comments` | whole-tree count, advisory | same | same | same |
| `jscpd` | `jscpd . --min-tokens 50 --baseline .coast/jscpd-baseline.json --fail-on-new-clones` | same | same | same |
| `gh-ruleset` | read-only `gh api` check that the default branch has an active ruleset with `pull_request`, `deletion`, `non_fast_forward` and no bypass | same | same | same |

- **Time limit.** Test runs are stopped after `tests_deadline_seconds` (default 900), and the push is refused with a message saying a test is hanging.
- A missing tool is a refusal with its install command.
- Xcode uses the scheme in `.coast/xcode-scheme`, or the first one listed. Builds run with `CODE_SIGNING_ALLOWED=NO`.

### 8.4 Running seats by hand

```
sh .githooks/pre-push --seat lint,format        run the named checks
sh .githooks/pre-push --measure build,format    print MEASURE and MEASURE-FILE counts
```

Git never passes these flags. Such runs take no lock and skip previous hooks. With no ref lines piped in, `--seat` compares HEAD to its upstream (or to the empty tree). `--measure` always covers the whole tree.

### 8.5 One push at a time

A lock directory in the git directory lets one push run per checkout. A lock older than an hour is removed. After waiting, the hook fetches again and stops quickly if the remote moved ahead of this branch.

### 8.6 Excusing a seat

A person can skip one check until a date in `.coast/rules-exceptions.json`:

```json
{"exceptions": [
  {"seat": "build", "reason": "the build needs env vars this checkout has not got",
   "who": "the owner", "when": "2026-09-05", "until": "2026-09-19"}
]}
```

- `seat` is one of `build`, `tests`, `lint`, `format`, `rules-scan`, `doc-comments`, `jscpd`, `gh-ruleset`.
- `until` is required; an entry without it is ignored.
- Every push prints who excused it and why. The check returns the day after `until`.
- `--no-verify` stays forbidden.

### 8.7 A project's own hooks keep running

The installer records the previous hooks path (`core.hooksPath`, or git's hooks directory if it has executable hooks) in `.coast/previous-hooks-path`. Each shipped hook runs the previous hook of the same name after its own checks pass. The installer warns if a `package.json` `prepare` script would reset the path.

---

## 9. The Claude Code session hooks

The hooks are wired in the `hooks`, `disableAllHooks` and `permissions.deny` keys of `.claude/settings.json`. The entry point is `.coast/hooks/claude-hook.py <hook-id>`. It refuses by exiting 2 with the reason on stderr. A hook in `session_hooks.off` exits 0 with a note.

Behaviour follows Anthropic's hooks reference (https://code.claude.com/docs/en/hooks).

| Hook id | Event | Refuses |
|---|---|---|
| `governing-edit` | PreToolUse (edit tools) | editing a governing file, `.claude/settings.json` or `.claude/settings.local.json` |
| `chained-cd` | PreToolUse (Bash) | `cd` followed by another command |
| `infra-command` | PreToolUse (Bash) | mutating infrastructure commands (below) |
| `no-verify` | PreToolUse (Bash) | `--no-verify`, `git commit -n`, `-c core.hooksPath=` |
| `force-push` | PreToolUse (Bash) | `git push` with `--force`, `-f`, `--force-with-lease`, `--force-if-includes`, or `+refspec` |
| `scan-at-commit` | PreToolUse (Bash) | a commit whose staged scan fails |
| `scan-on-edit` | PostToolUse (edit tools) | nothing; shows the scanner's findings to the model |
| `unpushed-at-stop` | Stop | ending a turn with unpushed commits or uncommitted source changes |
| `rules-at-start` | SessionStart | nothing; prints the platform, ratchet counts and what will be refused |

**`infra-command`** refuses `fly`/`flyctl`, `wrangler`, `cloudflared`, `terraform`/`tofu`, `pulumi`, `doctl`, `aws`, `gcloud`, `az` and `nsupdate`, unless the command is read-only (for example `fly status`, `aws s3 ls`, `terraform plan`). It also refuses `gh repo delete`, `gh secret|variable|ruleset`, and mutating `gh api` calls on repo settings endpoints.

Bash hooks split a command on `&&`, `||`, `;`, pipes and newlines, and look inside `$(…)`, `sh -c`, `eval` and `find -exec`. They skip `VAR=value`, wrappers such as `sudo`, `env` and `npx`, and shell keywords. `test_claude_hooks.py` (`BashBypasses`) covers these routes.

**Permission layer.** `permissions.deny` blocks the mutating forms (`Bash(git push --force*)`, `Bash(git * --no-verify *)`, `Bash(fly deploy*)`, `Bash(terraform apply*)` and others) and edits to governing paths. It holds even where a hook cannot see the command.

**Switching hooks off.** The project's `"disableAllHooks": false` overrides a user setting. Only `claude --settings '{"disableAllHooks": true}'` turns them off, for one run; the git hooks still apply.

---

## 10. The installer — `adopt.py`

### 10.1 Usage

```
adopt.py <project> [--platform ios|macos|android|react-native|web|python]
                   [--dry-run] [--by <name>] [--secret-scan]
                   [--jscpd-bin <path>] [--measure-tools [build,format,lint,tests]]
                   [--release <version>|latest] [--lower-baselines]
                   [--init | --yes] [--owner <name>] [--product <name>] [--org <name>]
                   [--checks-dir <path>]
```

Every flag is described in [docs/options.md](../docs/options.md), and `adopt.py --help` prints them.

| Environment variable | Use |
|---|---|
| `COAST_STANDARDS_CACHE` | Release cache (default `~/.cache/coast-standards/`). |
| `COAST_STANDARDS_RELEASES` | Mirror address for release tarballs. |

`--release` is the only network use. A downloaded release whose `CHECKS-VERSION` does not match is refused. The report prints `wrote`, `replaced`, `unchanged`, `kept (founder-edited)` or `would write` for each file.

### 10.2 Platform detection

Without `--platform`, the installer reads `.coast/platform`, or else:

| Found | Platform |
|---|---|
| `Package.swift` with only `.iOS(` / only `.macOS(` | ios / macos |
| `.xcodeproj` whose `SDKROOT` / `SUPPORTED_PLATFORMS` name only `iphoneos` / only `macosx` | ios / macos (both or neither: asks) |
| Gradle files | android |
| `package.json` depending on `react-native` | react-native |
| other `package.json` | web |
| `pyproject.toml`, `requirements.txt`, `setup.py` | python |

### 10.3 What lands where

| Path | Owner | Contents |
|---|---|---|
| `.coast/checks/` | governing | The scanner, its modules and tables, `layout`, `config` (not the verifier). |
| `.coast/hooks/claude-hook.py` | governing | The session hook. |
| `.coast/config.json` | governing; edited by a person | Switches and names (§10.5). |
| `.coast/layout.sh` | governing | The layout table for the `sh` hooks. |
| `.githooks/` | governing | The three git hooks. |
| `.claude/settings.json` | governing keys only | `hooks` and `disableAllHooks` are replaced; `permissions.deny` is merged; other keys are kept. |
| `.coast/platform`, `.coast/standards-version` | governing | The platform, and the adopted release. |
| `.coast/seeds.json`, `.coast/installed.json` | governing | Seed hashes, and the files the last run installed (so later runs remove stale ones). |
| `.coast/paths.json` | governing; written once | Path-class overrides. |
| `.coast/ratchet-baseline.json`, `.coast/jscpd-baseline.json` | governing | Baselines. |
| `.coast/previous-hooks-path` | governing | The previous hooks path. |
| `.coast/rules-exceptions.json`, `.coast/module-kinds.json` | governing; written by a person | Exceptions, and module layers. |
| `.coast/xcode-scheme` | optional; written by a person | The Xcode scheme to build. |
| Linter configs | seed | Written when missing; updated while unedited; kept once edited. |
| `docs/domain-rules.md` | seed | Upgraded from an older rules version, keeping the old copy as `docs/domain-rules.v<N>.md`. |
| `CLAUDE.md` | the marked block only | Rewritten from `TEMPLATE-PROJECT-CLAUDE.md` between `<!-- coast-standards: begin -->` and `end -->`. Broken markers stop the run before anything is written. |

### 10.4 Idempotency

A second run changes nothing. The tests check this, along with: `--dry-run` writes nothing, text outside the `CLAUDE.md` block survives, and edited seeds are kept.

### 10.5 Configuration — `.coast/config.json`

Every key, default and layout path is listed in [docs/options.md](../docs/options.md). What a maintainer needs:

- One loader, `config.py`, reads the file for every part of the layer. `config.py --sh` prints it as shell variables for the hooks.
- Defaults are in `config.default.json`. The project file merges over them (objects by key; lists replace), then the run's flags.
- The loader refuses a raised severity, a `layout.state_dir`, a non-list `off`, and a non-integer `ratchet_days` or `tests_deadline_seconds`.
- An `off` switch also counts in the number. `verify_rules.py --config` shows it, for example `enforced by a check 21 of 74 (3 switched off)`.
- `--init` asks one screen of on/off questions per group. `--yes` writes `config.default.json` byte for byte.
- `layout.json` is the only place that names the layer's paths. Values may refer to other keys as `{key}`. `test_config.py` fails if any shipped file hard-codes an old path.

---

## 11. The linter configs

The configs in `lint/` switch on the rules the documents cite. The verifier fails if a cited rule is missing.

| File | Installed as | Notable settings |
|---|---|---|
| `swiftlint.yml` | `.swiftlint.yml` | `force_unwrapping`, `force_cast`, `force_try` at error; type 300 and file 400 lines as warnings |
| `swift-format.json` | `.swift-format` | Apple swift-format config |
| `eslint.config.mjs` | same | type-checked rules, `no-floating-promises`, react-hooks rules when the plugin is installed |
| `.prettierrc.json` | same | |
| `tsconfig.seed.json` | `tsconfig.json` | a strict starter, written only if the project has none |
| `detekt.yml` | same | `UnsafeCallOnNullableType`, `LargeClass` 300 |
| `lint.xml` | same | `HardcodedText` at error |
| `.editorconfig` | same | ktlint settings |
| `ruff.toml` | same | `B` (bugbear) |
| `mypy.ini` | same | `strict = True` |

---

## 12. Versioning

| What | Where |
|---|---|
| Release number | `CHECKS-VERSION` (semantic version) |
| Tag | `v<number>` |
| Notes | `CHANGELOG.md`, one `## <number> — <date>` section per release |
| Publishing | `.github/workflows/release.yml` checks the tag and publishes the GitHub release. |
| A project's release | `.coast/standards-version`: `1.0.0` from a tarball or tagged clone, `1.0.0+<commit>` otherwise |
| Rules version | First line of `docs/domain-rules.md`: `<!-- coast-rules-version: N -->`. The rules are at version 9. |

Each project has its own copy of the checks and upgrades on its own schedule with `--release`. An older rules document is upgraded at adoption. A current-version copy that differs is the owner's edit, and is left alone.

### 12.1 Cutting a release

1. Bump `CHECKS-VERSION`. Use a semantic version with no `v`.

   | Change | Release type |
   |---|---|
   | A new check, switch or refusal | minor |
   | Fixes only | patch |
   | A change that makes an adopted project's setup stop working | major |

2. In `CHANGELOG.md`, move the entries under `## Unreleased` into a new `## <version> — <YYYY-MM-DD>` section. Put it directly under `## Unreleased`, which stays, empty.
3. Commit both files.
4. Tag and push the tag:

   ```bash
   git tag v<version>
   git push origin v<version>
   ```

   The release workflow checks the tag against `CHECKS-VERSION` and the changelog. It then publishes the GitHub release, with that changelog section as its notes.

5. Do not re-adopt the owner's projects as part of a release. Each project takes the new release when its owner asks, with `adopt.py <project> --release <version>`.

#### How to write release notes

Add entries to `## Unreleased` in this format as each change lands. Then a release only moves them.

**Format:**

1. After the heading, one sentence that sums up the release.
2. Entries grouped under `### Added`, `### Changed`, `### Fixed` and `### Removed`. Include only the groups that have entries.
3. A final `### Upgrading` section: what an adopting project must do, or "Re-run `adopt.py <project>`. No other changes are needed."

**Each bullet:**

- Is **one line**. Do not wrap it. GitHub release pages show every line break, so a wrapped bullet shows as broken lines.
- Starts with a bold phrase that says what changed, in plain words.
- Follows with one or two sentences: the problem it solves, and what the reader needs to do or set, if anything.
- Names things the way a developer using the tool sees them. Write "the test step of the pre-push hook", not "the tests seat". Write "time limit", not "wall-clock deadline".
- Leaves out history: no incident stories, no dates other than the heading, no "born of", no rule numbers, no task ids, no internal decision numbers.

**Example of a good bullet:**

```markdown
- **The pre-push hook now stops test runs that take longer than 15 minutes.** A hanging test used to block the push forever with no message; now the push is refused with a message saying a test is hanging. Set `tests_deadline_seconds` in `.coast/config.json` to allow longer runs.
```

---

## 13. Troubleshooting

Refusals a developer meets day to day (a count went up or down, a hanging test, a build warning, another push running, no simulator, jscpd missing, a refused file, a wrong check) are covered in [docs/when-a-check-stops-you.md](../docs/when-a-check-stops-you.md). The cases below are the ones a maintainer meets.

**A ratchet count fell and the push was refused.**

- *What it means:* a scanner count is below its baseline.
- *What to do:* run `adopt.py <project> --lower-baselines` and commit the baseline with the change. An agent may do this, because it only lowers counts.

**"the rules scanner is not installed."**

- *What it means:* the project is not adopted, or its checks are missing.
- *What to do:* run `adopt.py` on the project.

**The session hooks never fire.**

- *What it means:* the session did not start at the repository root, or the settings are missing.
- *What to do:* start at the root, and check `.claude/settings.json` has `hooks` and `"disableAllHooks": false`, and that `.coast/hooks/claude-hook.py` exists.

**The secret scan flagged a test fixture.**

- *What it means:* the value looks like a real credential (`sk-ant-…`, `ghp_…`, `AKIA…`, a PEM header). Values starting `test-`, `fake_`, `dummy.`, `sample-` or `stub-` are already excused.
- *What to do:* excuse the path in `.coast/rules-exceptions.json` (§5.7).

**A signature is wrong.**

- *What it means:* the pattern flags good code.
- *What to do:* fix it in the standards repo with fixtures that prove both directions (§14.1), then re-adopt. Until then, the owner can excuse it (§5.7, §8.6).

**`CLAUDE.md` markers stop the run.**

- *What it means:* the `coast-standards` begin/end markers are out of order, unmatched or duplicated.
- *What to do:* fix the markers so there is exactly one block, then re-run.

---

## 14. Extending

### 14.1 Add a signature

1. Add a row to `checks/rules_signatures.json`, with a `platforms` entry for each platform.
2. Add its id to `EXPECTED_IDS` in `test_check_rules.py`.
3. Add `<id>.fail.<ext>` and `<id>.pass.<ext>` under `checks/tests/plants/<platform>/`.
4. Tag the rule: `[…; check: scan:<id>]` (or `ratchet:` / `advisory:`).
5. Run the tests and the verifier. The verifier's gap count must not rise.
6. Re-adopt the projects that need it.

### 14.2 Add a built-in

1. Write a module beside the scanner.
2. Register its id in `check_rules.builtin_hits`.
3. Set `"kind": "builtin"` on the signature, and add fixtures.

The installer ships every `.py` and `.json` in `checks/` except the verifier's files.

### 14.3 Add a seat

1. In `hooks/pre-push`, add the case behind `wants <name>`, print `gate: <name>`, and report failures as `FAIL` lines.
2. List it under `tools` in `battery.json` for each platform.
3. Tag the rule `tool:<name>`.
4. Add a passing and a failing test in `test_hooks_and_adopt.py`.

Seat exceptions work for the new name automatically.

### 14.4 Add a session hook

1. Add a function and dispatch entry in `claude-hook.py`.
2. Wire it in `claude-settings.json` with a `statusMessage` naming the id.
3. Tag the rule `session:<id>`.
4. Add a test in `test_claude_hooks.py`.

### 14.5 Add a platform

1. Add it to `paths.json`, `rules_signatures.json` and `battery.json`.
2. Write `rules/platform/domain-rules-<p>.md`.
3. Add the `pre-push` case and the linter configs.
4. Add it to `PLATFORMS`, `LINT_DESTINATIONS` and platform detection in the installer.

---

## 15. Tests

```bash
python3 -m unittest discover -s enforcement/checks/tests -p 'test_*.py'
```

Run from the standards repo root. It takes about two minutes. jscpd and node must be installed, or their tests fail.

| File | Covers |
|---|---|
| `test_check_rules.py` | Scanner modes, exceptions, ratchets, and every fixture. |
| `test_verify_rules.py` | The parser, config readers, bins, and the real corpus. |
| `test_corpus_sections.py` | Required sections in every app document. |
| `test_lint_configs.py` | Every cited linter rule is enabled; the ESLint config loads. |
| `test_claude_hooks.py` | Every session hook. |
| `test_hooks_and_adopt.py` | Installer idempotency, seeds, secret scan, git hooks, exceptions, previous hooks, layout moves. |
| `test_config.py` | The layout table, every switch, `--config`, the questions, and `--yes`. |

---

## 16. Limits, stated plainly

- The scanner reads lines, not program structure. Rules that need a syntax tree are deferred.
- Kotlin/Java nested members and accessors are not checked for doc comments.
- Warning, lint and format ratchets exist only for Swift. Other platforms run strict.
- The number is computed at adoption. The session-start hook does not recompute it.
- About half the rules are reviewer rules, with no machine check yet.
- Session hooks need a session started at the repository root, and a command-line `--settings` can turn them off for one run.
- `infra-command` reads verbs, not each tool's grammar. A read-only command with several option values before its verb is refused; reorder it.
