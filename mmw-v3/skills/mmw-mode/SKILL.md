---
name: mmw-mode
description: MMW's way of working on the owner's products. Use for /mmw-mode, or requests to work in this mode.
disable-model-invocation: true
---

<!--
Authoring guide for this file. Each section below carries its own guide in a comment like
this one. A section's content is written below its comment, and every comment stays until
the whole migration to v3 is complete. The same guide is in README.md beside this file.
The method every component follows is in ../README.md. The model to imitate, in content
as well as shape, is mmw-v3/upstream-pstack/skills/poteto-mode/SKILL.md.

Sections are divided by the moment they are used, not by topic: choosing a route at the
start of a task, a situation arising mid-task, deciding whether to ask the owner, spawning
a subagent, writing the reply, writing a code comment. The mode mostly names things and
says little about how to do them: a trigger names a skill, an index line names a
principle, a route line names a playbook. It carries full text only for what holds on
every task and has no other home: Autonomy, Subagents, Writing the reply, Comments.
"Cut ruthlessly. A mode skill is not a manual."
-->

# MMW mode

## Non-negotiables

<!--
Used: at any moment of any task, as soon as the situation a line names arises, whichever
playbook is running.

Content: one opening paragraph saying that the Principles section grounds every trigger,
and that the reply names each principle that shaped a decision and the choice it changed,
citing only principles whose full SKILL.md was read this session. Then one line per
trigger, in the form `Situation → what to use`, where what to use is a skill, a playbook
(with its path), a principle or a reference. A line names; it does not explain how. The
exception is a judgement that must be made on the spot, which is written into the line
(poteto-mode's "classify it before you ask" line).

Add a line when the situation can occur inside any playbook, so it cannot hang on one
step ("Before commit", "Any prose surface"). A situation that belongs to one step of one
playbook is written in that step instead.

Sources in MMW v2: rules of mmw-v2/prompt/shared.md that apply at a moment across tasks
(rule 7 → a prose skill; rule 14 → before proposing a design or non-trivial code), and
v2's own skills, compared one by one with their pstack counterparts before either is
kept: agent-facing prose → writing-for-agents (it takes the place poteto-mode gives
Cursor's create-skill); prose for people → technical-writing; any prose → unslop. The
comparison and its results are in mmw-v3/course lesson 4, figure 3.
-->

## Principles

<!--
Used: the index is read when the mode loads; a principle's full text is read only when
its condition arises and it is applied.

Content: two sentences of usage ("Read the leaf skill in full for any principle you
apply. Each entry names when it applies."), then the index in named groups (poteto-mode:
Core, Architecture, Verification, Delegation, Meta). Each line holds three things:
`**Name** (**principle-<slug>**). Condition. One-sentence rule.` The full text lives in
mmw-v3/skills/principle-<slug>/SKILL.md, never here.

Add a line in the same change that adds the principle skill. A principle is warranted
when one judgement is needed across many tasks ("Systemic issue -> principle"); a
recurring fix goes to a skill or a check, and anything a script can enforce goes to a
script.

Sources in MMW v2: most numbered rules of mmw-v2/prompt/shared.md (8, 10, 12, 13, 14, 15,
and the "it compiles is not it works" half of 4). Where a pstack principle already covers
one (principle-prove-it-works, principle-never-block-on-the-human), start from the pstack
text and merge MMW's specifics into it.
-->

Read the leaf skill in full for any principle you apply. Each entry names when it applies.

**Core**

- **Start from What Exists** (**principle-start-from-what-exists**). Before proposing an approach or writing non-trivial code. Search for what already exists and read it, then use it, extend it, or build only after the search came back empty.

**Verification**

- **Prove It Works** (**principle-prove-it-works**). After a task, before declaring done. Verify against the real artifact, not a proxy or "it compiles".
- **Read Before You Conclude** (**principle-read-before-you-conclude**). Saying what a file says, or changing it. Read enough to be sure, and read a file whole before you edit it.
- **Run the Smallest Test Set** (**principle-run-the-smallest-test-set**). Choosing which tests to run. Run the smallest set that proves the change; a full suite needs a named reason.

**Delegation**

- **Never Block on the Human** (**principle-never-block-on-the-human**). Tempted to ask "should I do X?" on reversible work, or a step failed or was interrupted. Proceed, present the result, finish what failed yourself, and let the human course-correct.

**Writing**

- **Write for Where It Is Read** (**principle-write-for-where-it-is-read**). Before writing anything someone else reads or runs. Name who picks it up, what they are doing then, and what they can and cannot see.
- **Anchor Every Reference** (**principle-anchor-every-reference**). Mentioning a file, a section, a rule, or an event in a reply or a document. Name it by its path and its heading, identifier, or rule number, copied verbatim.
- **Files Describe the Present** (**principle-files-describe-the-present**). Writing or editing any file. Say what is true of its subject now; what changed goes in the commit message and the reply.

## Autonomy

<!--
Used: whenever the agent is deciding whether to act or to ask the owner first.

Content: four paragraphs, each opening in bold, as in poteto-mode:
- **Just do it.** What proceeds without asking: reversible work, engineering decisions.
- **Always pause** for what only the owner decides: what the customer sees, money, scope
  and order, what goes public, what cannot easily be undone.
- **Session overrides:** what the owner's words change ("going to bed", an approved plan
  or ticket is the go signal).
- **No is an acceptable answer.** Disagreement is owed when there is a flaw, never
  manufactured.

Sources in MMW v2: mmw-v2/prompt/shared.md rules 1, 2, 3 and 11.
-->

## Subagents

<!--
Used: before spawning any subagent.

Content: decided in mmw-v3/course lesson 5, from MMW v2's own subagent rules (for the
workers, reviewers and other agents it spawns). pstack's ## Subagents is compared with
them rule by rule; nothing in it is copied by default.

