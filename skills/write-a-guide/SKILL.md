---
name: write-a-guide
description: House style for guides, the documentation that tells a reader what something is, how it works, how to use it and how to change it. Load it BEFORE writing any doc, docs or documentation, even when the request never says "guide". Covers internal docs for a team (dashboards, pipelines, scripts, tools, processes), product help for users, READMEs and handover docs, wherever they will live (a wiki, a README, a help page, a docs site). Trigger phrases: "document this", "create a document", "write a doc", "write the docs", "documentation for", "write up how this works", "explain how this works so the team can use it", "README", "how-to", "user guide", "help article", "handover", "instructions for the team". When in doubt about whether a request is documentation, load it. Not for research write-ups, findings or reports, and not for marketing copy. For developer documentation (installation, configuration, CLI and settings references, release notes, rule documents), also load write-developer-documentation; where the two differ, that skill wins for developer documentation.
---

# Write a guide

A guide tells someone who has to use or look after a thing what it is, how it works, how to use it and how to change it. It is short, plain and exact. Someone should be able to read it once, then do the thing.

## The model this skill is tuned for

This skill is tuned for Opus 5 at medium effort. On another model or effort level it may be followed less closely.

Each time you load this skill, tell the person you are working for, in one line, before you start writing:

- the model you are running on, as your system prompt names it
- the effort level, if your context states it; if it does not, say the effort level is not visible to you
- whether that matches Opus 5 at medium effort

Example: "Loaded write-a-guide, which is tuned for Opus 5 at medium effort. This session runs Opus 5; the effort level is not visible to me."

## Before writing

1. **Read one existing doc where this one will live.** Match its length, heading style, list punctuation and how it names people. A guide should read like the rest of that team's docs.
2. **Check every fact in the product itself.** Open the tool and read the real button labels, menu names and tab names ("Update insight", not "Save", if that is what the button says). Take the numbers from the source, not from memory. If you can't check something, leave it out or say so in the guide.
3. **Decide who is reading.** The default reader knows the product in general but has never seen this thing. Write for that person. Skip what they already know; explain what is specific to this thing.

## Shape

Most guides have the same four parts. Use only the ones the thing needs, in this order:

1. **Opening, 1 or 2 sentences.** What exists, where it lives and what it is built from. No "This document explains...".
2. **What there is.** One short paragraph per item, starting with the item's name in bold (linked if it has a URL), then a colon, then what it contains or does.
3. **How it works.** Only the mechanics that change how someone reads or uses the thing. Give the reason for a design choice in one clause ("because each metric follows the same customer across several events"). State known limits plainly, with dates and numbers.
4. **How to use it and how to change it.** Numbered steps, then a short list headed "A few things to know:" for the behaviour that surprises people.

Headings are short and plain, named for the section's topic: "Dashboards", "How they work", "Editing a chart", "Filtering". No clever headings.

Length: shorter than feels natural. A good guide to four dashboards, their mechanics, editing and filtering fits in about 600 words. If a section runs past one screen, it is probably explaining things the reader doesn't need.

## Sentences

- **Every sentence is a fact the reader will use.** Run the deletion test: if cutting it loses nothing the reader needs, cut it.
- **Present tense, current state only.** Describe how the thing works now. No history, no "we added", no "previously", no change log. No references to unfinished work, open tickets or future plans. A guide goes stale the moment it talks about plans.
- **Leave out detail the reader doesn't act on.** A true fact that nobody needs in order to find or use the thing does not belong in the guide.
- **Instructions are imperative.** "Click Filter and search for the property." Use "you" only where a sentence reads badly without it.
- **Name the person when an action goes to someone.** "ask Priya", not "contact the maintainer".
- **Be specific.** "Points based on fewer than 20 customers are hidden", not "small samples may be suppressed". Real dates, real counts, real names.
- **No commentary, no warm-up, no closer.** No "Note that", "It's worth mentioning", "Simply", "Easily", "Powerful", "Seamless". No closing summary or sign-off. End on the last useful fact.
- **No process narrative.** The guide never says how it was written, what was tested or who fixed what.
- Plain punctuation. No em dashes. Match the house spelling.

## Formatting

- **Bold** for UI labels exactly as they appear on screen (**Filter**, **Save filters**, **Update insight**) and for the name that opens a paragraph.
- `Code formatting` for anything typed or matched exactly: property names, values, IDs, file names, code fragments (`plan_type`, `true`, `(not set)`).
- Numbered lists for steps a reader performs in order. Bulleted lists for independent facts. No full stop at the end of list items, unless the house style uses them.
- Link each thing the first time it's named, if it has a URL. Give links descriptive text, never a bare URL.
- No tables unless the content is a real grid (several items across the same several attributes). No emoji. No horizontal rules.

## Screenshots

Add a screenshot where it saves the reader from hunting for something on screen. Usually that means three places:

1. The main screen of the thing, under its description, so the reader recognises it.
2. The step with a control that's hard to describe (a value picker that only appears after clicking a chip).
3. The result of an action, so the reader knows it worked (a chart split into one line per value).

Rules:
- Take them from the real product, in a clean state: no half-finished test filters, no error banners, no leftover glitches (reload if a legend or panel shows stale entries).
- Put each screenshot right after the step or paragraph it illustrates. No caption unless the house style uses them.
- Undo anything you changed to get the shot (discard filters, cancel edit modes) and confirm nothing was saved.
- Don't capture personal data, secrets or unrelated tabs.

## Examples

Opening:
> There are four retention dashboards in the analytics **Subscriptions** project. They are built from the events the billing service sends, which cover every customer since 1 March 2025.

An item in an inventory:
> **Retention outcomes**: the results the early signals should predict: first-year renewal rate, repeat renewal rate, lapsed customers coming back and trial conversion rate. The analytics tool has no data before 1 March 2025, so the earlier values on the two renewal charts come from the billing export and are written into the query.

A mechanism with its reason:
> Every chart is a SQL query rather than a regular trends chart, because each metric follows the same customer across several events (for example a first paid charge followed by auto-renew being turned off within 30 days).

Steps, followed by the surprise:
> 1. Click **Filter** and search for the property
> 2. Click the property, then click the chip that appears
> 3. Type the value and press Enter
>
> The tool only suggests values seen in the last 7 days, so older values have to be typed.

The same content written badly, for contrast:
> In this section, we'll walk through how you can easily filter the dashboards to unlock deeper insights! Simply head over to the Filter button — it's super intuitive. Note that we recently added this feature (see ticket DATA-850), and more improvements are coming soon.

Everything wrong there: a warm-up, filler words, an em dash, history, a ticket reference, a promise about the future, and no actual steps.

The same style applied to a product guide:
> **Agents** run the work on a project. Each agent has one role (planning, building, reviewing) and only sees the files its role needs.
>
> To start a run:
> 1. Open the project and click **New run**
> 2. Describe the change in the prompt box
> 3. Click **Start**
>
> A few things to know:
> - A run stops at the first failed check and shows the failing step
> - Runs are not saved until you click **Keep**

## Before publishing

Check each item:

1. Every button, tab and menu name matches the product exactly.
2. Every number, date and name has been checked against its source.
3. Nothing describes history, unfinished work, tickets or plans.
4. No sentence fails the deletion test; there's no warm-up and no closing summary.
5. Steps are numbered and imperative; identifiers are in code formatting; UI labels are in bold.
6. Screenshots are clean, sit in the right place, and the product was left as it was found.
7. Length and formatting match the other docs where it will live.
8. No em dashes.

Save the guide as a draft first. Ask before publishing unless you've been told to publish; publishing makes it visible to the whole team.
