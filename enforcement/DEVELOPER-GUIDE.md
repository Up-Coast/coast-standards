# Coast Standards Enforcement — Internal Developer Guide

*Last updated: 2026-09-08*

**Audience: people working on this layer itself** — the scanner, the hooks, the installer.
It is the full technical reference: how a rule is held, what is installed into a project,
every file and flag the code reads or writes, and how to extend or excuse it. It describes
what the code does today (release 1.0.0, 7 September 2026). The design rationale and
the build history live in [README.md](README.md).

If you are a founder or a developer **installing this into your own product**, you want the
public documentation instead: [docs/](../docs/README.md). It says the same things in plain
words and leaves out what only a maintainer needs.

---

## 1. What it is

A set of rule documents (`rules/`) where every rule names the check that holds it, plus
the machinery that makes those checks real in any git repository:

- a **scanner** (`check_rules.py`) that runs regex signatures over the lines a change adds,
  scoped by what kind of file they land in;
- a **doc-comment check** (`check_doc_comments.py`) for Swift, Kotlin/Java, TypeScript and
  Python;
- a **verifier** (`verify_rules.py`) that proves every rule names a check that exists, and
  prints the honest number, *"enforced by a check N of M"*;
- **linter configs** with the opt-in rules the documents cite switched on;
- three **git hooks** (`pre-commit`, `commit-msg`, `pre-push`) and a set of **Claude Code
  session hooks** that refuse the things an agent must not do;
- an **installer** (`adopt.py`) that puts all of it into a project idempotently and writes
  baselines so an existing codebase adopts without a rewrite day.

Everything is stdlib Python 3 and POSIX `sh`. No network, no model, no package to install
beyond the platform's own toolchain (Xcode, Gradle, Node, Python) and `jscpd`.

The one principle behind every design choice: **a rule that lives only in a document is a
request, and a request loses to whatever is cheapest for the session in front of the code.**
So every rule is sorted into a bin, out loud, and the machine-held ones refuse the change
on the builder's own machine, in seconds, before anything leaves it.

---

## 2. Concepts

| Term | Meaning |
|---|---|
| **Rule** | One bullet in a rule document (`- **L-1** …`) or one leaf section of prose. Every rule ends with a `[…; check: …]` tag. |
| **Check tag** | The last square bracket in a rule containing `check:`. Names one or more references, comma-separated. See §4. |
| **Bin** | Where a rule sits: `machine`, `partly`, `advisory`, `review`, `process`, or `open` (a gap). Only `machine` counts toward the headline number. |
| **Signature** | One row in `rules_signatures.json`: an id, a severity, the path classes it applies to, the words it prints, and a regex per platform it runs on. |
| **Path class** | A named set of globs in `paths.json` (`theme`, `ui`, `tests`, `governing`, `strings`, …). A file belongs to the first class in the platform's `order` that matches it. Signatures are scoped by class. |
| **Severity** | `block` (any hit fails), `ratchet` (counted over the tree; the count may only fall), `advisory` (printed, never fails). |
| **Baseline** | A committed count for a ratchet, with a deadline. `.coast/ratchet-baseline.json` for scanner and tool ratchets; `.coast/jscpd-baseline.json` for duplicate code. |
| **Seat** | One check in the pre-push battery: `build`, `tests`, `lint`, `format`, `rules-scan`, `doc-comments`, `jscpd`, `gh-ruleset`. Each prints `gate: <name>` and refuses in its own lines. |
| **Scope** | What a push changed, read before any seat runs (`scope.py`): `none` (prose only — the code seats are skipped), `files` (code — the seats run on the changed files and the affected modules), `all` (the checks themselves changed — everything runs). |
| **Governed file** | A file the installer owns and replaces on every run, and that agents may not edit (the session hooks refuse). |
| **Seed** | A file the installer writes once and the founder owns afterwards (linter configs, `docs/domain-rules.md`). |
| **Exception** | A human-written entry in `.coast/rules-exceptions.json` excusing one signature on one path, or one seat until a date. |
| **The number** | "Rules enforced by a check N of M", computed by the verifier from a rules document. It appears in a project's `CLAUDE.md`, in the verifier's output, in the session-start context, and in Coast's Rules tab. Its wording lives in one place, `enforcement/checks/vocabulary.json`, which the verifier, the installer and the hook read (the file ships to projects with the checks). To rename it: change `label`, append the old wording to `retired`, run the tests; `test_vocabulary.py` lists every page still using the old name, and the hook keeps reading CLAUDE.md blocks written under the old name until the project is re-adopted. |

---

## 3. Quick start

### 3.1 Requirements

| Platform | Needs on the machine |
|---|---|
| all | `python3` 3.10 or newer (the checks use `X \| None` annotations), `git`, `jscpd` 5.1.2 (`npm install -g jscpd@5.1.2`), `gh` optional |
| ios, macos | Xcode command line tools (`swift`, `xcodebuild`, `xcrun`), `swiftlint`, `swift-format` |
| android | a Gradle wrapper in the project, `ktlint`; detekt via the Gradle plugin |
| react-native, web | `node`/`npm`; `typescript`, `eslint`, `prettier` in `node_modules` |
| python | `ruff`, `mypy`, `pytest` (or unittest) |

Pinned versions and the primary sources they were verified against are in
[TOOLCHAIN.md](TOOLCHAIN.md).

### 3.2 Adopt a project

From a clone of this repo, or from a fetched release (the [quickstart](../docs/quickstart.md)
has the one command that puts the newest release at `~/.cache/coast-standards/<version>/`):

```bash
python3 enforcement/adopt.py /path/to/project --platform ios
```

Add `--dry-run` first to see the report without writing anything. `--platform` may be
omitted when the project's manifest makes it obvious (see §10.2).

A first adoption:

