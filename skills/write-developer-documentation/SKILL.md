---
name: write-developer-documentation
description: How to write developer documentation that a developer can read once and act on. Load it BEFORE writing or rewriting any documentation for people who install, configure, integrate, maintain or contribute to software, and for AI coding agents that follow written rules. Covers READMEs, quickstarts, installation and upgrade guides, settings and CLI references, troubleshooting pages, architecture and design documents, contributor guides, rule documents that agents follow, changelogs and release notes, and large rewrites of an existing doc set. Trigger phrases: "developer documentation", "dev docs", "write the README", "document the config", "document the flags", "write the release notes", "changelog entry", "cut a release", "the docs are too wordy", "make the docs readable", "rewrite the docs", "explain how to install", "explain how to configure", "troubleshooting page", "CONTRIBUTING". When another writing guide also applies (for example write-a-guide), follow both; where they differ, this skill wins for developer documentation.
---

# Write developer documentation

Developer documentation tells a developer what something is, how to install it, how to configure it, what to do when it stops them, and how to change it. A developer should be able to read a page once and then do the thing.

The same pages are often read by AI coding agents. Write so that both can act on every sentence.

## The model this skill is tuned for

This skill is tuned for Opus 5 at medium effort. On another model or effort level it may be followed less closely.

Each time you load this skill, tell the person you are working for, in one line, before you start writing:

- the model you are running on, as your system prompt names it
- the effort level, if your context states it; if it does not, say the effort level is not visible to you
- whether that matches Opus 5 at medium effort

Example: "Loaded write-developer-documentation, which is tuned for Opus 5 at medium effort. This session runs Opus 5; the effort level is not visible to me."

## The standard, in one list

1. Lead with what the reader does.
2. One idea per sentence, about 20 words or fewer.
3. Plain names for everything. Define a necessary term once, where it first appears.
4. No history. The why is one sentence naming the problem it prevents.
5. Steps, tables and short lists instead of long paragraphs.
6. One line per paragraph and per bullet. Never hard-wrap prose.
7. Every fact checked against the code. Nothing the reader needs is left out.

The rest of this skill explains each point and how to apply it to each kind of page.

## Before you write

1. **Name the reader.** The default reader is a developer who knows the language and platform, but has never seen this project. Skip what they already know. Explain what is specific to this project.
2. **Name what the reader must be able to do** after reading the page, in one sentence. Every part of the page serves that sentence.
3. **Read the code before you describe it.** Run `--help` on every command you document. Open the settings file, its defaults and its loader. Read the hook or script that does the work. Take names, flags, defaults and messages from there, never from memory or from an older doc.
4. **Find what code reads in the docs.** Some Markdown is parsed: rule documents read by a checker, templates with `{{PLACEHOLDERS}}`, text a test searches for, headings other files link to. List these before editing, and keep them intact.
5. **Read one neighbouring page** in the same doc set. Match its heading style and terms, unless the task is to change them.

## Sentences

- **Lead with the action.** "Run `adopt.py <project>`." comes before any explanation of what `adopt.py` does.
- **One idea per sentence.** Split any sentence that joins two ideas with "and", a semicolon or a dash.
- **About 20 words or fewer.** A long sentence is almost always two sentences.
- **Present tense, current behaviour.** Describe what the software does now.
- **Imperative for instructions.** "Set `tests_deadline_seconds`." Use "you" only when the sentence reads badly without it.
- **Be specific.** "The hook stops a test run that has not finished after 900 seconds", not "long runs may be interrupted".
- **Cut filler.** No "simply", "just", "easily", "note that", "it's worth mentioning", "in plain words", "powerful", "seamless". No warm-up paragraph and no closing summary. End on the last useful fact.
- **Apply the deletion test.** If removing a sentence loses nothing the reader needs, remove it.
- **No em dashes** in prose. Use a full stop or a comma.

## Names and jargon

Internal vocabulary is the most common reason a developer cannot follow a page. Replace it with what the developer sees on screen or in the files.

| Instead of | Write |
|---|---|
| "the tests seat" | "the test step of the pre-push hook" |
| "wall-clock deadline" | "time limit" |
| "the battery" | "the checks the pre-push hook runs" |
| "a governed file" | "a file that defines the checks; agents are not allowed to edit it" (once), then "a check file" |
| "a ratchet" | "a count of existing problems that may only go down" (once), then "the baseline" |
| "a plant" | "a test file the check must refuse" |
| "a wedge" | "a hanging test" |

Rules for names:

- **Define a term once**, where it first appears, only if the reader needs the term later. Otherwise use the plain description every time.
- **Keep literal names literal.** A config key, flag, file name or value that the reader types stays exactly as the code spells it, in code formatting, even when the concept around it gets a plain name.
- **Use one name per thing** across the whole doc set. Pick it, then search for every other spelling and replace it.

## History and the why

Developers integrating a change need what changed and what problem it solves. They do not need how it was found.

Leave out:

