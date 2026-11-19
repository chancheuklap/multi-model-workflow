# Set up mmwstack

In this page you install the plugin, pick which models mmwstack uses, and run your first task. Model setup takes one short conversation.

## Install the plugin

Install this copy with the local plugin or skill installation your environment provides. Keep the bundle together so relative links resolve. For project installs, expose the bundled `agents/` directory through `.claude/agents/` for Claude Code or `.cursor/agents/` for Cursor. For Codex, register each bundled agent by name in `.codex/agents/<name>.toml`. Embed the complete role instructions in `developer_instructions` and resolve skill links relative to the checkout that supplies the installed skills. The Cursor plugin manifest already registers `agents/`. To use it directly, give your agent [mmw-mode](../../skills/mmw-mode/SKILL.md) and your task. In this guide, `/name` refers to the skill of that name in the bundle.

## Pick your models

Choose from the models your host can assign to each role (code delegates, judgment, the advisor, the review panels). Save your choices and reasoning budget in the current host's section of `~/.agents/mmwstack-models.md` or supply a different rule file.

The `large` budget requests `xhigh` reasoning. `unlimited` lifts each model to its highest tier, up to `max`. `medium` and `small` lower the reasoning and spend fewer tokens.

The same role can use a different model in another host.

On Factory Droid, choose `light`, `medium`, or `heavy` for each role and panel entry. Factory's tier settings supply the model and reasoning. Sync the project's native Droid registrations before launching a session, including when a different model rule changes the advisor or Comment Sicko tier. [Droid registration in setup-mmwstack](../../skills/setup-mmwstack/SKILL.md#5-write-the-rule)

You might be wondering what happens if you use Auto. Set a role to `inherit-parent` or `auto` to run it on the parent chat's model. Both values mean the same thing, and neither is a model slug. Each runner panel has two seats. The entries can name the same model or tier. Autopilot starts PR owners on `coder`. Autopilot and Shipping use `verifier` for independent PR checks. For a model race, choose a configured model for each arm.

## Accept the verification offers, or don't

If your project has neither a project-local `verify-<app>` for the target surface nor an existing harness, project setup offers once to generate one with [create-verification-skill](../../skills/create-verification-skill/SKILL.md).

Say yes and it writes `verify-<app>/` in the project's skills directory, a project-local skill that teaches agents to drive your app the way a user does. It proves the skill works once before handing it over. Say no and setup moves on. You can run [create-verification-skill](../../skills/create-verification-skill/SKILL.md) yourself any time. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers it in depth.

If you're new to mmwstack, say yes. An agent that can check its own work keeps going until the check passes. When no project skill covers the surface, agents use [verify-this](../../skills/verify-this/SKILL.md). Of everything in this guide, the verification skill pays off the most.

Then setup offers once to generate a formal verification skill with [create-formal-verification-skill](../../skills/create-formal-verification-skill/SKILL.md), unless the project already has one. Tests check the cases someone thought to write. A formal verification skill checks one key property of your code, such as "a job never runs twice at once", in every case within a stated scope. Say yes when your code has concurrency, retries, a state machine, or a parser, where a bug is costly and tests rarely reach the case that breaks. Otherwise say no, and run it later if that changes. [Verify and ship](./06-verify-and-ship.md#prove-a-property-with-a-formal-verification-skill) covers it.

A new task starts by opening or reusing a GitHub work issue, and follow-ups stay on the same work issue. For code delivery, the agent links each execution ticket with its corresponding PR. [mmw-mode](../../skills/mmw-mode/SKILL.md) does this for every task it routes. A skill you name directly skips the mode. In the persistent instructions loaded by both local and cloud sessions, require the same work issue rule and [mmw-mode's execution environment rule](../../skills/mmw-mode/SKILL.md#subagents) for direct skill calls.

After setup, start a new chat. The model rule applies to new sessions.

## Keep the cost in check

mmwstack spends extra tokens on subagents and review panels. That's the price of the rigor. To spend fewer:

- Pick a smaller reasoning budget or cheaper models. A strong model in the main chat with cheaper, faster models in the code roles is a good split.
- Set a role to `auto` or `inherit-parent` so it runs on the chat's own model.
- Use a less expensive assignment for either runner seat.
- Save [mmw-mode](../../skills/mmw-mode/SKILL.md) for work that needs rigor. A small, obvious edit doesn't.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
/mmw-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the todo list. Its first items are the matched playbook's steps copied in, the Feature playbook for this prompt.

From here you can type normal follow-ups. If you want the mode to stay active across turns, keep it in the session's persistent instructions. You can also name `/mmw-mode` at the start of each task.

Next: [Route work through `/mmw-mode`](./02-mmw-mode.md).
