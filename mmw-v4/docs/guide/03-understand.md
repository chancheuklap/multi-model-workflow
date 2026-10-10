# Understand the code before changing it

An agent that edits code it has not traced fixes the symptom at the first plausible spot. Agents usually fail in one of two ways. They misread what you want, or they lack the context to do the work right. [The mmw-mode chapter](./02-mmw-mode.md) covers what goes in a request. This page covers context.

Four skills build it. The [how skill](../../skills/how/SKILL.md) explains what the code does now. The [why skill](../../skills/why/SKILL.md) finds the reasons it has that shape. The [teach skill](../../skills/teach/SKILL.md) blends both into one plain explanation. The [recall skill](../../skills/recall/SKILL.md) rebuilds recent working context on a topic. Each one makes the agent explain itself in words you can check, which is how you supervise an agent that may know the code better than you do.

![A detective studies a machine blueprint with a magnifying glass while robots fetch case files; the evidence board behind her links clues under /how and /why.](./images/understanding.jpg)

## Ask for findings, not a fix

When the cause is unclear, ask a read-only question:

```text
investigate why background jobs time out every few hours. give me what we know, what data you used, and your best hypotheses. don't change any code yet.
```

Every session reads the `mmw-mode` skill first, and its `## Playbooks` list routes a read-only question to the [Investigation playbook](../../skills/mmw-mode/playbooks/investigation.md). The playbook runs the how skill, and adds the why skill for a question about motivation. For a question whose answer lives outside the repository, such as a third-party API or a published standard, it sends one `researcher` session with the dispatch skill. The answer comes back in the how skill's sections (Overview, Key Concepts, How It Works, Where Things Live, Gotchas). For a choice between options, it comes back as a recommendation with a trade-offs table.

Asking "what data you used" makes the agent separate evidence from guesses. The playbook already requires that a claim resting on a file the agent did not read is labelled inferred (**principle-read-before-you-conclude**). Investigation changes no code and opens no pull request. When the findings point at a fix, start the fix as a new task, which routes to Bug fix or Feature.

## Trace behavior with the how skill

```text
/how do we dedupe notifications? is there an n+1 when we look up subscribers?
```

Ask the question you actually have. The how skill answers at the level of a senior engineer who walks you onto a subsystem: the runtime flow, the key types, and the parts that surprise people. A narrow question gets one pass by the session itself. A subsystem that spans many files gets two to four `researcher` sessions first, one per angle, sent with `dispatch.sh send researcher`. Each researcher runs on the host and model that `~/.mmw/models.json` gives the `researcher` role. The session that asked writes one explanation from their answers and checks it against the code before it presents it.

## Find the history with the why skill

```text
/why was the retry limit set to five? does the reason still hold?
```

The why skill anchors on the code first: the file, the lines, `git blame`, and the pull requests behind the last commits. It then sends one `researcher` per kind of evidence the session can reach, in parallel. The seven kinds are source control, the issue tracker, long-form documents, team chat, infrastructure observability, error tracking, and product analytics. Source control is always searched. A kind with no matching MCP server is listed as a gap, not skipped in silence.

The answer keeps what was found apart from what is inferred, lists competing explanations, and says what is still unknown. Its Sources Consulted section has one line per kind of evidence, including the ones that returned nothing. "Nobody wrote down why" is itself an answer. When the question comes before a change, the answer ends with a Preserve, Change, Avoid and Risk list for planning that change.

The two skills combine. `do why first then how` is a good request when you suspect the history explains the mess.

## Understand it with the teach skill

```text
/teach me how this change handles retries. convince me it fixes the cause and not the symptom.
```

The teach skill is for when a summary is not enough. It runs the how skill and the why skill, or one of them for a small change, and blends the findings into a plain explanation. It starts with a short definition, ties it to the case in front of you, and goes deeper when you ask. For anything with three or more moving parts, it draws a series of diagrams, each adding one part to the last. It keeps the why skill's confidence words as they are, because those hedges are findings.

The "convince me" framing turns the explanation into an argument you can test. The teach skill also works on the agent's own choices:

```text
/teach me why you implemented it this way and not with a queue. what did you trade off, and why?
```

An agent that must explain its work has to read the code and back each claim with evidence.

## Rebuild recent context with the recall skill

```text
/recall catch me up on the export work from last week
```

The recall skill builds a short brief from two records. One is your own recent chats. The other is the shared record, searched through the why skill's investigators: the issues, the fixes that shipped and were reverted, and the errors still firing. It checks every pull request, branch, and ticket it names against `git` and `gh` before it reports. The brief has four parts: a capsule of at most five bullets, one line per thread with a status tag such as `[merged #N]` or `[in flight <branch>]`, the recurring problems, and the next move.

The skill's text names one place to read chats from: Cursor's transcript folder, `~/.cursor/projects/<slug>/agent-transcripts/`. On another host, expect the brief to rest on the shared record.

Start new work on an old topic by loading the context first, then hand over the new input:

```text
/recall my work on the virtualized list from yesterday, then read this bug report.
```

To resume one specific session, use Session pickup, below, not the recall skill.

## Take over prior work with Session pickup

When another agent, or you last week, left a branch half done:

```text
take over this branch. read what the last session decided, figure out what's done, and continue from there. don't redo finished work.
```

The [Session pickup playbook](../../skills/mmw-mode/playbooks/session-pickup.md) treats the prior trail as authoritative (**principle-progress-is-what-the-record-says**). It reads the host's record of the prior session for this repository only, or the pushed branch. It rebuilds the branch state and the decisions, names the resume point, and routes the rest of the work to the matching playbook. It then checks the inherited claims against the original goal on the real product, because a prior agent's report that it passed is not proof.

To stop work so another session can pick it up cleanly, use the [Pause safely playbook](../../skills/mmw-mode/playbooks/pause-safely.md).

**Pitfall.** Do not skip these skills on the grounds that the agent will read the code anyway. An agent that edits before it has a traced model fixes the symptom at the first plausible spot. A run of the how skill costs less than the second bug.

Next: [Design the change](./04-design.md).
