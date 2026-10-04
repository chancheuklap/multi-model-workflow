# mmw-v3/skills: the components and the method

MMW v3 is MMW rebuilt on pstack's architecture and in pstack's manner: the same kinds of component, each written the way pstack writes it, filled with what MMW does. pstack is in `mmw-v3/upstream-pstack/` (cursor/plugins `e43c7ee`, pstack 0.15.9). MMW v2, the live version, is in `mmw-v2/` and is the main source of content. The course that explains all of this, with the evidence, is `mmw-v3/course/` (lessons 1 to 3, and `reference/pstack-anatomy.html`).

Read this file before writing or moving anything into v3, and again whenever a placement is in doubt. Each component directory has a README with the specifics of that component.

## The components and where they live

| Component | Where | Answers | Guide |
| --- | --- | --- | --- |
| mode skill | `mmw-mode/SKILL.md` | The owner's way of working: what to use when, which playbook a task follows | `mmw-mode/README.md` |
| playbook | `mmw-mode/playbooks/<name>.md` | How one kind of task is done, start to end | `mmw-mode/playbooks/README.md` |
| principle | `principle-<slug>/SKILL.md` | How to decide when a certain situation arises | this file, below |
| skill | `<name>/SKILL.md` | How one thing is done, and what it hands back | this file, below |
| reference | `<skill>/references/<file>.md` | Material one step needs | `mmw-mode/references/README.md` |
| script | `<skill>/scripts/<file>` | The part a program can do or check | `mmw-mode/scripts/README.md` |
| subagent | none yet | Who a spawned agent is and what it reads first | this file, below |
| configuration | outside the skills (`~/.mmw/models.json`) | Which model each role runs on | this file, below |

## The method

These hold for every component. They come from how pstack itself adds and changes components (course lesson 2) and from what went wrong in the two earlier attempts.

1. **Imitate pstack in content, not only in shape.** Before writing a component, read the pstack component of the same kind that does the closest job. Where a pstack text already covers what MMW needs (a principle, a section of poteto-mode, a skill), start from that text and merge MMW's specifics into it. A file with pstack's headings and MMW's old text under them is not a migration.
2. **Compare before you choose; pstack is not the default winner.** When v2 and pstack each have a component doing the same job, read both in full and keep the one that does more, or keep both when they do different jobs. Several v2 skills do more than their pstack counterpart (`wait-what` over `bro`, `writing-for-agents` in the place of Cursor's `create-skill`, `grilling`, which pstack has no counterpart for). The comparisons made so far are in `mmw-v3/course/` lesson 4, figure 3; where every rule of `shared.md`, and every communication rule only pstack has, goes is in figures 4 and 5.
3. **Place each piece of text by these questions, not by what type of text it looks like.** Who needs it, at which moment? How many places use it? Does it change a decision? Can a mechanism (a script, a check, a hook already in v2) enforce it? The two earlier attempts placed text by type ("move each passage to the layer its type belongs to") and produced one situation with two different actions in two places (#880), the same rule written twice (#884) and references to things that had moved (#885).
4. **The default is to edit an existing home or to delete, not to create.** A new component needs all three: "no existing skill is a real home, the pattern recurs, and the topic deserves its own skill" (pstack `reflect`). "When in doubt, delete. Keep only prose that changes a decision." (pstack `authoring-a-skill.md`).
5. **What can be a check is not written as prose.** Order of preference: architecture, types, a lint or check whose error names the fix, a test, and prose last (pstack `correct`). "Skill prose is for things mechanisms cannot enforce" (pstack `reflect`).
6. **One rule, one place.** When a rule moves, every place that named it is updated in the same change: the mode's lines, playbook steps, other skills, and the prompts `mmw-v2` scripts build for agents.
7. **Register in the same change.** A new playbook gets its route line in `mmw-mode/SKILL.md` `## Playbooks`; a new principle gets its index line in `## Principles`; a reference or script gets named, with its path or command, by the step that uses it.
8. **What pstack does not say is labelled.** pstack has no written rule for some decisions (when a new playbook is warranted, for one). A placement that rests on an inference from pstack's examples says so, and goes to the owner.

## principle

- **For:** one judgement that many tasks need. "One-off -> brain note. Recurring fix -> skill or lint rule. Systemic issue -> principle." (pstack `principle-encode-lessons-in-structure`). In pstack every principle is named by at least two files besides the mode's index.
- **Not for:** a judgement only one playbook needs (it stays in that playbook's step), or a repeated mistake a script can stop.
- **Loading:** the mode's `## Principles` holds one line per principle and is always in context once the mode loads; the full text is read only when the condition arises. This is how a rule loads at the moment it applies, without a hook.
- **Shape** (models: `mmw-v3/upstream-pstack/skills/principle-*/SKILL.md`):
  - Frontmatter: `name: principle-<slug>`; `description` begins "Apply when", states the condition, then the rule.
  - `# <Title>` and the rule in one or two sentences.
  - `**Why:**` one sentence.
  - The checkable practice, one point per bullet, under a label such as `**Pattern:**`, `**Rule:**` or `**The test:**`.
  - `**Stop:**` when to stop going further, where it applies.
  - A closing line separating it from the principle most easily confused with it, linking to that one.
- **Register:** its line in `mmw-mode/SKILL.md` `## Principles`, and its name on every step where it applies.
- **Main source in MMW v2:** the numbered rules of `mmw-v2/prompt/shared.md`, which is the source of `~/.claude/CLAUDE.md` and of the generated `AGENTS.md` files for Codex, Pi and Grok.

## skill

- **For:** one thing that recurs and that nothing else handles. "A workflow you keep hitting but isn't captured → propose a new skill." It is either used by many steps, or worth invoking directly.
- **Not for:** what an existing skill can hold. Edit that skill.
- **Invocation:** only `mmw-mode` sets `disable-model-invocation: true`. Every other skill, principles included, can be invoked by the model. A skill that should not be invoked on its own gets a description with no specific trigger phrases, or one that says not to invoke it on its own.
- **Shape** (models: `swarm`, `how`, `figure-it-out` under `mmw-v3/upstream-pstack/skills/`):
  - Frontmatter: `name`, `description` (what it does, then `Use for …` with the words someone would use).
  - `# <Title>` and one paragraph: what it does and what it hands back.
  - When it spawns subagents, one paragraph naming each subagent's role in `~/.mmw/models.json` and the default when the role is absent.
  - `## Start`: open a todolist with one item per phase.
  - The phases or steps; a step that needs a template names `references/<file>`.
  - What it hands back, and in what form.
- **Main source in MMW v2:** v2's skills under `mmw-v2/skills/` and the changed upstream skills under `mmw-v2/upstream/skills/`, each with a merge-note in `mmw-v2/merge-notes/`.

## subagent

- **For:** a role that must start with the same prompt every time it is spawned. pstack's `poteto-agent` exists because a general subagent skips reading the mode: "Substituting `generalPurpose` skips that read and drifts."
- **Not for:** a single-purpose job done in one go; that is a skill.
- No subagent directory exists yet. Whether MMW gets one (for agents it spawns to load `mmw-mode` first) is a decision for the owner.

## configuration

- **For:** a choice that differs per person or machine and must hold in every session, such as the model for each role. Every skill keeps its own default, so nothing breaks without the configuration.
- **Not for:** text in the mode or a skill.
- MMW's is `~/.mmw/models.json`, changed only through `models.py`.
