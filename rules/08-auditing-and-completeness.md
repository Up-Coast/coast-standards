# Auditing and completeness — never trust the tracker

The core rule: **an audit rebuilds the list from the code; it never reviews the list.** A tracker, an inventory page or a "what's left" document only records what somebody remembered to write down. Checking it against itself only proves that it agrees with itself.

Why: a page claiming "everything not on this page is built" can be wrong in many places, and an audit that checks the page instead of the source will miss all of them.

## The method

1. **Name the scope out loud before starting, and again in the report.** "I audited the frontend against the design" can be true. "I audited the project" almost never is. An audit of one layer proves nothing about the other layers. A report that does not name its layer will be read as covering everything.
2. **Rebuild the inventory from primary sources.** Go through the code, the specs and the decision log, and work out what should exist. Then compare that list with the existing tracker. Items missing from the tracker are the findings. Tracker items that the code already satisfies are stale and should be closed.
3. **Sweep for the shapes that hide unbuilt work.** These checks are mechanical and fast, and they are where missed work is usually found:
   - Dispatch tables, factories and hook maps that return nothing for a case. An empty branch is a feature that silently does not exist.
   - Comments admitting deferral: "not built yet", "not implemented", "stub", "placeholder", "until … lands", "filed", "TODO", "for now".
   - Code that throws or refuses with a message written for a person. Those messages tell you, in the system's own words, what is missing.
   - Every declared role, mode, kind or type in an enum: does anything create it? A case that nothing creates is a design that never shipped.
   - Every user-facing setting or toggle: does anything read it? A setting that no code reads is a promise to the user that nothing keeps.
   - Every public function that is built and exported: does anything call it outside the tests? If only tests call it, it was built but never connected.
   - Every stage or step named in the spec: is it in the sequence the runtime actually runs?
4. **Check the paths tests never take.** Find the conditions no test fixture ever sets, such as a flag that is false in every fixture, or a branch no sample data reaches. Unbuilt work survives exactly where the tests never look.
5. **File everything in the same session, where pending work lives.** A finding that stays only in the report gets missed again. Add it to the project's real pending-work list, with what it is, what happens today when someone hits that path, and how severe it is.
6. **Rank by what a user can reach.** A gap behind a button that ships outranks a gap behind a flag nobody has turned on. Say clearly which findings a user can reach today, and how.
7. **Retire false completeness claims.** If a document says everything not listed is done, either prove it with a sweep or delete the sentence. Replace it with what was actually checked, and when. [check: process]

## Every built surface is on a route

A public view or component is not done unless something on a route in the shipping product creates it, whatever its tests and captures say. A route counts if the product has it, either on by default or behind a declared feature flag whose off state is a named deferral. A debug component gallery, a catalogue, a preview, a storybook or a test does not count as a route.

If a view is deliberately not mounted yet, the comment above its declaration says so: `not-mounted-yet: <the task that mounts it>`. This keeps the list of deferred views in the code, not in a document nobody builds from. The rules scanner checks this across the whole codebase. The acceptance criteria of every UI task name the route (and the flag, if there is one).
[check: scan:unreached-view]

## Audit against the product's promise, not only against its specs

Comparing code to specs finds things that were designed and never built. It cannot find the more dangerous gap: **capabilities everyone assumes the product has, but that were never designed.** There is no spec for the code to fall short of, so the sweep comes back clean and the false belief survives.

Why: every spec-versus-code sweep can agree that a feature works, while the product cannot do something basic that everyone assumes it does, because no spec ever described it.

So, in every audit, also do the following:

- **Write down what the product claims**, from its marketing, its onboarding, its help text, and what the team says about it. Then check each claim against the code, whether or not a spec covers it. [check: process]
- **Walk the first-run path as a new user**, not as someone who knows where the working parts are. The gaps a team cannot see are the ones their habits avoid. [check: process]
- **Treat "we always said it does X" as a finding to verify**, never as an assumption. [check: process]
- When a claim turns out to be unsupported, report two findings: the missing code, and the fact that nobody questioned the belief.

## Case log — what has actually been missed, and the check each one produces

**This list grows.** Each time an audit misses something significant, add the miss here with the mechanical check that would have caught it. Each entry is a real failure paired with a check that is cheap to run, and that list is the most valuable part of this file.

All entries below come from August–September 2026. Several audits in the same few days came back clean while these problems were in the code.

