# mmw-mode: how this skill is written

Read `../README.md` first: it holds the method every component follows. This file covers the mode itself. Hosts load only `SKILL.md`; this file is for whoever writes or edits the mode.

The model to imitate, in content as well as shape, is `mmw-v3/upstream-pstack/skills/poteto-mode/SKILL.md` (2,971 words, seven sections).

## What the mode is for

The owner's way of working: in what situation to use what, and which playbook a task follows. It is loaded once and stays in context for the rest of the session. Three routes load it: the person types `/mmw-mode`; `scripts/mode-hook.py`, which `install.sh` registers at SessionStart on Claude Code and Codex, tells a session in a repository with `.mmw/` to read `SKILL.md`; the start prompt `dispatch.sh` gives a worker or reviewer opens with the same instruction and the file's path.

It is one of the three skills only the person starts (`teach` and `wait-what` are the others); every other skill can be invoked by the model. So the hook and the start prompt tell a session to read the file, never to use the skill: a model cannot call it by name.

## Frontmatter

- `name: mmw-mode`.
- `description`: the style in one phrase and the triggers (`/mmw-mode`, requests to work in this mode).
- `disable-model-invocation: true`, paired with `policy.allow_implicit_invocation: false` in `agents/openai.yaml` for Codex.

poteto-mode's `mode`, `reminder`, `icon` and `color` are Cursor fields and are left out.

## The two rules that shape every section

1. **Sections are divided by the moment they are used, not by topic.** Choosing a route at the start of a task, a situation arising mid-task, deciding whether to ask the owner, spawning a subagent, writing the reply, writing a comment.
2. **The mode names; other components hold the how.** A trigger names a skill, an index line names a principle, a route line names a playbook. The mode carries full text only for what holds on every task and has no other home: Autonomy, Subagents, Writing the reply, Comments. "Cut ruthlessly. A mode skill is not a manual."

## Section by section

### `## Non-negotiables`

- **Used:** at any moment of any task, as soon as the situation a line names arises, whichever playbook is running.
- **Content:** one opening paragraph saying that the Principles section grounds every trigger (a principle's index line is itself a trigger), and that the reply names each principle that shaped a decision and the choice it changed, citing only principles whose full `SKILL.md` was read this session. Then one line per trigger: `Situation → what to use`, where what to use is a skill, a playbook (with its path), or a reference. A line names; it does not explain how. The exception is a judgement that must be made on the spot, written into the line (poteto-mode's "classify it before you ask" line).
- **When to add a line:** the situation can occur inside any playbook, so it cannot hang on one step ("Before commit", "Any prose surface"). A situation that belongs to one step of one playbook is written in that step instead. A situation a principle's index line already names gets no line here, unless the line adds an action the principle does not hold (poteto-mode's "Any code → name the data shape first").
- **Sources in MMW v2:** rules of `mmw-v2/prompt/shared.md` that apply at a moment across tasks (rule 7 → a prose skill), and v2's own skills, compared one by one with their pstack counterparts before either is kept: agent-facing prose → `writing-for-agents` (it takes the place poteto-mode gives Cursor's `create-skill`); prose for people → `technical-writing`; any prose → `unslop`. The comparison and its results are in `mmw-v3/course/` lesson 4, figure 3. The `PRODUCT_RULES` sentence of `mmw-v2/skills/dispatch/scripts/dispatch.sh`, which every worker's start prompt carried → the `ui-acceptance` skill's five rules (lesson 5, decision 5). The `how` line is poteto-mode's own, brought in with the `how` skill (lesson 6, section 5). The `setup-mmw` line: a repository not set up is met in several playbooks and scripts, and only that skill sets one up (lesson 11). The `diagram-design` line: a page drawn for a person is met inside a discussion, Investigation and several playbooks, and without the line the host's own page guidance is what a session follows.

### `## Principles`

- **Used:** the index is read when the mode loads; a principle's full text is read only when its condition arises and it is applied.
- **Content:** two sentences of usage ("Read the leaf skill in full for any principle you apply. Each entry names when it applies."), then the index in named groups (poteto-mode: Core, Architecture, Verification, Delegation, Meta). Each line holds three things: `**Name** (**principle-<slug>**). Condition. One-sentence rule.` The full text lives in `mmw-v3/skills/principle-<slug>/SKILL.md`, never in the mode.
- **When to add a line:** in the same change that adds the principle skill. When a principle is warranted is in `../README.md`.
- **Sources in MMW v2:** most numbered rules of `mmw-v2/prompt/shared.md` (8, 10, 12, 13, 14, 15, and the "it compiles is not it works" half of 4). Where a pstack principle already covers one (`principle-prove-it-works`, `principle-never-block-on-the-human`), start from the pstack text and merge MMW's specifics into it.

This index is how a rule loads at the moment it applies: one line is always in context, the full text is read when the condition arises. No hook is needed for it.

### `## Autonomy`

