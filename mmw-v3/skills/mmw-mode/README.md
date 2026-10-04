# mmw-mode: how this skill is written

Read `../README.md` first: it holds the method every component follows. This file covers the mode itself. Hosts load only `SKILL.md`; this file is for whoever writes or edits the mode.

The model to imitate, in content as well as shape, is `mmw-v3/upstream-pstack/skills/poteto-mode/SKILL.md` (2,971 words, seven sections).

## What the mode is for

The owner's way of working: in what situation to use what, and which playbook a task follows. It is loaded once, when `/mmw-mode` is invoked or when an agent MMW spawns is told to load it first, and stays in context for the rest of the session.

It is the only skill with `disable-model-invocation: true`. Every other skill can be invoked by the model.

## Frontmatter

- `name: mmw-mode`.
- `description`: the style in one phrase and the triggers (`/mmw-mode`, requests to work in this mode).
- `disable-model-invocation: true`.

poteto-mode's `mode`, `reminder`, `icon` and `color` are Cursor fields and are left out.

## The two rules that shape every section

1. **Sections are divided by the moment they are used, not by topic.** Choosing a route at the start of a task, a situation arising mid-task, deciding whether to ask the owner, spawning a subagent, writing the reply, writing a comment.
2. **The mode names; other components hold the how.** A trigger names a skill, an index line names a principle, a route line names a playbook. The mode carries full text only for what holds on every task and has no other home: Autonomy, Subagents, Writing the reply, Comments. "Cut ruthlessly. A mode skill is not a manual."

## Section by section

### `## Non-negotiables`

- **Used:** at any moment of any task, as soon as the situation a line names arises, whichever playbook is running.
- **Content:** one opening paragraph saying that the Principles section grounds every trigger, and that the reply names each principle that shaped a decision and the choice it changed, citing only principles whose full `SKILL.md` was read this session. Then one line per trigger: `Situation → what to use`, where what to use is a skill, a playbook (with its path), a principle or a reference. A line names; it does not explain how. The exception is a judgement that must be made on the spot, written into the line (poteto-mode's "classify it before you ask" line).
- **When to add a line:** the situation can occur inside any playbook, so it cannot hang on one step ("Before commit", "Any prose surface"). A situation that belongs to one step of one playbook is written in that step instead.
- **Sources in MMW v2:** rules of `mmw-v2/prompt/shared.md` that apply at a moment across tasks (rule 7 → a prose skill; rule 14 → before proposing a design or non-trivial code), and v2's own skills, compared one by one with their pstack counterparts before either is kept: agent-facing prose → `writing-for-agents` (it takes the place poteto-mode gives Cursor's `create-skill`); prose for people → `technical-writing`; any prose → `unslop`. The comparison and its results are in `mmw-v3/course/` lesson 4, figure 3.

### `## Principles`

- **Used:** the index is read when the mode loads; a principle's full text is read only when its condition arises and it is applied.
- **Content:** two sentences of usage ("Read the leaf skill in full for any principle you apply. Each entry names when it applies."), then the index in named groups (poteto-mode: Core, Architecture, Verification, Delegation, Meta). Each line holds three things: `**Name** (**principle-<slug>**). Condition. One-sentence rule.` The full text lives in `mmw-v3/skills/principle-<slug>/SKILL.md`, never in the mode.
- **When to add a line:** in the same change that adds the principle skill. When a principle is warranted is in `../README.md`.
- **Sources in MMW v2:** most numbered rules of `mmw-v2/prompt/shared.md` (8, 10, 12, 13, 14, 15, and the "it compiles is not it works" half of 4). Where a pstack principle already covers one (`principle-prove-it-works`, `principle-never-block-on-the-human`), start from the pstack text and merge MMW's specifics into it.

This index is how a rule loads at the moment it applies: one line is always in context, the full text is read when the condition arises. No hook is needed for it.

### `## Autonomy`

- **Used:** whenever the agent is deciding whether to act or to ask the owner first.
- **Content:** four paragraphs, each opening in bold, as in poteto-mode:
  - **Just do it.** What proceeds without asking: reversible work, engineering decisions.
  - **Always pause** for what only the owner decides: what the customer sees, money, scope and order, what goes public, what cannot easily be undone.
  - **Session overrides:** what the owner's words change ("going to bed"; an approved plan or ticket is the go signal).
  - **No is an acceptable answer.** Disagreement is owed when there is a flaw, never manufactured.
- **Sources in MMW v2:** `mmw-v2/prompt/shared.md` rules 1, 2, 3 and 11.

### `## Subagents`

- **Used:** before spawning any subagent.
- **Content:** decided in `mmw-v3/course/` lesson 5, from MMW v2's own subagent rules (for the workers, reviewers and other agents it spawns). pstack's `## Subagents` is compared with them rule by rule; nothing in it is copied by default.
- **Sources in MMW v2:** MMW's own subagent rules, listed in full in lesson 5, among them `mmw-v2/prompt/hosts/codex.md` ("Never interrupt subagents…") and `~/.mmw/models.json`, which holds the model for each role and is changed through `models.py`.

### `## Writing the reply`

- **Used:** while writing every reply.
- **Content:** the rules every reply shares, one point per bullet, each stated as an action: who reads the reply and what they can and cannot see; evidence or its label in the same sentence; reasons and consequences rather than files and functions; plain standard vocabulary; anchored references with names copied verbatim; when lists and tables help. Close with the division of labour: each playbook's `**Reply:**` line names only what is unique to that playbook.
- **Sources in MMW v2:** the reader facts at the top of `mmw-v2/prompt/shared.md` (condensed to what changes a decision), its rules 4, 5, 6 and 9, and its closing section "What this file looks like when it is working", which becomes the reply's finish criterion. Where every unit of shared.md goes is in mmw-v3/course lesson 4, figure 4.

### `## Comments`

- **Used:** while writing a code comment or any file's prose about the code.
- **Content:** one paragraph. A comment is kept only for a non-obvious why the code cannot show; a file describes its subject now, never its own history.
- **Source in MMW v2:** the code half of `mmw-v2/prompt/shared.md` rule 13. The section is deleted if nothing in MMW belongs here.

### `## Playbooks`

- **Used:** at the start of a task, to choose its route.
- **Content, in this order:**
  1. Usage: open a todolist whose first items are the matched playbook's steps copied in verbatim; a step not done stays in the list as `skip: <reason>`.
  2. The routing exceptions: large, cross-cutting or step-away work, and work no playbook fits, route to `figure-it-out`, which designs a playbook for that one run.
  3. One route line per playbook: ``**Name.** What task it is, and how it differs from the playbook most easily confused with it. `playbooks/<file>.md`.``
- **When to add a line:** in the same change that adds the playbook file. Whether a playbook is warranted is in `playbooks/README.md`.
- **Sources in MMW v2:** the `## Find your moment` tables of the `dispatch`, `verify-ticket`, `design-pages`, `ui-acceptance` and `code-review` skills, and the numbered procedures they point to (`implement`'s `## Closing steps`, `dispatch`'s `references/night.md`).
