# Working with models and agents in a codebase

Read this when a task picks a model or effort level, or needs a change in code it does not own.

## Model effort is set deliberately, and frugally

Never use the provider's default effort. A frontier model defaults to medium; a mid-tier model may default to high.

- **Use the lowest effort that reliably clears the job's quality bar.** [check: process]
- **Set it per role, not globally.** Reviews and second opinions lean higher; classification, extraction and yes/no checks run at minimum. [check: process]
- **Tune from recorded real spend, never from paid calibration runs.** [check: process]

## Know which model is running before you start

- **Read the actual model identity before beginning a task that was assigned to a specific model.** If it differs, stop and say so before building. [check: process]

## Don't dictate diffs into code you don't own

Send the owner of that code (agent, team or maintainer) the task and the goal, never the diff, and let it decide how. [check: process]

## Check what you already have before adding manual steps

Before asking a person to do something by hand, check skills, the tooling reference, memory and connected servers. If a block prevents automation, say so and how to fix it; never invent a manual workaround. [check: process]

---

[← All rules](README.md) · [Documentation](../docs/README.md)
