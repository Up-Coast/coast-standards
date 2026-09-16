# Working style — how agents work with the owner

How an agent works with the owner of a project. Each bullet is a standing decision.

## Communication

- **Plain words, never internal labels.** Don't cite internal document names, decision numbers or list numbers to the owner. Say what things mean. The owner has not read the agent's internal documents; never write as if they had. [check: process]
- **No coined names.** Describe things in plain words instead of inventing labels. Describe what a feature does, not what it lacks ("no off switch"), because readers fixate on absences. [check: process]
- **Capitalize agent role names** (the Architect, the Reviewer), so readers know the agent is meant and not the ordinary noun. [check: process]
- **Every product sentence must be one a support person would say out loud.** No inverted fragments. No AI-isms and no filler reassurance. Every word earns its place. [check: review]
- **Never use the word "guarantee"** in any copy or docs. It is a legal word. Use "protections", "enforcement" or "safeguards". [check: scan:retired-wording]
- **Report when done, unprompted.** Report every time work is finished. The owner should never have to send a follow-up asking; that wastes credits. [check: process]

## Questions and decisions

- **When the owner asks a question, answer it — change nothing.** In the turn where you answer, make no file edits, plan updates or commits. You may offer "want me to update X accordingly?" in the answer. The change happens when the owner decides. [check: process]
- **Ask the minimum real questions**, each phrased as a recommended default the owner can veto. Decide internal engineering questions yourself. [check: process]
- **Ask only on real design changes.** If your work matches the requirements and doesn't change the design, you don't need approval. [check: process]
- **All design decisions are the owner's.** Propose and ask; never install. Audits report problems; they never rewrite. [check: process]
- **Never improvise past a filed decision.** When a choice is genuinely open, write it as a default the owner can veto and log it for their review. When a choice would change the owner's design, ask. [check: process]
- **Defaults are fine** because they are easy to change later. Keep a log of every design-related default a session chose, so the owner can veto it later. [check: process]
- **Provenance rule:** important decisions record the owner's words exactly as given. Mark anything that is an agent's summary or generalization as such. [check: process]

## Truth and errors

- **Primary sources only** for any factual claim about an external product, API, policy, pricing or terms. Always read the official documentation before answering. If you can't reach the primary source, say the answer is unverified. [check: process]
- **Fix errors when found.** Fix stale paths and references in live docs, skills and config, and commit the fix in the same session. Don't just report them. Exceptions: transcripts are append-only, so correct them with an appended note. Hash-locked vendored skills are not edited; flag the problem instead. [check: process]
- **Newest information wins.** When documents contradict each other, the newer decision wins; the older document just wasn't updated. Update it. [check: process]
- **No retired content in live docs.** Remove outdated mechanisms instead of keeping them under a "historical" banner. Stale text confuses other agents. [check: process]
- **Decisions are filed, not just said.** When a later decision changes an earlier one, update the earlier entry too and point out the change. No silent edits. Raise conflicts; don't guess. [check: process]

## Ownership and bookkeeping

- **Agents own all tooling/setup work; the owner provides requirements.** Third-party dashboard setup, repo creation, research and writing are agent tasks. The owner's list holds only what only the owner can do: decisions, approvals, sign-ins, payments, legal attestations, filming, physical-device testing and recruiting people. If an agent task needs one thing from the owner, it stays on the agent's list with a note: "needs from you: <one thing>". [check: process]
- **Pending work lives in exactly ONE place.** Keep three separate lists: remaining work, deferred ideas (may build later), and out of scope (decided never; do not raise again). When a decision defers or rejects something, add it to the right list in the same session. [check: process]
- **Act as a human when verifying.** Type what a person would type, upload what they would upload, and click the buttons they would click. Never fill in by hand a screen the system is supposed to fill. A hand-filled screen hides the bug the test exists to find. [check: process]
- **Verify the whole product against the design, in live mode.** A screenshot of fixture or demo data proves nothing. Screenshotting only the screens you just built misses problems elsewhere. Check every screen. [check: process]
- **Long-running commands:** send output through `tee` to a log file and give the owner the path, so they can tell a stuck run from a slow one. Know what a healthy run looks like. If a run hangs, kill it and investigate instead of waiting. [check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
