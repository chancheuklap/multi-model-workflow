### Improve codebase architecture

**You own the deepening opportunities and the recommendation.** Surface architectural friction and propose **deepening opportunities**: refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

1. **Explore.** Use [codebase-dic](../../codebase-dic/SKILL.md) for the architecture vocabulary (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) and its principles. Read the project's glossary and any ADRs in the area you're touching first. Follow the project's glossary map when it has one. The domain vocabulary gives names to good seams. ADRs record decisions this investigation should not re-litigate.

   **Scope before you scan: YAGNI.** Deepening a module pays off by making future changes to it easier, so put extra weight on the parts of the codebase that have recently changed. Decide *where* to look before you look:

   - If the user named a direction (a module, a subsystem, a pain point), take it, and skip the inference below.
   - Otherwise, walk back a good stretch of the commit history (`git log --oneline`) to find the codebase's hot spots, the files and areas that keep coming up, and let those paths pull your attention first. If the changes are scattered with no clear hot spot, widen the net.

   Give a fresh [poteto-agent](../../../agents/poteto-agent.md) the read-only exploration, the work issue URL, the absolute path to [poteto-mode](../SKILL.md) and the scope. Use the `judgment and prose` role from the [setup-pstack](../../setup-pstack/SKILL.md#model-rule) model rule. Include the relevant glossary, ADRs and [codebase-dic](../../codebase-dic/SKILL.md) in the brief. Ask for real call sites and file paths that show the friction. Include the following questions and the deletion test in the exploration prompt.

   Don't follow rigid heuristics; explore organically and note where you experience friction:

   - Where does understanding one concept require bouncing between many small modules?
   - Where are modules **shallow**, with an interface nearly as complex as the implementation?
   - Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
   - Where do tightly-coupled modules leak across their seams?
   - Which parts of the codebase are untested, or hard to test through their current interface?

   Apply the **deletion test** to anything you suspect is shallow. Imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep. Check the returned findings against the cited code.

2. **Present the deepening opportunities as an HTML report.** Write a self-contained HTML file to the OS temp directory so nothing lands in the repo. Resolve the temp dir from `$TMPDIR`, falling back to `/tmp` (or `%TEMP%` on Windows), and write to `<tmpdir>/architecture-review-<timestamp>.html` so each run gets a fresh file. Show the report to the user and link its HTML file.

   Use [big-pics-little-words](../../big-pics-little-words/SKILL.md) with [html](../../html/SKILL.md). Each opportunity gets a **before/after visualisation**. Use the [HTML report format](../references/improve-codebase-architecture/html-report.md) for the scaffold, diagram patterns, and styling guidance. For dependency categories, consult [Deepening](../../codebase-dic/references/deepening.md).

   For each opportunity, render a card with:

   - **Files**: which files/modules are involved
   - **Problem**: why the current architecture is causing friction
   - **Solution**: plain English description of what would change
   - **Benefits**: explained in terms of locality and leverage, and how tests would improve
   - **Before / After diagram**: side-by-side, custom-drawn, illustrating the shallowness and the deepening
   - **Recommendation strength**: one of `Strong`, `Worth exploring`, `Speculative`, rendered as a badge

   Mark the opportunity you'd tackle first with a `Recommended first` badge on its card, with the reason beside the badge.

   Use the project's domain vocabulary for the domain and the architecture vocabulary from [codebase-dic](../../codebase-dic/SKILL.md) for the architecture. If the glossary defines "Order," talk about "the Order intake module," not "the FooBarHandler," and not "the Order service."

   **ADR conflicts**: if an opportunity contradicts an existing ADR, only surface it when the friction is real enough to warrant revisiting the ADR. Mark it clearly in the card (e.g. a warning callout: _"contradicts ADR-0007, but worth reopening because…"_). Don't list every theoretical refactor an ADR forbids.

   Do NOT propose interfaces yet. After the file is written, ask the user: "Which of these would you like to explore?"

3. **Grilling loop.** Once the user picks an opportunity, use [grilling](../../grilling/SKILL.md) to walk the decision tree with them: constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

   Side effects happen inline as decisions crystallize; use [domain-modeling](../../domain-modeling/SKILL.md) to keep the domain model current as you go:

   - **Naming a deepened module after a concept not in the project's glossary?** Add the term to the relevant glossary. Create the file lazily if it doesn't exist.
   - **Sharpening a fuzzy term during the conversation?** Update the glossary right there.
   - **User rejects the opportunity with a load-bearing reason?** Offer an ADR, framed as: _"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"_ Only offer when the reason would actually be needed by a future explorer to avoid re-suggesting the same thing; skip ephemeral reasons ("not worth it right now") and self-evident ones.

   **Want to explore alternative interfaces for the deepened module?** Show the user the constraints any new interface would need to satisfy, the dependencies it would rely on and which category they fall into, and an illustrative snippet that is not a proposal. Give [architect](../../architect/SKILL.md) the selected module, real call sites and settled constraints, and ask for alternative interfaces to the module. This playbook leaves implementation to the execution ticket, so architect returns its design package.

   Present each candidate design package from the arena run in turn, so the user can absorb each one. Then compare them in prose. Contrast by **depth** (leverage at the interface), **locality** (where change concentrates), and **seam placement**. Show the synthesized design package and explain why you recommend it.

**Reply:** Link the HTML report. Record the findings and decisions on the work issue with [to-tickets](../../to-tickets/SKILL.md#update) and name any project glossary or ADR file that step 3 changed. Stop on the work issue before Opening a PR. When the operator authorizes implementation, put the approved design package on the execution ticket as a settled baseline. Give that ticket to the code-writing agent through [Refactoring](refactoring.md) for a change that preserves behavior, or [Feature](feature.md) for changed behavior. Mark that playbook's architect step `skip: design settled in Improve codebase architecture`.
