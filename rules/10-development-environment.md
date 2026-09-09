# The development environment

Rules about the machine the work happens on. They exist because each one has already cost a
real session real time.

## Run atomic commands

Run one command at a time from the working directory, with minimal piping. **Never chain
`cd X && …`.**

The mechanical reason: permission rules match on the command pattern, and a compound chain
never matches a saved rule — so every unique chain prompts again, and approving one saves
only that exact string. Atomic commands match the project's wildcard allowlist and stop
generating prompts. (Origin: 50+ permission prompts in a single session, all from chained
commands.)

Keep the project's allowlist in its local settings file current as new read-only commands
prove routine. [check: session:chained-cd]

## Disk space is a real constraint, and it breaks the tools

A full disk doesn't just fail the build — it breaks the harness itself: command output can't
be written, notes can't be saved, and failures start looking like unrelated bugs. Toolchain
state accumulates invisibly across sessions, and nobody is watching it.

- **Check free space before booting an unfamiliar simulator runtime or emulator image.** A
  new runtime can consume the last of the disk with no warning. [check: process]
- The sanctioned cleanup set, in order of safety: delete stale simulator runtimes (keeping
  the one the current project targets), shut down and erase unused simulator devices and
  delete unavailable ones, clear build-artifact caches (DerivedData and equivalents), and
  clear scratch directories belonging to **ended** sessions — never the current one.
- **Never delete a person's own files to reclaim space.** Report what's large and let them
  decide. [check: process]

## Branch switching has a cost — plan for it

With one checkout per project rather than worktrees, switching branches invalidates
build-artifact caches, so the next build is a cold one. That's an accepted trade for
predictable disk use, but it means: batch work on a branch rather than hopping, and don't
read a slow first build after a switch as a regression. [check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
