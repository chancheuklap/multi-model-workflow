# Work only a person can do

Reached from step 4 of [`SKILL.md`](../SKILL.md) when a criterion stops at question 3 (a person's reaction) or question 4 (out of reach), and from the `triage` skill when an issue is judged `ready-for-human`.

**Work only a person can do is its own ticket, not a criterion on someone else's**, and you split it off here, while writing the ticket, not when closing it. A criterion no agent can decide leaves its ticket unable to finish; so the ticket that produces the thing stays an agent's, and the looking becomes a second ticket blocked by it.

Write one such ticket per thing to be looked at, labelled `ready-for-human`. It is shorter than the template below and holds **the five things** only:

- **Parent**.
- **Which kind**: *reaction* or *reach*, in one word. A *reach* ticket adds one line naming what would retire it — a test account, a spare device, a runner, a mechanism under **How a test arrives at a state** that nobody owns yet, or a testability rule of the consuming repository that gives a test no exit. This is the only exit in the pipeline that owes no account to a machine, so it attracts whatever the writer did not want to think about; being unable to name the kind is the sign that the thing belongs at question 1, 2 or 5 instead.
- **What to look at**: a link that opens, not a command to run. This is read in the morning, on a phone, by someone carrying none of your context.
- **What makes it right**: the standard to judge against, so the answer can be something other than "I couldn't say".
- **Blocked by**: the ticket that produces the thing. This is the edge that matters most in the batch — wrong, and the person is sent to look at something that does not exist yet.

