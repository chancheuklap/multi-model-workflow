---
name: ask-matt
description: Ask which skill or flow fits your situation. A router over the upstream skills in this repo and the interface chain beside them. Use when you know what you want to do but not which skill does it, or when you are choosing what to do at a phase boundary.
---

# Ask Matt

You don't remember every skill, so ask.

A **flow** is a path through the skills. Most paths run along one **main flow**, and two **on-ramps** merge onto it. Everything else is standalone, or a vocabulary layer that runs underneath.

## The main flow: idea → ship

The route most work travels. You have an idea and want it built.

1. **the `grill-with-docs` skill** sharpens the idea by interview. Start here whenever you are **working in a working directory**: it's stateful, retaining what it learns in `CONTEXT.md` and ADRs. (No working directory? Use the `grill-me` skill instead, covered under Standalone. Both run the same `grilling` primitive; `grill-with-docs` is the one that leaves a paper trail, which makes it the better of the two whenever a repo is there to leave it in.)
2. **Branch: can you settle every question in conversation?** If a question needs a runnable answer (state, business logic, a UI you have to see, a library or approach you have to run), detour through a prototype, bridged by **the `handoff` skill** in both directions (a prototype lives in its own directory, which is exactly what the `handoff` skill is for; see Phase boundaries):
   - **the `handoff` skill** out, then open a fresh session against that file,
   - **the `prototype` skill** to answer the question with runnable code,
   - **the `handoff` skill** back what you learned, and reference it from the original idea thread.

   **A UI question's answer goes on, not back.** Once a variant wins, the interface is designed in Claude Design, not in the repo: **the `design-pages` skill** sets up the Claude Design project the user designs in (with a design system built from that winner when one is wanted) and pulls the signed-off project back as the **design package**; then **the `write-screen-contract` skill** binds each control to what it calls, which field feeds each shown value, and what state follows. Only then does step 3 have something to write a spec from. Each of those skills' closing section names the next, so you do not come back here between them. With a wayfinder map the two steps are a **design ticket** and an **alignment ticket** on it; with no map (an existing product gaining one surface), they run in a single session with the user present, prototype through contract, before **the `to-spec` skill**.
3. **Branch: is this a multi-session build?**
   - **Yes** → **the `to-spec` skill** (turn the thread into a spec), then **the `to-tickets` skill** to split it into tracer-bullet tickets, each declaring its **blocking edges** as native blocking links on the tracker, so any ticket whose blockers are done can be grabbed. Then **the `dispatch` skill** runs the published tickets: a night over the spec's batch, or one ticket outside a night. Each ticket is self-contained, and each worker starts in a fresh session, working from its ticket.
   - **No** → **the `tdd` skill** in this session, to build a concrete behaviour test-first without a spec or tickets.

   A dispatched worker loads **the `implement` skill**, which builds its ticket by driving **the `tdd` skill** internally (one red-green slice at a time), then closes out with **the `code-review` skill**, a review of the ticket's diff along Standards, Spec and Tests, plus a pilot UI axis on a ticket with a story criterion. **The `code-review` skill** reviews one ticket's diff; it has no use on a branch or PR without a ticket.

### Context hygiene

