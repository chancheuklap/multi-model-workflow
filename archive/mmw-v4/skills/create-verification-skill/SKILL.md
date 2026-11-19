---
name: create-verification-skill
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Create a verification skill

A coding agent that changes an app should be able to prove the change the
way a user would see it. This skill writes that proof recipe for one
project as a skill, `.agents/skills/verify-<product>/`, built on e2e. The
config launches the app, fixed-step tests pin what must hold, and
`.e2e/` keeps the evidence. Write
the output for the next agent, not for a human. It will be read cold,
mid-task, by an agent that has never seen the app.

Keep the caller's product, scope, checkout, branch and authority. Reuse adequate existing methods and matching proof. A call for one result returns to its original step.

| Work in hand | Read |
| --- | --- |
| Supply missing local tools for the current prototype | [Prepare environment](references/prepare-environment.md) |
| Establish or extend the reusable product verification skill | [Generate and prove](references/generate.md) |
| Read the feature format or record a settled feature description | [Record the feature map](references/feature-map.md) |

Generation returns the actual project-local SKILL.md, config, feature map, tests, complete command, evidence and any pending product proof. The generated method is first used to prepare its proving test, then followed before handoff. Later acceptance preparation, workers and delivery use that returned method rather than generating it again.
