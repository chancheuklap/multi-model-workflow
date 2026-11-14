### Prototype

**You own the design decision, not the code. The prototype is a throwaway instrument. The real build follows Feature.**

The one playbook where [principle-laziness-protocol](../../principle-laziness-protocol/SKILL.md)'s "smallest change" and the verification bar invert. Speed over polish, code quality does not matter, no planning. The rigor is in picking the right design cheaply. Propose variations the user didn't ask for, throw an approach away and try another.

1. Scope the decision the prototype exists to make: which layout, which interaction, which density, or for an empirical fork which behavior, timing, or approach. Identify the question from the user's prompt and the surrounding code. Ask if it is still unclear and the user is around. No decision means no prototype. Return to the caller, or route a standalone implementation request to Feature.
2. Gather references when the design space is open. Search for prior art, summarize a moodboard of themes, palettes, and layouts, let the user pick directions before building. Skip when the direction is set.
3. For a standalone sketch, build throwaway in an isolated scratch dir, separate from production source. For a visual decision, vanilla HTML/CSS/JS or the lightest stack that renders the idea, CDN deps, a dev server with hot reload. For a behavioral or timing decision, the smallest script that exercises the question. No production framework, no tests, no abstractions.
   - To let someone try business rules or state transitions, use the [logic demo](../references/prototype/logic.md). Build a single shareable HTML file (free-play buttons plus tabbed guided walkthroughs) that pushes the state machine through cases that are hard to reason about on paper, and that a non-developer can drive.
   - To judge the UI against the surrounding app, use the [UI prototype](../references/prototype/ui.md) in an isolated worktree. Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.

   Follow the [shared rules](#logic-and-ui-prototypes) for a logic demo or in-app UI. If the choice between a logic demo and in-app UI is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a page or component → UI) and state the assumption at the top of the prototype.

4. When comparing alternatives, build them behind one switcher (buttons or a keypress), each variant labeled. This is the [principle-exhaust-the-design-space](../../principle-exhaust-the-design-space/SKILL.md) principle skill made cheap.
   Competing UI layouts must be **structurally different**: different layout, different information hierarchy, different primary affordance, not just different colours.
5. Verify on the matching surface. For a visual decision or logic demo, use the project's `verify-<app>` for the prototype surface ([verify-this](../../verify-this/SKILL.md#local-surfaces) if none matches) to drive the interaction. For visual variants, screenshot each one. For a logic demo, try a free-play action and a guided walkthrough. Observe the state after each action. For a behavioral or timing decision, observe the thing you are deciding by logging the timing, printing the output, or watching the render. The observation is the test here, not an assertion.
6. When comparing alternatives, present them with their tradeoffs and a recommendation. The output is the decision plus the throwaway artifact, not shippable code. For an empirical question, report what you observed. When the decision belongs to the operator, show the evidence and give them the prototype to try. Their answer settles the question.
   When another step called Prototype, return the decision, evidence and artifact to it and resume that step. For a standalone prototype, deliver them to the operator and record the question and its answer on the work issue. If the standalone request also authorizes implementation, link the approved prototype from the execution ticket and hand the chosen direction to **Feature** (or [architect](../../architect/SKILL.md) for the shape).

#### Logic and UI prototypes

- **Throwaway from day one, and clearly marked as such.** Name it so a casual reader can see it's a prototype. In the worktree, locate in-app prototype code next to the module or page it's prototyping for. For throwaway UI routes, obey whatever routing convention the project already uses; don't invent a new top-level structure.
- **Trivial to run.** A UI prototype starts from one command in the project's task runner: `pnpm <name>`, `python <path>`, `bun <path>`, etc. A logic demo is a single HTML file the user double-clicks. Either way, no thinking required to start it.
- **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE, wipe me" name.
- **Skip the polish.** No tests, no error handling beyond what makes the prototype _runnable_, no abstractions. The point is to learn something fast.
- **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed.
- **Capture it when done.** Commit the runnable demo or full set of variants to a throwaway branch, out of main. Push the branch and link the commit from the work issue.

**Reply:** the answer or the question still open, the evidence (screenshots for a visual decision, the observed state, output or timing for a behavioral one), and a path or URL the recipient can open. Say plainly that the prototype is throwaway.
