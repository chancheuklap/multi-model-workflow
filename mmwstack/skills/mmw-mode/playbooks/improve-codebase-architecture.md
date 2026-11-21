### Improve codebase architecture

**You own the deepening opportunities and the recommendation.** Surface architectural friction and propose **deepening opportunities**: refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

1. **Explore.** Use [codebase-dic](../../codebase-dic/SKILL.md) for the architecture vocabulary (**module**, **interface**, **implementation**, **depth**, **seam**, **adapter**, **leverage**, **locality**) and its principles. Read the project's glossary and any ADRs in the area you're touching first. Follow the project's glossary map when it has one. The domain vocabulary gives names to good seams. ADRs record decisions this investigation should not re-litigate.

   **Scope before you scan: YAGNI.** Deepening a module pays off by making future changes to it easier, so put extra weight on the parts of the codebase that have recently changed. Decide *where* to look before you look:

   - If the user named a direction (a module, a subsystem, a pain point), take it, and skip the inference below.
   - Otherwise, walk back a good stretch of the commit history (`git log --oneline`) to find the codebase's hot spots, the files and areas that keep coming up, and let those paths pull your attention first. If the changes are scattered with no clear hot spot, widen the net.

   Spawn a fresh `mmw-agent` for the read-only exploration. Give it the work issue URL and scope. Use the model and settings from the current host's `judgment and prose` entry in `~/.agents/mmwstack-models.md` (or the supplied rule file). Include the relevant glossary, ADRs and [codebase-dic](../../codebase-dic/SKILL.md) in the brief. Ask for real call sites and file paths that show the friction. Include the following questions and the deletion test in the exploration prompt.

   Don't follow rigid heuristics; explore organically and note where you experience friction:

   - Where does understanding one concept require bouncing between many small modules?
   - Where are modules **shallow**, with an interface nearly as complex as the implementation?
   - Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
   - Where do tightly-coupled modules leak across their seams?
   - Which parts of the codebase are untested, or hard to test through their current interface?

   Apply the **deletion test** to anything you suspect is shallow. Imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep. Check the returned findings against the cited code.

2. **Present the deepening opportunities as an HTML report.** Produce a single self-contained HTML report and deliver it per the operator's and host's HTML artifact rules. Show the report to the user and link it.

   Render each deepening opportunity as a card with a **before/after visualization** per [HTML report format](../references/improve-codebase-architecture/html-report.md), which governs the scaffold, card structure, diagram patterns, and brevity bounds. Use [big-pics-little-words](../../big-pics-little-words/SKILL.md) and [html](../../html/SKILL.md) for offline HTML and SVG craft while keeping every card within those brevity bounds. For dependency categories, consult [Deepening](../../codebase-dic/references/deepening.md).

   Mark the opportunity you'd tackle first with a `Recommended first` badge on its card, with the reason beside the badge.

   Use the project's domain vocabulary for the domain and the architecture vocabulary from [codebase-dic](../../codebase-dic/SKILL.md) for the architecture. If the glossary defines "Order," talk about "the Order intake module," not "the FooBarHandler," and not "the Order service."

   **ADR conflicts**: if an opportunity contradicts an existing ADR, only surface it when the friction is real enough to warrant revisiting the ADR. Mark it clearly in the card (e.g. a warning callout: _"contradicts ADR-0007, but worth reopening because…"_). Don't list every theoretical refactor an ADR forbids.

   Do NOT propose interfaces yet. After the file is written, ask the user: "Which of these would you like to explore?"

3. **Grilling loop.** Once the user picks an opportunity, use [grilling](../../grilling/SKILL.md) to walk the decision tree with them: constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

   While grilling keeps the domain model current, handle two architecture-review cases inline:

   - **Naming a deepened module after a concept not in the project's glossary?** Add the term to the relevant glossary. Create the file lazily if it doesn't exist.
   - **User rejects the opportunity with a load-bearing reason?** Offer an ADR, framed as: _"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"_ Only offer when the reason would actually be needed by a future explorer to avoid re-suggesting the same thing; skip ephemeral reasons ("not worth it right now") and self-evident ones.

   **Want to explore alternative interfaces for the deepened module?** Pass the selected module, real call sites, dependencies, and settled constraints to [architect](../../architect/SKILL.md), and ask for alternative interfaces to that module. Tell it that implementation belongs to the execution ticket, so it returns the design package and design rationale for this session to record.

**Reply:** Link the HTML report. Record the findings and decisions on the work issue with [to-tickets](../../to-tickets/SKILL.md#update) and name any project glossary or ADR file that step 3 changed. Stop on the work issue before Opening a PR. When the operator authorizes implementation, route the execution ticket to [Refactoring](refactoring.md) for a change that preserves behavior, or [Feature](feature.md) for changed behavior. If step 3 produced an accepted design package from [architect](../../architect/SKILL.md) (whether from a plain-language summary or from a design review before implementation), attach it to the execution ticket as a settled baseline and note that the design is settled so the downstream playbook skips its architect step. If step 3 settled constraints without producing a design package, the downstream playbook runs architect as usual.
