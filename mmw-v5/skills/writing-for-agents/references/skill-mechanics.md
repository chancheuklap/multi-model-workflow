# Skill mechanics

The skill-specific branch of [`writing-for-agents`](../SKILL.md): frontmatter and splitting by invocation. Everything else about writing it is the universal reference in `../SKILL.md`.

## Invocation

A **model-invoked** skill keeps a `description`, so the agent can fire it autonomously, and other skills can reach it. You can still type its name: model-invocation always _includes_ user reach; a description only ever adds agent discovery, never removes the human's. The description is the skill's top-level context pointer, forced to stay loaded at all times: permanent context load in exchange for discoverability. A model-invoked skill whose content is all reference is also one home for shared reference: another skill can invoke it, so reference needed by several skills lives in one place. Write a model-facing description carrying the trigger branches (the pointer-writing rules in `../SKILL.md` apply in full).

## Splitting by invocation

The invocation cut of splitting (the sequence cut lives in `../SKILL.md`): split off a model-invoked skill when you have a distinct leading word that should trigger it on its own (a trigger word you actually use in your prompts), or another skill must reach it. You pay context load for the new always-loaded description, so that independent reach has to be worth it.
