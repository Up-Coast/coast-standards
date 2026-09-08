# Auditing and completeness — never trust the tracker

The rule this file exists for: **an audit rebuilds the list from the code; it
never reviews the list.** A tracker, an inventory page, or a "what's left"
document records what somebody remembered to write down. Auditing it against
itself proves only that it is internally consistent.

Origin (20 August 2026, Coast): a page headed "Everything not on this page is
built, tested and pushed" was wrong in thirteen places, including agent roles
that existed with rules and toolboxes but nothing that ever started them, and
a founder-facing switch wired to nothing. A large audit had run weeks earlier
and missed all of it, because that audit was scoped to one layer and checked
the tracker rather than the source. The owner's instruction: an in-depth audit
looks at the sources the page comes from and essentially rebuilds the page.

## The method

1. **Name the scope out loud before starting, and again in the report.** "I
   audited the frontend against the design" is an honest sentence. "I audited
   the project" almost never is. An audit of one layer proves nothing about
   any other layer, and a report that doesn't say which layer it covered will
   be read as covering everything.
2. **Rebuild the inventory from primary sources.** Walk the code, the specs,
   and the decision log, and derive what should exist. Then compare that
   derived list against the existing tracker. Items the tracker is missing are
   the finding; items it has that the code already satisfies are stale rows to
   close.
3. **Sweep for the shapes that hide unbuilt work.** These are mechanical and
   fast, and they are where the misses actually live:
   - Dispatch tables, factories, and hook maps that return nothing for a case
     — an empty branch is a feature that silently does not exist.
   - Comments admitting deferral: "not built yet", "not implemented", "stub",
     "placeholder", "until … lands", "filed", "TODO", "for now".
   - Code that raises or refuses with a message aimed at a human — those
     sentences are the system telling you what is missing, in its own words.
   - Every declared role, mode, kind, or type in an enum: does anything
     construct it? A case with no construction site is a design that never
     shipped.
   - Every user-facing setting or toggle: does anything read it? A dial no
     code consults is a promise to the user that nothing keeps.
   - Every public function built and exported: does anything call it outside
     the tests? Tests-only callers mean the seam was built and never wired.
   - Every stage or step named in the spec: is it in the sequence the runtime
     actually executes?
4. **Check the paths tests never take.** Ask what conditions no test fixture
   ever sets — a flag always false in every fixture, a branch no sample data
   reaches. Unbuilt work survives precisely where the tests never look.
5. **File everything in the same session, where pending work lives.** A
   finding that stays in the report is a finding that gets missed again. It
   goes onto the project's real pending-work list, with what it is, what
   happens today when the path is hit, and how severe it is.
6. **Rank by what a user can reach.** A gap behind a shipping button outranks
   a gap behind a flag nobody has turned on. Say plainly which findings are
   reachable today and how.
7. **Retire false completeness claims.** If a document asserts that everything
   not listed is done, either prove it with a sweep or delete the sentence.
   Replace it with what was actually checked, and when. [check: process]

## Audit against the product's promise, not only against its specs

Comparing code to specs finds things that were designed and never built. It cannot find the
more dangerous gap: **capabilities everyone assumes the product has, that were never
designed in the first place.** There is no spec for the code to fall short of, so the sweep
comes back clean and the belief survives.

Origin (20 August 2026): repeated sweeps of the Coast codebase found every designed-but-
unbuilt piece, and all of them agreed the setup step worked. None noticed that the product
could not *create* a project at all — it only ever installed governance onto a repository
that already existed. That was never a spec violation; the specs were written around
adopting existing code. It was a gap between what the product was believed to do and what
anyone had ever designed.

So, in every audit, also do this:

- **Write down what the product claims** — from its marketing, its onboarding, its own
  help text, and the sentences the team says out loud about it. Then check each claim
  against the code, as a claim, independent of whether a spec exists for it.
  [check: process]
- **Walk the first-run path as a new user**, not as someone who knows where the working
  parts are. The gaps a team can't see are the ones their habits route around.
  [check: process]
- **Treat "we always said it does X" as a finding to verify**, never as a premise.
  [check: process]
- When a claim turns out to be unsupported, the finding is not just the missing code — it
  is also that the belief went unchallenged, and both belong in the report.

## Case log — what has actually been missed, and the check each one produces

**This list grows.** Every time an audit misses something significant, the miss gets added
here with the mechanical check that would have caught it. The value of this file is not its
principles — it is this list, because each entry is a failure that really happened and a
check that is cheap to run.

All entries below are from Coast, August 2026. Several audits ran in the same few days and
all of them came back clean while these were sitting in the code.

