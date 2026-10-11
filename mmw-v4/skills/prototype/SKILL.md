---
name: prototype
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Prototype

A prototype is **code that answers a question**. It lives in the repo and is iterated as the answer sharpens; the real implementation is written with it as reference. The question decides the shape.

Scope the decision the prototype exists to make first: which layout, which interaction, which density, or for an empirical fork which behavior, timing, or approach. No decision means no prototype: route to the Feature playbook of the **mmw-mode** skill.

## Pick a branch

Identify which question is being answered, using the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a single shareable HTML file (free-play buttons plus tabbed guided walkthroughs) that pushes the state machine through cases that are hard to reason about on paper, and that a non-developer can drive.
- **"What should this look like?"** → [UI.md](UI.md). Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.
- **"How should this actually be implemented?"** → [EXP.md](EXP.md). Build the smallest runnable experiment that exercises the library, algorithm, or integration in question (which behavior, timing, or approach holds up), and record what it shows.
- **"What shape should this code take?"** (its interface, its modules, where the seams go) → the **architect** skill, which writes its sketch and rationale into the leaf directory `SKETCH/`; the rationale is the leaf `README.md`. Run it only when both hold: no prototype, ADR, or earlier spec has already settled this shape, and the shape reaches beyond one ticket. A shape inside one ticket is left to whoever builds that ticket. No one is asked: the candidate sketches are compared and the result decides.

The branches produce very different artifacts, so getting this wrong wastes the whole prototype. If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a page or component → UI; a third-party library, algorithm, or integration → experiment) and state the assumption at the top of the prototype.

## Rules that apply to every branch

1. **Lives in `efforts/<effort>/prototypes/`, so a casual reader can see it's a prototype, not production.** Every prototype sits in a **leaf directory** `efforts/<effort>/prototypes/<issue>/<UI|LOGIC|EXP|SKETCH>/`, with a leaf `README.md` beside the code holding the question, the current conclusion, and which parts the real code has taken. `<effort>` is the development effort's directory name under `efforts/`, which holds every file of that effort, lowercase ASCII words joined by `-`: the one the `## Notes` of the wayfinder map that filed the ticket names, when there is one; otherwise ask the user which effort this is, falling back to the current branch name with `/` replaced by `-`. `<issue>` is the ticket number, or a short feature name when there is no ticket. A UI prototype that needs its own route obeys whatever routing convention the project already uses; don't invent a new top-level structure.
2. **Trivial to run.** A UI prototype or an experiment starts from one command in the project's task runner: `pnpm <name>`, `python <path>`, `bun <path>`, etc. A logic demo is a single HTML file, published as a live page when the host can do that, otherwise opened by double-click. Either way, no thinking required to start it. A sketch type-checks with one command.
3. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE, wipe me" name. A sketch touches no data at all.
4. **Skip the polish.** No tests: those are written when the real code lands, never here. No error handling beyond what makes the prototype _runnable_. No abstractions beyond a clear boundary around the part the real code will draw on. The point is to learn something fast. A sketch has no implementation: its bodies are `not implemented`.
5. **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed; every experiment run writes its evidence page. A sketch has no state to show.
6. **Record the answer, keep the prototype.** Present the alternatives, their tradeoffs, and a recommendation to whoever asked for the prototype. Write the verdict and the question it settled into the leaf `README.md`. The validated decision reaches the real code through a ticket: the leaf directory and its verdict go under the ticket's **Read first** as a baseline, and the worker rewrites it to production standard, with the prototype as reference. The leaf `README.md` outlives this session and is read by people who were not in it: a spec cites it as the source of a decision, a ticket copies its exact values, and a worker builds from its verdict at night with no one to ask. So the verdict states what was decided, with the exact names and values, and what was tried and ruled out, and why; a pointer to where the decision is discussed is not a verdict. The leaf directory is the only place the prototype lives once it is folded in, so the next round of the same question iterates it instead of starting over. When a ticket triggered it, link the leaf directory from the ticket as an asset.
