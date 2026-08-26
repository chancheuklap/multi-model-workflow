---
name: prototype
description: Build a prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, explore what a UI should look like, or work out how a feature should be implemented before writing it for real.
---

# Prototype

A prototype is **code that answers a question**. It lives in the repo and is iterated as the answer sharpens; the real implementation is written with it as reference. The question decides the shape.

## Pick a branch

Identify which question is being answered — from the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a single shareable HTML file — free-play buttons plus tabbed guided walkthroughs — that pushes the state machine through cases that are hard to reason about on paper, and that a non-developer can drive.
- **"What should this look like?"** → [UI.md](UI.md). Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.
- **"How should this actually be implemented?"** → [EXP.md](EXP.md). Build the smallest runnable experiment that exercises the library, algorithm, or integration in question, and record what it shows.

The branches produce very different artifacts — getting this wrong wastes the whole prototype. If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a page or component → UI; a third-party library, algorithm, or integration → experiment) and state the assumption at the top of the prototype.

## Rules that apply to every branch

1. **Lives in `prototypes/`, so a casual reader can see it's a prototype, not production.** Every prototype sits at `prototypes/<task>/<issue>/<UI|LOGIC|EXP>/`, with a `README.md` beside the code holding the question, the current conclusion, and which parts the real code has taken. `<task>` is the development effort it belongs to: the title of the wayfinder map that filed the ticket, when there is one; otherwise ask the user which effort this is, falling back to the current branch name with `/` replaced by `-`. `<issue>` is the ticket id, or a short feature name when there is no ticket. On the main branch, stop and ask for a task branch first. A UI prototype that needs its own route obeys whatever routing convention the project already uses; don't invent a new top-level structure.
2. **Trivial to run.** A UI prototype or an experiment starts from one command in the project's task runner — `pnpm <name>`, `python <path>`, `bun <path>`, etc. A logic demo is a single HTML file — published as a live page when the host can do that, otherwise opened by double-click. Either way, no thinking required to start it.
3. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE — wipe me" name.
4. **Skip the polish.** No tests — those are written when the real code lands, never here. No error handling beyond what makes the prototype _runnable_. No abstractions beyond a clear boundary around the part the real code will draw on. The point is to learn something fast.
5. **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed; every experiment run writes its evidence page.
6. **Record the answer, keep the prototype.** Write the verdict and the question it settled into the leaf `README.md`, then fold the validated decision into the real code — rewritten to production standard, with the prototype as reference. The leaf directory is the only place the prototype lives once it is folded in, so the next round of the same question iterates it instead of starting over. When a ticket triggered it, link the leaf directory from the ticket as an asset.
