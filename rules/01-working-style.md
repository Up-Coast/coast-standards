# Working style — how agents work with the owner

Extracted from Coast's working agreements and decision log. Every bullet is a filed
decision, stated in plain words.

## Communication

- **Plain words, never internal labels.** Don't cite internal doc names, decision numbers,
  or list numbers to the owner — say what things mean. The owner does not know the
  contents of an agent's internal documents and should never be addressed as if they did.
  [check: process]
- **No coined names.** Describe things in plain words instead of inventing labels. Don't
  call out absences ("no off switch") that readers may fixate on — describe what a feature
  does. [check: process]
- **Capitalize agent role names** (the Architect, the Reviewer) so it's clear the agent is
  meant, not the noun. [check: process]
- **Every product sentence must be one a support person would say out loud.** No inverted
  fragments. No AI-isms, no filler reassurance copy; every word earns its place.
  [check: review]
- **Never use the word "guarantee"** in any copy or docs — it is a legal word. Use
  protections / enforcement / safeguards. [check: scan:retired-wording]
- **Report when done, unprompted.** Every time work is done, report it. The owner should
  never have to send a follow-up message asking, because that wastes credits.
  [check: process]

## Questions and decisions

- **When the owner asks a question, answer it — change nothing.** (2026-08-20.) No file
  edits, plan updates, or commits in the same turn as answering; offering "want me to
  update X accordingly?" inside the answer is fine. The change happens when the owner
  decides. [check: process]
- **Ask the minimum real questions**, each phrased as a recommended default the owner can
  veto. Decide internal engineering questions yourself. [check: process]
- **Ask only on real design changes.** If what you've done matches the requirements and
  doesn't change the design, you don't need approval. [check: process]
- **All design decisions are the owner's.** Propose and ask; never install. Audits report;
  they never rewrite. [check: process]
- **Never improvise past a filed decision.** A genuinely open choice is authored as a
  veto-able default and logged for the owner's review; a choice that would change the
  owner's design is asked. [check: process]
- **Defaults are fine** — they can be changed easily later — but keep a log of every
  design-ish default a session authored, so the owner can veto later.
  [check: process]
- **Provenance rule:** load-bearing decisions record the owner's words as given; anything
  that is an agent's summary or generalization is marked as such. [check: process]

## Truth and errors

- **Primary sources only** for any factual claim about an external product, API, policy,
  pricing, or terms. Always read the official documentation before giving an answer.
  If the primary source is unreachable, say the answer is unverified.
  [check: process]
- **Fix errors when found.** Stale paths and references in live docs/skills/config get
  fixed and committed the same session, not just reported. Exceptions: transcripts are
  append-only (correct via appended notes); hash-locked vendored skills are
  flag-don't-edit. [check: process]
- **Newest information wins.** Where documents contradict, the newer decision wins; the
  older doc simply wasn't updated — update it. [check: process]
- **No retired content in live docs.** Remove outdated mechanisms rather than keeping them
  with "historical" banners; stale text confuses other agents. [check: process]
- **Decisions are filed, not just said.** When a later decision changes an earlier one, the
  earlier entry is updated too and the change is called out — no silent edits. Conflicts get
  surfaced, not guessed. [check: process]

## Ownership and bookkeeping

- **Agents own all tooling/setup work; the owner provides requirements.** Third-party
  dashboard config, repo creation, research, and writing are agent tasks. The owner's list
  holds only what is genuinely the owner's: decisions, approvals, sign-ins, payments, legal
  attestations, filming, physical-device testing, recruiting humans. A task needing one
  unlock from the owner stays on the agent's list with a "needs from you: <one thing>"
  note. [check: process]
- **Pending work lives in exactly ONE place.** Keep separate lists for: remaining work,
  deferred ideas (may build later), and out-of-scope (decided never — do not re-raise).
  When a decision defers or rejects something, file it the same session.
  [check: process]
- **Act as a human when verifying.** Type what needs to be typed, upload what should be
  uploaded, click the buttons that should be clicked. Never hand-seed a surface the system
  is supposed to populate — an invented screen hides the bug the walk exists to find.
  [check: process]
- **Verify the whole product against the design, in live mode.** A fixture/demo screenshot
  proves nothing; self-screenshotting only the screens you just built is the failure mode
  that produced Coast's conformance crisis. Walk everything. [check: process]
- **Long-running commands:** stream output through `tee` to a log file and give the owner
  the path, so they can tell stuck from slow. Know what a healthy run looks like; kill and
  investigate a wedged one instead of waiting. [check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