- incident stories ("born of a real push on 2026-09-15…")
- dates, except in a changelog heading or a deliberate log
- task ids, ticket numbers and internal decision numbers
- "we added", "previously", "since 1.1.0", unless the reader must act on it
- who fixed what, and how the doc was written
- plans, open tickets and unfinished work

Keep the why as one sentence that names the problem the thing prevents:

> A hanging test used to block the push forever with no message.

## Formatting

- **Numbered steps** for anything done in order. One action per step. Put the command in a code block under the step.
- **Tables** for anything with the same attributes across several items: settings, flags, files, check names, error messages. Typical columns: name, type, default, what it does.
- **Bulleted lists** for independent facts. Start each bullet with a bold phrase when the list is long enough to scan.
- **Code formatting** for anything typed or matched exactly: commands, flags, keys, values, paths, file names.
- **Code blocks** for every command a reader runs. Tag them with the shell (`bash`) so tools can offer a run button.
- **One line per paragraph and per bullet.** Never wrap prose at a fixed width. GitHub release pages, some comment fields and some renderers show every line break, so a wrapped bullet renders as broken lines. Tables and code blocks are exempt.
- **Headings** are short and name the topic: "Install", "Update", "Customize", "When a check stops you". No clever headings. Keep any section number that other files cite.
- **Links** are relative inside a repository, and absolute (full URL) anywhere the text is copied out of the repository, such as release notes. Link a page, not an anchor, when the target page is being edited by someone else.

## Facts

- **Never invent.** Every flag, key, default, path, message and behaviour comes from the code. If you cannot confirm something, leave it out or say it is unverified.
- **Shorter by leaving out what the reader does not need.** Never shorter by leaving out what they do need.
- **Move, don't drop.** When a detail leaves a page, put it where it belongs (usually the reference page) and link to it.
- **Fix contradictions you find.** When an old doc disagrees with the code, the code wins. Correct the doc and note the correction in your report.
- **One home per fact.** A detail lives on one page. Other pages link to it. A settings table that appears in three pages will be wrong in two of them within a month.

## When the code changes

Documentation goes stale one change at a time. Every change that alters what a reader sees or does updates the documents that describe it, in the same change.

1. List what the change alters: behaviour, commands, flags, settings and their defaults, file locations, messages, screens.
2. Search every document for each item, by its literal name and by the words a reader would use for it.
3. Update each match: the README, guides, the settings reference, troubleshooting pages, templates, diagrams and the changelog.
4. Remove text that describes the old behaviour. Do not keep it under a "previously" note.
5. Where a machine can check it, add a test: for example, one that fails when a flag or setting is missing from the reference page.

## Page shapes

Use the shape that matches the page. Use only the sections the project needs, in this order.

### README

1. **What it is.** Two or three sentences: what it does, who it is for, what it is made of.
2. **Install.** Numbered steps, one action each, commands in code blocks. Follow with a short table of what the install adds and where.
3. **Update.** The one command, and what it keeps (edited files) and replaces.
4. **Customize.** Where the settings file lives, how to create and edit it, how to switch something off, how to make a temporary exception. Link to the full settings reference.
5. **When something stops you.** The two or three most common refusals and what to do, with a link to the troubleshooting page.
6. **Read more.** A short list of links, one line each.
7. **License.** One or two sentences and a link.

A personal introduction written by the owner stays exactly as written.

### Quickstart

The shortest path from nothing to working. Numbered steps only, with a table of what gets installed where. Every option and edge case goes to the reference page, linked.

### Settings and CLI reference

The complete, exact list. It is the one page allowed to be long.

- One table per group: key, type, default, what it does.
- One table for command-line flags: flag, what it does, when to use it.
- An example file for anything with structure (JSON, YAML), in a code block.
- Check every row against the loader, the defaults file and `--help`.

### Troubleshooting

One heading per situation, named the way the reader experiences it ("The push was refused because a count went down"). Under each heading:

1. **What it means**, in one or two sentences.
2. **What to do**, as numbered steps.
3. **Who decides**, when the fix is not the reader's to make ("A person raises the limit in `.coast/config.json`").

### Architecture and design documents

1. A short summary: what the system is and its parts.
2. A table of the parts: name, what it does, where it lives.
3. A contents list.
4. Each part: how it works, in short paragraphs and tables. File formats, exit codes and output line formats in code blocks.
5. Decisions: the decision and its reason, one short paragraph each.

A build-plan or task table may keep task ids and status. Cut each cell to what was built and how it is tested.

### Contributor guide

Setup steps, how to change each kind of thing, what every change must include (tests, changelog entry), and how a pull request is checked. Link to the release instructions instead of repeating them.

### Rule documents that agents follow

- One checkable statement per rule. A reviewer must be able to answer "does this change break it?" with yes or no.
- The reason in one sentence, when it is not obvious.
- Rewrite for clarity only. **Never change what a rule requires.** If a sentence is ambiguous, keep it close to the original.
- Rule ids, headings, the opening bold text and any machine-read tag stay byte-for-byte. A checker reads them.
- A section that is the same on several platforms or products is written once and included, never pasted into each file.

