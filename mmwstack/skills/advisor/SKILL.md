---
name: advisor
description: "Consult an independent advisor on major decisions or when stuck. Use only on /advisor, \"ask the advisor\", a second opinion from a stronger model, or advisor mode. Never start on your own."
---

# Advisor

The advisor is a fresh read-only agent. If the operator specifically requests a stronger model, check that the configured choice meets the request before dispatch. It reads your brief and the repository, returns a verdict and edits nothing. You keep doing the work and own the decision.

## When to consult

Consult only when the operator asks.

- "Ask the advisor ...", `/advisor <question>`, or a request for a second opinion from a stronger model is one consult now. The mode stays as it was.
- "Advisor on", or `/advisor` with no question, turns advisor mode on for this conversation. Consult at the checkpoints below until the operator says "advisor off". Keep the mode in the conversation. A session you start consults only when its brief says advisor mode is on.

Checkpoints:

1. **Before a major decision.** Choosing between architectures or approaches; changes that are hard to reverse or have a wide blast radius (schema or data migrations, deleting or rewriting a module, public API or config format changes, dependency swaps, auth, payments, or other security-sensitive code); or a request ambiguous in a way that would change the work materially. Consult once you have a concrete plan and the options in hand, not before you understand the problem. One consult covers the plan, so skip a consult per file.
2. **When stuck.** The same error or failing test after two genuine fix attempts; behavior you cannot explain from the code; or when you are about to reach for a workaround: a retry loop, a `sleep`, a broad `try/except`, skipping a test, or disabling a check to get past something.

Each consult starts a separate agent. Go on without one when reading the sources or a small check settles the question, or when no answer would change your next action. If a task needs more than about four consults, split the task or ask the operator.

## How to consult

1. Write the brief from the [briefing template](references/briefing-template.md).
2. Start a fresh read-only `advisor` with the brief. Follow [Subagents](../mmw-mode/SKILL.md#subagents). Use the model and settings from the current host's `advisor` entry in `~/.agents/mmwstack-models.md` (or the supplied rule file). Do not restate its rules. Continue independent work while it runs, and wait for the verdict before you act on the decision.
3. When the advisor asks for missing input, supply it once by resuming the advisor (a fresh one with the input added when the host cannot resume). Give a later checkpoint a fresh advisor.
4. Act on the verdict.
   - `proceed`: go.
   - `proceed with changes`: make the changes unless they conflict with the operator's instructions or facts you have verified. Say which you skipped and why.
   - `stop`: leave the plan. Rethink it, or bring the disagreement to the operator when it is a product or scope question.
   - The advisor is a strong second opinion, so you stay accountable for the result. When it is wrong about the codebase, show it the evidence once, or overrule it and tell the operator why. A missing verdict is not agreement.
   - Keep approved baselines and authorization fixed. Pass a `For the operator` section to the operator as it stands.
5. Report each consult in one or two lines: `Advisor: <verdict>. <one-line summary>. <what you did about it>.` Keep the full response out of the chat unless the operator asks. Record the verdict and what you did with it on the work issue, per [to-tickets](../to-tickets/SKILL.md#update).

Done when you have acted on the verdict, or told the operator why the consult could not complete.

## Guardrails

- The advisor is read-only. Ask it for a verdict and leave the task and every edit to yourself.
- Ask at most one follow-up per checkpoint.
- When the `advisor` role is unfilled, tell the operator once and continue without it.
