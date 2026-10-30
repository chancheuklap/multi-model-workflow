### To tickets

**You own the breakdown, approved by the user before anything is published.**

Break a plan, spec, or conversation into a set of **tickets**: tracer-bullet vertical slices, each declaring the tickets that **block** it, published as GitHub issues. Each ticket is read by agents who were not in this conversation and cannot ask it anything: a worker at night, a reviewer in another session. This session is the last one that holds the spec, the codebase and the user at once, so settle here what can be settled: a choice left open is made at night by a worker who cannot ask. The shared format and criterion rules are in `references/ticket-format.md`; read them before drafting.

1. **Gather context.** Work from whatever is already in the conversation context. If the user passes a reference (a spec path, an issue number or URL), fetch it and read its full body and comments. A batch requires a published spec. Return a missing spec to the caller, which can use the **to-spec** skill; use the independent entry when the requested result is one ticket outside a spec. Done when you hold the spec's issue number and have read its full body and comments.
2. **Explore the codebase**, if you have not already. Ticket titles and descriptions use the project's domain glossary vocabulary and respect ADRs in the area you're touching. Look for opportunities to prefactor the code to make the implementation easier: "Make the change easy, then make the easy change." Done when you know the module or directory each ticket will write to.
3. **Draft vertical slices**, per **Vertical slices** below. Done when the work is drafted as slices, each one vertical or one step of an expand–contract sequence.
4. **Write each acceptance criterion**, per **Acceptance criteria** in `references/ticket-format.md`. For each UI ticket, put the winner's exact path and affected feature files under **Read first** as baselines. For UI work, finalize the interface contract and update the API fake to match it before writing tests. Done when every criterion on every ticket carries a number, a `CHECK:` and an `EXPECT:`, each `CHECK:` aimed at behaviour its ticket adds has its base-command result checked by draft lint in step 6, with behavioral-red proof left to the test-audit writing method, each UI acceptance test has passed against `design` and failed against `product`, its tests and feature files are committed and pushed to the night's branch before `dispatch.sh open`, and everything that stopped at question 2, 3, 4 or 5 has landed where that question sends it.
5. **Give each ticket its blocking edges**, per **Blocking edges** below. Done when every path marked `(new)` has the files that put it in service under the same ticket's **Owns**.
6. **Write and lint the drafts.** Write each ticket in the shape of `references/ticket-format.md` as one draft in a directory `mktemp -d` makes, as the `verify-ticket` skill's `references/linting.md` describes a draft. Each carries `mmw:ticket`, and, for a ticket an agent works, `ready-for-agent` beside the `junior-worker` or `senior-worker` label you propose for it; a ticket a person must judge carries `ready-for-human` instead, and no worker label. Run `verify-ticket.py <spec> --lint --drafts <dir>` and fix every `ERROR` in the drafts. Done when the lint prints no `ERROR` and every `WARN` has been read once and either fixed or kept on purpose. Each ticket is written for a worker who reads only it and what it names (**principle-write-for-where-it-is-read**).
7. **Quiz the user** on the linted drafts, per **The quiz** below, after the ambiguity scan it opens with. Iterate until the user approves the drafts. After every change to a draft, run the lint of step 6 again and fix every `ERROR`. Done when the user has approved the drafts as the last lint left them, every answered choice is written into a draft's **What to build** or the spec, and step 5's Done when still holds for the approved drafts.
8. **Publish the batch** as the user approved it with `verify-ticket.py <spec> --publish --drafts <dir>`, which creates each draft as a sub-issue of the spec in dependency order with its labels and blocking edges, and ends by linting the published spec. Close no parent issue. Done when `--publish` has run and every approved ticket is a sub-issue of the spec.
9. **Read every ticket back**, per **Read-back** below. Done when every check there passes.

#### Vertical slices

Break the work into **tracer bullet** tickets.

<vertical-slice-rules>

- Every ticket runs from one action of the product's user to a result that user sees, through every layer it needs. The user uses the shipped product from outside it, either an end user or, in a tooling repository, the agent or owner who runs the tool. Another layer or service of the same product never counts as the user. No reason to split outweighs this rule.
- A completed slice is demoable or verifiable on its own
- Any prefactoring should be done first

</vertical-slice-rules>

Horizontal slices fail for five reasons:

- Nothing is usable until the last ticket lands.
- Mismatches between layers appear late, when those layers finally connect.
- A night stopped halfway leaves half-built layers rather than complete deliverable features.
- A horizontal ticket's acceptance checks prove that one layer works, not that the user can use the product.
- Splitting by layer does not buy parallel work when each layer still waits for the previous one, and only adds hand-offs.

For UI work, each slice combines its part of the prototype front end with the interfaces, back end, database and tests it needs. The first slice owns any shared page skeleton; the others are blocked by it. The final ticket only removes mount points and is blocked by every slice. It is the contract step of the prototype's integration, an exception to vertical slicing. With only one ticket, remove the mount points in its last commit.

