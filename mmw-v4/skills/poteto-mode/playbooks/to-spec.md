### To spec

**You own the spec, not the decisions in it.** Do NOT interview the user for facts; just synthesize what you already know.

Takes the current conversation context and codebase understanding, or a reference the user passes, and produces a spec, published as a GitHub issue. The template is `../references/spec.md`; the `gh` commands are in `../references/github-issues.md`.

A spec is the last text a person checks before agents build from it unattended: whatever it leaves open, a worker decides alone at night, and whatever it states is built as written, including what nobody decided. So record decisions rather than make them. An engineering call the sources leave open (a module's seam, a data shape, the seam a test observes at) is yours: make it and mark it "this spec's decision". A call on what the user sees, what happens to money, or what is in scope that no source settles is not yours: put it to the user before you publish. That, and the division in step 1, are the only things you ask them.

1. **Read the sources.** If the user passed a reference (an issue number, a URL, a file path), read its full body and comments before anything else. When the reference is a published spec and one of its sections has to change, run the Revising a spec playbook (`playbooks/revising-a-spec.md`) instead of the steps below. When the reference is a wayfinder **map**: read the map body; then walk **Decisions so far** and read each closed ticket's **resolution comment**; where a ticket links a prototype or a research file, read that through to its conclusion. The map's **Out of scope** carries into the spec's Out of Scope unchanged.

   Then judge whether what you have read is one spec or several. Decisions that share a **seam** belong in one spec. Split only where a part needs a different **seam** and lands and demos on its own; where it can stay one spec, keep it one spec. A part may depend on a part before it: a product delivered in stages (a server registration, then the client that logs into it, then the work the client does) has no reading under which the later stages depend on nothing, and forcing it into one spec produces one nobody can read. What the dependencies may not do is run backwards or in a circle: every one points at a part earlier in the order, and the `## Specs` section writes that order down.

   One spec: write it. Several, or a reference that already carries a **spec division** (a map's `## Specs` section, or a spec whose `## Further Notes` lists several specs): follow **Several specs from one reference** in `../references/spec.md`.

   Done when every source the reference leads to has been read and you know which one spec this run writes.
2. **Explore the repo** to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching. Done when you know which existing modules and ADRs each decision touches, or that none exists yet.
3. **Sketch out the seams** at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better. The ideal number is one. The repository's `TESTING.md` says which test layers exist, which external seams may be stubbed and how tests run; the seam and `## Testing Decisions` draw on it.

   A seam says where a test **observes**. Ask the other half in the same breath: for each state this feature's behaviour turns on, can a test put the system into that state through the seam you picked? Where the seam does not reach, say what would, and whether that thing ships.

   The seam is yours to decide, not the user's: they are not asked to confirm it. What they see of it is the plain-words opening sentence of Testing Decisions, which says where a test looks at the result.

   Done when every state this feature's behaviour turns on has a seam where a test observes it, and either a way a test puts the system into it through that seam or a named mechanism that would.
4. **Check that nothing load-bearing is undecided.** A code shape the spec rests on that meets the conditions of the **prototype** skill's sketch branch has not been settled, and a spec that states it records a decision nobody made: stop and take it back to the discussion it came from (Grill with docs, or the map) instead of writing the spec around it. A call on what the user sees, money, or scope that no source settles goes to the user now. Done when every decision the spec will state has a source, is an engineering call marked "this spec's decision", or the user has answered it.
5. **Write the spec** using `../references/spec.md`. Done when every section of the template is filled, and every decision names where it came from.
6. **Publish it** as a GitHub issue with the `mmw:spec` label and no queue label: a spec is a container for the tickets underneath it, not a piece of work, and a queue label would put it in a queue somebody has to sort back out. When the reference is a wayfinder map, publish the spec as a sub-issue of the map and confirm the link; for any other reference, give it no parent. Done when the spec is published with `mmw:spec`, and, from a map, the map's sub-issues include it.
7. **Cut the tickets.** Run the To tickets playbook (`playbooks/to-tickets.md`) on the published spec, in this same session. Done when To tickets has started on this spec's issue number.

**Reply:** the spec by name with its link; each "this spec's decision" and each answer the user gave; and, when the work divides, the division and which spec this run wrote.