1. copies the checks to `.coast/checks/` and the three git hooks to `.githooks/`;
2. installs the Claude Code session layer (`.coast/hooks/claude-hook.py`; the `hooks`,
   `disableAllHooks` and `permissions.deny` keys of `.claude/settings.json`, rendered
   from the template with the layout's paths);
3. writes `.coast/config.json` (§10.5) — at a terminal it asks the on/off questions first,
   one screen per group; `--yes` takes every default — and `.coast/layout.sh`, the layout
   table rendered for the `sh` hooks;
4. writes the platform's linter seeds (not the ones the config switches off) and
   `docs/domain-rules.md` if absent;
5. binds the theme file it finds into `.coast/paths.json`;
6. **measures** the tree: scanner ratchets (`check_rules.py --tree`), then the build's
   warnings, the formatter's and linter's findings, and whether a test target exists
   (`pre-push --measure build,format,lint,tests`); writes them to
   `.coast/ratchet-baseline.json` with a deadline `ratchet_days` (default 90) out;
7. writes `.coast/jscpd-baseline.json` from jscpd's fingerprints;
8. rewrites the marked block in `CLAUDE.md` with the platform, the release, the names
   from the config and the number (with the count switched off);
9. sets `git config core.hooksPath .githooks`, recording any previous hooks path so those
   hooks keep running;
10. runs a secret scan over every tracked file and exits 1 if it finds anything.

Then commit what it wrote and push. The first push runs the whole battery; the scanner
starts at the adoption commit, so lines committed before the checks existed are legacy and
belong to the baselines.

### 3.3 Take a newer version

Re-run the same command, or ask the installed copy to fetch a release:
`python3 <copy>/enforcement/adopt.py /path/to/project --release 1.1.0` (or `latest`). The
release is downloaded into the cache and its own installer runs. Governed files are replaced, seeds you edited are kept with a
note, a baseline whose count fell is lowered (the deadline does not move), and nothing
changes when nothing changed. `--measure-tools` forces the tool baselines to be
re-measured; `--measure-tools format,lint` re-measures without a build.

### 3.4 Run the checks by hand

```bash
# the scanner, from the project root
python3 .coast/checks/check_rules.py --tree --platform ios
python3 .coast/checks/check_rules.py --staged --platform ios
python3 .coast/checks/check_rules.py origin/main HEAD --platform ios
python3 .coast/checks/check_rules.py --files Sources/App/HomeView.swift --platform ios

# one seat of the push battery
sh .githooks/pre-push --seat lint
sh .githooks/pre-push --seat build,tests

# the number, from the standards repo (with the project's switches applied)
python3 enforcement/checks/verify_rules.py --document /path/to/project/docs/domain-rules.md --platform ios --config /path/to/project/.coast/config.json
```

---

## 4. The rule documents and the check tag

### 4.1 What is a rule

The verifier's parser treats these as rules:

- a column-0 bullet that opens in bold: `- **L-1 — No hardcoded user-facing text** … [check: …]`.
  The id is the leading `PREFIX-n` inside the bold when there is one; otherwise a slug of the
  bold title. Indented continuation lines belong to the rule; a blank line or an unindented
  line ends it.
- a leaf section (a heading with no bullet rules and no sub-headings) of prose; the tag may
  appear anywhere in it and the last one wins.

Not rules: the H1, and any section titled "Sources".

### 4.2 The tag grammar

```
[Coast standard; check: scan:ui-string-literal]
[Swift practice; check: swiftlint:force_unwrapping, swiftlint:force_try]
[SRP; check: advisory:type-size, review]
```

| Reference | Meaning | Bin |
|---|---|---|
| `scan:<id>` | a scanner signature with severity `block` | machine |
| `ratchet:<id>` | a scanner signature with severity `ratchet` | machine |
| `advisory:<id>` | a scanner signature that never fails | advisory |
| `<linter>:<rule>` | a rule the shipped config enables: `swiftlint:force_unwrapping`, `eslint:react-hooks/rules-of-hooks`, `detekt:UnsafeCallOnNullableType`, `androidlint:HardcodedText`, `tsc:strict`, `ruff:E501`, `mypy:strict` | machine |
| `<linter>` | the linter as a whole: `prettier`, `ktlint`, `swiftformat` | machine |
| `tool:<name>` | a tool the pre-push battery runs: `tool:jscpd`, `tool:gh-ruleset`, `tool:warnings-as-errors` | machine |
| `session:<id>` | a Claude Code or git hook: `session:chained-cd`, `session:attribution-trailer` | machine |
| `review` | only a mind can judge it; a per-rule review row | review |
| `process` | held by the pipeline or a person | process |
| `context` | this bullet explains a rule and is not one; not counted (cannot share a tag) | — |

A rule with more than one reference is `machine` when every reference is a machine check,
`partly` when a machine check shares the rule with `review`, `process` or `advisory`.

### 4.3 How a reference resolves

Resolution is files on disk, nothing else:

- `scan`/`ratchet`/`advisory`: the id is in the signatures table of **every** platform the
  document applies to, with the severity the tag claims.
- `<linter>:<rule>`: the platform's `battery.json` entry lists that linter, its config exists,
  and the config **names** the rule enabled. The verifier reads SwiftLint and detekt YAML,
  ESLint flat config, `lint.xml`, `tsconfig`, `mypy.ini` and `ruff.toml`. It does not know
  any linter's default set: a config must name the rule or the rule is not held.
- `tool:<name>`: the manifest's runner file exists and mentions the tool.
- `session:<id>`: one of the manifest's session-hook files mentions the id.

Also a gap: a signature that no rule names.

### 4.4 Which documents apply to which platform

`battery.json` lists every document with its platforms. The numbered `rules/0x-*.md` files
apply to all (04 and 05 to the app platforms only); `rules/platform/domain-rules-<p>.md`
to its platform; `rules/platform/ai-features.md` to all. A project carries one platform
document as `docs/domain-rules.md`, and its number is computed from that file alone.

---

## 5. The scanner — `check_rules.py`

### 5.1 Modes

```
check_rules.py <base> <head> --platform <p>     lines added between two commits
check_rules.py <base> WORKTREE --platform <p>   tracked changes since base + every untracked file
check_rules.py --staged --platform <p>          the index (pre-commit); touched files only, no ratchets
check_rules.py --files a b c --platform <p>     whole files (editor hook); every line is "added"
check_rules.py --tree --platform <p>            no diff: tree-scope signatures and ratchets only
check_rules.py --ratchet <id> --count <n>       judge a tool's count as a ratchet (see §5.5)
check_rules.py --ratchet <id> --log <log> [--measured <listing>]
                                                count the tool's own output and judge it; with a
                                                listing, over those files against the per-file map
check_rules.py --measure <id> --log <log>       MEASURE and MEASURE-FILE lines for the installer
check_rules.py --has-baseline <id> [--per-file] exit 0 when the baseline has an entry for <id>
                                                (with --per-file: one carrying the per-file map)
```

Options: `--only id[,id]` runs only the named signatures (used by the installer's secret
scan; git never passes it); `--paths-override <file>` names a project's own path bindings
(default `.coast/paths.json`). The platform also comes from `COAST_PLATFORM`. Run from the
repository root. The project's config (§10.5) is read on every run: a signature in
`rules.off` is not in the list, a severity in `rules.severity` is lowered, and the
`retired_words` join the `retired-wording` pattern; a config that asks to raise a
severity is refused with a `FAIL config` line and exit 1.

The whole-tree pass with the ratchets is `--tree` alone, and the push runs it once. Every
other mode judges the change: the added-scope signatures on the added lines, the tree-scope
`block` signatures on the changed files only, no ratchet — so a commit-time or editor-time
scan takes seconds on a large repository.

What "the change" means, precisely:

- Every diff is asked for with rename detection (`-M`), and a renamed or copied file is
  diffed under both its paths, so a `git mv` adds nothing and only the lines the move
  changed count.
- A file whose name is a secret or data shape (`.env`, `.p12`, `.sqlite`, `.jks`, …) is
  `secret-file` when git's status letter says it is new, renamed or copied — its content is
  never read, because a binary adds no line to any diff.
- A built-in reads the file as the diff saw it: the index blob for `--staged`, the commit's
  blob for `<base> <head>`, the worktree file for `WORKTREE`, `--files` and untracked files.
  Partial staging cannot move or hide a hit.

A diff that touches only governing or git paths passes: gate maintenance is the founder's
own work.

### 5.2 Output

```
FAIL <check> <path>:<line>:<id>: <words> [<rule>]
ADVISORY <check> <path>:<line>:<id>: <words> [<rule>]
OK ratchet <id>: <n> in the tree, equal to the baseline; deadline <date> [<rule>]
PASS rules
{"result": "pass", "advisories": 0}
```

Exit 0 on pass, 1 on any FAIL. The last line is always a JSON summary. The `FAIL` line is
the format every hook, the battery, CI and Coast parse; keep it stable.

### 5.3 The signature table — `rules_signatures.json`

One row per signature. The row carries the fields every platform shares once; under
`platforms`, one entry per platform the signature runs on carries that platform's own
globs and regex, plus any shared field whose value differs there. A signature absent from
a platform is not listed under it.

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

`check_rules.flatten_signatures` turns the file into one list per platform, in row order,
each entry the row's shared fields with the platform's entry laid over them. That flat
shape is what the scanner, the plants and the verifier read; nothing downstream sees the
rows. A platform value equal to the row's is a needless copy — `test_check_rules.py`
refuses it.

| Field | Where | Required | Meaning |
|---|---|---|---|
| `id` | row | yes | the signature's name; a rule's `scan:<id>` tag names it |
| `rule` | row, platform may differ | yes | the rule id it holds, printed in brackets on every hit (each platform document numbers its own rules) |
| `severity` | row | yes | `block`, `ratchet` or `advisory` |
| `scope` | row | yes | `added` (only added lines) or `tree` (every file, at push) |
| `applies_to` | row, platform may differ | yes for regex | path classes the signature runs on; `["*"]` for every class |
| `excludes` | row, platform may differ | no | path classes it never runs on (`tests`, `strings`, `theme`, …) |
| `kind` | row, or a platform's own | no | `builtin` for signatures implemented in code rather than regex (§5.4) |
| `group` | row | no | a label such as `native-pattern` or `secret-literal` grouping related ids |
| `once` | row | no | `true` to report a file once, not per line (`second-theme-file`, `secret-file`) |
| `words` | row, platform may differ | yes | the sentence printed on a hit — say what is wrong and where it belongs |
| `files` | platform | no | file globs narrowing it further (`**/*.swift`) |
| `files_excluded` | platform | no | file globs it skips even inside an applying class |
| `pattern` | platform | yes for regex | a Python `re` pattern matched against each line |
| `paired` | platform | no | a second pattern that must also match within the same joined-lines window (native-pattern shape) |

Every signature has a plant: `checks/tests/plants/<platform>/<id>.fail.<ext>` must hit and
`<id>.pass.<ext>` must not. `test_check_rules.py` runs every plant in both directions, and
pins the ids each platform's flattened list holds, in order, so a row that drops a platform
shows in a test and not in a hook.

### 5.4 Built-ins

Some rules need more than a line regex. These are implemented in code beside the scanner
and dispatched by id:

| Built-in | Module | What it does |
|---|---|---|
| `ui-string-literal` | `literals.py` | lexes the whole file the way Coast's copy guard did: Swift (with the guard's skip contexts — SF Symbols, identifiers, URLs, comparisons, SQL), Kotlin/XML, TSX/JSX text between tags, bare text on its own line and the known text props (a comparison, an arrow, a generic or one name of a multi-line import is not copy), Python message shapes; only added lines are reported |
| `doc-comments` | `check_doc_comments.py` | every public declaration without a doc comment (§6) |
| `import-matrix` | `import_matrix.py` | module-layer imports against `.coast/module-kinds.json` (app / feature / shared) over the platform's layout: Swift package targets, Gradle modules, Node `Modules/<M>/src` or the root `src/`, and for Python the project package's subpackages (`src/<pkg>/` or `<pkg>/`, found by `__init__.py`; the package root is the app target) or, with several packages side by side, each package (imports read with `ast`); a TypeScript named list broken over lines is read as one import |
| `blocking-call` (python) | `async_blocking.py` | a blocking call counted only inside `async def` |
| `test-criterion-tag` | `test_criteria.py` | a test declaration with no `AC-<n>` or "criterion" in its name, the three lines above, or its first body line |
| `type-size` | `type_size.py` | a type past 300 lines or a file past 400, reported once (advisory) |
| `secret-file` | `check_rules.py` | a file whose name matches the signature's globs, judged from git's status letter (new, renamed, copied); the content is never read, so a binary is caught |
| `plaintext-http` | `check_rules.py` | a plain `http://` URL or `usesCleartextTraffic="true"` on a line, and the plist toggle `<key>NSAllowsArbitraryLoads</key>` followed by `<true/>` on the same or the next line — reported at the `<true/>` line, the one a flip adds |
| `exported-component` (android) | `check_rules.py` | a manifest component with `android:exported="true"`, no `android:permission` on the tag and no LAUNCHER category in its body, the tag spanning any number of lines — reported at the `exported` line |