Split a vertical ticket into narrower vertical tickets where they can run at the same time, or where one ticket's criteria can fail without the other's. Every resulting ticket still completes a user action and its visible result. Write a release order such as "the gateway ships first" inside the vertical ticket's **What to build**, never as a ticket of its own.

**Wide refactors are the other exception to vertical slicing.** A **wide refactor** is one mechanical change (rename a column, retype a shared symbol) whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify ticket; green is promised only there.

Each expand–contract step and the final mount-point removal ticket opens **What to build** with one sentence naming its sequence and its step, either expand, migrate, contract, or mount-point removal, instead of a user action and visible result.

#### Blocking edges

A ticket's **blocking edges** are the other tickets that must complete before it can start. The edges are the night's schedule: every ticket whose blockers have landed may start at once, as many as `max_workers` leaves room for, so a missing edge sends a worker onto work not built yet, and an edge that gates nothing makes the night wait for no reason.

**What a ticket creates is put in service by an edit to something it did not create**: the registry, router, parent template, index, story adapter or stylesheet that has to name it. Until one does, no criterion of that ticket can see it; and when several tickets that can run at the same time each make that edit, all but the first to land bounce on a merge conflict. For each path a ticket marks `(new)`, `grep` the nearest existing file of its kind twice, once for its file name and once for the one identifier it declares for others (its root class, exported symbol or route path), and put every file that answers under this ticket's **Owns**, whoever created it. Where that sibling is still to be built in this batch, its ticket's **Owns** is the same list.

A blocking edge means only that one ticket needs what another ticket builds. **Owns** describes the expected scope of edits, not a lock on files. Parallel tickets may write the same file. Resolve conflicts during `integrate` and landing.

#### The quiz

Have the spec and the drafts scanned for ambiguities before you list the breakdown: the scan's questions belong in each ticket's **Choices** when the user first sees it. When the host can run subagents, start your host's general-purpose subagent, on the `default` row and restricted to reading and searching where the host allows it, with:

```
Read the mmw-mode skill in full, then read the to-tickets skill's `references/ambiguity-scan.md` and scan spec #<spec> and the drafts in <dir> for ambiguities. It is your whole task: what came before it is done, and you start no agent it does not name.
```

Hold this turn until it returns; where the host runs subagents in the background, ask for it to be waited on. When the host cannot run subagents, run the scan yourself from `references/ambiguity-scan.md`, and write its result to a file before you list the breakdown.

Present the proposed breakdown as a numbered list. For each ticket an agent works, show:

- **Title**: short descriptive name
- **Customer action**: the opening sentence of **What to build**, naming the one action the product's user takes and what they see, or the sequence and step for an exception named in **Vertical slices**. A ticket that can state neither is a horizontal slice and goes back to step 3.
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work
- **Worker**: `junior-worker` or `senior-worker`, and the one-line reason. `junior-worker` is the default, and a ticket goes to `senior-worker` when getting it wrong is wrong **silently** (money that has to reach a terminal state, recovery after a crash, a contract an installed base already reads, a security default), because none of those fail on the day they are written. A ticket whose **Seam** already names a precedent to copy stays on `junior-worker`.
- **Choices**: every choice question 5 sent here, and every question the ambiguity scan returned, one line each: the options, and the one you would take. Omit the line when there are none.

Then the `ready-for-human` tickets, in the same list, each with its **Title**, **Blocked by**, its kind (*reaction* or *reach*) and what is to be looked at.

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct: does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?
- Is each worker grade right for what going wrong on that ticket would cost?
- For each choice listed: which option?

Write each answered choice that only changes what one ticket delivers into that draft's **What to build**. Write each answered choice that changes a decision in a spec section back through the **to-spec** skill's revise entry, then into the drafts.

#### Read-back

For each published ticket an agent works, check that **What to build** opens with the sentence naming the one action the product's user takes and what they see once the ticket is done, or the sequence and step for an exception named in **Vertical slices**. Check `ready-for-human` tickets against the five things in `references/person-ticket.md`, not this opening sentence.

Read the lint `--publish` ran on the published spec as the `verify-ticket` skill's `references/linting.md` says: no `ERROR`, and every `WARN` read once and either fixed or kept on purpose. The drafts runs of steps 6 and 7 do not stand in for it: only this run sees the tracker's labels, sub-issues and blocking edges. Fix each `ERROR` on its ticket and run `verify-ticket.py <spec> --lint` again. Then fetch each `ready-for-human` ticket again and check it holds all of **the five things** in `references/person-ticket.md`, because no agent can repair one. Checking sub-issues, labels and blockers by hand again found nothing across 158 published tickets; the publish command and this lint hold them.

**Reply:** each ticket by name with its link, its blocking edges and its worker grade, in dependency order; the `ready-for-human` tickets with their kind; each choice the user answered, with where it was written; for each UI ticket, the two result lines showing its acceptance e2e test passed against `design` and failed against `product`; and that the batch runs when the user tells a session to start the night on this spec (Run a night, `playbooks/run-a-night.md`).
