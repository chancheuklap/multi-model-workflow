---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
---

Implement the work described by the user in the spec or tickets.

Before writing any code, check the ticket is the one to work: its title and **What to build** describe the same slice, and it is on the **frontier** — every ticket under **Blocked by** is closed. If either fails, stop and report.

Then read yourself in: the ticket in full, comments included; then every item under its **Read first**, each through to its conclusion — the last section of a research file, the chosen artifact of a prototype, the Decision of an ADR; then follow **Parent** to the spec and read that in full, with the Implementation Decisions sections the ticket names, the Testing Decisions and the Out of Scope as the parts you must be able to restate; then the domain glossary if the repo has one. A ticket without **Read first** is an older one: fall back to every item under the spec's **Sources**.

Then say in one sentence which **seam** this ticket is tested at — copied from the ticket's **Seam**. If the ticket has no **Seam**, derive it from the spec's Testing Decisions and post it as a comment on the ticket before you start, so the ticket is complete for the next reader.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work.

Commit your work to the current branch. Then close the loop on the tracker, or the tickets this one blocks never unlock:

1. Comment on the ticket with the branch, the commit, and the evidence for each acceptance criterion — the command run and what it printed — and tick the criteria that passed.
2. Push the branch and open a pull request that references the ticket.
3. Close the ticket. A ticket with an unmet criterion stays open, with the comment saying which one and why.