An added-scope built-in lexes the whole file and reports only the added lines, so a hit that
needs context (the key above a toggled value) survives a one-line edit.

### 5.5 Ratchets and baselines

`.coast/ratchet-baseline.json`:

```json
{
  "baselines": [
    {"id": "spacing-literal", "count": 839, "deadline": "2026-12-03",
     "written": "2026-09-04", "by": "Pat Lee", "moves": []},
    {"id": "build-warnings",  "count": 22,  "deadline": "2026-12-03",
     "written": "2026-09-04", "by": "Pat Lee", "moves": []}
  ]
}
```

Two kinds of ratchet share the file:

- **Scanner ratchets** (`spacing-literal`, `inline-comment`, `pii-in-log`): the scanner counts
  the tree deterministically. Above the baseline fails. Below it fails too, until the baseline
  is lowered in the same commit (the message says the number). No entry means a baseline of 0.
- **Tool ratchets** (`build-warnings`, `format-findings`, `lint-findings`, `tests-missing`):
  the pre-push seat runs the tool into a log and hands the log to
  `check_rules.py --ratchet <id> --log <log>`, the one reader of the `file:line:col:
  warning|error:` lines (`tests-missing` hands a count). Above the baseline fails; **below it
  passes with a note**, because a build's warning count depends on what it recompiled. With
  no entry the seat runs strict (`-warnings-as-errors`, `--strict`), so a fresh repository is
  held at zero from its first push.
- **The per-file map** (`files`, written by `adopt.py --measure-tools`): each tool entry
  carries the count per file beside its total. A scoped push (§8.3) hands the seat's
  listing as `--measured`, and the judgment is over those files — plus any file the tool
  reported on — against the same files' baseline: a rise refuses and names the file, a fall
  passes with the note, files the push did not touch keep their numbers. An entry without
  the map cannot judge a scoped run (`--has-baseline <id> --per-file` says so), so the seat
  runs whole and prints the re-measure that enables it. The map follows a lowered or equal
  total; a rise leaves entry and map as they were.

Past the deadline every ratchet becomes `block`: anything above zero refuses. An entry with
no `deadline` is refused before any count is judged (`FAIL ratchet
.coast/ratchet-baseline.json:0:<id>: … has no deadline`) — a baseline without a date would be
a permanent allowance nobody agreed to. Lowering the count never moves the date. Only a person moves a deadline, and the move is recorded under
`moves` with who and why. The installer writes and lowers baselines; nothing raises one.

### 5.6 Path classes — `paths.json` and `.coast/paths.json`

Per platform: `extensions` (what counts as source), `order` (which class wins when several
match), and `classes` (name → globs). The shipped classes are `git`, `governing`, `plans`,
`generated`, `schema`, `theme`, `ui_lib`, `strings`, `manifest`, `docs`, `design_bundle`,
`tests`, `ui`, `config_home`; a file in none of them is ordinary product source.

