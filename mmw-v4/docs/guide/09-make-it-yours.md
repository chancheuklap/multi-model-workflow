# Make it yours

The skill set is the owner's own: `mmw-mode` is one owner's way of working, and every skill under `mmw-v4/skills/` can be changed to fit how you work. This page covers changing a skill the way the set expects, the standards the change is held to, testing a change before you trust it, capturing what a session taught, and fixing a repository so agents stop repeating a mistake.

Start smaller than you think. Prompt plainly, watch where sessions go wrong, and change a skill or add a check when the same failure shows up twice.

## Change a skill through its playbook

Changing the skill set matches the Authoring or modifying a skill playbook ([authoring-a-skill.md](../../skills/mmw-mode/playbooks/authoring-a-skill.md)). It accepts your words, a registered problem or retrospective proposal, an upstream release, or a doubt about a part of the set:

```text
the bug fix playbook should tell the session to save the original repro command in the ticket. change it.
```

The playbook runs six steps:

1. **Open the ticket.** Record the source of the change and open its `fix-<n>` branch.
2. **Gather the evidence.** Your words prompt a search for the meaning in the set. If it already says what you asked for, the session tells you where and whether the installed checkout carries it, closes the ticket, and stops. A registration or proposal has its evidence checked on the project branch. An upstream release follows `UPSTREAM.md`. A doubt prompts a list of the text's tasks, a usage measurement with `scripts/usage.py`, and checks of the scoped passages. Each finding carries evidence you can open in a file committed on `fix-<n>`.
3. **Judge it against the design.** Name the intent each change serves. A conflict with an intent or a deliberate departure waits for your decision.
4. **Plan the fix.** Remove, merge, move or simplify before adding. Give each passage one component and file. Put a rule a script can check into a check, and preserve upstream text unless a design intent requires changing it.
5. **Write the ticket, by size.** A change one ticket can carry goes into that ticket. Its **Read first** names the section that governs each passage, so the worker and reviewer receive the same standards. A larger change goes through To spec and To tickets and runs as a night ([Run work while you sleep](./07-overnight.md)).
6. **Hand it back.** The session presents the plan. On your go, One ticket sends the worker, or To spec plans the larger change.

**Prove it, once** follows the worker's passing ticket, or your acceptance of a night and its completed `finish`. The session runs `scripts/check` and the suites a changed script needs. When the change alters what an agent does in a task, one fresh agent walks a real task on the changed text. A wording-only fix skips the walk. The walk's record is committed on `fix-<n>` and linked from the pull request. A missing required record, a wrong ending, a premature stop or a guess at a sentence the change wrote fails the check. Other guesses are findings for later. One ticket delivers one pull request, merged on your yes.

The playbook's bias is to delete: every sentence in a skill costs attention on every run that loads it, so answering each slip with one more sentence makes the skill worse.

A skill's body is live on the next call after the installed checkout moves on your release, because install links each skill directory rather than copying it. The running checkout stays frozen during a night. A changed frontmatter `description` takes effect in a new session after release, because a host reads it at session start. The repository's `AGENTS.md` `## Gotchas` holds the release steps.

## The standards: `writing-for-agents`

The [writing-for-agents](../../skills/writing-for-agents/SKILL.md) skill holds every standard a text in the set is written to. Its `SKILL.md` names the levers that make an agent take the same path every run:

- **Context pointers.** A skill's description, or a line naming a document, decides when an agent reaches the material behind it. Its wording, not its target, decides how reliably.
- **The two loads.** Context load is what always-loaded text costs the agent on every turn. Cognitive load is what the set costs the person who has to know which document exists.
- **Information hierarchy.** Steps the agent performs come first; reference it consults on demand sits below; reference only some branches need moves to a separate file behind a pointer.
- **Completion criteria.** Every step ends on a condition that tells done from not done, and the stronger the demand, the more thorough the work.
- **Leading words.** One familiar word, repeated, anchors a whole behaviour in fewer tokens than a sentence. State the behaviour you want, not the one you forbid.
- **Pruning.** One meaning lives in one place; a line that no longer changes behaviour goes.

Its other files apply those levers to this set:

| File | What it answers |
| --- | --- |
| [`SKILL-SET-RULES.md`](../../skills/writing-for-agents/SKILL-SET-RULES.md) | The checks every passage in the set is held to, and how to edit without breaking them |
| [`SKILL-SET-COMPONENTS.md`](../../skills/writing-for-agents/SKILL-SET-COMPONENTS.md) | Which component a text belongs in (the mode, a playbook, a principle, a skill, a reference, a script, the configuration, the user-level prompt), when a new one is warranted, and the shape of each |
| [`DESIGN-INTENTS.md`](../../skills/writing-for-agents/DESIGN-INTENTS.md) | What the set is built to keep true, and the deliberate departures from its upstreams. A change that breaks an intent waits for the owner's word |
| [`WALKING-A-SKILL-SET.md`](../../skills/writing-for-agents/WALKING-A-SKILL-SET.md) | How a fresh agent walks a real task to prove a change |
| [`SKILL-MECHANICS.md`](../../skills/writing-for-agents/SKILL-MECHANICS.md) | Frontmatter, invocation, and the mode as the router |
| [`UPSTREAM.md`](../../skills/writing-for-agents/UPSTREAM.md) | How to carry a newer upstream version, what Matt Pocock's skills and pstack each set out to do, and which MMW intents take them |

