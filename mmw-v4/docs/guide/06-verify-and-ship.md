# Verify the result and ship one pull request

"It compiles" is not evidence. [`principle-prove-it-works`](../../skills/principle-prove-it-works/SKILL.md) makes the agent check the real thing before it reports success: the running process, the value actually stored, the screen the user sees. A caveat about its own work, such as "not yet run against the real API", is an unmet criterion, not a footnote. Your job is to make the real thing checkable. This page covers stating a finish condition, driving the product, vetting a measured number, giving your app a verification skill, and shipping the change as one pull request.

Verification is the slowest step in most agent work, because it is the step that usually waits on a person. Make the agent able to do it, and you stop being the bottleneck. Skip it, and running more agents only gets you more unchecked work.

![A prototype plane flies a real test course while she times it with a stopwatch and robots film and checklist the run; the terminal reads verify: pass, evidence: captured.](./images/verification.jpg)

## State the finish condition up front

Put what done means in the first request, in whatever words fit:

```text
add json output to this command. text output stays byte-identical, the json parses, both run against the sample project. show me the evidence.
```

Now the agent has three checks it can run, not a mood to satisfy. The reply should carry the commands it ran and what they printed. If a check could not run, a good reply says "inconclusive". Treat a confident reply without evidence as a warning sign. The `## Writing the reply` section of the `mmw-mode` skill's `references/handling-a-request.md` requires every claim to carry its evidence or a label in the same sentence: measured, inferred, or guess.

Match the check to the change:

- A CLI change runs the real command.
- A UI change walks the changed flow in the running app. When it must match a reference pixel for pixel, a `toHaveScreenshot` test in `tests/e2e/<product>/` compares the screenshots.
- A parser or migration replays a saved input.
- A perf change compares before and after profiles.
- A storage change reads back the written value.

Ask for the proof as something you can inspect yourself: the failing test and then the passing one, the trace, the screenshot. An artifact beats a plausible explanation, because you can challenge it without replaying the whole run.

## Drive the product with the control skills

The `mmw-mode` skill's `## Non-negotiables` sends product driving to its `verify-<product>` skill, or to control-cli or control-ui when the product has none. Profiles, heaps, CDP traces, and screenshots still use control-ui or control-cli. A bug fix reproduces the bug on that same surface before anything else.

The [control-cli skill](../../skills/control-cli/SKILL.md) drives an interactive command-line program or terminal UI. It reuses the repository's own test or demo harness when one exists. Otherwise it starts the program in an isolated `tmux` session or a short pseudo-terminal script, sends one keystroke or line at a time, and waits for a concrete prompt before the next. It saves the transcript, and it captures CPU profiles, heap snapshots, and startup timings for performance work.

The [control-ui skill](../../skills/control-ui/SKILL.md) drives a web page, an IDE, or an Electron app through a browser or the Chrome DevTools Protocol. It reuses the repository's Playwright or browser harness when one exists. It picks elements by accessibility role, label, or a stable `data-*` attribute, not by screen position. It takes one action at a time and captures a fresh screenshot or page snapshot after each, so every step has a before and an after.

For a small diff you do not fully trust, the [blast-radius skill](../../skills/blast-radius/SKILL.md) finds what it could break elsewhere. It names the one or two facts the change is safe because of, and proves them by running code instead of writing an essay.

## Vet a measured number with the benchmark-checklist skill

A before-and-after number is the easiest evidence to get wrong by accident. A warm cache, a debug build on one side, or work that never ran inside the timed region can each produce a convincing speedup. The `mmw-mode` skill's Non-negotiables run the [benchmark-checklist skill](../../skills/benchmark-checklist/SKILL.md) before any session reports or acts on a number it measured. The Perf issue playbook vets its baseline and every number after it, and Hillclimb vets its harness before freezing it. Type it yourself when someone else's number looks too good:

```text
/benchmark-checklist vet the export speedup in this pull request
```

The skill asks seven questions and wants evidence from a run for each:

1. What limits the number, and why is it not twice as good?
2. Did every side run tuned the way production runs?
3. Does the result break a physical limit, such as disk bandwidth or core count?
4. Did anything error or return wrong output?
5. Does it reproduce over alternating runs, with a median and a range?
6. Does it matter end to end, on the path a user waits on?
7. Did the work actually happen inside the timed region?

The verdict is one of faster, slower, no measurable difference, or inconclusive, with the run count, the range, and the limiter. It is inconclusive when the limiter has no name or a side ran untuned. The skill is the working form of [`principle-explain-the-number`](../../skills/principle-explain-the-number/SKILL.md).

## Give your app a verification skill

The control skills are generic. To verify a feature, an agent needs to know how your app starts, what to click, and what result proves the feature works. If your project has no scripted way to do that, run:

```text
/create-verification-skill
```

The [create-verification-skill skill](../../skills/create-verification-skill/SKILL.md) interviews the repository, not you. It works out what a user touches, how the app starts locally, what can drive it, what evidence proves behavior, and whether two instances can run side by side. It asks you only what the code cannot answer.

