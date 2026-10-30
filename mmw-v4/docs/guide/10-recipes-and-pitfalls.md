# Recipes and pitfalls

Prompts worth copying, then the mistakes everyone makes once. Swap in your own paths, issue numbers and checks. The prompts are informal on purpose: that is how they get typed, and `mmw-mode` reads the intent and picks the playbook. A slash command names a skill only where you want that skill and no other.


## Understand an unfamiliar subsystem

```text
use /how first to understand how this initialization works. then use /why to find out why it broke recently.
```

Mechanics first, history second. The [how](../../skills/how/SKILL.md) skill explains how the code works; the [why](../../skills/why/SKILL.md) skill investigates what led to its shape and says which parts it knows and which it infers.

## Restate a noisy report before touching code

```text
read this thread. restate the underlying issue in your own words, in plain english. don't change any code yet.
```

"Don't change any code yet" keeps the session in the Investigation playbook. A misreading shows up in the restatement, where it costs one message to correct. Keep your own theory back until the session has stated its own.

## Prototype before you pick

```text
prototype a few options for the settings layout. put them behind a switcher and send me screenshots of each.
```

You pick from things that run, not from descriptions. The [prototype](../../skills/prototype/SKILL.md) skill also settles layout and timing questions by observing them instead of asking you.

## Sharpen a plan, then record it

```text
grill me on this plan for the export retry. write the glossary and the ADRs as we go.
```

```text
turn what we decided into a spec.
```

```text
cut spec #212 into tickets.
```

Grill with docs settles the decisions in one session. The to-spec skill records them as a GitHub issue, with no new interview. The to-tickets batch entry cuts the spec into tickets with acceptance criteria and blocking edges and shows you the breakdown before it publishes. For an idea too large for one session, use the wayfinder skill's chart entry:

```text
we want offline mode for the mobile app, and i don't know yet what that takes. chart it as a map.
```

## Run the night

```text
spec #212's tickets are published. run the night on them. i'm going to bed.
```

In the morning you get one pull request whose first line opens your visual page. The body is the short record; the page shows the result and what you decide. When you accept it:

```text
i accept the night's pull request for #212. finish it.
```

[Run work while you sleep](./07-overnight.md) explains each step.

## Fix a bug with proof

```text
the export writes duplicate rows when a retry lands mid-run. repro first, then fix and verify.
```

Develop a change uses the bug-fix skill to reproduce the bug on the same surface a user meets it, finds the cause with runtime evidence, writes one ticket whose first criterion is a regression test that fails today, and sends a worker to it. It then runs the original reproduction again and delivers one pull request.

```text
repro this with /verify-<product>. if it repros on the project branch, fix it and show me screenshots or the e2e `trace.md` as proof.
```

`/verify-<product>` stands for the project's own verification skill, which the `create-verification-skill` skill generates. "If it repros" lets the run stop early when the bug is already gone.

## Get a second opinion on a decision

```text
before we commit to this schema, get the advisor's opinion on it.
```

The session sends an `advisor` session a brief carrying the decision, the options, the constraints and which way it leans. The answer is advice: the session takes it or sets it aside with a reason, and one that changes a decision of yours comes to you.

To compare whole designs rather than judge one:

```text
ask /arena for three designs of the sync engine, then graft the best parts onto the strongest.
```

## Review a change before it merges

```text
review this branch with /code-review. don't change anything. no nitpicks unless it's a real bug or a regression.
```

The [code-review](../../skills/code-review/SKILL.md) skill reads the diff on four axes (Standards, Spec, Tests, Correctness), checks each finding against the code before reporting it, and sorts out the ones that do not hold.

## Vet a number before you post it

```text
/benchmark-checklist vet this 40% speedup before it goes on the pull request's page
```

You get faster, slower, no measurable difference, or inconclusive, with the run count, the range, and what limits the number.

## Stop correcting the same mistake

```text
/correct agents keep adding new config flags without registering them in the schema
```

The fix lands in the repository as architecture, a type, a lint or a test, so the next session cannot make the mistake.

## Change which model a role runs on