Sources in MMW v2: MMW's own subagent rules, listed in full in lesson 5, among them
mmw-v2/prompt/hosts/codex.md ("Never interrupt subagents…") and ~/.mmw/models.json,
which holds the model for each role and is changed through models.py.
-->

## Writing the reply

<!--
Used: while writing every reply.

Content: the rules every reply shares, one point per bullet, each stated as an action:
who reads the reply and what they can and cannot see; evidence or its label in the same
sentence; reasons and consequences rather than files and functions; plain standard
vocabulary; anchored references with names copied verbatim; when lists and tables help.

Sources in MMW v2: the reader facts at the top of mmw-v2/prompt/shared.md (condensed to
what changes a decision), its rules 4, 5, 6 and 9, and its closing section "What this
file looks like when it is working", which becomes the reply's finish criterion. Where
every unit of shared.md goes is in mmw-v3/course lesson 4, figure 4.
-->

## Comments

<!--
Used: while writing a code comment or any file's prose about the code.

Content: one paragraph. A comment is kept only for a non-obvious why the code cannot
show; a file describes its subject now, never its own history.

Source in MMW v2: the code half of mmw-v2/prompt/shared.md rule 13. Delete this section
if nothing in MMW belongs here.
-->

## Playbooks

<!--
Used: at the start of a task, to choose its route.

Content, in this order:
1. Usage: open a todolist whose first items are the matched playbook's steps copied in
   verbatim; a step not done stays in the list as `skip: <reason>`.
2. The routing exceptions: large, cross-cutting or step-away work, and work no playbook
   fits, route to figure-it-out, which designs a playbook for that one run.
3. One route line per playbook: `**Name.** What task it is, and how it differs from the
   playbook most easily confused with it. `playbooks/<file>.md`.`

Add a route line in the same change that adds the playbook file. How to judge whether a
playbook is warranted is in playbooks/README.md.

Sources in MMW v2: the `## Find your moment` tables of the dispatch, verify-ticket,
design-pages, ui-acceptance and code-review skills, and the numbered procedures they point
to (implement's `## Closing steps`, dispatch's references/night.md).
-->

- **Authoring or modifying a skill.** Writing or editing a skill, a playbook, a principle, a reference or this mode. `playbooks/authoring-or-modifying-a-skill.md`.
- **Review the skill set.** Reviewing the text of the whole skill set, or of some of its skills, by walking the tasks agents do with it ("review the skills", "audit the skill set"). Distinct from `playbooks/authoring-or-modifying-a-skill.md`, which changes the text. `playbooks/review-the-skill-set.md`.