It builds on tester-army/e2e and writes `verify-<product>` in the product repository's `.agents/skills/verify-<product>/`, with Read first, Launch, Doctor, Drive, Evidence, Cleanup, Rules, and Helpers sections. Its feature map lives under `features/`, one file per user-facing feature, saying how to reach it, which tests cover it, and what end state proves it works. The tests and config live in `tests/e2e/<product>/`. Before handing it over, the generator runs its instructions once end to end and checks that cleanup preserves the evidence. A generated skill that never ran is a draft. It commits and pushes the generated skill, map, tests, config, and required setup changes directly, without a ticket.

From then on, "verify it in the app" is a step any agent can run in this repository with no setup conversation:

```text
build the bulk-archive action. use /verify-<product> to verify it and show me screenshots as proof.
```

Treat the verification skill as infrastructure. Commit it, so every person and every agent drives the app the same way. Then build the lever, as [`principle-build-the-lever`](../../skills/principle-build-the-lever/SKILL.md) says. When agents keep writing throwaway scripts to click through the app, ask for a small control CLI that the verification skill calls instead. A CLI that agents use well has these traits:

- A few commands that each do real work, rather than many thin ones.
- A `--dry-run` option on anything destructive.
- Error messages that say what to do instead.
- Full `--help` text.
- Machine-readable output, such as JSON.

Make the development setup repeatable too: test users and one command that starts the environment the same way every time. Launch starts from an empty data directory; tests create their data through the product's own entry points.

Apps change and feature maps go stale. Run the [maintain-verification-skill skill](../../skills/maintain-verification-skill/SKILL.md) only when you want that review. It reads every feature from source in parallel, then follows `verify-<product>` for its live pass. For a feature with tests, running them is the live pass; for one without tests, it uses control-ui. It ends in one of three outcomes. `clean` means full coverage and nothing to change. `changed` means it commits and pushes proven corrections directly to the current branch, within the verification skill's own directory and `tests/e2e/<product>/`. `blocked` names what stopped it. It never edits product code. A product regression it finds is reported, not hidden by a doc edit.

## Ship each change as one pull request

The ticket and pull-request path ends in exactly one pull request. A few kinds of change commit directly without a ticket; the execution constraints are in the `mmw-mode` skill's [`references/handling-a-request.md` `## Non-negotiables`](../../skills/mmw-mode/references/handling-a-request.md#non-negotiables). A change is never split into a stack of dependent pull requests. Which path runs depends on who wrote the code.

**One ticket.** On the ticket and pull-request path, a change outside a night goes through a ticket a worker builds, and ends with the [One ticket playbook](../../skills/mmw-mode/playbooks/one-ticket.md). The session checks the result the way the playbook that wrote the ticket says, for a bug the original reproduction. It merges the latest project branch into `fix-<n>`, runs `dispatch.sh land <n>`, and runs [Opening a PR](../../skills/mmw-mode/playbooks/opening-a-pr.md): one pull request from `fix-<n>` to the project branch, its checks and comments settled, merged with `gh pr merge --merge` when you say yes.

**A night's batch.** A night ends in one pull request from the night's branch to the project branch, titled `Night #<spec>: <the spec's title>`. Its first line opens the visual page you read; its body records the tickets, evidence links, checks and `NIGHT SUMMARY`. After you accept it, `dispatch.sh finish <spec>` merges it and closes the spec issue as completed. The local night branch remains available, and `finish` creates or fast-forwards the local project branch to the fetched origin tip. A clean project worktree fast-forwards too; uncommitted changes or local commits outside origin leave it unchanged, with the reason on stderr. Landing deletes local and origin ticket branches when cleanup permits it. `finish` removes the origin night branch when cleanup permits it. A worktree on the night branch stays in place. If cleanup or closing the spec fails after merging, run `finish` again to close it without merging again. `finish` refuses while any check is red or still running, or any review thread is unresolved, and nothing merges until those are settled. Merging the project branch into the repository's default branch stays your release decision. [Run work while you sleep](./07-overnight.md) covers the night.

One playbook writes every pull request: [Opening a PR](../../skills/mmw-mode/playbooks/opening-a-pr.md). The title follows Conventional Commits, such as `fix(dispatch): refuse a finish whose pull request has an open thread`. The body's first line is the address or local path of your page. Its remaining lines are a short record for identifying, searching and tracing back: what the change does, the tickets and their verdicts, evidence links, check summaries, unresolved work, the retrospective receipt and, at night, the verbatim `NIGHT SUMMARY`. Every pull request opens ready for review, never as a draft.

Your page is mostly pictures, with six blocks in the same order on every pull request: what you decide, what changed before and after, what the merge touches and whether it can be taken back, not done and left over, a short retrospective list with issue links and conclusions, and links. Decision cards include a recommendation. The page links to the pull request, tickets and task board. The session publishes it with the richest HTML page tool it controls, or uses a local page when none is available. Fixes and routed findings update that same page and its record. The final reply points to the pull request instead of repeating the page.

[Opening a PR step 3](../../skills/mmw-mode/playbooks/opening-a-pr.md) checks review comments against the pull request's current version. The session fixes confirmed problems, answers disproved claims with evidence, and investigates unresolved claims. Only a product trade-off or a decision outside its authority comes to you.

Next: [Run work while you sleep](./07-overnight.md).
