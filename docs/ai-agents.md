# Working with AI coding agents

*Last updated: 2026-09-07*

Coast Standards exists because AI coding agents do not reliably follow written rules.
The checks are scripts, and the agent gets the verdict in seconds while it still has the
code in front of it.

## What the agent sees

- **At session start**, a short summary: the platform, the number of rules held by a
  machine, the starting-line counts and their dates, and what will refuse it.
- **After every file it saves**, the scanner's findings for that file, immediately.
- **Before every commit**, the scanner on what it staged. A red scan blocks the commit.
- **In your `CLAUDE.md`**, a block the installer keeps current: where the rules are, the
  number, and the files it must not touch.

## What it cannot do

These are refused before they run, in every permission mode:

| It tries to | Why it is refused |
|---|---|
| edit the files that define the checks | an agent never changes its own guard-rails |
| run `cd somewhere && …` chains | commands should be atomic; a chained `cd` hides where it ran |
| run commands that change cloud infrastructure (Fly, Cloudflare, Terraform, AWS, GitHub secrets and rulesets) | it must ask you in one line first |
| skip the hooks (`--no-verify`) or force-push | that turns the checks off or rewrites history |
| end its turn with commits it has not pushed | every commit gets pushed in the same session |

## What a good agent does when refused

Says so in plain words and stops. If the check is wrong, the agent should name which check
and why, so you can set it aside with a dated entry (see
[When a check stops you](when-a-check-stops-you.md)). Only a person can add that entry.

## Setting it up

The installer writes the hooks into `.claude/settings.json` in your project. Any other
settings you had in that file are kept. Claude Code picks the hooks up when a session
starts at the project root. If you have disabled all hooks in your personal Claude Code
settings, these are disabled too.

## A skill for the install itself

Every release carries one small skill folder, `skills/adopt-coast-standards/`. Copy that
folder into `~/.claude/skills/` to have it in every project, or into your project's
`.claude/skills/`. When you ask an agent to adopt or upgrade Coast Standards, the skill
tells it where the releases are, the commands to fetch one and run the installer, and to
dry-run first and ask you the few real questions before it writes anything.

The skill holds nothing else. The rules, the checks, and the hooks live in your project's
own copy, not in the skill. That is deliberate: nothing about the standards sits in every
chat's context, and an agent reads the rules where they apply, in the project.

## Commit attribution

A commit made from an agent session must name the model in a trailer:

```
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

A bare "Claude" or "Claude Code" is refused, because it does not say who did the work.