A project overrides bindings in `.coast/paths.json`, which is merged **over** the platform's
defaults class by class (a class you name replaces the shipped globs for that class;
`extensions` replaces too):

```json
{
  "platforms": {
    "ios": {
      "classes": {
        "theme": ["KetoTracker/DesignSystem/Theme.swift"],
        "ui_lib": ["KetoTracker/DesignSystem/**"],
        "plans": ["plans/**", "docs/handoff/**"]
      }
    }
  }
}
```

The installer writes the first version of this file when it finds a theme-shaped file
outside the default theme path. It is governing after that.

The `strings` class is the one catalog home: `one-catalog-per-locale` never fires inside it
and fires on every catalog file outside it (`messages.json` beside a feature, a `strings.json`
in a module). Rebinding the class moves the exemption with it — on web and React Native the
table carries no hand-listed catalog paths of its own.

### 5.7 Exceptions

`.coast/rules-exceptions.json` excuses one signature on one path:

```json
{
  "exceptions": [
    {"id": "secret-literal", "path": "Tests/AuthTests/FixtureKeys.swift",
     "reason": "a fake sk-ant key read by the code under test",
     "who": "Pat Lee", "when": "2026-09-04"}
  ]
}
```

`path` is an exact path or a `dir/**` glob. Coast projects also honour the plan's
`approved_native_deviations` in `plans/<feature>/proof.json`. The file is governing: an agent
cannot write it. The same file carries seat exceptions (§8.6).

---

## 6. The doc-comment check — `check_doc_comments.py`

```
check_doc_comments.py --files a b c --platform <p>   named files (a Swift file reads its whole module so extensions fold)
check_doc_comments.py --all --platform <p>           the tree
```

Reports `FAIL doc-comments <path>:<line>:<name>: …` for every public declaration with no
doc comment directly above it.

| Language | Public means | Doc comment means |
|---|---|---|
| Swift | `public`/`open`, membership of a public extension or protocol, a case of a public enum; extensions fold into their type per module (`Sources/<Target>`, `Modules/<M>/Sources`) | `///` or `/** */` |
| Kotlin / Java | Kotlin public by default; Java only when declared; a Java interface's members | `/** */` |
| TypeScript | exported declarations and the non-private members of exported classes and interfaces; read over JavaScript-sanitized source (single-, double-quoted and template strings emptied, `${…}` interpolations still read) | `/** */` directly above; decorators (multi-line ones too) and `//` comments may sit between, a blank line may not |
| Python | PEP 257, read with the stdlib `ast` module: public module-level defs and classes (inside `if`/`try`/`with` too), public methods, `__init__` and nested public classes of a public class; functions nested in a function body are not read; an `@overload` signature and a property's setter or deleter need no doc | a docstring as the first statement |

A Python file the interpreter cannot parse reports nothing. A TypeScript regex literal
holding a quote is the JavaScript sanitizer's one blind spot.

It is also the `doc-comments` built-in signature, so the scanner holds it on added lines at
commit and push; the pre-push seat prints the whole-tree count as an advisory.

---

## 7. The verifier — `verify_rules.py`

```
verify_rules.py                                   the whole corpus, from the standards repo root
verify_rules.py --summary                         per-document lines and totals only
verify_rules.py --document <file> --platform <p>  one project's copy (repeatable)
verify_rules.py --json                            machine-readable report
verify_rules.py --baseline <file>                 ratchet mode: pass only while the gap count equals the file's count
```

Output: one line per document, `FAIL verify-rules <path>:<line>:<id>: <words>` per gap, the
totals, exit 1 on any gap. The standards repo's own pre-commit hook runs it in ratchet mode
against `checks/verify-baseline.json` (currently 0 gaps, deadline 2026-12-03) and then the
whole test suite.

The verifier and `battery.json` are **not** installed into projects: they read the
standards repo's layout. The installer runs the verifier at adoption to compute the number
for `CLAUDE.md`.

---

## 8. The git hooks

All three are POSIX `sh`, installed at `.githooks/` with `core.hooksPath` pointed there.
Each sources `.coast/layout.sh` (the layout table rendered at adoption — the one name a
hook carries is the state dir) and evaluates `config.py --sh` from the checks dir, so a
seat, a linter or the attribution check the config switches off prints `gate: <name> OFF
(config)` and runs nothing. Every refusal is a `FAIL` line on stderr. Every hook clears git's `GIT_DIR`-family variables
first so the checks act on the right repository, and exports `PYTHONDONTWRITEBYTECODE=1`
so no `__pycache__` lands in the project.

### 8.1 `pre-commit`

The scanner on the staged diff (`--staged`). The doc-comment check runs inside it as the
`doc-comments` built-in signature, on added lines. Seconds.

### 8.2 `commit-msg`

- a subject line that exists and fits in 100 characters;
- `session:attribution-trailer`: a commit from an agent session (Claude Code exports
  `CLAUDECODE`) must carry `Co-Authored-By: Claude <Model> <version> <email>`; any Claude
  trailer from any session must name a model. A bare "Claude" or "Claude Code" refuses.

A comment line is `#` alone or `#` followed by a space or tab, as git writes them; a
subject like `#123 fix the crash` is kept. The messages git writes itself — `Merge branch
…`, `Merge remote-tracking branch … into …`, `Merge pull request …`, `Merge tag …`, and
`Revert "…"` over `This reverts commit <sha>.` — are git's words: the length and trailer
rules do not apply to them, and the hook says so with a `gate:` line.

### 8.3 `pre-push` — the battery

