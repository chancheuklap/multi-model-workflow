---
name: prototype
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Prototype

A prototype is **code that answers a question**. It lives in the repo and is iterated as the answer sharpens; the real implementation is written with it as reference. The question decides the shape.

## Pick a branch

Identify which question is being answered, using the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a single shareable HTML file (free-play buttons plus tabbed guided walkthroughs) that pushes the state machine through cases that are hard to reason about on paper, and that a non-developer can drive.
- **"How should this actually be implemented?"** → [EXP.md](EXP.md). Build the smallest runnable experiment that exercises the library, algorithm, or integration in question, and record what it shows.

The branches produce very different artifacts, so getting this wrong wastes the whole prototype. If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a third-party library, algorithm, or integration → experiment) and state the assumption at the top of the prototype. A question of what something should look like is not prototyped with this skill: say so to the user and stop.

## Rules that apply to every branch

1. **Lives in `prototypes/`, so a casual reader can see it's a prototype, not production.** Every prototype sits in a **leaf directory** `prototypes/<effort>/<issue>/<LOGIC|EXP>/`, with a leaf `README.md` beside the code holding the question, the current conclusion, and which parts the real code has taken. `<effort>` is the development effort's directory name, lowercase ASCII words joined by `-`: the one the `## Notes` of the wayfinder map that filed the ticket names, when there is one; otherwise ask the user which effort this is, falling back to the current branch name with `/` replaced by `-`. `<issue>` is the ticket number, or a short feature name when there is no ticket.
2. **Trivial to run.** An experiment starts from one command in the project's task runner: `pnpm <name>`, `python <path>`, `bun <path>`, etc. A logic demo is a single HTML file, published as a live page when the host can do that, otherwise opened by double-click. Either way, no thinking required to start it.
3. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE, wipe me" name.
4. **Skip the polish.** No tests: those are written when the real code lands, never here. No error handling beyond what makes the prototype _runnable_. No abstractions beyond a clear boundary around the part the real code will draw on. The point is to learn something fast.
5. **Surface the state.** After every action (logic), print or render the full relevant state so the user can see what changed; every experiment run writes its evidence page.
6. **Record the answer, keep the prototype.** Write the verdict and the question it settled into the leaf `README.md`, then fold the validated decision into the real code, rewritten to production standard, with the prototype as reference. The leaf `README.md` outlives this session and is read by people who were not in it: a spec cites it as the source of a decision, a ticket copies its exact values, and a worker builds from its verdict at night with no one to ask. So the verdict states what was decided, with the exact names and values, and what was tried and ruled out, and why; a pointer to where the decision is discussed is not a verdict. The leaf directory is the only place the prototype lives once it is folded in, so the next round of the same question iterates it instead of starting over. When a ticket triggered it, link the leaf directory from the ticket as an asset.
