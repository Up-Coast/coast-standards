# Working with AI coding agents

Coast Standards was built because AI coding agents follow written rules only when it is
convenient. The checks make that stop mattering: the rules are enforced by scripts the
agent cannot argue with, and the agent gets the verdict in seconds while it still has the
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
[When a check stops you](when-a-check-stops-you.md)). That door exists and only a person
can open it, which is the point.

## Setting it up

The installer writes the hooks into `.claude/settings.json` in your project. Any other
settings you had in that file are kept. Claude Code picks the hooks up when a session
starts at the project root. If you have disabled all hooks in your personal Claude Code
settings, these are disabled too; that is your machine and your choice.

## Commit attribution

A commit made from an agent session must name the model in a trailer:

```
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

A bare "Claude" or "Claude Code" is refused, because it does not say who did the work.
