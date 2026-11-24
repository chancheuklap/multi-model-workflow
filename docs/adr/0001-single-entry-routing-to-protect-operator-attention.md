---
status: accepted
---

# Single-entry routing protects operator attention

`mmwstack` bundles dozens of specialized skills and playbooks. Expecting the operator to remember skill names, tell close cousins apart (such as `reframe` and `sharpen`, or `ketchup` and `recall`), and choose a workflow before writing a prompt taxes working memory and interrupts the thought itself.

We route operator requests through two front-door skills instead of exposing a flat catalog of mandatory commands.

1. [mmw-mode](../../mmwstack/skills/mmw-mode/SKILL.md) is the single entry for **doing work**. The operator states the goal and finish condition in plain words. The main chat matches a playbook and invokes leaf skills when its steps need them.
2. [bro](../../mmwstack/skills/bro/SKILL.md) is the single entry for **aligning understanding and preparing prompts**. The operator types `/bro` alone to hear their goal and the agent's last reply in plain words, or types `/bro` followed by a plain-language request and lets the agent route to the narrowest matching clarity skill (such as `ketchup`, `ketchup-video`, `recall`, `teach`, `big-pics-little-words`, `reframe`, or `sharpen`).

Leaf skills stay directly callable for explicit overrides and for internal calls from playbooks or other skills. Direct invocation is an escape hatch, never a prerequisite for getting the right method.

## Considered options

- **Flat slash-command catalog (upstream pstack default).** Users learn and invoke `/reframe`, `/sharpen`, `/in-your-own-words`, `/ketchup`, `/recall`, `/teach`, and `/bro` individually. Rejected because tool selection shifts routing work onto the human and breaks focus before the prompt is even sent.
- **One monolithic clarity skill.** Merging all clarity and prompt-prep instructions into `bro` removes routing, but it bloats context load on every call and prevents playbooks or other skills from invoking focused leaves independently. Rejected under [writing-for-agents](../../mmwstack/skills/writing-for-agents/SKILL.md) progressive disclosure and invocation splitting.
- **Two front-door routers (`mmw-mode` for work, `bro` for understanding) dispatching to focused leaf skills (chosen).** Protects operator attention while keeping leaf skills modular, reusable, and loaded on demand.

## Consequences

- Every new clarity, explanation, catch-up, or prompt-preparation skill added to `mmwstack` must be evaluated for routing under `bro` instead of shipping only as a standalone slash command.
- `bro` owns clear intent-routing and close-call disambiguation rules so plain operator phrasing lands on the right leaf skill without requiring the operator to echo that skill's jargon.
- When syncing upstream skills that set `disable-model-invocation: true`, `mmwstack` removes that flag unless strict manual isolation is required, so front-door routers and playbooks can dispatch to them.
- New workflow capabilities default to fitting inside an existing `mmw-mode` playbook or `bro` route before justifying a new operator-facing entry point.
