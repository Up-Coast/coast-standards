# Working with AI coding agents

*Last updated: 2026-09-16*

AI coding agents do not reliably follow written rules. Coast Standards turns the rules into scripts, so the agent gets a verdict in seconds while the code is still in front of it.

## What the agent sees

| When | What |
|---|---|
| Session start | A summary: platform, number of enforced rules, baseline counts and deadlines, and what will refuse it |
| After each file it saves | The scanner's findings for that file |
| Before each commit | The scanner on the staged changes. Any failure blocks the commit. |
| Always, in `CLAUDE.md` | A block the installer keeps current: where the rules are, the enforced count, and the files it must not edit |

## What the agent is blocked from doing

These are refused in every permission mode:

| Action | Why |
|---|---|
| Editing the files that define the checks | An agent must not change its own guard-rails |
| Running `cd somewhere && …` chains | A chained `cd` hides where a command ran; use absolute paths |
| Changing cloud infrastructure (Fly, Cloudflare, Terraform, AWS, GitHub secrets and rulesets) | It must ask you first. Read-only commands still work. |
| Skipping hooks (`--no-verify`) or force-pushing | That turns the checks off or rewrites history |
| Ending its turn with unpushed commits | Every commit is pushed in the same session |

A person can switch individual session hooks off in `.coast/config.json`. See [Options](options.md).

## When the agent is refused

It should say what was refused and stop. If it thinks the check is wrong, it should name the check and the reason. A person can then set the check aside with a dated entry. See [When a check stops you](when-a-check-stops-you.md).

## Setup

1. Run the installer. It writes the hooks into `.claude/settings.json` and keeps your other settings in that file.
2. Start Claude Code at the project root. The hooks load at session start.

`disableAllHooks: true` in your personal Claude Code settings does not turn these hooks off. The project file sets it to `false`, which takes priority.

## The install skill

Each release includes one skill folder, `skills/adopt-coast-standards/`. It tells an agent how to fetch a release, dry-run the installer, ask you the few real questions, and then install or upgrade.

1. Copy the folder into `~/.claude/skills/` (all projects) or your project's `.claude/skills/`.
2. Ask the agent to adopt or upgrade Coast Standards.

The skill contains nothing else. The rules, checks and hooks live in your project, where the agent reads them.

## Commit attribution

A commit from an agent session must name the model in a trailer:

```
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

A bare "Claude" or "Claude Code" is refused, because it does not say which model did the work.
