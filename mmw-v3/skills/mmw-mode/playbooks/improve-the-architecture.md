### Improve the architecture

**You own one architecture review: the deepening opportunities in the codebase, shown as a visual HTML report, and the one candidate the owner picks grilled into a decision handed to Write a spec; an explorer subagent walks the codebase.** A **deepening opportunity** is a refactor that turns shallow modules into deep ones; the aim is testability and AI-navigability. This playbook changes no code: refactoring here would skip the tickets and the acceptance checks that make the change safe to land. Distinct from the `codebase-design` skill, which answers one design question in its vocabulary, and from Write a spec, which this playbook hands its decision to.

The review is informed by the project's domain model and built on a shared design vocabulary:

- Read the `codebase-design` skill's `SKILL.md` for the architecture vocabulary (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) and its principles (the deletion test, "the interface is the test surface", "one adapter = hypothetical seam, two = real"). Use these terms exactly in every suggestion, and don't drift into "component," "service," "API," or "boundary."
- The domain language in `CONTEXT.md` gives names to good seams; ADRs in `docs/adr/` record decisions this review should not re-litigate.

1. **Scope before you scan: YAGNI.** Deepening a module pays off by making future changes to it easier, so put extra weight on the parts of the codebase that have recently changed. Decide *where* to look before you look. If the owner named a direction (a module, a subsystem, a pain point), take it, and skip the inference below. Otherwise, walk back a good stretch of the commit history (`git log --oneline`) to find the codebase's hot spots, the files and areas that keep coming up, and let those paths pull your attention first. If the changes are scattered with no clear hot spot, widen the net.
   Done when you can name the paths the review will walk, and why those.
2. **Explore.** Read the project's domain glossary (`CONTEXT.md`) and any ADRs in the area you're touching first. Then send out one subagent, the architecture explorer, to walk the codebase, with the paths of step 1 and the prompt in the `mmw-mode` skill's `references/architecture-explorer.md`. Apply the **deletion test** to anything it reports as shallow: would deleting it concentrate complexity, or just move it? A "yes, concentrates" is the signal you want.
   Done when the explorer has returned and each friction point it reports has had the deletion test.
3. **Present candidates as an HTML report.** Write a self-contained HTML file to the OS temp directory so nothing lands in the repo. Resolve the temp dir from `$TMPDIR`, falling back to `/tmp` (or `%TEMP%` on Windows), and write to `<tmpdir>/architecture-review-<timestamp>.html` so each run gets a fresh file. Open it for the owner (`xdg-open <path>` on Linux, `open <path>` on macOS, `start <path>` on Windows) and tell them the absolute path.
   The report's look and every diagram in it come from the `diagram-design` skill: read its `SKILL.md` and follow it. Each candidate gets a **before/after visualisation**. Be visual.
   For each candidate, render a card with:
   - **Files**: which files/modules are involved
   - **Problem**: why the current architecture is causing friction
   - **Solution**: plain English description of what would change
   - **Benefits**: explained in terms of locality and leverage, and how tests would improve
   - **Before / After diagram**: side-by-side, custom-drawn, illustrating the shallowness and the deepening
   - **Recommendation strength**: one of `Strong`, `Worth exploring`, `Speculative`, rendered as a badge

   End the report with a **Top recommendation** section: which candidate you'd tackle first and why.
   **Use CONTEXT.md vocabulary for the domain, and the `codebase-design` skill's vocabulary for the architecture.** If `CONTEXT.md` defines "Order," talk about "the Order intake module," not "the FooBarHandler," and not "the Order service."
   **ADR conflicts**: if a candidate contradicts an existing ADR, only surface it when the friction is real enough to warrant revisiting the ADR. Mark it clearly in the card (e.g. a warning callout: _"contradicts ADR-0007, but worth reopening because…"_). Don't list every theoretical refactor an ADR forbids.
   The `mmw-mode` skill's `references/architecture-report.md` says what goes on the page and which diagram fits which candidate.
   Do NOT propose interfaces yet. After the file is written, ask the owner: "Which of these would you like to explore?"
   Done when the report is open in front of the owner, its path is in your message, and the owner has picked a candidate or put the review down.
4. **Grill the picked candidate.** Read the `grilling` skill's `SKILL.md` first and run the decision tree with the owner as it describes: constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive. Side effects happen inline as decisions crystallize; read the `domain-modeling` skill's `SKILL.md` and keep the domain model current as you go:
   - **Naming a deepened module after a concept not in `CONTEXT.md`?** Add the term to `CONTEXT.md`. Create the file lazily if it doesn't exist.
   - **Sharpening a fuzzy term during the conversation?** Update `CONTEXT.md` right there.
   - **The owner rejects the candidate with a load-bearing reason?** Offer an ADR, framed as: _"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"_ Only offer when the reason would actually be needed by a future explorer to avoid re-suggesting the same thing; skip ephemeral reasons ("not worth it right now") and self-evident ones.
   - **Want to explore alternative interfaces for the deepened module?** Read the `codebase-design` skill's `SKILL.md` and use its design-it-twice pattern.

   Done when the owner has confirmed a decision (the deepened module, its interface, where the seam sits, which tests move to it), or rejected the candidate.
5. **Hand the decision on.** When the owner confirms the decision, run **Write a spec** with this conversation as its source, which turns it into a spec the landing pipeline can build and verify. Take one candidate per session, and tell the owner the report's path so the others can be picked up later.
   Done when Write a spec's last step is done, or the owner rejected the candidate and the ADR they wanted is written.

**Reply:** the report's path; the candidates it holds, each with its recommendation strength; the candidate picked and the decision the grilling settled, or the owner's reason for rejecting it and the ADR recorded; the terms added to `CONTEXT.md`; then Write a spec's reply.
