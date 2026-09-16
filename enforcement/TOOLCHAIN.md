# The enforcement toolchain — pinned versions

*Last updated: 2026-09-16*

This page lists every program the pre-push hook (`enforcement/hooks/pre-push`) runs, with the version it was checked against.

- Nothing is downloaded at run time. If a program is missing, the hook stops the push and prints the install command.
- The hook's error messages name the same versions as this table.
- If jscpd is not on `PATH`, the hook tries `npx --no-install jscpd`, or set `JSCPD_BIN` to the binary.
- Change a row only after checking the tool's own documentation again.

| Tool | Pinned version | Install | Checked against (primary source) | Used for |
|---|---|---|---|---|
| jscpd | **5.1.2** | `npm install -g jscpd@5.1.2` (the npm package wraps a prebuilt Rust binary per platform: `jscpd-darwin-arm64`, `jscpd-darwin-x64`, `jscpd-linux-*`, `jscpd-windows-*`) | The binary's own `jscpd --help` (5.1.2, run 2026-09-04), and `docs/rust.md` in the jscpd repository, https://github.com/kucherenko/jscpd/blob/master/docs/rust.md. The package's README.md (npm `jscpd@5.1.2`) links to that page for "Full options". | `tool:jscpd` — the duplicated-code check |
| swiftlint, swift-format | the Mac's current | `brew install swiftlint swift-format` | — | lint and format checks (ios, macos) |
| gh | the Mac's current | `brew install gh` | GitHub REST: `GET /repos/{owner}/{repo}/rulesets`, `GET /repos/{owner}/{repo}/rulesets/{id}` | `tool:gh-ruleset` — a read-only check of the branch protection ruleset; skipped with a note when `gh` is not installed |
| detekt (gradle plugin), ktlint | the project's | `brew install ktlint`; detekt through the Gradle plugin | — | lint and format checks (android) |
| tsc, eslint, prettier | the project's `node_modules` (`npx --no-install`) | `npm install` | — | typecheck, lint and format checks (react-native, web) |
| ruff, mypy, pytest | the environment's | `pip install ruff mypy pytest` | — | lint, types, format and test checks (python) |

## jscpd 5.1.2 — the flags the hook uses

Descriptions are quoted from `jscpd --help` of the pinned binary. `docs/rust.md` in the jscpd repository uses the same words.

| Flag | What the tool says | How the hook uses it |
|---|---|---|
| `--baseline <FILE>` | *"Path to a clone baseline file (e.g. .jscpd-baseline.json): clones whose fingerprint is absent from it are reported as new"* | Points at `.coast/jscpd-baseline.json`. |
| `--fail-on-new-clones [<N>]` | *"Exit 1 when more than N new clones are found (default N: 0; requires --baseline or --baseline-from-ref)"* | Refuses any duplicated code not already in the baseline. |
| `--update-baseline` | *"Rewrite the baseline file from the current run, creating it if missing, and print added/removed fingerprint counts (requires --baseline)"* | `adopt.py` runs it on a scratch copy, then merges the fingerprints into the project's baseline. A direct rewrite would drop every key except `version` and `fingerprints`. |
| `--baseline-from-ref <REF>` | *"Compare against an ephemeral baseline built from a git ref's tree (e.g. origin/main)"* | Not used. The committed baseline is needed because it carries the deadline. |
| `--exit-code [<EXIT_CODE>]` | *"Exit with code if duplicates found (default code: 1)"* | Used after the baseline's deadline has passed: any duplicated code is refused. |
| `--min-tokens <MIN_TOKENS>` | *"Minimum number of tokens to consider a duplicate"* | 50, the README default and the value in the design (enforcement/README.md §5.3). |
| `--reporters json` with `--output <OUTPUT>` | The JSON report | `statistics.total.clones` gives the clone count the baseline is compared with. |
| `--ignore <IGNORE>` | *"File-level glob patterns to ignore, e.g. "**/node_modules/**" (comma-separated)"* | Skips the folders in the `jscpd_ignore` list in `enforcement/checks/layout.json` (dependencies, build output, the installed checks). |
| `--silent` | *"Do not write detection progress and result to console"* | Keeps the hook output short. |

jscpd respects `.gitignore` by default. `--no-gitignore` turns that off; the hook never uses it.

### The baseline file

jscpd reads this shape (checked by running it):

```text
{"version": 1, "fingerprints": {"<hash>": 1, …}}
```

jscpd ignores extra top-level keys when reading. So `.coast/jscpd-baseline.json` can also hold the baseline fields the hook needs: `clones`, `written`, `by`, `deadline` and `moves`. A baseline is a count of existing problems that may only go down.

### Tested behaviour

Tested with the pinned binary on 2026-09-04:

- A tree with one copied block, and a baseline that contains that block, passes `--fail-on-new-clones` (exit 0).
- A second copy is reported as `[NEW]` and refused (exit 1, *"ERROR: jscpd found 1 new clones not in the baseline (allowed: 0)"*).
