---
name: mmw-help
description: Guides users through mmwstack setup, /mmw-mode, and picking the skill, playbook, or principle for a task. Type /mmw-help with a question.
---

# MMW help

Answer the user's question about mmwstack, hand them a prompt they can send, and link the file the answer came from. For a help question, don't start the work. The user asked how, and an mmwstack run spends real tokens, so let them send the prompt.

A message that asks for work, such as "use mmwstack to fix this bug", is not a help question. Read [mmw-mode](../mmw-mode/SKILL.md), do the work under it, and mention persistent mode only if the user's host offers it.

This file maps questions to the skills and guide pages that hold the answers. Those files own the details. Read the file you route to before you quote it, and trust it when it disagrees with this map. Link the file you actually read. For a remote user, link the same revision in the source repository when available.

## Find out what they need

Infer the need from the message and the conversation. A named situation, such as "which skill reviews a PR?", goes straight to its section. If the need is still unclear, ask one multiple-choice question with these options, then answer only the section they pick:

- Get set up
- Start a task with [mmw-mode](../mmw-mode/SKILL.md)
- Pick a skill for a situation
- Fix a run that went wrong
- Make mmwstack my own

Check the state that changes the answer, and mention it only when it does:

- When the question depends on which model runs, read the assigned role in the current host's section in the supplied rule file or `~/.agents/mmwstack-models.md`. If the host section or role is missing, say which one.
- For proof of app behavior, use the project's `verify-<app>` for the target surface, or [verify-this](../verify-this/SKILL.md) if none matches. For a reusable project harness, point to [create-verification-skill](../create-verification-skill/SKILL.md).
- No formal verification skill in the project means no property is checked past what tests reach. Mention [create-formal-verification-skill](../create-formal-verification-skill/SKILL.md) when the question is about a race, an invariant, or another case tests rarely hit. When one exists and the code it covers changed after the commit it records as last in sync, mention [maintain-formal-verification-skill](../maintain-formal-verification-skill/SKILL.md) if the question touches that code.

## Get set up