A skill that drives your app to prove behaviour is a verification skill. The `create-verification-skill` and `maintain-verification-skill` skills generate and keep it; [Verify and ship](./06-verify-and-ship.md) covers both.

## Write docs to a standard with `technical-writing`

Skills are not the only prose that ships. Docs, readmes and commit messages go through the [technical-writing](../../skills/technical-writing/SKILL.md) skill, then the [unslop](../../skills/unslop/SKILL.md) skill:

```text
/technical-writing review the readme changes
```

Its goal is prose a tired engineer understands on the first read. It cuts words that do no work, prefers the short everyday word, writes the real file or command name instead of a description of it, and reads each sentence for a second meaning. Pull requests use the [Opening a PR](../../skills/mmw-mode/playbooks/opening-a-pr.md) playbook's fixed record. Its summary sentence and your page follow the owner's reply rules and `unslop`.

## Test a skill change blind with the Eval playbook

A skill edit affects every later session, so test it as an experiment. The same holds before you adopt someone else's skill.

```text
run the eval playbook on this change to the bug fix playbook. same task for both variants, candidates stay blind.
```

The [Eval playbook](../../skills/mmw-mode/playbooks/eval.md) is built around one failure: an agent that knows it is being tested behaves differently. So candidates get an ordinary-looking task in directories with ordinary project names. No file or prompt they see says "eval", "candidate", "rubric" or "benchmark", and no candidate knows the others exist. The rubric of three to six criteria goes to the judge only. One judge, on a different model family, scores every output under neutral labels in one pass. Whether a candidate followed the chain of skills is graded from the files its transcript shows it opened and from the shape of its code, never from what it says it did.

Read every output yourself before accepting the verdict. If you disagree with the judge, suspect the rubric first.

Asking for the eval in the same request as the edit keeps the edit honest:

```text
change the code-review skill so its tests axis flags a test with no assertion, and eval the change.
```

A fix written from one bad session tends to fit that session only, and over many edits the skill drifts. The eval catches the drift before it ships.

## Register problems and review a run

When an agent finds a problem it cannot fix in its current work, the [register-problem](../../skills/register-problem/SKILL.md) skill records its evidence, cost and responsible repository. It looks for the same cause before opening an issue and preserves each new occurrence. A worker's in-ticket product problem stays in its child-issue workflow.

After a night or one ticket, the [Retrospective playbook](../../skills/mmw-mode/playbooks/retrospective.md) uses [retro](../../skills/retro/SKILL.md) to gather registrations and run signals. Independent analysts sort the material by judgment, environment and process. The sending session checks their evidence before applying the results. It reads events, issues and git, not transcripts.

You can also ask for a retrospective of a named run:

```text
review the problems registered during ticket #<n>. run the retrospective and recommend which proposals to pick.
```

The pull request's page presents each new proposal as a decision card with its problem, solution and recommendation. Earlier unanswered lessons get a count and query link; a problem that recurs after you refused it gets a reminder. Picking a proposal starts its planning playbook. Your later Go authorizes implementation. A retrospective failure is reported without blocking the merge.

## Fix the repository with `correct`

When you correct sessions for the same mistake again and again, the fix belongs in the repository, not in your next prompt:

```text
/correct agents keep calling the database client directly instead of going through the repository layer
```

The [correct](../../skills/correct/SKILL.md) skill reads recent commits, reverts, review comments and comments that explain workarounds, and groups the mistakes into classes. A class counts once it has happened twice. It plans each fix at the highest level that works:

1. Make the mistake impossible with architecture: one owner per piece of state, one supported way per task.
2. Block it with types, or with a lint or check whose error names the fix.
3. Catch it with a test.
4. Write a rule, last, and only for a judgement call, because nothing fails when an agent skips a rule.

It writes no fix itself. It writes the plan and its acceptance criteria into a ticket and hands it back to you, naming the check to add and the real past commit the check must first fail on; after your Go, a worker builds it. A rule goes into a principle, the glossary or an ADR, never into `AGENTS.md` or `CLAUDE.md`. A class whose rule is written down and enforced by nothing counts as a repeat. Started from a registered lesson, it counts that lesson's occurrences; named by you with no registration, it finds the classes from history on its own.

Retrospective proposes improvements for your decision; `correct` plans the change that keeps a class of mistake from coming back, for a worker to build.

## Where these skills assume Cursor

The Eval playbook keeps text written for Cursor and looks for transcripts in the workspace's `agent-transcripts/` directory, a path Cursor's system prompt names. This is the place to look first when Eval stalls on another host. Retrospective uses tracker and git evidence. `create-verification-skill` writes `verify-<product>` in the product repository's `.agents/skills/verify-<product>/`.

**Pitfall:** do not edit a skill mid-task because it misbehaves. The mode's Non-negotiables say to fix a broken skill in its own pull request and keep the task moving. A skill edit tangled into feature work is invisible to review and cannot be evaluated.

Next: [Recipes and pitfalls](./10-recipes-and-pitfalls.md).