| What was missed | Why it survived the audit | The check that catches it |
|---|---|---|
| A specialist agent had a full role definition — rules, tool permissions, refusal messages, question routing — and **no implementation**. Any work needing it stopped and asked a human to do it by hand. | Audits were scoped to a different layer, and no live run had ever contained the kind of work that would trigger it. | **Every case in every enum needs a construction site.** Grep for each case being constructed, not just declared. A case nothing constructs is a design that never shipped. And **every branch in a dispatch table that returns nothing is a missing feature** — read them all. |
| A pipeline stage would **permanently block** on certain work, with no way for a human to clear it, because the stop was placed before the code that reads a human's decision. | **No test fixture ever set the flag that triggers it.** Every fixture in the suite used the default value. | **List the flags, states, and inputs that no fixture ever exercises**, and read those paths by hand. Unbuilt and broken work survives exactly where the tests never look. |
| A user-facing setting — a switch a founder could turn on — **was read by nothing.** The feature it promised silently never happened. | Tests confirmed the setting existed and persisted. Nothing tested that anything consumed it. | **Every user-facing setting must have a reader.** For each one, grep for something that consults it in logic, not just something that stores it. |
| A safety rule ("no work starts before approval") was **silently off in the live product**, because it was conditioned on a record that only the demo path could create. | The rule's code existed and its tests passed — against fixtures that could produce the record. | **A guard conditioned on state that one mode cannot produce is disabled in that mode.** For each guard, ask which modes can actually satisfy its precondition. |
| A cost-affecting path was computed, shown to the user, and **read by no step that does work.** Users were told the work would be more thorough, and it was identical. | The computation and the display were both correct and both tested. | **Every value that reaches the interface must reach the logic.** Trace each displayed value forward: who acts on it? A value that only ever gets shown is a promise nothing keeps. |
| Work built and exported, then **never wired in** — its only callers were its own tests. | Coverage looked fine. Tests are callers. | **Grep every exported function for callers outside the test directory.** Test-only callers mean a seam was built and never connected. |
| Deliverables that existed but **nothing installed** — several documents written for other platforms, unreachable because the only code that installs them refused those platforms. | The documents were real, complete, and reviewed. Nobody checked whether anything consumed them. | **Every artifact needs a consumer.** For each shipped file or asset, find the code that puts it where it's used. |
| A gap **named inside a decision record** in one month, never transferred to the work list, still open two months later. | The decision log is not the work list, and nobody diffed one against the other. | **Diff the decision log against the work list.** Any decision that names an unfinished thing must have a corresponding filed task, or the gap lives only in prose nobody builds from. |
| A product **claiming five platforms** whose pipeline had **no per-project platform field at all** — the detection function had one caller, at launch time, falling back to the first platform. So every stage was written for that one platform, and re-corrected sessions kept reproducing it. | Audits went capability by capability — is the gate built, is the scaffold built — and each capability looked complete for the platform it was written for. Nobody walked one project of EACH platform through EVERY stage. | **Build the stage x variant table and fill every cell.** For each dimension the product claims to vary over (platform, project type, tier, locale), walk one instance of each variant through every stage in order and mark each cell supported or not. The table is the audit. A capability list cannot find a variant nothing branches on — and first check that the variant is even *stored* somewhere every stage can read. |
| A capability everyone believed the product had — **creating a project** — which no specification ever described, so no spec-versus-code audit could find it. | Every sweep compared code to specs. There was no spec to fall short of. | The product-promise method above: **audit the claims, not just the specs.** |
| An inventory page asserting *"everything not on this page is built"* — **which was false in more than a dozen places.** | The claim was inherited and never re-verified; later sessions trusted it as a premise. | **Treat every completeness claim in a document as an unverified assertion** until this sweep proves it. Retire the ones you can't prove. |
| A rules document still stating the **opposite of a decision made hours earlier.** | The decision was recorded in one place; the document carrying the old guidance was not updated. | **When a decision reverses guidance, update every document that carries it in the same session** — then grep for the old wording to prove none survives. |

The pattern across almost all of these: **the code was honest and the documents were not.**
Nearly every gap was visible in the source — an empty branch, a comment admitting deferral,
a message written for a human explaining what wasn't built. What failed was that nobody read
the code for those signals, and the tracker was trusted instead.
[check: process]

## Reporting

State the scope, the method, and the limits. "I checked every enum case for a
construction site and every settings dial for a reader; I did not verify
behaviour of the built paths" is a useful report. A confident "all clear" that
was never earned is worse than no audit, because it stops the next person from
looking.

Two claims are never made without a sweep that checked them: **"everything
else is built"** and **"this is complete."** [check: process]

## When an audit misses something, add it here

This is the maintenance rule for this file. A missed finding is not just a bug to fix — it
is evidence that the method has a hole. When something significant is found that a previous
audit should have caught:

1. Add a row to the case log: what was missed, why it survived, and the **mechanical check**
   that would have caught it. The check is the part that matters — "be more careful" is not
   a check.
2. If the miss doesn't fit any existing check, it is a new one. Say so.
3. Do it in the same session as the discovery, while the reason it survived is still clear.

Filed 20 August 2026, after several audits in the same week each came back clean while
major pieces sat unbuilt: the list of learnings exists so that future audits are more
correct. [check: process]
