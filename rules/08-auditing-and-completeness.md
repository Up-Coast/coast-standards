# Auditing and completeness — never trust the tracker

Read this when a task audits a project or claims work is complete.

**An audit rebuilds the list from the code; it never reviews the list.** A tracker only records what someone wrote down.

## The method

1. **Name the scope** at the start and in the report. One layer proves nothing about others.
2. **Rebuild the inventory from primary sources** (code, specs, decision log) and compare it with the tracker. Missing items are findings; items the code satisfies are closed.
3. **Sweep for the shapes that hide unbuilt work:**
   - Dispatch tables, factories and hook maps that return nothing for a case.
   - Deferral comments: "not built yet", "not implemented", "stub", "placeholder", "until … lands", "filed", "TODO", "for now".
   - Code that throws or refuses with a message written for a person.
   - Every enum role, mode, kind or type: does anything create it?
   - Every user-facing setting or toggle: does anything read it?
   - Every exported public function: does anything outside the tests call it?
   - Every stage or step in the spec: is it in the sequence the runtime runs?
4. **Check the paths tests never take**: conditions no fixture sets, such as a flag false in every fixture or a branch no sample data reaches.
5. **File every finding that session** in the pending-work list: what it is, what happens today on that path, severity.
6. **Rank by what a user can reach.** Say which findings a user can reach today, and how.
7. **Retire false completeness claims.** Prove "everything not listed is done" with a sweep or delete it, and state what was checked and when. [check: process]

## Every built surface is on a route

A public view or component is done only when a shipping route creates it. A route is on by default or behind a declared flag whose off state is a named deferral. A debug gallery, catalogue, preview, storybook or test is not a route. A view deliberately not mounted carries `not-mounted-yet: <the task that mounts it>` in the comment above its declaration. Every UI task's acceptance criteria name the route, and the flag if any. [check: scan:unreached-view]

## Audit against the product's promise, not only against its specs

Spec sweeps miss capabilities assumed but never designed. In every audit:

- **Write down what the product claims** in marketing, onboarding, help text and team talk. Check each against the code. [check: process]
- **Walk the first-run path as a new user**, not as someone who knows where the working parts are. [check: process]
- **Treat "we always said it does X" as a finding to verify**, never an assumption. [check: process]
- For an unsupported claim, report two findings: the missing code, and that nobody questioned the belief.

## Case log — what has actually been missed, and the check each one produces

Add each significant audit miss here with the mechanical check that would have caught it.

| Missed | Why it survived | Check |
|---|---|---|
| A defined role with no implementation. | Audits covered another layer. | Grep each enum case for a creation site. Read every dispatch branch that returns nothing. |
| A stage that blocked forever before reading the person's decision. | No fixture set the flag. | List flags, states and inputs no fixture exercises; read those paths. |
| A setting nothing read. | Tests checked saving, not use. | Every user-facing setting needs a reader in logic. |
| A safety guard off live; its record came only from the demo path. | Fixtures could create the record. | For each guard, check which modes can meet its precondition. |
| A displayed option no step read. | Display was tested, not use. | Trace every displayed value to the logic that acts on it. |
| Exported code called only by tests. | Tests count as callers. | Grep every exported function for callers outside tests. |
| Documents nothing installed. | Nobody checked use. | Every shipped file or asset needs code that puts it in place. |
| A gap in a decision record, never filed. | Nobody compared log and list. | Every decision naming unfinished work needs a filed task. |
| No stored per-project platform; every stage built for one. | Capabilities were checked alone. | Fill a stage × variant table (platform, project type, tier, locale) after checking every stage can read the stored variant. |
| An assumed capability no spec described. | Sweeps compared code to specs. | Audit the claims, not just the specs. |
| A false "everything else is built" page. | Inherited unchecked. | Treat completeness claims as unverified until swept; remove unproven ones. |
| A document contradicting a newer decision. | One place was updated. | When a decision reverses guidance, update every document carrying it that session, then grep for the old wording. |
| A finished screen shown only in a debug gallery. | The gallery looked like a caller. | A gallery, harness, storybook, preview or test is not a consumer; see the route rule above. |

Read the code for these signals, not the tracker. [check: process]

## Reporting

State the scope, the method and the limits, for example: "I checked every enum case for a creator and every setting for a reader; I did not verify built paths' behaviour." Never claim **"everything else is built"** or **"this is complete"** without a sweep that checked it. [check: process]

## When an audit misses something, add it here

In the same session as the discovery:

1. Add a case-log row: what was missed, why it survived, and the **mechanical check** that catches it. "Be more careful" is not a check.
2. If no existing check fits, say a new one is needed. [check: process]

---

[← All rules](README.md) · [Documentation](../docs/README.md)
