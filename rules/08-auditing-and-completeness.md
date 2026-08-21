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
the tracker rather than the source. Abbey: "for an in-depth audit we should be
looking at the sources that page comes from and essentially rebuilding that
page."

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
   Replace it with what was actually checked, and when.

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
- **Walk the first-run path as a new user**, not as someone who knows where the working
  parts are. The gaps a team can't see are the ones their habits route around.
- **Treat "we always said it does X" as a finding to verify**, never as a premise.
- When a claim turns out to be unsupported, the finding is not just the missing code — it
  is also that the belief went unchallenged, and both belong in the report.

## Reporting

State the scope, the method, and the limits. "I checked every enum case for a
construction site and every settings dial for a reader; I did not verify
behaviour of the built paths" is a useful report. A confident "all clear" that
was never earned is worse than no audit, because it stops the next person from
looking.

Two claims are never made without a sweep that checked them: **"everything
else is built"** and **"this is complete."**
