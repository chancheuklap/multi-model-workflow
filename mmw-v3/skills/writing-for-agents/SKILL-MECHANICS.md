# Skill mechanics

The skill-specific branch of [`writing-for-agents`](SKILL.md): what changes when the document is a skill (frontmatter, invocation, and the mode as router). Everything else about writing it is the universal reference in `SKILL.md`.

## Invocation

Only the mode skill, `mmw-mode`, sets `disable-model-invocation: true`. The person starts it by typing its name, and from then on it names every other component at the moment that uses it.

Every other skill is **model-invoked**: the mode or another skill reaches it by name, and the person can still type it, since model-invocation always _includes_ user reach. Its `description` decides whether the agent also starts it on its own. A skill the agent should start on its own carries its trigger branches (the pointer-writing rules in `SKILL.md` apply in full). The description is the skill's top-level context pointer, loaded at all times: permanent context load in exchange for discoverability. A model-invoked skill whose content is all reference is the one home for reference several skills need: they name it, and it holds the reference once.

A skill the agent should not start on its own has one sentence as its whole description, the same for every such skill: `Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.` Whoever names it already knows what it does. A skill is in this group when its upstream kept it user-invoked for a reason that still holds.

## Splitting by invocation

The invocation cut of splitting (the sequence cut lives in `SKILL.md`): split off a model-invoked skill when you have a distinct leading word that should trigger it on its own (a trigger word you actually use in your prompts), or another skill must reach it. You pay context load for the new always-loaded description, so that independent reach has to be worth it.

## The mode as router

The cognitive load of many skills is carried by `mmw-mode`: its trigger lines, its principle index and its route lines name each component with the moment that uses it, so the person remembers one skill instead of many. Because the skills it names are model-invoked, a line in the mode makes the agent reach them, not only hints at them. A line in the mode names; the method stays in the skill it names.
