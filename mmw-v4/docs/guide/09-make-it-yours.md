# Make it yours

The skill set is the owner's own: `mmw-mode` is one owner's way of working, and every skill under `mmw-v4/skills/` can be changed to fit how you work. This page covers changing a skill the way the set expects, the standards the change is held to, testing a change before you trust it, capturing what a session taught, and fixing a repository so agents stop repeating a mistake.

Start smaller than you think. Prompt plainly, watch where sessions go wrong, and change a skill or add a check when the same failure shows up twice.

## Change a skill through its playbook

Writing or editing a skill, a playbook, a reference or a principle matches the Authoring or modifying a skill playbook ([authoring-a-skill.md](../../skills/mmw-mode/playbooks/authoring-a-skill.md)):

```text
the bug fix playbook should tell the session to save the original repro command in the ticket. change it.
```

The playbook opens a ticket for the change first, then:

1. **Read the standards.** The session first searches the set for the meaning you asked for. If the text already says it, the session tells you where, closes the ticket, and stops. Otherwise it names the design intent the change serves, decides which component and which file each passage belongs in, and reads how text is written. All three come from the `writing-for-agents` skill, below.
2. **Write the ticket, by size.** A change one ticket can carry is written into the ticket and handed back to you; on your go, a worker writes the text. A larger one goes through To spec and To tickets and runs as a night ([Run work while you sleep](./07-overnight.md)).
3. **Prove it, once.** Once the worker's ticket passes, or after the night, the session runs the checks that apply: the test suites a changed script needs, `uv run -q mmw-v4/tests/lib/check_skill_frontmatter.py`, `python3 mmw-v4/tests/lib/check_wiring.py` (prints `WIRING OK`), the host-neutrality `grep`, and `python3 mmw-v4/skills/dispatch/scripts/check-interfaces.py` (prints `INTERFACES OK`) when a dispatched session's prompts or wakes changed. Then one fresh agent walks one real task the change touches. A place where that agent ended wrong, stopped short or guessed at a sentence the change wrote fails the check, and the change does not land; every other guess goes into the reply as a finding for later.
4. **Deliver it.** One ticket lands the change and opens one pull request, merged on your yes.

The playbook's bias is to delete: every sentence in a skill costs attention on every run that loads it, so answering each slip with one more sentence makes the skill worse.

A skill's body is live on the next call, because install links each skill directory rather than copying it. A changed frontmatter `description` is read when a host starts, so it takes effect in a new session.

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
| [`UPSTREAM-INTENTS.md`](../../skills/writing-for-agents/UPSTREAM-INTENTS.md) | What Matt Pocock's skills and pstack each set out to do, for comparing the set with them |

A skill that drives your app to prove behaviour is a verification skill. The `create-verification-skill` and `maintain-verification-skill` skills generate and keep it; [Verify and ship](./06-verify-and-ship.md) covers both.

## Write docs to a standard with `technical-writing`

Skills are not the only prose that ships. Docs, readmes, pull request descriptions and commit messages go through the [technical-writing](../../skills/technical-writing/SKILL.md) skill, then the [unslop](../../skills/unslop/SKILL.md) skill:

```text
/technical-writing review the readme changes
```

Its goal is prose a tired engineer understands on the first read. It cuts words that do no work, prefers the short everyday word, writes the real file or command name instead of a description of it, and reads each sentence for a second meaning. The Opening a PR playbook applies it to every pull request MMW opens, with every layer except Diátaxis.

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

## Capture a session's lessons with `reflect`

Right after a task that taught you something:

```text
/reflect that took far too long. capture what we learned so the next run doesn't repeat it.
```

The [reflect](../../skills/reflect/SKILL.md) skill sends the session's transcript to three reviewers in parallel (judgment, tooling, and a divergent reader), then a synthesizer sorts their proposals into `Accepted`, `Rejected` and `Backlog`. A proposal a lint, a script or a check would enforce better moves to `Backlog`. Nothing is changed until you approve which `Accepted` items to apply. Approve one only if it would change a future decision; one odd session is an anecdote, not a rule.

## Fix the repository with `correct`

When you correct sessions for the same mistake again and again, the fix belongs in the repository, not in your next prompt:

```text
/correct agents keep calling the database client directly instead of going through the repository layer
```

The [correct](../../skills/correct/SKILL.md) skill reads recent commits, reverts, review comments and comments that explain workarounds, and groups the mistakes into classes. A class counts once it has happened twice. It fixes each class at the highest level that works:

1. Make the mistake impossible with architecture: one owner per piece of state, one supported way per task.
2. Block it with types, or with a lint or check whose error names the fix.
3. Catch it with a test.
4. Write a doc or an agent rule, last, and only for a judgement call, because nothing fails when an agent skips a rule.

It fixes the most frequent classes one commit each, and proves each new check fails on a real past mistake. It keeps a table in the repository's agent instruction file that pairs each rule with what enforces it, so a rule nothing enforces shows up as a repeat. Run with no argument, it finds the classes from history on its own.

`reflect` improves skills from one session; `correct` changes a repository so a class of mistake cannot come back.

## Where these skills assume Cursor

`reflect` and the Eval playbook keep text written for Cursor. `reflect` names Cursor's `create-skill` skill for drafting. `reflect` names a `pstack-models.mdc` rule for its reviewers' models and falls back to the defaults its table gives when the rule is missing. The Eval playbook and `reflect` look for transcripts in the workspace's `agent-transcripts/` directory, a path Cursor's system prompt names. These are the places to look first when one of them stalls on another host. `create-verification-skill` writes `verify-<product>` in the product repository's `.agents/skills/verify-<product>/`.

**Pitfall:** do not edit a skill mid-task because it misbehaves. The mode's Non-negotiables say to fix a broken skill in its own pull request and keep the task moving. A skill edit tangled into feature work is invisible to review and cannot be evaluated.

Next: [Recipes and pitfalls](./10-recipes-and-pitfalls.md).