Keep steps 1–3 in **one unbroken context window** (don't compact or clear until after the `to-tickets` skill has run) so the grilling, spec, and tickets all build on the same thinking. Each run of the `implement` skill then starts fresh, working from the ticket.

The limit on this is the **[smart zone](https://www.aihero.dev/ai-coding-dictionary/smart-zone)**: the window (~150k tokens on state-of-the-art models) within which the model still reasons sharply. If a session approaches it before the `to-tickets` skill, don't push on degraded; compress the session into a summary at the nearest phase boundary and carry on from it (see Phase boundaries).

## On-ramps

A starting situation that generates work, then merges onto the main flow.

- **Bugs and requests piling up** → **the `triage` skill**. It moves issues through triage roles, and routes the work it judges agent-ready into **the `to-spec` skill** and then **the `to-tickets` skill**.

  Triage is for issues **you didn't create**: bug reports, incoming feature requests, anything that arrives raw. Tickets that the `to-tickets` skill produced are already agent-ready, so **don't triage them**, except a ticket the pipeline handed back to `needs-triage`, which triage judges again.

- **Something's broken** → **the `diagnosing-bugs` skill**. For the hard ones: the bug that resists a first glance, the intermittent flake, the regression that crept in between two known-good states. It refuses to theorise until it has a **tight feedback loop** (one command that already goes red on *this* bug), then fixes with a regression test. Its post-mortem hands off to **the `improve-codebase-architecture` skill** when the real finding is that there's no good seam to lock the bug down.

- **A huge, foggy effort: a greenfield project or a huge feature build, too big for one session** → **the `wayfinder` skill**, the most cognitively demanding flow here. When the way from here to the destination isn't visible yet, it charts a **shared map** of **decision tickets** on the issue tracker and resolves them one at a time, producing **decisions, not deliverables**, until the fog is pushed back and the way is clear. Where **the `grill-with-docs` skill** sharpens an idea you can hold in one session, wayfinder is for the idea you can't, and it's slower and denser, so save it for exactly that, never a well-scoped feature.

  When the map clears, **it hands off, it doesn't build**: merge onto the main flow at **the `to-spec` skill**, which collapses the map's linked decisions into a buildable plan, then the `to-tickets` and `dispatch` skills as usual. Building straight from the map skips that collapse and throws the linked detail away, so go straight to step 3's **No** branch only when the effort turned out genuinely small.

## Codebase health

Not feature work, just upkeep.

- **the `improve-codebase-architecture` skill** runs whenever you have a spare moment to keep the codebase good for agents to operate in. It surfaces **deepening opportunities**; picking one _generates an idea_ you can take into the main flow at the `grill-with-docs` skill. It's the survey that finds the candidates; **the `codebase-design` skill** (below) is the bench you design the chosen one on.

## Vocabulary underneath

Two model-invoked references that run *beneath* the other skills, each the single source of truth for its vocabulary. Reach for them directly when the **words**, not the process, are the problem; or let the skills above pull them in.

- **the `domain-modeling` skill**: sharpen the project's *domain* language: challenge a fuzzy term, resolve an overloaded word ("account" doing three jobs), record a hard-to-reverse decision as an ADR. It's the active discipline the `grill-with-docs` skill drives to keep `CONTEXT.md` a clean glossary.
- **the `codebase-design` skill** is the deep-module vocabulary (module, interface, depth, seam, adapter, leverage, locality) for designing a module's *shape*: a lot of behaviour behind a small interface at a clean seam. the `tdd` and `improve-codebase-architecture` skills both speak it.

## Phase boundaries

Emptying a session's context and compressing it into a summary both exist on every host, under a different name on each; use the one your host gives you.

A **phase** is a chunk of work inside a session: the grilling, the implementation, the QA. At the **boundary** between two of them you have five options, and picking between them is the fuzziest decision in this whole map:

- **Continue**: stay put. Costs nothing, loses nothing.
- **Clear**: empty the window, when nothing here matters to what's next.
- **Handoff**: the `handoff` skill writes a portable markdown file. Narrow: only for a **new host**, a **new directory**, a **colleague**, or forking a side task **mid-phase**. What it buys is portability.
- **Subagent**: send a tightly-scoped task to its own window and get a report back.
- **Compact** compresses this context and seeds a fresh session with it. The **default**, at the bottom of the tree rather than the first reach.

Read [PHASE-BOUNDARIES.md](PHASE-BOUNDARIES.md) for the ordered tree: the five questions, the reasoning behind each branch, and why the primary-source cost makes **Continue** the one to rule out first. Make the decision **at** a boundary; mid-phase, continue or split the rest into subagents.

## Standalone

Off the main flow entirely.

- **the `grill-me` skill**: the same relentless interview as the `grill-with-docs` skill, but **stateless**: it saves nothing locally and builds no `CONTEXT.md`. Reach for it when you are **not working in a working directory** (sharpening a plan, a design, a piece of writing, anything with no repo under it). If you are in a working directory, use the `grill-with-docs` skill instead: it runs the same interview and leaves a paper trail, so it is strictly the better one.
- **the `grilling` skill** is the interview primitive itself: rounds, the frontier, facts are the agent's job and decisions are yours. the `grill-me` and `grill-with-docs` skills are the two named ways in, and the `triage`, `wayfinder` and `improve-codebase-architecture` skills all run it internally. Reach for it directly only when you want the interview with no wrapper around it.
- **the `resolving-merge-conflicts` skill** works a merge that went wrong: an in-progress merge or rebase conflict, hunk by hunk, or a clean merge that turned the repository checks red, by finding the change it collides with on the other side. It resolves by **intent** traced to each side's primary source rather than by picking lines, then finishes the operation. It never runs `--abort`. Standalone and off every flow: reach for it when you are already mid-conflict, or when a merge you just made left the checks red.
- **the `prototype` skill** is a small program that answers one design question: does this state model feel right, what should this UI look like, or how should this actually be implemented. A logic or implementation answer folds into the real code, rewritten to production standard; a winning UI variant does not: it is handed to Claude Design, and the real code is written from the design pages that come back (see the interface branch in step 2). Either way the prototype itself stays under `prototypes/` in the repo as the reference it was written from, iterated the next time the same question comes up. It's the detour in step 2 of the main flow, but reach for it any time a design question is hard to settle on paper.
- **the `research` skill**: delegate reading legwork to a **background agent**: it investigates a question against **primary sources**, then leaves a cited Markdown file in the repo. Keep working while it reads. The file it produces is something to take *into* the main flow at the `grill-with-docs` skill, since research feeds the thinking rather than replacing it.
- **the `to-questionnaire` skill** comes in when the thing blocking you isn't in your head or the codebase but in **someone else's**, and it writes them a questionnaire to fill in. It's the inverse of the `grill-me` skill: instead of interviewing you about the subject, it interviews you about the **send** (who it's going to, what you need back) and aims the questions at the gap. What comes back is material for the `grill-with-docs` or `to-spec` skills.
- **the `wizard` skill** is for the steps only a **human** can take: provisioning infrastructure, setting up credentials or CI secrets, clicking through an unfamiliar third-party dashboard, running a one-off migration or cutover. It generates an interactive bash script that opens each URL, captures each value, and writes it into `.env` and GitHub secrets, so the procedure stops being something you re-explain to an agent every time. Model-invoked, so the agent reaches for it the moment it hits a wall only you can pass. If the agent could just do it itself, it should; this is for where a human is genuinely in the loop.
- **the `wait-what` skill** is the corrective for a message that didn't land. Use it mid-conversation, inside any other skill, and the agent re-pitches what it just said with the context you were missing, in plain English, using the `CONTEXT.md` vocabulary. It works after the fact; the `grill-with-docs` skill is the upfront cure, because a shared language agreed early is what stops the jargon arriving at all.
- **the `teach` skill**: learn a concept over multiple sessions, using the current directory as a stateful workspace.
- **the `writing-for-agents` skill** is the reference for writing documents agents consume: skills, AGENTS.md, pointed-at docs.

## Precondition

**the `setup-matt-pocock-skills` skill**: run before your first engineering flow to configure the issue tracker, triage labels, and doc layout the other skills assume. Custom issue trackers also work.