- **Used:** whenever the agent is deciding whether to act or to ask the owner first.
- **Content:** five paragraphs, each opening in bold, the first four as in poteto-mode:
  - **Just do it.** What proceeds without asking: reversible work, engineering decisions, and any fact you could observe by running something (behaviour, timing, layout, output), which is found by running it, not asked.
  - **Always pause** for what only the owner decides (the list is in the user-level prompt, which every session loads) and for irreversible writes.
  - **Session overrides:** what the owner's words change ("going to bed"; an approved plan or ticket is the go signal).
  - **No is an acceptable answer.** Disagreement is owed when there is a flaw, never manufactured.
  - **Unattended.** How a session a script started works with nobody to ask: which of the four paragraphs above hold for it, and what replaces asking. It is the only text a start prompt relies on for working unwatched; the start prompt itself carries no rule (lesson 5, decision 5).
- **Sources in MMW v2:** `mmw-v2/prompt/shared.md` rules 1, 2 and 3. Rule 11 is `principle-never-block-on-the-human`'s, whose index line is read at the same moment. From poteto-mode's "classify it before you ask" line, only the clause on facts found by running something; which calls are the owner's is the Always pause list. Unattended: the `AUTONOMOUS` sentence of `mmw-v2/skills/dispatch/scripts/dispatch.sh`, the scripted-session paragraph of `mmw-v2/prompt/shared.md`, and the first bullet of `implement`'s code-writing rules ("Put no question on the screen").

### `## Subagents`

- **Used:** before spawning any subagent.
- **Content:** the rules for a subagent a skill or playbook sends out from inside a session, one paragraph each: which subagent to use and on which model; that work needing a model of its own is a session role; what its brief states; what to do on a host that cannot run one; who owns what it returns. Every subagent in MMW is sent out by a skill or a playbook, which writes its prompt (an axis of `code-review`, the fact-finder of `grilling`, the ambiguity scanner of Cut tickets); no subagent loads this mode. Sessions a script starts (worker, reviewer, advisor, researcher, explainer, synthesizer) are not subagents; their start and their models are the `dispatch` skill's, and its `roles.json` lists every role of both kinds.
- **Sources in MMW v2:** `mmw-v2/prompt/hosts/codex.md` ("Never interrupt subagents or other agents while they are working"), `manage-agents-md` ("your host's general-purpose subagent, with no model named"), `code-review` `references/session.md` section 2, `to-tickets` ("Hold this turn until it returns"), `SKILL-SET-RULES.md` ("A subagent's brief states what it returns and its length"), ADR 0015. From poteto-mode's `## Subagents`, only "You own every subagent's work".

### `## Writing the reply`

- **Used:** while writing every reply.
- **Content:** the rules every reply shares, one point per bullet, each stated as an action: evidence or its label in the same sentence; reasons and consequences rather than files and functions; plain standard vocabulary; when lists and tables help. A rule's reason stands beside it. Who reads the reply and what they can and cannot see are facts about the owner, in `mmw-v3/prompt/shared.md`, which every session carries with or without the mode. Anchored references are `principle-anchor-every-reference`'s. Close with the division of labour: each playbook's `**Reply:**` line names only what is unique to that playbook.
- **Sources in MMW v2:** rules 4, 5, 6 and 9 of `mmw-v2/prompt/shared.md`, with their reasons, and its closing section "What this file looks like when it is working", which becomes the reply's finish criterion. Where every unit of shared.md goes is in mmw-v3/course lesson 4, figure 4, and lesson 15, section 6.

### `## Comments`

- **Used:** while writing a code comment or any file's prose about the code.
- **Content:** one paragraph. A comment is kept only for a non-obvious why the code cannot show. That a file describes its subject now, never its own history, is `principle-files-describe-the-present`'s, and holds for comments too.
- **Source:** poteto-mode's `## Comments`. The code half of `mmw-v2/prompt/shared.md` rule 13 is in `principle-files-describe-the-present`.

### `## Playbooks`

- **Used:** at the start of a task, to choose its route.
- **Content, in this order:**
  1. Usage: match the task to a route line and open its playbook.
  2. One route line per playbook: ``**Name.** What task it is, and how it differs from the playbook most easily confused with it. `playbooks/<file>.md`.``
  3. One sentence for a session a script started: the playbook its start prompt names is its route, chosen by whoever dispatched it (`mmw-v3/course/` lesson 5, decision 3).
  4. One sentence for a task no route line matches (poteto-mode sends it to `figure-it-out`, which MMW does not carry).
- **When to add a line:** in the same change that adds the playbook file. Whether a playbook is warranted is in `playbooks/README.md`.
- **Sources in MMW v2:** the `## Find your moment` tables of the `dispatch`, `verify-ticket`, `design-pages`, `ui-acceptance` and `code-review` skills, and the numbered procedures they point to (`implement`'s `## Closing steps`, `dispatch`'s `references/night.md`).
