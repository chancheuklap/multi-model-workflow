# Make it yours

[mmw-mode](../../skills/mmw-mode/SKILL.md) is one person's style. The playbooks, routing, and model roles underneath it work just as well with yours. This page covers generating a personal mode, capturing lessons from a session, fixing the repo so agents stop repeating mistakes, authoring a focused skill, and testing a skill change before you trust it.

Start smaller than you think. You don't need many skills on day one, or even this whole plugin. Prompt plainly, watch where agents fail, and add a skill or a check when the same failure shows up twice.

## Generate your own mode with [automate-me](../../skills/automate-me/SKILL.md)

```text
/automate-me
```

You don't describe your style, because [automate-me](../../skills/automate-me/SKILL.md) reads it out of your history. It mines your recent transcripts in the active workspace for repeated preferences, in how you like replies, delegation, verification, code, prose, and process, then asks you which patterns are really you. It drafts `<your-name>-mode/SKILL.md` in your project's skills directory with the bundled [create-skill](../../skills/create-skill/SKILL.md) and [writing-for-agents](../../skills/writing-for-agents/SKILL.md) skills, runs the draft through [unslop](../../skills/unslop/SKILL.md), and opens a PR from a worktree so you review it like any other change.

Run it again whenever your habits drift:

```text
/automate-me update my mode skill with everything since its last edit
```

Update mode mines only the history since the skill last changed. It keeps rules you haven't contradicted, revises the ones with new evidence, and adds sections only for new patterns.

## Fix the environment with [correct](../../skills/correct/SKILL.md)

When agents repeat a mistake or struggle through a session, route the fix to the highest level of enforcement that works instead of repeating yourself in chat:

1. Make the mistake impossible with architecture or a better data structure.
2. Block it with types, or with a lint or CI check whose error names the fix.
3. Catch it with a behavioral test.
4. Write it down last, as a review standard, a skill edit, or a navigation pointer, only for genuine judgment calls.

Human review is not on the list. A reviewer who must catch the same mistake on every PR is the problem this fixes. [correct](../../skills/correct/SKILL.md) handles both repository environment improvements and durable skill edits from one entry point:

```text
/correct agents keep calling the database client directly instead of going through the repository layer
```

For repeated repository mistakes, [correct](../../skills/correct/SKILL.md) reads recent commits, reverts, review comments, and workaround comments, groups repeated errors into mistake classes (two or more occurrences), fixes the most frequent classes one commit each, and proves each new check fails on a real past mistake. It keeps a rule table pairing each rule with what enforces it in a dedicated repository standards or rules doc, linked by a single navigation pointer in `AGENTS.md` or `CLAUDE.md`, so an unenforced rule that breaks again escalates immediately.

For a rough session, ask for a retro or tell it to reflect lessons into skills:

```text
/correct retro on this session. capture durable lessons in skills or repo checks.
```

In a session retro, [correct](../../skills/correct/SKILL.md) reads the transcript and audits both repository environment friction (navigation pointers, unwired or missing guardrails, coding standards, bloated agent instruction files, tool economy, no-ops, and information access) and existing skills (six-month durability filter, body edits, and missed-trigger description tuning). Anything a check can enforce routes as a repository improvement candidate rather than skill prose. Single-session candidates and all skill edits wait for your approval before anything changes.

Pair [correct](../../skills/correct/SKILL.md) with [architect](../../skills/architect/SKILL.md) when the fix is a new boundary. Use [repo-checks](../../skills/repo-checks/SKILL.md) when the change is installing or maintaining `.agents/checks.json` and repository hooks. [Run many projects in parallel](./07-overnight.md#run-many-projects-in-parallel) has a prompt that runs [correct](../../skills/correct/SKILL.md) and [architect](../../skills/architect/SKILL.md) across a whole repo.

## Author a focused skill

When you already know the workflow you want to capture:

```text
/mmw-mode write a skill for verifying database migrations in this repo
```

Writing a skill matches the [Authoring or modifying a skill playbook](../../skills/mmw-mode/playbooks/authoring-a-skill.md), which uses the bundled [writing-for-agents](../../skills/writing-for-agents/SKILL.md) and [create-skill](../../skills/create-skill/SKILL.md) skills, validates the frontmatter and links, and ships the result through the Opening a PR playbook. Agent-facing prose has a higher bar than human prose, because an unhelpful sentence becomes an instruction some future agent follows. Let the playbook hold that bar rather than writing a `SKILL.md` freehand.

Two special cases have their own generators. A skill that must drive your app and prove behavior is a verification skill, so use [create-verification-skill](../../skills/create-verification-skill/SKILL.md) and [maintain-verification-skill](../../skills/maintain-verification-skill/SKILL.md) instead. A skill that checks a property of your code with a model checker, a proof, or another verifier is a formal verification skill, so use [create-formal-verification-skill](../../skills/create-formal-verification-skill/SKILL.md) and [maintain-formal-verification-skill](../../skills/maintain-formal-verification-skill/SKILL.md). [Verify and ship](./06-verify-and-ship.md#prove-a-property-with-a-formal-verification-skill) covers both kinds.

## Write docs to a standard with [technical-writing](../../skills/technical-writing/SKILL.md)

Skills aren't the only prose you ship. For docs, RFCs, readmes, PR descriptions, and commit messages:

```text
/technical-writing review the readme changes
```

[technical-writing](../../skills/technical-writing/SKILL.md) applies a layered standard. Its goal is prose that a tired engineer understands on the first read. It picks the document's mode first (tutorial, how-to, reference, or explanation), then works sentence by sentence: who does what, one thought per sentence, nothing readable two ways. Use it to review what you or an agent just wrote, or name it up front when you ask for a doc.

## Test a skill change blind

A skill edit affects every future session, so test it like the experiment it is. The same goes for adopting someone else's skill. Check that it makes the agent better on your work before you keep it.

```text
/mmw-mode run the eval playbook on this skill change. same task for both variants, candidates stay blind.
```

When a skill keeps missing and you know what it should do, change and test it in one task:

```text
/mmw-mode update the review skill so it flags missing migrations, and eval the change.
```

Asking for the eval up front keeps the edit honest. A fix written from one bad session tends to overfit that session, and over many edits the skill drifts. The eval catches the drift before it ships.

The [Eval playbook](../../skills/mmw-mode/playbooks/eval.md) is built around one failure mode, the observer effect. An agent that knows it's being evaluated behaves differently. So candidate agents get an organic-looking task in sanitized directories, never the words "eval" or "candidate", and never each other's existence. One judge scores all outputs under neutral labels, and chain-following gets graded from which files each candidate actually read, not from what it claims.

Read every output yourself before accepting the verdict. If you disagree with the judge, suspect the rubric before you suspect your judgment.

## Build a bot UI with [make-bot-ui](../../skills/make-bot-ui/SKILL.md)

One situational skill is for Grok Bot users. [make-bot-ui](../../skills/make-bot-ui/SKILL.md) builds a small page whose buttons wake a bot over a webhook routine. For example, you could swipe through a review queue and have each swipe ask the bot to act on that item. A server on your machine holds the webhook's sender key, so the key never reaches the browser or the chat. The skill also covers exposing the page on Tailscale.

**Pitfall:** don't edit a skill mid-task because it's misbehaving. Fix it in its own PR and keep the task moving. A skill edit that ships tangled into feature work is invisible to review and impossible to evaluate.

Next: [Recipes and pitfalls](./10-recipes-and-pitfalls.md).
