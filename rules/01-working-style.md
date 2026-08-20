# Working style — how agents work with Abbey

Extracted from Coast's CLAUDE.md and capture log. Quotes are Abbey verbatim; everything else
is a faithful paraphrase of a filed decision.

## Communication

- **Plain words, never internal labels.** Don't cite internal doc names, decision numbers,
  or list numbers to Abbey — say what things mean. "I really wish you would stop referring
  to your internal documents as if I know the contents of them."
- **No coined names.** Describe things in plain words instead of inventing labels. Don't
  call out absences ("no off switch") that readers may fixate on — describe what a feature
  does.
- **Capitalize agent role names** (the Architect, the Reviewer) so it's clear the agent is
  meant, not the noun.
- **Every product sentence must be one a support person would say out loud.** No inverted
  fragments. No AI-isms, no filler reassurance copy; every word earns its place.
- **Never use the word "guarantee"** in any copy or docs — "that's a legal word." Use
  protections / enforcement / safeguards.
- **Report when done, unprompted.** "Everytime work is done I would like you to report that
  to me... I shouldn't have to add a follow up message asking this as it wastes credits."

## Questions and decisions

- **When Abbey asks a question, answer it — change nothing.** (Abbey, 2026-08-20: "stop
  making changes when I ask a question.") No file edits, plan updates, or commits in the
  same turn as answering; offering "want me to update X accordingly?" inside the answer is
  fine. The change happens when she decides.
- **Ask the minimum real questions**, each phrased as a recommended default Abbey can veto.
  Decide internal engineering questions yourself.
- **Ask only on real design changes.** "If what you've done matches my requirements and
  doesn't change my design then you don't need my approval."
- **All design decisions are hers.** Propose and ask; never install. Audits report; they
  never rewrite.
- **Never improvise past a filed decision.** A genuinely open choice is authored as a
  veto-able default and logged for her review; a choice that would change her design is
  asked.
- **Defaults are fine** ("defaults are fine, we can change them easily later if I want") —
  but keep a log of every design-ish default a session authored, so she can veto later.
- **Provenance rule:** load-bearing decisions quote Abbey's words verbatim; anything that is
  an agent's summary or generalization is marked as such.

## Truth and errors

- **Primary sources only** for any factual claim about an external product, API, policy,
  pricing, or terms. "YOU SHOULD ALWAYS READ OFFICIAL DOCUMENTS BEFORE GIVING ME AN ANSWER."
  If the primary source is unreachable, say the answer is unverified.
- **Fix errors when found.** "when you find errors can you please fix them?" Stale paths and
  references in live docs/skills/config get fixed and committed the same session, not just
  reported. Exceptions: transcripts are append-only (correct via appended notes); hash-locked
  vendored skills are flag-don't-edit.
- **Newest information wins.** Where documents contradict, the newer decision wins; the
  older doc simply wasn't updated — update it.
- **No retired content in live docs.** Remove outdated mechanisms rather than keeping them
  with "historical" banners; stale text confuses other agents.
- **Decisions are filed, not just said.** When a later decision changes an earlier one, the
  earlier entry is updated too and the change is called out — no silent edits. Conflicts get
  surfaced, not guessed.

## Ownership and bookkeeping

- **Claude owns all tooling/setup work; Abbey provides requirements.** Third-party dashboard
  config, repo creation, research, and writing are agent tasks. Abbey's list holds only what
  is genuinely hers: decisions, approvals, sign-ins, payments, legal attestations, filming,
  physical-device testing, recruiting humans. A task needing one unlock from her stays on
  the agent's list with a "needs from you: <one thing>" note.
- **Pending work lives in exactly ONE place.** Keep separate lists for: remaining work,
  deferred ideas (may build later), and out-of-scope (decided never — do not re-raise).
  When a decision defers or rejects something, file it the same session.
- **Act as a human when verifying.** "Type what needs to be typed, upload what should be
  uploaded, click buttons that should be clicked." Never hand-seed a surface the system is
  supposed to populate — an invented screen hides the bug the walk exists to find.
- **Verify the whole product against the design, in live mode.** A fixture/demo screenshot
  proves nothing; self-screenshotting only the screens you just built is the failure mode
  that produced Coast's conformance crisis. Walk everything.
- **Long-running commands:** stream output through `tee` to a log file and give Abbey the
  path, so she can tell stuck from slow. Know what a healthy run looks like; kill and
  investigate a wedged one instead of waiting.
