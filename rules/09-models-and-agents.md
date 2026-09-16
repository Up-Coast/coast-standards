# Working with models and agents in a codebase

These rules apply to every project where AI agents write, review or plan code. They are engineering rules, not conversation rules. They cover spending, correctness, and the integrity of the git history.

## Model effort is set deliberately, and frugally

Never use the provider's default effort setting. Provider defaults are tuned to show what the model can do, not to spend someone else's money carefully. Be frugal with the customer's money. A mid-tier model may default to high effort. A frontier model should default to medium effort; its provider default is high, which only complex work needs.

- **Use the lowest effort that reliably clears the job's quality bar.** A more capable model needs less effort: a frontier model defaults one level *lower* than a mid-tier model on the same job, because it needs less reasoning to reach the same answer. [check: process]
- **Set it per role, not globally.** Reviews and second opinions lean higher, because a missed defect costs more than the tokens. Small, bounded jobs (classification, extraction, a yes/no check) always run at minimum effort. [check: process]
- **Tune from recorded real spend, never from paid calibration runs.** Running paid experiments to find the right setting spends the money the setting was meant to save. [check: process]

## Know which model is running before you start

- **Read the actual model identity before beginning a task that was assigned to a specific model.** If it is not the assigned model, stop and say so *before* building. Cleaning up work done by the wrong model costs more than not starting, and is never as good as building it right the first time. [check: process]
- **Commit trailers name the model that actually did the work.** A wrong attribution makes the history useless for tracing which model caused a problem. This is a git-integrity rule, not a courtesy. [check: session:attribution-trailer]

## Don't dictate diffs into code you don't own

When your work needs a change in code that someone else owns (another agent, another team, or another module's maintainer), **send the task and the goal, not the diff.** Say what you are trying to achieve and why. Let the owner decide whether to extend an existing function, add a new one, or tell you the existing API already does it.

Why: an owner handed a specific edit, especially an agent eager to help, tends to just apply it. The codebase then collects changes that nobody checked against the surrounding code. The owner must do what is best for its own part of the codebase: keep it readable, clear, simple and DRY, and follow best practices.
[check: process]

## Check what you already have before adding manual steps

Before asking a person to do something by hand, check these in order: your installed skills, the project's tooling reference, the memory directory, and the connected servers. Giving someone a manual task that you had a tool for has a real cost. If a permission or safety block really prevents the automated path, **say so clearly, and say how to fix it**. Do not quietly invent a manual workaround.
[check: process]

---

[← All rules](README.md) · [Priority rules](00-priority-rules.md) · [Project types](PROJECT-TYPES.md) · [Documentation](../docs/README.md)
