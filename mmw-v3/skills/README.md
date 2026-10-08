# mmw-v3/skills: the components and the method

MMW v3 is MMW rebuilt on pstack's architecture and in pstack's manner: the same kinds of component, each written the way pstack writes it, filled with what MMW does. pstack is in `mmw-v3/upstream-pstack/` (cursor/plugins `e43c7ee`, pstack 0.15.9); mattpocock's skills, which many v2 skills came from, are in `mmw-v3/upstream-mattpocock/` (mattpocock/skills `d81f3a1`). MMW v2, the previous generation, is in `mmw-v2/` and is the main source of content. The course that explains all of this, with the evidence, is `mmw-v3/course/` (lessons 1 to 3, and `reference/pstack-anatomy.html`).

The rules for placing and writing the set's text are the `writing-for-agents` skill's `SKILL-SET-COMPONENTS.md` and `SKILL-SET-RULES.md`.

## Where each component's text came from

### mode

#### `## Non-negotiables`

- **Sources in MMW v2:** rules of `mmw-v2/prompt/shared.md` that apply at a moment across tasks (rule 7 → a prose skill), and v2's own skills, compared one by one with their pstack counterparts before either is kept: agent-facing prose → `writing-for-agents` (it takes the place poteto-mode gives Cursor's `create-skill`); prose for people → `technical-writing`; any prose → `unslop`. The comparison and its results are in `mmw-v3/course/` lesson 4, figure 3. The `PRODUCT_RULES` sentence of `mmw-v2/skills/dispatch/scripts/dispatch.sh`, which every worker's start prompt carried → the `ui-acceptance` skill's five rules (lesson 5, decision 5). The `how` line is poteto-mode's own, brought in with the `how` skill (lesson 6, section 5). The `setup-mmw` line: a repository not set up is met in several playbooks and scripts, and only that skill sets one up (lesson 11). The `diagram-design` line: a page drawn for a person is met inside a discussion, Investigation and several playbooks, and without the line the host's own page guidance is what a session follows.

#### `## Principles`

- **Sources in MMW v2:** most numbered rules of `mmw-v2/prompt/shared.md` (8, 10, 12, 13, 14, 15, and the "it compiles is not it works" half of 4). Where a pstack principle already covers one (`principle-prove-it-works`, `principle-never-block-on-the-human`), start from the pstack text and merge MMW's specifics into it.

#### `## Autonomy`

- **Sources in MMW v2:** `mmw-v2/prompt/shared.md` rules 1, 2 and 3. Rule 11 is `principle-never-block-on-the-human`'s, whose index line is read at the same moment. From poteto-mode's "classify it before you ask" line, only the clause on facts found by running something; which calls are the owner's is the Always pause list. Unattended: the `AUTONOMOUS` sentence of `mmw-v2/skills/dispatch/scripts/dispatch.sh`, the scripted-session paragraph of `mmw-v2/prompt/shared.md`, and the first bullet of `implement`'s code-writing rules ("Put no question on the screen").

#### `## Subagents`

- **Sources in MMW v2:** `mmw-v2/prompt/hosts/codex.md` ("Never interrupt subagents or other agents while they are working"), `manage-agents-md` ("your host's general-purpose subagent, with no model named"), `code-review` `references/session.md` section 2, `to-tickets` ("Hold this turn until it returns"), `SKILL-SET-RULES.md` ("A subagent's brief states what it returns and its length"), ADR 0015. From poteto-mode's `## Subagents`, only "You own every subagent's work".

#### `## Writing the reply`

- **Sources in MMW v2:** rules 4, 5, 6 and 9 of `mmw-v2/prompt/shared.md`, with their reasons, and its closing section "What this file looks like when it is working", which becomes the reply's finish criterion. Where every unit of shared.md goes is in mmw-v3/course lesson 4, figure 4, and lesson 15, section 6.

#### `## Comments`

- **Source:** poteto-mode's `## Comments`. The code half of `mmw-v2/prompt/shared.md` rule 13 is in `principle-files-describe-the-present`.

#### `## Playbooks`

- **Sources in MMW v2:** the `## Find your moment` tables of the `dispatch`, `verify-ticket`, `design-pages`, `ui-acceptance` and `code-review` skills, and the numbered procedures they point to (`implement`'s `## Closing steps`, `dispatch`'s `references/night.md`).

### playbook

**Sources in MMW v2:** Numbered procedures that already have this shape: `implement`'s `## Closing steps` (eight steps, each ending in "Done when"), `dispatch`'s `references/night.md` (sections 1 to 6), `dispatch`'s `references/one-ticket.md`, and the routing rows of the `## Find your moment` tables that point to them. Decide each one by the tests in the `writing-for-agents` skill's `SKILL-SET-COMPONENTS.md` `## playbook`, not by its current location.

### principle

- **Main source in MMW v2:** the numbered rules of `mmw-v2/prompt/shared.md`, which is the source of `~/.claude/CLAUDE.md` and of the generated `AGENTS.md` files for Codex, Pi and Grok.

### skill

- **Main source in MMW v2:** v2's skills under `mmw-v2/skills/` and the changed upstream skills under `mmw-v2/upstream/skills/`, each with a merge-note in `mmw-v2/merge-notes/`.

### reference

**Sources in MMW v2:** The `references/` files of v2's skills (for example `dispatch/references/inside-a-ticket.md`, `to-tickets/references/person-ticket.md`, `to-spec/references/revising-a-spec.md`). Many of them are numbered procedures, which may be playbooks instead; decide by the tests in the `writing-for-agents` skill's `SKILL-SET-COMPONENTS.md` `## playbook` and `## reference`.

### script

**Sources in MMW v2:** v2's programs already follow "scripts are tools; judgement belongs to the main agent" (ADR `0009`): `dispatch.sh`, `relay.py`, `watchdog.py`, `turn-guard.py`, `tool-guard.py`, `verify-ticket.py` and the rest. A rule that one of them already enforces is not written again as prose; the mode or a playbook names the program in one line at most.

### user-level prompt

- **Main source in MMW v2:** `mmw-v2/prompt/shared.md`, which reaches the hosts as `~/.claude/CLAUDE.md` and the generated `AGENTS.md` files. Where each of its rules went is in `mmw-v3/course/` lesson 4, figure 4; where its reader facts and the reasons beside its rules went is in lesson 15, section 6.
