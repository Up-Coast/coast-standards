# The development environment

Read this when running commands, freeing disk or switching branches.

## Run atomic commands

Run one command at a time, with little piping. Never chain `cd X && …`: it never matches a saved permission. Keep the local settings allowlist current. [check: session:chained-cd]

## Disk space is a real constraint, and it breaks the tools

- **Check free space before booting an unfamiliar simulator runtime or emulator image.** [check: process]
- Cleanup order: old simulator runtimes (keep the project's), unused and unavailable simulator devices, build caches, scratch directories of ended sessions only.
- **Never delete a person's own files to reclaim space.** Report what is large. [check: process]

## Branch switching has a cost — plan for it

A branch switch invalidates build caches. Batch work per branch; a slow first build after a switch is not a regression. [check: process]

---

[← All rules](README.md) · [Documentation](../docs/README.md)
