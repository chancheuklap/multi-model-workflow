# references/: how a reference is written

Read `../../README.md` first: it holds the method every component follows. This file covers the files in a skill's `references/` directory. It applies to this directory, which belongs to the mode, and to the `references/` directory of any other skill.

The models to imitate: `mmw-v3/upstream-pstack/skills/how/references/explorer-prompt.md` (a prompt template) and `mmw-v3/upstream-pstack/skills/poteto-mode/references/bugbot-triage.md` (a lookup table).

## What a reference is for

Material that one step needs and the skill's main text does not: the prompt handed to a subagent, or a table consulted to make one kind of judgement. It is read when the step that names it runs, and not before.

A reference belongs to one skill and sits under it. There is no directory of references shared across skills. This directory holds what the mode's triggers and playbooks open.

## When a new reference is warranted

- **The material is used only on one branch, or only by one subagent.** `research` opens `references/explorer.md` or `references/investigator.md` only on the branch its brief calls for, and an investigator reads only the `references/sources/<source>.md` of its category.
- **Several playbooks or triggers open the same material.** That is still a reference. `bugbot-triage.md` is opened by four playbooks and one `## Non-negotiables` line.
- **Not for material every invocation uses.** That goes in the skill file itself: "Templates and references used on every invocation belong in the skill file, not in separate files that cost a read each time."

In the same change: the step or trigger that opens it names its path.

## The shape of the file

- **A prompt template:** a title, one or two sentences on what the template is and how to fill it, then the full prompt with placeholders in braces (`{QUESTION}`).
- **A lookup table:** a title, what judgement it serves, then the table or the decision rules.

## Sources in MMW v2

The `references/` files of v2's skills (for example `dispatch/references/inside-a-ticket.md`, `to-tickets/references/person-ticket.md`, `to-spec/references/revising-a-spec.md`). Many of them are numbered procedures, which may be playbooks instead; decide by the tests in `../playbooks/README.md` and above.