### Changelog and release notes

Each version is one section. The same text is published as the release notes when that version is released.

```markdown
## 1.5.0 — 2026-09-16

One sentence summarising the release.

### Added

- **Bold phrase saying what changed.** The problem it solves. What to do or set, if anything.

### Changed

### Fixed

### Removed

### Upgrading

What an adopting project must do, or "Re-run `<install command>`. No other changes are needed."
```

- Use only the groups that have entries, in the order Added, Changed, Fixed, Removed, then Upgrading.
- Each bullet is **one line**. Never wrap.
- Each bullet starts with a bold phrase in plain words, then one or two sentences: the problem it solves, and what the reader needs to do or set.
- No incident stories, no dates other than the heading, no rule numbers, task ids or internal terms.
- Links are absolute URLs, because release pages do not resolve relative links.
- Add entries under `## Unreleased` in this format as each change lands. When the change merges, the version is raised and the entries move under the new version's heading. A project that versions every merge gets one section per merge.

Good bullet:

```markdown
- **The pre-push hook now stops test runs that take longer than 15 minutes.** A hanging test used to block the push forever with no message. Set `tests_deadline_seconds` in `.coast/config.json` to allow longer runs.
```

Bad bullet, for contrast:

```markdown
- **The tests seat runs under a wall-clock deadline** (`tests_deadline_seconds` in the
  config, default 900; `tool:tests-deadline` on rule 06's long-runs line). Born of a real
  run on 2026-09-16: a new guard slid a word stamp pixel by pixel over a bitmap…
```

Everything wrong there: internal terms ("seat", "wall-clock deadline"), a rule reference, an incident story, a date, and hard-wrapped lines that render broken on the release page.

## Before and after

A single installation step, before:

> Run `python3 enforcement/adopt.py <project-dir> --measure-tools` (`--dry-run` first if you like). The installer can be run from a fetched release rather than a clone: the quickstart has the one command that fetches the newest release into `~/.cache/…`. It installs the checks under `.coast/checks/`, the three git hooks under `.githooks/` with `core.hooksPath` set, the Claude Code session hooks…, the platform's linter seeds, … and writes the answers to `.coast/config.json`; `--yes` skips the questions, `--init` asks them again…

After:

> 1. Preview what the installer will change:
>
>    ```bash
>    python3 enforcement/adopt.py <project-dir> --dry-run
>    ```
>
> 2. Install:
>
>    ```bash
>    python3 enforcement/adopt.py <project-dir> --measure-tools
>    ```
>
> 3. Answer the setup questions, or press Enter to keep everything on.
>
> | Installed | Where |
> |---|---|
> | The checks | `.coast/checks/` |
> | Git hooks | `.githooks/` |
> | Your settings | `.coast/config.json` |

A rule, before:

> - **ENG-1** Reactive state: any state that can change while it is
>   displayed, or that outlives a single function call, lives in the
>   framework's state system … — never module-level variables the UI
>   polls or refreshes manually. …

After:

> - **ENG-1** Reactive state: state that can change while it is on screen, or that lasts longer than one function call, lives in the framework's state system (component state, or a store the UI subscribes to). The UI re-renders from it. Never keep it in module-level variables that the UI polls or refreshes by hand.

## Rewriting a large doc set

1. **Inventory.** List every Markdown file with its word count. Note which files are parsed by code, templated, or searched by tests.
2. **Protect what code reads.** Before editing, snapshot the parsed structure (rule ids, tags, headings, placeholders). After each file, compare against the snapshot. A rewrite that changes the snapshot is wrong unless the change was intended.
3. **Find duplicated text.** Text that appears word for word in several files becomes one source that the files include. Rewrite it once.
4. **Write a shared brief** before splitting the work: the reader, these sentence rules, the jargon table, the parsed-structure constraints, and the checks to run. Parallel writers who share a brief write in one voice.
5. **Split by file,** never by section of the same file. No two writers edit the same file.
6. **Verify at the end:** the project's tests, the parsed-structure snapshot, a strict docs build that fails on broken links, and word counts before and after. Spot-check every fact a writer flagged as unverified.
7. **Check the length went the right way.** Guides and READMEs should get much shorter. A reference page may grow because it becomes complete. Rule documents keep their content and gain clarity, so they may stay about the same length.

## Before you finish

Check each item:

1. The first thing on each page tells the reader what it is or what to do.
2. Every step is numbered, has one action, and shows its command in a code block.
3. Every setting, flag and file is in a table on the reference page, checked against the code.
4. No internal jargon is left undefined. Literal names match the code exactly.
5. No history, incident stories, task ids, tickets or plans.
6. No sentence fails the deletion test. No warm-up and no closing summary.
7. No prose line is hard-wrapped. No em dashes.
8. Every link resolves. Release notes use absolute URLs.
9. Everything code reads (ids, tags, headings, placeholders) is unchanged, and the tests pass.
10. Each fact lives on one page, and other pages link to it.
11. Every document that describes something this change altered is updated.
