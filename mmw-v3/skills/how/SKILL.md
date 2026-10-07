---
name: how
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# How

Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer onboarding onto a subsystem, enough to build a working mental model, not so much that it reads like annotated source code.

Each agent below is a session of its own, on the model `~/.mmw/models.json` gives its role: researchers read the code, an explainer writes the explanation. Start them with the `dispatch` skill's `dispatch.sh brief <role> <file>...`, one brief file per session; each brief is the template the step names with its placeholders filled, since the session sees the brief and nothing else. Every session one call starts is one batch, and the relay wakes you once, with `brief <batch> done`, when all of them have answered: end your turn after starting them, and on the wake follow the `dispatch` skill's `## On waking`. Each one only reads: end each brief with the line `Read only. Change no file of the repository, and run nothing that changes state but the report command below.`, since not every host has a read-only switch.

## Step 1. Assess Complexity

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): no sessions. You explore and explain it in a single pass. Go to Step 2b.
- **Complex** (a subsystem spanning multiple files or services, a cross-cutting feature, a full architectural overview): start parallel researchers first, then hand off to the explainer. Go to Step 2a.

When in doubt, take the simple path.

## Step 2a. Explore (complex questions only)

Decompose the question into 2 to 4 exploration angles, each a distinct slice of the subsystem. Start one researcher per angle, all in one `dispatch.sh brief researcher` call. Each researcher's brief is `references/explorer-prompt.md` with its angle filled in. Then go to Step 3.

## Step 2b. Direct Explain (simple questions)

Explore and write the explanation yourself, in the sections and style of `references/explainer-prompt.md` (its `## Output Format` and `## Communication Style`). Go to Step 4.

## Step 3. Synthesize (complex questions only)

Once the researchers' batch has woken you, start one explainer with `dispatch.sh brief explainer` to synthesize their findings into one explanation. Build its brief from `references/explainer-prompt.md`, with the path of every researcher's answer file in place of the explorer findings. Close the researchers' batch after the explainer has answered, not before: closing removes those files.

## Step 4. Present

Check the explanation against the code before you use it, then write it to the user as mmw-mode's `## Writing the reply` says. Close every batch you started.

## Output Format

The explanation uses the sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.
