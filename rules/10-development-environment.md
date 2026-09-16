# The development environment

Rules about the machine where the work happens. Each one prevents a problem that wastes real session time.

## Run atomic commands

Run one command at a time from the working directory, with as little piping as possible. **Never chain `cd X && …`.**

Why: permission rules match on the command pattern, and a chained command never matches a saved rule. Every new chain asks for permission again, and approving it saves only that exact string. Single commands match the project's wildcard allowlist, so they stop triggering prompts.

Keep the allowlist in the project's local settings file up to date as new read-only commands become routine. [check: session:chained-cd]

## Disk space is a real constraint, and it breaks the tools

A full disk does not just fail the build. It breaks the agent's own tools: command output cannot be written, notes cannot be saved, and failures look like unrelated bugs. Toolchain files pile up across sessions without anyone noticing.

- **Check free space before booting an unfamiliar simulator runtime or emulator image.** A new runtime can use up the rest of the disk without warning. [check: process]
- Approved cleanup, safest first: (1) delete old simulator runtimes, but keep the one the current project targets; (2) shut down and erase unused simulator devices, and delete unavailable ones; (3) clear build caches (DerivedData and similar); (4) clear scratch directories of sessions that have **ended**, never the current session's.
- **Never delete a person's own files to reclaim space.** Report what is large and let them decide. [check: process]

## Branch switching has a cost — plan for it

With one checkout per project instead of worktrees, switching branches invalidates the build caches, so the next build starts from scratch. That is an accepted cost for predictable disk use. So: finish a batch of work on one branch before switching, and do not treat a slow first build after a switch as a regression. [check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