| What was missed | Why it survived the audit | The check that catches it |
|---|---|---|
| A specialist agent had a full role definition but **no implementation**. Any work that needed it stopped and asked a person to do it by hand. | Audits covered a different layer, and no live run ever included work that needed this agent. | **Every case in every enum needs a place that creates it.** Grep for each case being created, not just declared. Also read **every dispatch-table branch that returns nothing**: each is a missing feature. |
| A pipeline stage **blocked permanently** on certain work, with no way for a person to clear it. The stop ran before the code that reads the person's decision. | **No test fixture ever set the flag that triggers it.** Every fixture used the default. | **List the flags, states and inputs that no fixture exercises**, and read those paths by hand. |
| A user-facing setting **was read by nothing**, so the feature it promised never happened. | Tests checked that the setting existed and was saved, not that anything used it. | **Every user-facing setting must have a reader.** Grep for code that uses it in logic, not just code that stores it. |
| A safety rule ("no work starts before approval") was **silently off in the live product**. It depended on a record that only the demo path could create. | The rule's code existed, and its tests passed against fixtures that could create the record. | **A guard that depends on state one mode cannot produce is off in that mode.** For each guard, check which modes can meet its precondition. |
| A cost-affecting option was computed and shown to the user, but **no working step read it.** Users were told the work would be more thorough; it was identical. | The calculation and the display were both correct and both tested. | **Every value shown in the interface must reach the logic.** Trace each displayed value forward to the code that acts on it. |
| Code was built and exported but **never connected**. Its only callers were its own tests. | Coverage looked fine, because tests count as callers. | **Grep every exported function for callers outside the test directory.** |
| Documents for other platforms existed, but **nothing installed them**, because the installer refused those platforms. | The documents were complete and reviewed. Nobody checked whether anything used them. | **Every artifact needs a consumer.** For each shipped file or asset, find the code that puts it where it is used. |
| A gap **named in a decision record** was never added to the work list and was still open two months later. | The decision log is not the work list, and nobody compared the two. | **Compare the decision log with the work list.** Every decision that names unfinished work needs a filed task. |
| A product **claiming five platforms** had **no per-project platform field**. Detection ran once at launch and fell back to the first platform, so every stage was built for that one platform only. | Audits checked one capability at a time, and each looked complete for its platform. Nobody took one project of EACH platform through EVERY stage. | **Build the stage × variant table and fill every cell.** For each dimension the product claims to vary over (platform, project type, tier, locale), take one instance of each variant through every stage and mark each cell supported or not. First check that the variant is *stored* where every stage can read it. |
| Everyone believed the product could **create a project**. No spec ever described that, so no spec-versus-code audit could find it was missing. | Every sweep compared code to specs, and there was no spec to fall short of. | The product-promise method above: **audit the claims, not just the specs.** |
| An inventory page claimed *"everything not on this page is built"*. **It was false in more than a dozen places.** | The claim was inherited and never re-checked. Later sessions took it as true. | **Treat every completeness claim in a document as unverified** until a sweep proves it. Remove the ones you cannot prove. |
| A rules document still said **the opposite of a decision made hours earlier.** | The decision was recorded in one place, and the document with the old guidance was not updated. | **When a decision reverses guidance, update every document that carries it in the same session.** Then grep for the old wording to prove none is left. |
| The product's home screen was **built, tested, approved from screenshots and marked complete, but only shown in a debug component gallery.** No route in the app drew it. | The acceptance criteria were all about the component, none about a caller. The gallery made a caller search look satisfied. | **A gallery, harness, storybook, preview or test is not a consumer.** Every public view needs a construction site on a shipping route, or an entry on the not-mounted-yet list with the task that will mount it. UI acceptance criteria name the route (and flag, if any). The rules scanner's `unreached-view` check enforces this. |

The pattern in almost every case: **the code was honest and the documents were not.** Nearly every gap was visible in the source: an empty branch, a comment admitting deferral, or a message explaining to a person what was not built. The failure was that nobody read the code for those signals, and everyone trusted the tracker instead.
[check: process]

## Reporting

State the scope, the method and the limits. For example: "I checked every enum case for a place that creates it and every setting for a reader; I did not verify the behavior of the built paths." That is a useful report. A confident "all clear" that was never earned is worse than no audit, because it stops the next person from looking.

Never claim **"everything else is built"** or **"this is complete"** without a sweep that checked it. [check: process]

## When an audit misses something, add it here

This is how this file is maintained. A missed finding is not just a bug to fix. It shows the audit method has a gap. When you find something significant that an earlier audit should have caught:

1. Add a row to the case log: what was missed, why it survived, and the **mechanical check** that would have caught it. The check is what matters; "be more careful" is not a check.
2. If the miss does not fit any existing check, it needs a new one. Say so.
3. Do this in the same session as the discovery, while the reason it was missed is still clear.

The purpose of this list is to make each future audit more accurate than the last. [check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
