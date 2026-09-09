# Working with models and agents in a codebase

Applies to any project where AI agents write, review, or plan code — which is all of them
here. These are engineering rules, not conversation rules: they govern spend, correctness,
and the integrity of the git history.

## Model effort is set deliberately, and frugally

Never inherit the provider's default. Provider defaults are tuned to show off capability,
not to spend someone else's money carefully. The posture, set by the owner: be frugal with
the customer's money. A mid-tier model may default to high effort, but a frontier model
should default to medium; the provider default for a frontier model is high, which is not
needed except for complex work.

- **Use the lowest effort that reliably clears the job's quality bar.** Capability
  substitutes for effort: a frontier-class model defaults one notch *lower* than a mid-tier
  model on the same job, because it needs less deliberation to reach the same answer.
  [check: process]
- **Set it per role, not globally.** Reviews and second opinions err upward — a missed
  defect costs more than the tokens. Small bounded jobs (classification, extraction, a
  yes/no check) run at minimum effort everywhere. [check: process]
- **Tune from recorded real spend, never from paid calibration runs.** Adjusting a default
  by running experiments to find the right setting spends the money the setting was meant to
  save. [check: process]

## Know which model is running before you start

- **Read the actual model identity before beginning a task that was assigned to a specific
  model.** If it's not the one specified, stop and say so *before* building — cleaning up
  after the wrong model is worse than not starting. (Origin: about 5,000 lines of
  committed, tested work by the wrong model had to be discarded; cleaning up another
  agent's work is never as good as building right from the start.)
  [check: process]
- **Commit trailers name the model that actually did the work.** Mis-attributing a commit
  corrupts the history's usefulness for exactly the debugging this rule exists to support.
  This is a git-integrity rule, not a courtesy.
  [check: session:attribution-trailer]

## Don't dictate diffs into code you don't own

When work needs a change in a part of the codebase someone else owns — another agent,
another team, another module's maintainer — **send the task and the goal, not the diff.**
Name what you're trying to achieve and why; let the owner decide whether the right move is
extending an existing function, adding a new one, or telling you the existing API already
covers it.

The failure this prevents: an owner who is handed a specific edit tends to be accommodating
and just apply it, which is how a codebase accumulates changes nobody evaluated against the
surrounding code. An owning agent may be reactive or overly helpful and simply apply what
it is handed; it needs to do what is best for its own part of the codebase — keeping it
readable, clear, simple, and DRY, following best practices for its own small world.
[check: process]

## Check what you already have before adding manual steps

Before telling a human to do something by hand, check — in this order — your installed
skills, the project's tooling reference, the memory directory, and the connected servers.
Assigning someone a manual task you had a tool for is a real cost, not a rounding error.
When a permission or safety block genuinely prevents the programmatic path, **say that
explicitly, with the fix**, rather than quietly inventing a manual workaround.
[check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