```text
run the reviewer on a stronger model from now on.
```

The [dispatch](../../skills/dispatch/SKILL.md) skill changes the role's row of `~/.mmw/models.json` through `models.py config set`. The next session it starts uses the new row; nothing needs a restart.

## Ask how without starting the work

```text
/mmw-help how do i run one ticket without a whole night?
```

The [mmw-help](../../skills/mmw-help/SKILL.md) skill answers, hands you a prompt to send, and links the file the answer came from. Nothing runs until you send that prompt.

## Stop cleanly and pick up later

```text
pause here. i'm restarting the machine.
```

```text
pick up the work on branch fix-export-retry. read the resume note, find what's done, and continue.
```

Pause safely finishes or backs out of the current step, commits a `wip:` checkpoint and writes a resume note. Session pickup resumes from the note and the commits, not from anyone's memory. "Keep going" never triggers a pause.

## Redirect a drifting run

Steering prompts are one line:

```text
i said the goal is to repro. i did not ask for a fix yet.
```

```text
apply prove it works. show me the real output, not the build log.
```

```text
/unslop that, no long dashes
```

State the goal that the run missed. The mode loads the relevant [shared principles](./08-principles.md); naming one yourself is an optional correction.

## Get the reply in plain words

```text
/wait-what
```

That is the whole prompt. The [wait-what](../../skills/wait-what/SKILL.md) skill re-pitches the last message with the context it skipped, in short sentences and the project's own names. Use it when a reply is thorough and you still cannot tell what it said. `/wait-what visual` makes the same re-pitch one page of pictures. `/wait-what ketchup` catches you up on progress since your last message and names decisions waiting for you. `/wait-what in-your-own-words` restates your goal and waits for your confirmation or correction before work starts.

## The pitfalls

- **Listing skills in the prompt.** "Use /how then /prototype then /arena" reorders steps the playbook already sequences. State the goal and the check; name a skill only to override a default.
- **A finish condition that cannot fail.** "Make it better" gives nothing to check. A ticket's `CHECK:` that passes on a broken product is the same mistake in a ticket; To tickets and `verify-ticket.py --lint` exist to catch it.
- **Leading with your theory of the cause.** The session searches where you pointed. Ask it to restate the problem first, then share your hunch.
- **Taking the first design.** One attempt locks in the first shape the model thought of. Ask for prototypes, including the sketch branch for code shape, and pick from evidence.
- **Polishing an abstract plan.** Adversarial review of a plan with no code behind it invents risks that never happen. Settle open questions with prototypes, then review what got built.
- **Running a night on undecided work.** Each worker guesses an open question differently. Settle it with Grill with docs or a map, then publish the tickets.
- **Handing a ticket to a session to build by hand.** A ticket with acceptance criteria is worked only by a dispatched worker. Given one anywhere else, the session runs the One ticket playbook on it.
- **Parallel sessions in one worktree.** They overwrite each other. The pipeline gives each ticket its own worktree under `.worktrees/issue-<n>`; for work of your own, say "own worktree per attempt".
- **Trusting an unvetted number.** A warm cache or a skipped code path can fake a speedup. Run `/benchmark-checklist` before the number goes anywhere.
- **Correcting the same mistake by hand.** A correction in chat helps one run. `/correct` fixes the repository so no later run repeats it.
- **Accepting every review comment.** [Opening a PR step 3](../../skills/mmw-mode/playbooks/opening-a-pr.md) checks each claim against the current version before acting.
- **Editing `~/.mmw/models.json` by hand.** Change a role's host, model or effort only through `models.py config`, which checks the row against what the host offers.
- **Reporting success off a green build.** A build proves it compiles. Ask for the real command, flow, stored value or profile, and expect the evidence in the reply.
- **Writing a `SKILL.md` freehand.** Route it through the Authoring or modifying a skill playbook ([Make it yours](./09-make-it-yours.md)) so the standards and the checks apply.

That's the guide. If you skipped ahead, go back to [setup](./01-setup.md) and run one real task. The habits stick from use, not from reading.

Back to the [guide index](./README.md).