1. Open the local skill or use your environment's local plugin or skill installation.
2. [Pick a reasoning budget and a model for each role](../../docs/guide/01-setup.md#pick-your-models), either by editing `~/.agents/mmwstack-models.md` directly or running optional [setup-mmwstack](../setup-mmwstack/SKILL.md). The rule applies to new chats.
3. Start a real task with [mmw-mode](../mmw-mode/SKILL.md), a goal, and a check that can pass or fail.

[to-spec](../to-spec/SKILL.md) and [to-tickets](../to-tickets/SKILL.md) can load from the user's words. The [README](../../README.md) and [guide page 1](../../docs/guide/01-setup.md) have the details. Offer to word their first prompt with them, per [`references/prompting.md`](references/prompting.md).

If cost is the worry, say where the tokens go and how to spend fewer. mmwstack spends extra tokens on subagents and review panels. Edit `~/.agents/mmwstack-models.md` or rerun [setup-mmwstack](../setup-mmwstack/SKILL.md) to pick a smaller budget or cheaper models. A role set to `auto` or `inherit-parent` runs on the chat's model, which saves tokens when the chat runs on Auto or a cheaper model. A shorter panel list runs fewer subagents, one for each entry. Save [mmw-mode](../mmw-mode/SKILL.md) for work that needs rigor.

## Start a task with [mmw-mode](../mmw-mode/SKILL.md)

[mmw-mode](../mmw-mode/SKILL.md) matches the task to a playbook, copies the playbook's steps into the todo list, and runs the other skills as the steps need them. A good prompt states the goal and how to tell it's done. It doesn't list skills, because a hand-written sequence tends to drop or reorder steps the playbook would keep. Read [`references/prompting.md`](references/prompting.md) before you help word one. [Guide page 2](../../docs/guide/02-mmw-mode.md) has examples.

For a whole conversation, keep the mode in the session's persistent instructions if available. You can also name `/mmw-mode` at the start of each task. Mid-chat, "new task" makes the mode match a fresh playbook. [mmw-mode](../mmw-mode/SKILL.md) already uses `mmw-agent` for the subagents its playbook steps spawn. To get the same style for your own delegation, spawn `mmw-agent`.

## Pick a skill

The default answer is [mmw-mode](../mmw-mode/SKILL.md), which runs most of the others when its steps need them. Name a skill directly when the user wants more or less of something than the playbook gives. Read the skill before you recommend it, and give one example prompt.

| The user wants to | Skill |
|---|---|
| Do any non-trivial task with rigor | [mmw-mode](../mmw-mode/SKILL.md) |
| Check that the agent understood their goal and the problem before it starts | [in-your-own-words](../in-your-own-words/SKILL.md) |
| Get a prompt rewritten deeper, not bigger, before sending it: what a top professional would add, their raw material and methods, and an outside check. It returns the prompt and doesn't do the task | [sharpen](../sharpen/SKILL.md) |
| Know how code works now, or where new code should live | [how](../how/SKILL.md) |
| Know why code is shaped this way, or where a number came from | [why](../why/SKILL.md) |
| Understand a change or subsystem, explained plainly | [teach](../teach/SKILL.md) |
| Catch up on their own recent work on a topic | [recall](../recall/SKILL.md) |
| Catch up on what changed in this chat since their last message, in plain words and small visuals, with every item waiting on them listed and decidable from the reply alone | [ketchup](../ketchup/SKILL.md) |
| Understand a subject through large visuals and the text needed to explain them | [big-pics-little-words](../big-pics-little-words/SKILL.md) |
| Create a self-contained HTML plan, report, wireframe, mockup, interactive prototype, or diagram | [html](../html/SKILL.md) |
| Catch up like [ketchup](../ketchup/SKILL.md), in a short subtitled video of slides, with the waiting calls as text under it | [ketchup-video](../ketchup-video/SKILL.md) |
| Know what a small diff could break outside itself | [blast-radius](../blast-radius/SKILL.md) |
| Settle types and module shape before code that crosses a function boundary | [architect](../architect/SKILL.md) |
| Look up interface depth, locality, seams, or the deletion test | [codebase-dic](../codebase-dic/SKILL.md) |
| Get several attempts at one brief, merged into the best one | [arena](../arena/SKILL.md) |
| Ask the advisor for an independent verdict before a major decision or when stuck | [advisor](../advisor/SKILL.md) |
| Review a finished project branch once, on three axes | [code-review](../code-review/SKILL.md) |
| Write the tests for code you are landing, failing-first for a bug | [write-tests](../write-tests/SKILL.md) |
| Apply TypeScript rules to `.ts` or `.tsx` work | [typescript-best-practices](../typescript-best-practices/SKILL.md) |
| Strip comments before review, using a reviewer that didn't write them | [no-comments](../no-comments/SKILL.md) |
| Clean AI tells out of prose | [unslop](../unslop/SKILL.md) |
| Write docs, an RFC, a README, a PR description, or a commit message to a standard | [technical-writing](../technical-writing/SKILL.md) |
| Write or edit a document an agent reads: a skill, `AGENTS.md`, `CLAUDE.md`, or a doc reached by a pointer | [writing-for-agents](../writing-for-agents/SKILL.md) |
| Walk them through steps only they can do (credentials, CI secrets, a third-party dashboard, a one-off cutover) with a generated bash script | [wizard](../wizard/SKILL.md) |
| Align understanding: have the agent restate their goal, then restate its last message in plain words. They say what they need and it hands off to the matching skill | [bro](../bro/SKILL.md) |
| Give agents a scripted way to drive the app and prove behavior | [create-verification-skill](../create-verification-skill/SKILL.md) |
| Bring a verification skill and its feature map back in line with the app | [maintain-verification-skill](../maintain-verification-skill/SKILL.md) |
| Formally verify a race, invariant, or other property that tests rarely reach | [create-formal-verification-skill](../create-formal-verification-skill/SKILL.md) |
| Bring a formal verification back in line after the code it covers changed, and learn whether a failure is drift or a bug | [maintain-formal-verification-skill](../maintain-formal-verification-skill/SKILL.md) |
| Build a Windows install package for an Electron and compiled Python product, or bring a new product into that system | [exe-release](../exe-release/SKILL.md) |
| Show a PM or designer what the user sees as a chart checked by a TLA+ model, with the shortest path to each state that breaks a rule | [statechart](../statechart/SKILL.md) |
| Vet a performance number before reporting or acting on it | [benchmark-checklist](../benchmark-checklist/SKILL.md) |
| Run a large or cross-cutting change, or one to review after stepping away | [figure-it-out](../figure-it-out/SKILL.md) |
| Keep a decision log during a run, and review it afterward | [show-me-your-work](../show-me-your-work/SKILL.md) |
| Discuss a design tree one decision at a time and update the project's glossary and ADRs inline | [grilling](../grilling/SKILL.md) |
| Settle the project's domain terms and record them in its glossary | [domain-modeling](../domain-modeling/SKILL.md) |
| Investigate a question against primary sources and return a cited report | [research](../research/SKILL.md) |
| Turn an existing discussion or a Wayfinder map into a published spec | [to-spec](../to-spec/SKILL.md) |
| Open or update a GitHub work issue, or draft execution tickets from a spec or plan | [to-tickets](../to-tickets/SKILL.md) |
| Pick a model for each role and a reasoning budget | [setup-mmwstack](../setup-mmwstack/SKILL.md) or [Pick your models](../../docs/guide/01-setup.md#pick-your-models) |
| Turn their own working habits into a personal mode skill | [automate-me](../automate-me/SKILL.md) |
| Stop agents from repeating mistakes in a repo, run a session retro, or turn session lessons into skill edits | [correct](../correct/SKILL.md) |
| Build a page whose buttons wake a Grok Bot over a webhook | [make-bot-ui](../make-bot-ui/SKILL.md) |
| Find their way around mmwstack | [mmw-help](SKILL.md) |

For a task the table does not cover, read the matching skill's frontmatter and route by its description. The `principle-*` directories are covered under principles below.

Close calls:

- [how](../how/SKILL.md) explains what the code does. [why](../why/SKILL.md) explains the reasons. [teach](../teach/SKILL.md) runs one or both and explains the result plainly.
- [arena](../arena/SKILL.md) gives each runner the same brief and merges the best parts. For parallel coverage, assign each agent its scope and collect the results.
- When a playbook hands the code to another agent, [architect](../architect/SKILL.md) returns the design to that playbook.
- [blast-radius](../blast-radius/SKILL.md) looks for breakage outside the diff and proves the one fact that makes the change safe. [code-review](../code-review/SKILL.md) checks a finished project branch once, on three axes, and the Code review playbook repairs it once.
- [recall](../recall/SKILL.md) rebuilds context across recent chats. [ketchup](../ketchup/SKILL.md) covers only this chat since the user's last message. Resuming one specific chat or branch is the Session pickup playbook.
- [bro](../bro/SKILL.md) is the one entry for aligning understanding. It hands off to [ketchup](../ketchup/SKILL.md), [ketchup-video](../ketchup-video/SKILL.md), [recall](../recall/SKILL.md), [teach](../teach/SKILL.md), [big-pics-little-words](../big-pics-little-words/SKILL.md), or [sharpen](../sharpen/SKILL.md) when the user's words call for one, and each still works on its own.
- [figure-it-out](../figure-it-out/SKILL.md) designs one rigorous run. The Autonomous run playbook drives one task to a finish condition.

Other skill providers:

- This copy lists its [bundled skill dependencies](../../README.md#bundled-skill-dependencies). Link the local files when the user asks about them.
- mmwstack has no `/orchestrate` skill. If the slash menu shows `/orchestrate`, another plugin provides it.

## Playbooks and principles

Playbooks are step lists inside [mmw-mode](../mmw-mode/SKILL.md), not skills, so they have no slash command. Inside [mmw-mode](../mmw-mode/SKILL.md), describing the task picks one, and these phrases name one directly:

- "babysit this pr" or "check on pr 123" runs Babysit. It drives the PR to merge-ready and stops there. It doesn't merge unless the user asks to merge, land, or ship.
- "use Wayfinder to map the open decisions" or "continue Wayfinder with this decision ticket" runs [Wayfinder](../mmw-mode/playbooks/wayfinder.md).
- "find modules worth deepening" runs [Improve codebase architecture](../mmw-mode/playbooks/improve-codebase-architecture.md). It compares opportunities in an HTML report and explores the opportunity you pick.
- "land the stack" runs Shipping.
- "build the installer" runs [Release an install package](../mmw-mode/playbooks/release-an-install-package.md). It builds a package for each product the change touched and stops for the user's install test. It builds no PR and lands none.
- "code review project/billing" runs [Code review](../mmw-mode/playbooks/code-review.md). It reviews a finished project branch once and fixes it once.
- "take over this branch" runs Session pickup.
- "pause safely" runs Pause safely.
- "full autopilot on this queue" runs Autopilot-full. "autopilot, don't merge" runs Autopilot-stack.
- "run the eval playbook" runs Eval.

The Playbooks section of [mmw-mode](../mmw-mode/SKILL.md) lists every playbook. [Guide page 6](../../docs/guide/06-verify-and-ship.md) covers opening, babysitting, and landing a PR.

For work across phases, ask [mmw-mode](../mmw-mode/SKILL.md) for a [multi-phase plan](../mmw-mode/playbooks/multi-phase-plan.md). To turn the checked plan into independently assignable tickets, ask for [to-tickets](../to-tickets/SKILL.md#split). On authorized execution, each code ticket gets its own linked PR. For a design question, the Prototype playbook or [architect](../architect/SKILL.md) settles it in code first.

Principles are one-rule skills that [mmw-mode](../mmw-mode/SKILL.md) reads and cites in its replies. The user rarely invokes one. They steer with the names instead, as in "apply prove it works. show me the real output." Typing `/principle-<name>` still loads one on demand. [Guide page 8](../../docs/guide/08-principles.md) lists them.

## Fix a run that went wrong

| Symptom | Fix |
|---|---|
| The mode stopped applying after a few turns | Start each task with [mmw-mode](../mmw-mode/SKILL.md), or use a persistent mode when available. |
| A question got treated as the next step of the last task | Say "new task", or say the turn doesn't need the mode. |
| A new model choice had no effect | Start a new chat. On Factory Droid, [sync the native registrations](../setup-mmwstack/SKILL.md#5-write-the-rule) before launch if a Factory tier binding or the `advisor` or `judgment and prose` tier changed. On Antigravity (AGY), confirm `## agy` uses exact IDs from `agy models` and `.agents/agents/` is synced for `scripts/agy-delegate`. |
| Runs cost more than expected | See the cost paragraph under Get set up. |
| A skill didn't load on its own | The agent picks a skill from its description. Name the skill, or use a playbook that calls it. |
| Parallel agents overwrote each other | Give concurrent writers separate worktrees. |
| An overnight run moved but finished nothing | The run needs a check that can pass or fail, not a duration. See [guide page 7](../../docs/guide/07-overnight.md). |
| The reply claims success from a green build | Ask for the real command, flow, stored value, or profile. That's the prove-it-works principle. |

For a run that drifts, [`references/prompting.md`](references/prompting.md) has one-line steers. [Guide page 10](../../docs/guide/10-recipes-and-pitfalls.md) has more pitfalls and the recipes worth copying.

## Make mmwstack my own

- [automate-me](../automate-me/SKILL.md) drafts a personal mode skill from the user's own history, to use alongside [mmw-mode](../mmw-mode/SKILL.md).
- [correct](../correct/SKILL.md) hardens a repo against repeated mistake classes, audits a session's environment friction, and turns durable session lessons into skill edits the operator approves.
- `/mmw-mode write a skill for <workflow>` runs the authoring playbook, which shapes the skill with [writing-for-agents](../writing-for-agents/SKILL.md) and drafts it with [create-skill](../create-skill/SKILL.md). The eval playbook tests a skill change blind.
- Fix a misbehaving skill in its own PR, not inside the feature work where it went wrong.

[Guide page 9](../../docs/guide/09-make-it-yours.md) covers each of these.

## Reply

Lead with the answer. Give at most one example prompt in a code block, adapted from [`references/recipes.md`](references/recipes.md) when one fits, then the link to that file. Keep it short unless the user asked for the whole map.
