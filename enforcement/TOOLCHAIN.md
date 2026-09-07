# The enforcement toolchain — pinned versions

*Last updated: 2026-09-07*

Every program the gate battery (`enforcement/hooks/pre-push`) runs, with the
version it was verified against and where the verification came from. A
row changes only when someone re-verifies the tool's own documentation;
the hook names the same versions in its refusals. Nothing here is fetched
at run time — the battery refuses with an install line when a program is
missing.

| Tool | Pinned version | Install | Verified against (primary source) | Used for |
|---|---|---|---|---|
| jscpd | **5.1.2** | `npm install -g jscpd@5.1.2` (the npm package wraps a prebuilt Rust binary per platform: `jscpd-darwin-arm64`, `jscpd-darwin-x64`, `jscpd-linux-*`, `jscpd-windows-*`) | the binary's own `jscpd --help` (5.1.2, run 2026-09-04) and `docs/rust.md` in the jscpd repository, https://github.com/kucherenko/jscpd/blob/master/docs/rust.md; the package's README.md (npm `jscpd@5.1.2`) points at that page as "Full options" | `tool:jscpd` — duplicated-code seat |
| swiftlint, swift-format | the Mac's current | `brew install swiftlint swift-format` | — | lint and format seats (ios, macos) |
| gh | the Mac's current | `brew install gh` | GitHub REST: `GET /repos/{owner}/{repo}/rulesets`, `GET /repos/{owner}/{repo}/rulesets/{id}` — the same shape Coast's `GitHubAPI.swift` writes | `tool:gh-ruleset` — read-only ruleset check; skipped with a note when absent |
| detekt (gradle plugin), ktlint | the project's | `brew install ktlint`; detekt through the Gradle plugin | — | lint and format seats (android) |
| tsc, eslint, prettier | the project's `node_modules` (`npx --no-install`) | `npm install` | — | typecheck, lint and format seats (react-native, web) |
| ruff, mypy, pytest | the environment's | `pip install ruff mypy pytest` | — | lint, types, format and test seats (python) |

## jscpd 5.1.2 — the flags the battery uses, quoted from the tool

Quoted from `jscpd --help` of the pinned binary (2026-09-04); `docs/rust.md`
in the repository documents the same flags with the same words:

- `--baseline <FILE>` — *"Path to a clone baseline file (e.g.
  .jscpd-baseline.json): clones whose fingerprint is absent from it are
  reported as new"*
- `--fail-on-new-clones [<N>]` — *"Exit 1 when more than N new clones are
  found (default N: 0; requires --baseline or --baseline-from-ref)"*
- `--update-baseline` — *"Rewrite the baseline file from the current run,
  creating it if missing, and print added/removed fingerprint counts
  (requires --baseline)"* — `adopt.py` runs this into a scratch copy and
  merges the fingerprints into the ratchet-shaped baseline (below), because
  a rewrite drops every key that is not `version`/`fingerprints`.
- `--baseline-from-ref <REF>` — *"Compare against an ephemeral baseline
  built from a git ref's tree (e.g. origin/main)"* — not used: the committed
  baseline carries the deadline decision 2 requires.
- `--exit-code [<EXIT_CODE>]` — *"Exit with code if duplicates found
  (default code: 1)"* — the seat past the baseline's deadline: any clone
  refuses.
- `--min-tokens <MIN_TOKENS>` — *"Minimum number of tokens to consider a
  duplicate"* (README default 50; the design says 50 — enforcement/README.md
  §5.3).
- `--reporters <REPORTERS>` with `json` and `--output <OUTPUT>` — the JSON
  report (`statistics.total.clones`) gives the clone count the ratchet
  compares.
- `--ignore <IGNORE>` — *"File-level glob patterns to ignore, e.g.
  "**/node_modules/**" (comma-separated)"*; `--silent` — *"Do not write
  detection progress and result to console"*. `.gitignore` is respected by
  default (`--no-gitignore` turns that off; the battery never does).

Baseline file the tool reads, verified by running it: `{"version": 1,
"fingerprints": {"<hash>": 1, …}}`. Extra top-level keys are tolerated on
read, which is how `.coast/jscpd-baseline.json` also carries the ratchet's
`clones`, `written`, `by`, `deadline` and `moves`.

Proven on this Mac 2026-09-04 with the pinned binary: a tree with one
copied block and a baseline of that block passes `--fail-on-new-clones`
(exit 0); a second copy is reported `[NEW]` and refused (exit 1, *"ERROR:
jscpd found 1 new clones not in the baseline (allowed: 0)"*).
