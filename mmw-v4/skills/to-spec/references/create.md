### To spec

**You own the spec, not the decisions in it.** Do NOT interview the user for facts; just synthesize what you already know.

Takes the current conversation context and codebase understanding, or a reference the user passes, and produces a spec, published as a GitHub issue. A spec is the last text a person checks before agents build from it unattended: whatever it leaves open, a worker decides alone at night, and whatever it states is built as written, including what nobody decided. So record decisions rather than make them. An engineering call the sources leave open (a module's seam, a data shape, the seam a test observes at) is yours: make it and mark it "this spec's decision". Apply **principle-never-block-on-the-human** to the decisions the sources leave open; put an unresolved owner decision to the user before publishing. That, and the division in step 1, are the only things you ask them. The template is below. Read a supplied issue with its full body and comments.

1. **Read the sources**, per **Reading the sources** below, and judge whether they make one spec or several. When the several-specs entry already selected one part of a confirmed division, keep that selection rather than reentering division. Done when every source the reference leads to has been read and you know which one spec this run writes.
2. **Explore the repo** to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching. Reuse the prepared affected-feature result, or find it with the **maintain-verification-skill** skill's **Find affected features** entry when missing, and put that list in Implementation Decisions. For a new UI design, name the winner's exact path as its baseline. A settled UI repair or behavior-preserving change names its requirement, reproduction or current-behavior source, with no invented winner. When a UI design has an API fake, use it as the draft interface contract and finalize it through **grilling**. Record relevant formal check results or agreed rules and still-unbuilt checks in Testing Decisions; spec writing itself does not invoke a generator. Testing Decisions covers only the repository's own tests, not e2e tests. Done when you know which existing modules and ADRs each decision touches, or that none exists yet, and each affected existing feature has its behaviour decision and each UI subsection its actual baseline and any required final interface contract.
3. **Sketch out the seams** at which you're going to test the feature, per **Seams** below. Done when every state this feature's behaviour turns on has a seam where a test observes it, and either a way a test puts the system into it through that seam or a named mechanism that would.
4. **Check that nothing load-bearing is undecided.** First run the **sharpen** skill on the work the spec will describe. Treat the winner and recorded decisions as settled sources, not questions to ask the owner again. For a new UI design, the outside check is the same tests passing on both `design` and `product`, plus Spec's screenshot comparison. A settled repair or behavior-preserving change uses its real-product proof. Propose other outside checks only for questions the prototype cannot answer, listed in Design a UI (`mmw-mode/playbooks/design-a-ui.md`) **Iterate with the owner**. Keep conclusions that preserve the recorded decisions as source-backed checks, without asking for those decisions again. Bring only a concrete unresolved owner decision to the user, with its reason, in one batch. A new outside check changes Testing Decisions only when the owner agrees to that new requirement; existing agreed checks remain the baseline. The caller receives any missing prerequisite rather than a fabricated answer. A code shape the spec rests on that meets the conditions of the **prototype** skill's sketch branch has not been settled, and a spec that states it records a decision nobody made: stop instead of writing the spec around it, and take it back to where it came from. From Grill with docs, settle it there; from a map, add a `prototype` ticket for it to the map with the **wayfinder** skill's resolve entry, and return that missing prerequisite to the caller. An unresolved owner decision goes to the user now. Done when every load-bearing decision has a recorded source, is an engineering call marked "this spec's decision", or has the owner's answer; a settled decision needs no new response.
5. **Write the spec** using **The template** below, then draw it for the owner as one page with the **diagram-design** skill: each flow a user goes through once it is built, what they do and see at each step and where it branches, named as the spec names them. Use the feature map's feature names in the diagram. Done when every section of the template is filled, and every decision names where it came from. Write it for agents who were not in this conversation (**principle-write-for-where-it-is-read**), and copy every settled answer and chosen artifact into it (**principle-baseline-is-the-contract**).
6. **Publish it**: write the spec to a file and run `verify-ticket.py --publish --spec-body <file> --title "<title>"` of the `verify-ticket` skill, adding `--map <map>` when the reference is a wayfinder map; for any other reference, give it no parent. It gives the spec the `mmw:spec` label and no queue label: a spec is a container for the tickets underneath it, not a piece of work, and a queue label would put it in a queue somebody has to sort back out. Done when the command exits 0 and prints the spec's number.
7. **Return the published spec.** Return its issue number, page, decision sources and any remaining spec-division continuation to the caller. Ticket decomposition belongs to that caller's requested scope. Done when the caller has this spec and its next permitted continuation.

#### Reading the sources

If the user passed a reference (an issue number, a URL, a file path), read its full body and comments before anything else. When the reference is a published spec and one of its sections has to change, use this skill's revision entry (`references/revise.md`) instead of these steps. When the reference is a wayfinder **map**: read the map body; then walk **Decisions so far** and read each closed ticket's **resolution comment**; where a ticket links a prototype or a research file, read that through to its conclusion. The map's **Out of scope** carries into the spec's Out of Scope unchanged.

Then judge whether what you have read is one spec or several. Decisions that share a **seam** belong in one spec. Split only where a part needs a different **seam** and lands and demos on its own; where it can stay one spec, keep it one spec. A part may depend on a part before it: a product delivered in stages (a server registration, then the client that logs into it, then the work the client does) has no reading under which the later stages depend on nothing, and forcing it into one spec produces one nobody can read. What the dependencies may not do is run backwards or in a circle: every one points at a part earlier in the order, and the `## Specs` section writes that order down.

One spec: write it. Several, or a reference that already carries a **spec division** (a map's `## Specs` section, or a spec whose `## Further Notes` lists several specs): follow `references/several-specs.md`.

#### Seams

Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better. The ideal number is one.

A seam says where a test **observes**. Ask the other half in the same breath: for each state this feature's behaviour turns on, can a test put the system into that state through the seam you picked? Where the seam does not reach, say what would, and whether that thing ships.

The seam is yours to decide, not the user's: they are not asked to confirm it. What they see of it is the plain-words opening sentence of Testing Decisions, which says where a test looks at the result.

**Reply:** the spec by name with its link, and where its page is; each "this spec's decision" and each answer the user gave; and, when the work divides, the division and which spec this run wrote.


## The template


Replace each section's guidance with the content.

<spec-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

The implementation decisions that were made, grouped into numbered subsections (`### 1. …`, `### 2. …`) that tickets point at by number. Each subsection can cover:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Each subsection states a complete decision baseline for the tickets naming it. A dependency on another subsection names that source explicitly. These citations define which decisions govern the ticket, not a separate file-loading boundary.

**Every decision names where it came from**, at the end of the sentence or table row that states it: a decision ticket number, an ADR id, the link of a research answer or verdict comment, or a prototype path. A decision with no source is written as "this spec's decision", citing what it rests on (and, where the user confirmed it, say so). What an ADR decides that shapes a decision is written into the subsection it shapes, citing the ADR: the worker reads the spec, not the ADR.

**A user story's conclusion is folded into the subsection that implements it.** A worker reads the Implementation Decisions subsections its ticket names and never a story, so a behaviour that is settled only in a story reaches nobody. Whatever a story decides about a value, a transition or a failure is stated here, in the subsection that implements it, with the story number as its source.

Do NOT include implementation file paths (the module you will edit, the function you will add) or code snippets. They may end up being outdated very quickly. Paths and links to source material (ADRs, research answer comments, prototype directories, domain docs, test directories, shared contract locations) are what the tickets and the implementer read from: write them.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

## Testing Decisions

Name the executor verification methods and their baseline sources for any required product observation outside the acceptance commands. A skill-set behavior change names the **mmw-mode** skill's `references/prove-skill-change.md` before owner acceptance. These requirements use this existing section, not an extra phase or issue field.

The first sentence says, in plain words a reader with no testing vocabulary understands, where a test looks at the result: a browser page, an HTTP endpoint, or a function call ("Tests look at the result on the browser page."). The next sentence names the **seam** chosen in step 3: what is real on each side of it, and which external seams (third-party APIs, paid services) may be stubbed. Then:

- A description of what makes a good test (only test external behavior, not implementation details)
- The test layers this feature lands in, each with its directory and the precedent to copy (i.e. similar types of tests in the codebase); every ticket cut from this spec will name one of these layers as the place it is verified
- **How a test arrives at a state.** Per test layer: what a test writes to put the system into a state, and what it cannot write. A state this feature's behaviour turns on, that a test cannot write through the seam, gets a line of its own here: the mechanism that will reach it, and which builds carry that mechanism. Where the repository's tests have no way to reach such a state, say so: closing that is the repository's to do, not this spec's, and To tickets cuts a *reach* ticket for it. Whoever cuts the tickets reads this section to know whether a criterion can be written at all, and one of them will own building each mechanism named here.

## Out of Scope

A description of the things that are out of scope for this spec.

## Sources

Links to the first-hand material this spec was built from, one line per kind. Write "none" for a kind that has none, so a reader can tell "nothing there" from "forgot to list":

- Wayfinder map
- Decision tickets (each named by the decision it settled)
- Upstream specs this one builds on, including an earlier spec the decision tickets cite as their basis
- ADRs
- Research answers (the ticket comments that hold them)
- Prototype directories
- Domain docs
- Evidence (measurements, cost runs, real-call records)

## Further Notes

Any further notes about the feature. When step 1 divided the work into several specs and the reference was not a map, the division lives here in the first spec: one line per spec, with its name, what it covers, its position in the order, and its link once published. A later spec in that division says here which spec carries it.

</spec-template>