**What the push changed comes first.** Before any seat, `scope.py` reads the pushed
ranges (git's ref lines on stdin) and prints one of three kinds, which the hook echoes as
`gate: scope <kind> — <reason>`:

| Kind | When | What runs |
|---|---|---|
| `none` | no code changed: only paths in the `docs`, `plans`, `design_bundle`, `generated` or `git` classes, or with a prose extension (`paths.json`: `not_code_classes`, `prose_extensions`) | the diff scan, `gh-ruleset`, the project's own hooks; every other seat prints `gate: <name> SKIPPED — no code changed` |
| `files` | code changed | `lint` and `format` on the changed files of their kind (`swiftlint --force-exclude`, `swift-format`, `eslint`, `prettier`, `ruff`, `ktlint` take the list). The build and the tests follow the platform's module graph — the targets that own the changed files plus every target that depends on them, transitively: a Swift package by `swift package describe` (`build` rebuilds the affected targets, `tests` runs `swift test --filter '^(A\|B)\.'`, and says so when no test target depends on the change); Gradle by `settings.gradle[.kts]` and `project(':x')` edges (`./gradlew :m:build`, `:m:test`); npm workspaces by the root `package.json` (`npm test -w`), and with a `jest` or `vitest` test script the changed files go to `--findRelatedTests` / `vitest related` instead; Python by every file's imports resolved in the tree (`pytest` on the test files the change reaches, `SKIPPED` when none). An Xcode project, `tsc`, `mypy`, `npm run build` and `detekt` run whole; the tree scan, `doc-comments` and `jscpd` run whole |
| `all` | a `governing` or `manifest` path changed (`full_run_classes`), a code file no target owns, `--measure`, or `COAST_SCOPE=all` in the environment | everything, as before |

Seats run in this order; each prints `gate: <name>` and stops the push on failure.

| Seat | ios / macos | android | react-native / web | python |
|---|---|---|---|---|
| `build` | SwiftPM: `swift build -Xswiftc -warnings-as-errors`; Xcode: `xcodebuild build` with `SWIFT_TREAT_WARNINGS_AS_ERRORS=YES` (or the warnings ratchet on a full rebuild) | `allWarningsAsErrors` required in the build files, then `gradlew build test lint` | `tsconfig` must have `strict: true`; `tsc --noEmit`; `npm run build` if the script exists | — |
| `tests` | `swift test` or `xcodebuild test` on the newest iPhone simulator (falls back to the Mac's Designed-for-iPad destination); or the `tests-missing` ratchet | in `build` | `npm test` | `pytest -q` (or unittest) under `PYTHONWARNINGS=error` |
| `lint` | `swiftlint --strict` (or the `lint-findings` ratchet) | `gradlew detekt` | `eslint . --max-warnings 0` | `ruff check .`, `mypy .` |
| `format` | `swift-format lint --strict` on every tracked Swift file (or the `format-findings` ratchet) | `ktlint` | `prettier --check .` | `ruff format --check .` |
| `rules-scan` | the scanner on the lines added by what is being pushed — each `<local sha>` from git's ref lines on stdin against its `<remote sha>` (a new ref against the remote's default branch), starting at the adoption commit on the first push — then `--tree` with the ratchets, once per push | same | same | same |
| `doc-comments` | whole-tree count, advisory | same | same | same |
| `jscpd` | `jscpd . --min-tokens 50 --baseline .coast/jscpd-baseline.json --fail-on-new-clones`; past the deadline `--exit-code` | same | same | same |
| `gh-ruleset` | read-only through `gh api`: the default branch has an active ruleset with `pull_request`, `deletion`, `non_fast_forward` and no bypass actors; a note when `gh` is absent or offline | same | same | same |

A missing tool is a refusal with its install line, never a silent pass.

Xcode projects: the scheme is `.coast/xcode-scheme` if present, else the first scheme
`xcodebuild -list` prints. Builds run with `CODE_SIGNING_ALLOWED=NO`.

### 8.4 Running seats by hand

```
sh .githooks/pre-push --seat lint,format        run named seats
sh .githooks/pre-push --measure build,format    counting mode: prints MEASURE <id> <count> and MEASURE-FILE <id> <count> <path>
```

Git never passes these flags, so they are not a bypass. A `--seat` or `--measure` run takes
no push lock and runs no previous hooks. A `--seat` run reads git's ref lines when they are
piped to it (the tests push a branch that is not HEAD this way); with none, it judges HEAD
against its upstream — with no upstream, against the empty tree, so everything is code that
changed. `COAST_SCOPE=all` runs every seat whole regardless of what changed; `--measure`
always measures the whole tree.

### 8.5 One push at a time

The hook serialises on a lock directory in the common git dir (`mkdir` is atomic; the
lock's age is the directory's own mtime). A lock older than an hour is broken. A signal
releases the lock and stops the gate. After waiting it re-fetches, and if
the remote moved and this branch does not contain it, it says so in seconds instead of
building for half an hour and losing the race.

### 8.6 Excusing a seat

A person can skip one seat until a date:

```json
{"exceptions": [
  {"seat": "build", "reason": "the build needs env vars this checkout has not got",
   "who": "Pat Lee", "when": "2026-09-05", "until": "2026-09-19"}
]}
```

Seat names: `build`, `tests`, `lint`, `format`, `rules-scan`, `doc-comments`, `jscpd`,
`gh-ruleset`. The hook prints who excused it and why on every push and refuses again the
day after `until`. An entry with no `until` is ignored: a permanent skip is how enforcement
quietly dies. `--no-verify` stays forbidden because it turns everything off at once and
leaves no record.

### 8.7 A project's own hooks keep running

If the project had `core.hooksPath` set before adoption, the path is recorded in
`.coast/previous-hooks-path`; with no `core.hooksPath`, git's own hooks directory
(`git rev-parse --git-path hooks`, where pre-commit-framework, lefthook and the old husky
install) is recorded when it holds an executable `pre-commit`, `pre-push` or `commit-msg`.
Each shipped hook runs the previous hook of the same name after its own checks pass, with
the same arguments and the same ref lines on stdin. An executable previous hook runs as
itself (its shebang may say python or bash); one that is not executable is handed to `sh`.
The installer also warns when a `package.json` `prepare` script would set the old path back.

---

## 9. The Claude Code session hooks

Committed in `.claude/settings.json` (the `hooks`, `disableAllHooks` and `permissions.deny`
keys; other keys are the founder's). One entry point, `.coast/hooks/claude-hook.py
<hook-id>`, reads the event JSON on stdin and exits 2 with the reason on stderr to refuse.
A hook id in the config's `session_hooks.off` exits 0 with a one-line note on stderr and
checks nothing; "ask the owner in one line first" says the owner's name when the config
gives one.
Every behaviour was verified against Anthropic's hooks reference
(https://code.claude.com/docs/en/hooks) and the quotes are in the file's docstring.

| Hook id | Event | Matcher | Refuses |
|---|---|---|---|
| `governing-edit` | PreToolUse | `Edit\|Write\|MultiEdit\|NotebookEdit` | a path in the platform's `governing` class, `.claude/settings.json` or `.claude/settings.local.json` |
| `chained-cd` | PreToolUse | `Bash` | a `cd`/`pushd` followed by another command: `cd X && …`, `cd X; …`, `if cd X; then`, `builtin cd X && …`, a `cd` line followed by more; a bare `cd`, or `cd` as the last command, passes |
| `infra-command` | PreToolUse | `Bash` | fly/flyctl, wrangler, cloudflared, terraform/tofu, pulumi, doctl, aws, gcloud, az, nsupdate — except their read-only forms (a verb such as status, logs, list, ls, show, describe-…, get-…, plan, preview, validate, output, whoami, version among the first three non-option words and no mutating verb beside it: `fly status`, `aws s3 ls`, `terraform plan` pass) — `gh repo delete`, `gh secret\|variable\|ruleset`, a mutating `gh api` on repo/ruleset/secret/hook/key/environment/deployment/protection endpoints |
| `no-verify` | PreToolUse | `Bash` | `--no-verify`, `git commit -n`, `-c core.hooksPath=` |
| `force-push` | PreToolUse | `Bash` | `git push` with `--force`, `-f`, `--force-with-lease`, `--force-if-includes`, or a `+refspec` |
| `scan-at-commit` | PreToolUse | `Bash` | a red `check_rules.py --staged` on the repository the command commits to (it reads the command itself; anything but a commit passes) |
| `scan-on-edit` | PostToolUse | `Edit\|Write\|MultiEdit` | nothing (the edit happened); exits 2 so the model sees the findings on stderr |
| `unpushed-at-stop` | Stop | — | ending the turn with commits not on the remote or uncommitted product-source changes; honours `stop_hook_active`; no upstream passes with a note |
| `rules-at-start` | SessionStart | — | nothing; prints the platform, the ratchet counts and what will refuse, as context |

The platform comes from `.coast/platform` or `COAST_PLATFORM`; the checks resolve from
`../checks/` beside the hook (the standards repo's layout and the installed one alike) then
the checks dir the project's config names under `layout`.

How a Bash hook reads the command. A backslash-newline continuation is joined first. The
text is split, outside quotes, on `&&`, `||`, `;`, `|`, `|&`, `&` and newlines; the bodies of
`$(…)`, backticks, `(…)` and `{ …; }` are commands of their own. In each command every
leading `VAR=value`, every wrapper (`sudo`, `env`, `time`, `timeout`, `nohup`, `nice`,
`command`, `builtin`, `exec`, `xargs`, `npx`, `pnpm dlx`, `bunx`, `yarn dlx`, `npm exec`)
and the shell keywords (`if`, `then`, `do`, …) are skipped to reach the program; a version
suffix (`wrangler@3`) is dropped. The string a shell runs (`sh|bash|zsh -c "…"`, `eval …`)
and the command after `find … -exec` are read the same way. `test_claude_hooks.py`
(`BashBypasses`) lists every route that passed before E2.8.

The permission layer. The same settings file carries `permissions.deny` rules and
`"disableAllHooks": false`. Anthropic's hooks page says to use the permission system, not a
hook, for a hard deny, and the permissions page says a deny rule applies inside subshells,
`$(…)` and loops and past `VAR=value`, whatever a hook returns. The rules name the mutating
forms — `Bash(git push --force*)`, `Bash(git * --no-verify *)`, `Bash(fly deploy*)`,
`Bash(fly * destroy*)`, `Bash(terraform apply*)`, `Bash(aws * delete*)`, `Bash(gh repo
delete*)`, `Bash(nsupdate*)` — never a whole program, because "a deny rule can't carry
allowlist exceptions" and the read-only forms must stay open; `Edit(./.claude/settings.json)`,
`Edit(./.coast/**)` and the other governing paths are denied to the edit tools too (the
template carries them as layout placeholders; the installer renders them). The hook still runs first and explains the refusal in words. `disableAllHooks: false`
in the project file overrides a `true` in the user's settings (the hooks page says so), so a
user setting cannot switch the hooks off; only `claude --settings '{"disableAllHooks": true}'`
on the command line can, for one run — that is the human's own machine, and the git hooks
still stand. `.claude/settings.local.json` sits above the project file in precedence, which
is why `governing-edit` refuses it.

---

## 10. The installer — `adopt.py`

### 10.1 Usage

```
adopt.py <project> [--platform ios|macos|android|react-native|web|python]
                   [--dry-run] [--by <name>] [--secret-scan]
                   [--jscpd-bin <path>] [--measure-tools [build,format,lint,tests]]
                   [--release <version>|latest]
                   [--init | --yes] [--owner <name>] [--product <name>] [--org <name>]
                   [--checks-dir <path>]
```

| Flag | What it does |
|---|---|
| `--platform` | the target platform; omitted when the manifest makes it obvious (§10.2) |
| `--dry-run` | print the report, write nothing |
| `--by <name>` | the name recorded on the baselines; defaults to the git user name |
| `--secret-scan` | run the whole-tree secret scan again |
| `--jscpd-bin <path>` | the jscpd executable to use |
| `--measure-tools [list]` | re-measure the tool baselines; a list without `build` skips the build |
| `--release <version>` | fetch that published release (`1.1.0`, or `latest`) into the cache and run its own installer with the other flags forwarded. The one thing in the installer that touches the network. |
| `--init` | ask the on/off questions (§10.5) and write the answers to the config; a first adoption at a terminal asks anyway, once |
| `--yes` | take every default without asking (everything on); a run with no terminal does the same |
| `--owner`, `--product`, `--org` | the names in the config's `owner` object, which every sentence that names a person or a product reads |
| `--checks-dir <path>` | put the checks elsewhere than the layout's default; recorded under `layout.checks_dir` in the config |

The cache is `~/.cache/coast-standards/<version>/`, or `COAST_STANDARDS_CACHE` when set.
`COAST_STANDARDS_RELEASES` overrides the address the tarballs are fetched from (the
default is the repository's `archive/refs/tags/`), for a mirror. A fetched release whose
own `CHECKS-VERSION` does not say the version asked for is refused.

The report prints one line per file: `wrote`, `replaced`, `unchanged`, `kept (founder-edited)`,
`would write` under `--dry-run`, plus `note` lines.

### 10.2 Platform detection

Without `--platform`, the installer reads `.coast/platform` if present, else the manifests:
`Package.swift` with `.iOS(` only → ios, `.macOS(` only → macos; otherwise an
`.xcodeproj` (in the root or one folder down) whose `project.pbxproj` names `iphoneos` only
in `SDKROOT` / `SUPPORTED_PLATFORMS` → ios, `macosx` only → macos (both or neither: ask);
Gradle files → android; `package.json` with `react-native` in its dependencies → react-native,
otherwise web; `pyproject.toml`/`requirements.txt`/`setup.py` → python.

### 10.3 What lands where

| Path | Ownership | Contents |
|---|---|---|
| `.coast/checks/*.py`, `*.json` | governed | the scanner, its modules and tables, `layout.py`/`layout.json`, `config.py`/`config.default.json` (not the verifier) |
| `.coast/hooks/claude-hook.py` | governed | the session hooks' entry point |
| `.coast/config.json` | governed, written once, human-edited | the switches and names (§10.5); a later run rewrites only the keys a flag names |
| `.coast/layout.sh` | governed | the layout table rendered for the `sh` hooks |
| `.githooks/pre-commit`, `commit-msg`, `pre-push` | governed | the git hooks |
| `.claude/settings.json` → `hooks`, `disableAllHooks` | governed keys | the session hook wiring, replaced from the template; other keys kept |
| `.claude/settings.json` → `permissions.deny` | merged | the shipped deny rules first, once each, then the project's own; `allow` and `ask` untouched |
| `.coast/platform` | governed | one word |
| `.coast/standards-version` | governed | the release adopted: `1.0.0` from a release tarball or a clone at the tag, `1.0.0+<commit>` from a clone that is not at a release tag |
| `.coast/seeds.json` | governed | sha256 of each seed as shipped, with the date |
| `.coast/installed.json` | governed | every governed file the last run installed; a later run removes any of them it did not put back — a file a newer release stops shipping, or one the layout moved (a project adopted before 1.1.0 carried them under `Scripts/`); a file the founder put there is not listed and stays |
| `.coast/paths.json` | governed, written once | the project's path-class bindings (theme, plans, ui) |
| `.coast/ratchet-baseline.json` | governed | the ratchet counts and deadlines |
| `.coast/jscpd-baseline.json` | governed | jscpd fingerprints plus `clones`, `deadline`, `written`, `by`, `moves` |
| `.coast/previous-hooks-path` | governed | the hooks path the project had before (`core.hooksPath`, or git's own hooks directory when it held executables) |
| `.coast/rules-exceptions.json` | governed, human-written | signature and seat exceptions |
| `.coast/module-kinds.json` | governed, human-written | app / feature / shared targets for the import matrix |
| `.coast/xcode-scheme` | optional, human-written | the scheme the battery builds |
| linter configs (`.swiftlint.yml`, `.swift-format`, `detekt.yml`, `lint.xml`, `.editorconfig`, `eslint.config.mjs`, `tsconfig.json`, `.prettierrc.json`, `ruff.toml`, `mypy.ini`) | seed | written when absent; replaced while still equal to a shipped seed; kept when edited |
| `docs/domain-rules.md` | seed | the platform's rules document; never replaced at the same corpus version. An older version is upgraded and the old copy kept as `docs/domain-rules.v<N>.md` |
| `CLAUDE.md` | the block between `<!-- coast-standards: begin -->` / `end -->` (the older `up-coast-standards` markers are recognised and replaced) | rewritten from `TEMPLATE-PROJECT-CLAUDE.md`; text outside the markers untouched; appended once if no markers. Markers in any other arrangement (an end before its begin, a begin with no end, two blocks) refuse the whole run before anything is written, naming the count found |

### 10.4 Idempotency

Running twice on the same tree produces no change the second time. The tests prove it:
adopt twice and diff, `--dry-run` writes nothing, founder text outside the block survives,
an edited seed is kept while an unedited one takes the new version.

### 10.5 Configuration — `.coast/config.json`

One file, GOVERNING, read by one loader (`config.py`, shipped beside the scanner) from
the scanner, the verifier, the session hook, the installer and the git hooks (`config.py
--sh` renders the switches as shell variables). The shape is `config.default.json`:

```json
{"version": 1,
 "owner": {"name": "", "product": "", "org": ""},
 "rules": {"off": [], "severity": {}, "retired_words": []},
 "seats": {"off": []},
 "session_hooks": {"off": []},
 "linters": {"off": []},
 "ratchet_days": 90,
 "layout": {}}
```

Merge order: the shipped defaults, then the project's file (an object merges key by key,
a list replaces the default list), then the flags of the run (`--owner`, `--product`,
`--org`, `--checks-dir`). Validation refuses, with a sentence: a severity above the
table's (`rules.severity` may only lower — block → ratchet → advisory), a `layout.state_dir`
(the anchor the hooks find the file by), a non-list `off`, a `ratchet_days` that is not a
whole number.

What `off` does, and where it shows:

| Switch | Effect | In the number |
|---|---|---|
| `rules.off: [id]` | the scanner never runs the signature (`--only` cannot bring it back) | every rule whose only machine check it was is `off`; a rule with another live check is `partly` |
| `seats.off: [name]` | `pre-push` prints `gate: <name> OFF (config)` and runs nothing for it; `--measure` measures nothing for it | a `tool:` reference on that seat is off (`tool:jscpd` → `jscpd`, `tool:gh-ruleset` → `gh-ruleset`, `tool:warnings-as-errors` → `build`) |
| `linters.off: [name]` | the seat skips that linter; the installer seeds no config for it | every `<linter>:<rule>` reference is off |
| `session_hooks.off: [id]` | the session hook exits 0 with a note; `attribution-trailer` in `commit-msg` prints `OFF (config)` | every `session:<id>` reference is off |

`verify_rules.py --config <file>` applies the switches (the installer passes the project's
config, a dry run included); the headline reads `enforced by a check 21 of 74 (3 switched
off)`, the `off` bin is in `--json`'s totals and each rule's `off` list names the
references switched off. The `CLAUDE.md` block and `rules-at-start` say the same number.

The questions (`--init`, or a first adoption at a terminal): one screen per group — the
signatures with their `words`, the eight seats, the ten session hook ids — each a list
with a sentence and one question, "names to switch OFF, Enter keeps every one on". An
unknown name is said and asked again. `--yes` writes `config.default.json` byte-for-byte
(`test_config.py` holds it to that).

The layout (`layout.json` beside the checks) is the one home of every path the layer
names: `checks_dir`, `hooks_dir`, `session_hook`, `settings_file`, `state_dir`,
`rules_document`, `ai_rules_document`, `context_file`, `lock_name`, `temp_prefix`,
`env_prefix` and the jscpd ignore list. A value may name another key as `{key}`;
`paths.json`'s governing classes and `claude-settings.json` are written that way and
rendered when read or installed. A project overrides a key under the config's `layout`
(never `state_dir`); `layout.sh` in the state dir is the table rendered for the `sh` hooks,
which carry one name of their own — the state dir — and source the rest. `test_config.py`
greps every shipped file for the old literals and fails on any.

---

## 11. The linter configs

Shipped under `lint/`, with the opt-in rules the documents cite switched on. The verifier
reads each config and fails when a cited rule is not named there.

| File | Lands as | Notable settings |
|---|---|---|
| `swiftlint.yml` | `.swiftlint.yml` | `force_unwrapping` opt-in at error; `force_cast`, `force_try` error; `type_body_length` 300 and `file_length` 400 as warnings |
| `swift-format.json` | `.swift-format` | Apple swift-format configuration |
| `eslint.config.mjs` | same | `recommendedTypeChecked` with `projectService`; `@typescript-eslint/no-floating-promises`; `max-lines` warn; `react-hooks/rules-of-hooks` and `exhaustive-deps` when `eslint-plugin-react-hooks` is installed — the plugin is required inside a `try`, so a web project without React lints without it |
| `.prettierrc.json` | same | |
| `tsconfig.seed.json` | `tsconfig.json` | a complete starter: `strict`, `noImplicitAny`, `noEmit`, bundler resolution, `jsx: react-jsx`, `include: ["src"]`; written only when the project has no `tsconfig.json` — a project's own is kept and the push gate reads `strict` from it |
| `detekt.yml` | same | layered on the default set; `UnsafeCallOnNullableType`, `LargeClass` 300 |
| `lint.xml` | same | `HardcodedText` at error |
| `.editorconfig` | same | ktlint's settings |
| `ruff.toml` | same | `B` (bugbear) selected |
| `mypy.ini` | same | `strict = True` |

---

## 12. Versioning

- Every release is a semantic version in the root `CHECKS-VERSION`, a git tag `v<number>`,
  and an entry in the root `CHANGELOG.md` (`## 1.0.0 — 2026-09-07`). The workflow
  `.github/workflows/release.yml` refuses a tag that does not match the file or has no
  changelog entry, then publishes a GitHub release with that entry.
- `.coast/standards-version` records the release a project adopted: `1.0.0` when the
  installer ran from a release tarball or a clone at the tag, `1.0.0+<commit>` when it ran
  from a clone that is not at a release tag. Re-running the installer moves it, and its
  last line prints the value.
- Each project holds its own copy of the checks. Nothing global carries the rules, so a
  project upgrades on its own schedule with `--release`.
- `docs/domain-rules.md` carries `<!-- coast-rules-version: N -->` on its first line. The
  corpus is at version 8. A project's copy at an older version is upgraded at adoption with
  the old copy preserved; a copy at the current version that differs is a founder's edit and
  is left alone.
- Coast vendors `enforcement/` pinned by commit and checksum, with a parity test (phase E3,
  not yet built).

### 12.1 Cutting a release

1. Bump `CHECKS-VERSION` (semantic version, no `v`).
2. Write the entry in `CHANGELOG.md` as `## <number> — <date>`, in plain words: what a
   project that upgrades will notice.
3. Commit both.
4. `git tag v<number>` and push the tag. The workflow checks the tag against the file and
   the changelog, and publishes the GitHub release with the entry as its notes.
5. Re-adopt the reference implementation and the adopted apps against it:
   `adopt.py <project> --release <number>` in each, then commit and push what changed.
   A project adopted before 1.1.0 carried the checks under `Scripts/`; the re-adopt moves
   them under `.coast/` and removes the old copies (the manifest names them).

---

## 13. Troubleshooting

**A push hangs at "another push is running in this checkout".** Another gate holds the lock,
or one died within the last hour. Wait, or remove the lock directory named in the message.

**"A check is wrong."** Say so in plain words and stop; do not bypass. The founder excuses
the seat (§8.6) or the signature on the path (§5.7), with a reason and a date. If the
signature is genuinely wrong, fix it in the standards repo with a plant that proves both
directions, then re-adopt.

**The push was refused for a ratchet that fell.** A scanner ratchet below its baseline
asks you to lower the baseline in the same commit: re-run `adopt.py`, which lowers counts
that fell, and commit the baseline with the change. A tool ratchet below its baseline just
passes with a note.

**The build's warning count read zero, then refused as a rise.** Warning counts are only
comparable on a full build. The ratcheted build seat rebuilds the project's own targets
(SwiftPM) or runs `clean build` (xcodebuild) for exactly this reason. If another session is
building in the same checkout, the push lock (§8.5) serialises them.

**No iOS simulator matched.** The tests seat picks the iPhone on the newest installed
runtime by id. If xcodebuild sees no concrete simulator at all, it falls back to the Mac's
Designed-for-iPad destination. Install a runtime matching the deployment target if you want
the simulator.

**"the rules scanner is not installed."** Run `adopt.py` on the project.

**jscpd: the clone baseline was never written.** jscpd was missing at adoption. Install it
(`npm install -g jscpd@5.1.2`) and re-run `adopt.py`.

**The session hooks never fire.** They fire only for a session started at the repository
root. Check `.claude/settings.json` has the `hooks` key and `"disableAllHooks": false`, and
that `.coast/hooks/claude-hook.py` exists. A user-level `disableAllHooks: true` does not
turn them off (the project `false` wins); `claude --settings '{"disableAllHooks": true}'` does.

**The secret scan flagged a test fixture.** A value beginning `test-`, `fake_`, `dummy.`,
`sample-`, `stub-` is already excused. A value shaped like a real credential (`sk-ant-…`,
`ghp_…`, `AKIA…`, a PEM header) is reported wherever it appears on purpose. Excuse the
path in `.coast/rules-exceptions.json` if it is a fixture.

**The commit was refused for the subject length.** 100 characters. Put the rest in the body.

---

## 14. Extending

### 14.1 Add a signature

1. Add a row to `checks/rules_signatures.json` with a `platforms` entry for every platform the
   rule applies to, then add its id to `EXPECTED_IDS` in `test_check_rules.py`.
2. Add `checks/tests/plants/<platform>/<id>.fail.<ext>` and `<id>.pass.<ext>` for each.
3. Tag the rule in the platform document(s): `[…; check: scan:<id>]` (or `ratchet:`/`advisory:`).
4. Run the tests and the verifier; both must be green. If the rule is new, the verifier's
   baseline count must not rise.
5. Re-adopt the projects that should carry it.

A signature needs a rule and a rule needs a check: the verifier fails on either half missing.

### 14.2 Add a built-in

Implement it as a module beside the scanner, register its id in `check_rules.builtin_hits`,
and mark the signature `"kind": "builtin"`. Add plants like any other signature. The
installer ships every `.py` and `.json` file in `checks/` except the verifier's three, so a
new module travels on its own.

### 14.3 Add a seat

Add the case to `hooks/pre-push` behind `wants <name>`, print `gate: <name>`, refuse in a
`FAIL` line, name it in `battery.json` under `tools` for each platform, and tag the rule
`tool:<name>`. Seat exceptions (§8.6) match on the name you chose, so nothing else is needed
for a person to be able to excuse it. Add a test to
`test_hooks_and_adopt.py` that runs `pre-push --seat <name>` on a fixture that fails and one
that passes.

### 14.4 Add a session hook

Add the id to `claude-hook.py` (a function and the dispatch), wire it in
`claude-settings.json` with a `statusMessage` naming the id, tag the rule `session:<id>`,
and add a test in `test_claude_hooks.py` that feeds the documented stdin JSON.

### 14.5 Add a platform

Add the platform to `paths.json`, `rules_signatures.json` and `battery.json`; write a
`rules/platform/domain-rules-<p>.md`; add the `pre-push` case and the linter seeds; add the
platform to the installer's `PLATFORMS` and `LINT_DESTINATIONS` and its detection rule.

---

## 15. Tests

`python3 -m unittest discover -s enforcement/checks/tests -p 'test_*.py'` from the standards
repo root. About two minutes; jscpd must be installed or the jscpd test fails out loud
(never skips).

| File | Covers |
|---|---|
| `test_check_rules.py` | every scanner mode on a synthetic git repo, exceptions, the ratchet in both directions and past its deadline, advisory, every plant in both directions, the web precision cases (TSX shapes that are not copy, the strings home rebound, a multi-line import) |
| `test_verify_rules.py` | the parser grammar, every config reader, every bin, both ratchet directions, the real corpus against the baseline |
| `test_corpus_sections.py` | every app document carries DRY-1..7, L-1..12, DES-1..4 |
| `test_lint_configs.py` | every config exists and every linter tag the corpus cites is enabled in it; the ESLint seed loads under `node` with and without a stub hooks plugin (node must be installed — fails out loud) |
| `test_claude_hooks.py` | every session hook fed the documented stdin JSON in a fixture repo with a bare origin |
| `test_hooks_and_adopt.py` | adopt twice = no diff, dry-run writes nothing, seeds kept/replaced, the secret scan, each git hook as installed, the jscpd seat, seat exceptions, previous hooks, a `scripts/` folder beside the state dir, the move from the pre-1.1.0 layout |
| `test_config.py` | the layout table (no old literal in any shipped file or document, the settings template and governing classes render), every switch (rule, severity, retired words, seat, linter, session hook), the verifier's `off` bin and `--config`, the names from the config, the prompt driven by a scripted answer file, `--yes` byte-for-byte |

---

## 16. Limits, stated plainly

- The scanner is line regex scoped by file kind. It holds "a literal in the wrong file"
  precisely and does not understand program structure. A rule that needs an AST is deferred
  (Semgrep is the named candidate).
- Kotlin/Java doc-comment scanning does not read nested members or accessors.
- The warnings, lint and format ratchets exist for the Swift seats. Android, web and Python
  seats run strict until a repository on one of them adopts and needs them.
- The verifier is not installed into projects, so a project's number is computed at
  adoption and written into `CLAUDE.md`; it is not recomputed by the session-start hook.
- Reviewer-bin rules (about half the corpus) are held by nothing mechanical yet. Coast's
  per-rule review rows (phase E3) are design, not code.
- The Claude Code hooks depend on the session being started at the repository root; a
  `--settings '{"disableAllHooks": true}'` on the command line turns them off for that run.
  The `permissions.deny` rules hold the named mutating forms without them.
- The read-only allowlist of `infra-command` reads verbs, not the programs' own grammars: a
  read-only command with several option values before its verb is refused (reorder it), and a
  mutating verb the list does not know passes only when a read-only verb stands beside it.
