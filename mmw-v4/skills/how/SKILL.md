---
name: how
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# How

Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer onboarding onto a subsystem, enough to build a working mental model, not so much that it reads like annotated source code.

## Step 1. Assess Complexity

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): no researchers. You explore and explain it in one pass. Go to Step 2b.
- **Complex** (a subsystem spanning multiple files or services, a cross-cutting feature, a full architectural overview): send parallel researchers first, then write the explanation from their findings. Go to Step 2a.

When in doubt, take the simple path.

## Step 2a. Explore (complex questions only)

Decompose the question into 2 to 4 exploration angles, each a distinct slice of the subsystem. Write one brief per angle: `## Task` the question and this angle; `## Known` what you have read so far, and the angle each other brief in this batch covers; `## For` one explanation you write from every angle. Send them all with one `dispatch.sh send researcher --follow "the research skill's references/explorer.md" <brief>...` of the **dispatch** skill and end your turn. Woken by `brief <batch> done`, follow the dispatch skill's `## On waking`, then go to Step 3.

## Step 2b. Direct Explain (simple questions)

Explore and write the explanation yourself, in the sections and style of `references/explainer-prompt.md` (its `## Output Format` and `## Communication Style`). Go to Step 4.

## Step 3. Synthesize (complex questions only)

Write one explanation yourself from the researchers' answers, as `references/explainer-prompt.md` says.

## Step 4. Present

Check the explanation against the code before you use it, then present it to the user. Asked by the person rather than by another skill, present it as one page drawn with the **diagram-design** skill: the parts it names and how they connect, and one run through them from start to end, the sections below as the words beside the pictures. Handed back to another skill, it stays text. Close the researchers' batch once nothing you still do needs their answers.

## Output Format

The explanation uses the sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.
