# Changelog

*Last updated: 2026-09-07*

What a project that upgrades will notice, one entry per release. The number lives in
`CHECKS-VERSION`; the release is the git tag `v<number>`.

## 1.0.0 — 2026-09-07

The first public release, under the Coast Standards License (source-available: use
and share unchanged, no resale, no derived products; see LICENSE.md).

- **Rules.** Six platform rule documents (iOS, macOS, Android, React Native, Web, Python
  backend) at corpus version 8, plus the AI-features rules; every rule names the check
  that holds it. Rules enforced by a check: 170 of 643 across the corpus.
- **Checks.** The rules scanner with per-platform signature tables, the doc-comment
  check, the import matrix, the type-size advisory, the async-blocking check, the
  duplicate-code seat (jscpd 5.1.2), the secret scan, and the shipped linter configs.
- **Hooks.** `pre-commit`, `commit-msg` and `pre-push` for git; the Claude Code session
  hooks that refuse edits to governed files, infrastructure commands, `--no-verify` and
  force-pushes, and that scan every edited file.
- **Installer.** `adopt.py` installs all of it into a project in one command, records
  starting lines with a 90-day deadline, and upgrades in place. It records the release
  it installed in `.coast/standards-version` and can fetch a named release itself
  (`--release 1.0.0`, or `latest`), so no clone is needed.
- **The `CLAUDE.md` block** is written between `coast-standards: begin` / `end` markers.
  A block written by an earlier private build under the older `up-coast-standards`
  markers is recognised and replaced.
