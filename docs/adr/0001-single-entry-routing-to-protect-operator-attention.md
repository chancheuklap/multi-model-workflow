---
status: accepted
---

# Single-entry routing protects operator attention

`mmwstack` bundles dozens of specialized skills and playbooks. Expecting the operator to remember skill names, tell close cousins apart (such as `reframe` and `sharpen`, or `ketchup` and `recall`), and choose a workflow before writing a prompt taxes working memory and interrupts the thought itself.

We route operator requests through three front-door skills instead of exposing a flat catalog of mandatory commands.

1. [mmw-mode](../../mmwstack/skills/mmw-mode/SKILL.md) is the single entry for **doing work**. The operator states the goal and finish condition in plain words. The main chat matches a playbook and invokes leaf skills when its steps need them.
2. [bro](../../mmwstack/skills/bro/SKILL.md) is the single entry for **aligning understanding and preparing prompts**. Bare `/bro` restates the operator's goal and clarifies the prior reply plainly (subsuming the retired `in-your-own-words` skill). `/bro` followed by a plain-language ask routes to the matching clarity skill (`ketchup`, `ketchup-video`, `recall`, `teach`, `big-pics-little-words`, `reframe`, or `sharpen`) and reads its `SKILL.md` in full.
3. [big-pics-little-words](../../mmwstack/skills/big-pics-little-words/SKILL.md) is the single implicit entry for **standalone HTML artifacts and visual explanations** (diagrams, plans, reports, explainers, wireframes, mockups, and prototypes). It holds the shared visual, flowchart, legend, and delivery defaults, then delegates rendering and specialist selection to [html](../../mmwstack/skills/html/SKILL.md). Specialized-format HTML owned by another skill (such as `make-bot-ui` or `improve-codebase-architecture`) stays with that skill.

Leaf skills stay directly callable for explicit overrides and for internal calls from playbooks or other skills. Direct invocation is an escape hatch, never a prerequisite for getting the right method.

## Considered options

- **Flat slash-command catalog (upstream pstack default).** Users learn and invoke `/reframe`, `/sharpen`, `/in-your-own-words`, `/ketchup`, `/recall`, `/teach`, `/html`, and `/bro` individually. Rejected because tool selection shifts routing work onto the human and breaks focus before the prompt is even sent.
- **One monolithic skill per domain.** Merging all clarity instructions into `bro` or all HTML specialist instructions into `big-pics-little-words` bloats context load on every call and prevents playbooks or other skills from invoking focused leaves independently. Rejected under [writing-for-agents](../../mmwstack/skills/writing-for-agents/SKILL.md) progressive disclosure and invocation splitting.
- **Front-door routers (`mmw-mode` for work, `bro` for understanding, `big-pics-little-words` for general HTML) dispatching to focused leaf skills (chosen).** Protects operator attention while keeping leaf skills modular, reusable, and loaded on demand.

## Consequences

- Every new clarity, explanation, catch-up, or prompt-preparation skill added to `mmwstack` must be evaluated for routing under `bro` instead of shipping only as a standalone slash command.
- General HTML and diagram craft rules live in `big-pics-little-words` and `html` (and its specialists), not duplicated in persistent agent instruction files like `AGENTS.md`.
- Overlapping leaf skills that a front door already covers (such as `in-your-own-words` inside `bro`) are retired rather than kept as parallel commands.
- When syncing upstream skills that set `disable-model-invocation: true`, `mmwstack` removes that flag unless strict manual isolation is required, so front-door routers and playbooks can dispatch to them.
- New workflow capabilities default to fitting inside an existing `mmw-mode` playbook, `bro` route, or `big-pics-little-words` delegation before justifying a new operator-facing entry point.
