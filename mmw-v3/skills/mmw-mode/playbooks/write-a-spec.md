### Write a spec

**You own one spec: what the owner and the sources already settled, written down and published on the tracker, then cut into its batch through Cut tickets.** Do not interview the owner for facts; synthesize what the conversation, the reference and the code already hold. A spec is the last text a person checks before agents build from it unattended: whatever it leaves open, a worker decides alone at night, and whatever it states is built as written, including what nobody decided. So record decisions rather than make them. An engineering call the sources leave open (a module boundary, a data shape, the seam) is yours: make it and mark it "this spec's decision". A call on what the customer sees, what happens to money, or what is in scope that no source settles is the owner's: put it to them before you publish. That, and a division into several specs, are the only things you ask them. Distinct from Revise a spec, which changes a spec already on the tracker, and from Make a small change, which needs no spec.

The repository's `docs/agents/issue-tracker.md` and `docs/agents/triage-labels.md` say how its tracker is reached and what its labels are called. If either is missing, tell the owner the repository is not set up for the pipeline, and stop.

1. **Read every source.** If the owner passed a reference (an issue number, a URL, a file path), read its full body and comments first; a triaged issue's agent brief comment is one of the sources. Follow every decision ticket, prototype or research file it links through to its conclusion. When the reference is a published spec and one of its sections has to change, run **Revise a spec** instead of this playbook.
   Then judge whether what you have read is one spec or several. Decisions that share a **seam** belong in one spec. Split only where a part needs a different seam and lands and demos on its own; where it can stay one spec, keep it one spec. A part may depend on a part before it (a server registration, then the client that logs into it, then the work the client does), but no dependency runs backwards or in a circle. Several: put the division to the owner (each spec's name, the decisions it covers, the order, and why the line falls there), and once they confirm, write it into the first spec's `## Further Notes`, one line per spec with its name, what it covers, its position in the order, and its link once published. This run writes and cuts the first spec only; the next is written by a later run with this spec as its reference. When the reference is a spec whose `## Further Notes` carries a division, write the first spec on it that has no link yet, and fill the link into its line through **Revise a spec**; when every line has a link, tell the owner the division is fully written and stop.
   Done when every source the reference leads to has been read and you know which one spec this run writes.
2. **Read the code, the glossary and the ADRs.** Explore the repository for the current state of what the spec touches. Use the project's domain glossary vocabulary (`CONTEXT.md`, or `CONTEXT-MAP.md` and the contexts it names) throughout the spec, and respect the ADRs in the area (**principle-start-from-what-exists**).
   Done when you know which existing modules and ADRs each decision touches, or that none exists yet.
3. **Choose the seam.** Sketch the seams at which the feature is tested. Prefer an existing seam to a new one, and the highest seam possible; the fewer seams across the codebase, the better, and the ideal number is one. The `## Tests` section of the repository's `CODING_STANDARDS.md` says which test layers exist, which external boundaries may be stubbed and how tests run; the seam and the spec's `## Testing Decisions` draw on it. A seam says where a test **observes**; ask the other half in the same breath: for each state the feature's behaviour turns on, can a test put the system into that state through this seam? Where it does not reach, say what would, and whether that thing ships. The seam is yours to decide, not the owner's; what they see of it is the plain-words opening sentence of `## Testing Decisions`.
   Done when every state the feature's behaviour turns on has a seam where a test observes it, and either a way a test puts the system into it through that seam or a named mechanism that would.
4. **Write the spec and publish it.** Write it in the shape of **The spec template** below, to a file. Put every call on what the customer sees, on money or on scope that no source settles to the owner, with the options and the one you would take, and write each answer into its subsection as a decision the owner confirmed. Then publish it with the `verify-ticket` skill's `verify-ticket.py --publish --spec-body <file> --title <the spec's title>`, which prints the new issue's number. The issue carries the label `mmw:spec` and no triage label: a spec is a container for the tickets under it, not a piece of work, and a triage label would put it in a queue somebody has to sort back out.
   Done when `--publish` exits 0 and you hold the spec's number.
5. **Cut its tickets.** Run **Cut tickets** on the published spec.
   Done when Cut tickets' last step is done.

**The spec template.** Step 4 writes the spec in this shape.

```markdown
## Problem Statement

The problem the customer is facing, from their perspective.

## Solution

The solution to the problem, from the customer's perspective.

## User Stories

A long, numbered list of user stories, covering every aspect of the feature, each in the form:

1. As an <actor>, I want a <feature>, so that <benefit>

## Implementation Decisions

The implementation decisions that were made, grouped into numbered subsections (`### 1. …`, `### 2. …`) that tickets point at by number. A subsection can cover the modules built or changed and their interfaces, architectural decisions, schema changes, API contracts, and specific interactions. Each subsection is read on its own: a worker opens only the subsections its ticket names, so a subsection that depends on another names it.

Every decision names where it came from, at the end of the sentence or table row that states it: a decision ticket number, an ADR id, a research or prototype path. A decision with no source is written as "this spec's decision", citing what it rests on, and says so where the owner confirmed it. A rule of the repository's `CODING_STANDARDS.md` that shapes a decision is stated in the subsection it shapes, citing its section: the worker reads the spec, not that file.

A user story's conclusion is folded into the subsection that implements it, with the story number as its source: a worker reads the subsections its ticket names and never a story.

No implementation file paths (the module you will edit, the function you will add) and no code snippets: they go stale fast. Paths to source material (ADRs, research files, prototype directories, domain docs, test directories) are what the tickets read from: write them. Exception: a prototype snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), trimmed to its decision-rich parts and marked as coming from a prototype.

## Testing Decisions

The first sentence says, in plain words a reader with no testing vocabulary understands, where a test looks at the result ("Tests look at the result on the browser page."). The next names the seam: what is real on each side of it, and which external boundaries (third-party APIs, paid services) may be stubbed. Then:

- What makes a good test here: external behaviour, not implementation details.
- The test layers this feature lands in, each with its directory and the precedent to copy; every ticket cut from this spec names one of them as the place it is verified.
- **How a test arrives at a state.** Per test layer: what a test writes to put the system into a state, and what it cannot write. A state the feature's behaviour turns on that a test cannot write through the seam gets a line of its own: the mechanism that will reach it, and which builds carry it. The mechanism takes the form the `## Tests` section of `CODING_STANDARDS.md` allows; where that section has no exit for one, say so, and Cut tickets cuts a *reach* ticket for it. One ticket will own building each mechanism named here.
- The commands to run before committing.

## Out of Scope

What this spec does not cover.

## Sources

The first-hand material this spec was built from, one line per kind; "none" for a kind that has none, so a reader can tell "nothing there" from "forgot to list":

- Originating issue (the triaged issue and its agent brief comment)
- Decision tickets (each named by the decision it settled)
- Upstream specs this one builds on
- ADRs
- Research files
- Prototype directories
- Domain docs
- Evidence (measurements, cost runs, real-call records)
- Repository rules: the sections of `CODING_STANDARDS.md` this spec relies on, `## Tests` among them

## Further Notes

Anything else about the feature. When step 1 divided the work into several specs, the division lives here in the first spec; a later spec of the division says here which spec carries it.
```

**Reply:** the spec's number and title, each decision marked "this spec's decision" that the owner may want to overturn, and the owner's answers it records; when the work was divided, which spec of the division this was and which comes next; then Cut tickets' reply.
