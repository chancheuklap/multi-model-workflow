# pstack

i'm [poteto](https://x.com/poteto). i'm not a president or ceo, but i've worked with millions of lines of code at Meta, Netflix, and Cursor. i'm also on the react core team where i help build and maintain react compiler.

there's a growing sense that ai writes too much slop code. i agree. i don't want to ship like a team of twenty slop artists. throughput without quality is not a goal i aspire to. if you want to go fast, go deep first. 

**pstack is my answer.** these are the same skills i use every day to ship high quality code at Cursor. the goal is not to maximize loc, in fact it's the opposite. pstack helps you write less, but higher quality code.

**pstack gives you fearless parallelism.** when you can go deep on one agent and trust it to write good, verifiable code, you can truly parallelize with confidence. start multiple agents up with [poteto-mode](skills/poteto-mode/SKILL.md) and trust that they'll apply rigorous engineering principles to their work.

every frontier model has its strengths and weaknesses. use the models your session can assign. in fact, many of my skills use multi-model workflows to take advantage of each model's unique strengths.

fork it. improve it. make it yours. PRs are welcome! 

## install

use the local plugin installation available in your agent environment and select this copy of pstack. you can also start directly from [poteto-mode](./skills/poteto-mode/SKILL.md). keep the `skills/` and `agents/` directories together so the mode can find its playbooks, skills, and delegate instructions.

## get started

two steps:

1. run [setup-pstack](./skills/setup-pstack/SKILL.md), pick a reasoning budget, and choose which models you want.
2. use [poteto-mode](./skills/poteto-mode/SKILL.md) whenever you're doing anything that requires rigor.

new here? the [pstack guide](./docs/guide/README.md) walks you through a first real task, from setup and prompting through verification and overnight runs. stuck, or unsure which skill fits? ask [poteto-help](./skills/poteto-help/SKILL.md).

the [pstack glossary map](./docs/GLOSSARY-MAP.md) takes you to the vocabulary for the part of the run you're working on.

that's it. the other skills are situational, and the mode skill uses them for you as needed. a bundled skill written as `/name` means `skills/<name>/SKILL.md` in this copy. the mode uses the models you chose for code, the hardest changes, prose, judgment, and review panels.

## usage

use [poteto-mode](./skills/poteto-mode/SKILL.md) at the start of a task. it opens or reuses a GitHub work issue, reads your request, picks from a set of playbooks, and runs the other skills as the steps need them.

### just use [poteto-mode](./skills/poteto-mode/SKILL.md)

this skill is the main shortcut. i use it whenever i need the agent to do rigorous engineering work. it comes with twenty-five playbooks:

```
/poteto-mode this pr has a subtle bug where the scroll drifts every 750ms even when idle. repro
first, then fix and verify.
```

```
/poteto-mode i'm going to bed. land the stack even if ci flakes. i want everything merged by
morning.
```

<details>
<summary>the twenty-five playbooks</summary>

| playbook | for |
|---|---|
| [investigation](./skills/poteto-mode/playbooks/investigation.md) | a read-only question. how does x work, why was y built this way, are we sure. |
| [bug fix](./skills/poteto-mode/playbooks/bug-fix.md) | reproduce a defect, root-cause it, and fix with runtime evidence. |
| [perf](./skills/poteto-mode/playbooks/perf-issue.md) | trace a measured slowness and improve it against a baseline. |
| [hillclimb](./skills/poteto-mode/playbooks/hillclimb.md) | sustained, scientific improvement of one metric against a target, looping hypotheses with before/after measurement and one commit per accepted win. |
| [runtime forensics](./skills/poteto-mode/playbooks/runtime-forensics.md) | diagnose a live symptom (leak, idle-cpu spin, glitch) from instrumentation. |
| [trace forensics](./skills/poteto-mode/playbooks/trace-forensics.md) | diagnose a captured profiling artifact (cpuprofile, trace, spindump, heap snapshot). |
| [feature](./skills/poteto-mode/playbooks/feature.md) | new or changed behavior, built from a named data shape. |
| [refactoring](./skills/poteto-mode/playbooks/refactoring.md) | a behavior-preserving change to structure or shape. |
| [improve codebase architecture](./skills/poteto-mode/playbooks/improve-codebase-architecture.md) | find modules worth deepening, see the before/after report, and discuss one opportunity. |
| [prototype](./skills/poteto-mode/playbooks/prototype.md) | a throwaway sketch to make a design or behavioral decision cheaply, or to settle an empirical fork by observing it. |
| [wayfinder](./skills/poteto-mode/playbooks/wayfinder.md) | chart unresolved decisions across sessions on a GitHub map, or continue from a decision ticket. |
| [visual parity](./skills/poteto-mode/playbooks/visual-parity.md) | pixel-exact ui equivalence between two implementations. |
| [authoring a skill](./skills/poteto-mode/playbooks/authoring-a-skill.md) | writing or editing a SKILL.md. |
| [eval](./skills/poteto-mode/playbooks/eval.md) | test how a skill or prompt change affects agent behavior, blinded. |
| [babysit](./skills/poteto-mode/playbooks/babysit.md) | drive a pr or a stack to merge-ready: conflicts, review threads, ci. |
| [shipping](./skills/poteto-mode/playbooks/shipping.md) | independently verify a green stack, then land the contiguous verified run bottom-up through github by default or origin when available. |
| [autonomous run](./skills/poteto-mode/playbooks/autonomous-run.md) | drive a long task to completion without stopping. |
| [orchestrate](./skills/poteto-mode/playbooks/orchestrate.md) | a standing project handed to one coordinator chat: multi-day, many stacked prs, fleets of subagents. |
| [autopilot-full](./skills/poteto-mode/playbooks/autopilot-full.md) | run independent prs to merged with one owner per pr. a swarm verifies each code-ready head, and every later change to the patch gets a fresh check. |
| [autopilot-stack](./skills/poteto-mode/playbooks/autopilot-stack.md) | autopilot-full without the merge. build and verify prs for the operator to review and land, stacking a pr only on a pr it builds on. |
| [session pickup](./skills/poteto-mode/playbooks/session-pickup.md) | resume or take over a prior agent's in-flight work. |
| [pause safely](./skills/poteto-mode/playbooks/pause-safely.md) | suspend in-flight work cleanly so it can be resumed later. |
| [multi-phase plan](./skills/poteto-mode/playbooks/multi-phase-plan.md) | plan outcomes, dependencies, and verification across phases. |
| [worktree cleanup](./skills/poteto-mode/playbooks/worktree-cleanup.md) | reclaim disk by pruning merged or abandoned worktrees and stale ios simulators, safety-gated. |
| [opening a pr](./skills/poteto-mode/playbooks/opening-a-pr.md) | open a ready pr from small ordered commits with a conventional commits title and a briefing-style body. invoked at the end of every other playbook. |

</details>



when invoked it:

1. matches your task to a [playbook](./skills/poteto-mode/playbooks/) and opens a todo list whose first items are its steps, copied in verbatim.
2. routes to the other skills as the steps fire.
3. writes unslopped replies framed for the consumer and the maintainer.

the full rules and playbooks live in [poteto-mode](./skills/poteto-mode/SKILL.md).

to keep [poteto-mode](./skills/poteto-mode/SKILL.md) active across turns, use the session's persistent instructions if available, or name the mode when you start a task. for unattended work, give the agent a checkable finish condition and a way to wake up and check it.

## skills

[poteto-mode](./skills/poteto-mode/SKILL.md) runs most of these for you when a step needs them ([how](skills/how/SKILL.md), [why](skills/why/SKILL.md), [architect](skills/architect/SKILL.md), [arena](skills/arena/SKILL.md), [swarm](skills/swarm/SKILL.md), [interrogate](skills/interrogate/SKILL.md), [unslop](skills/unslop/SKILL.md), [no-comments](skills/no-comments/SKILL.md), [technical-writing](skills/technical-writing/SKILL.md), [tdd](skills/tdd/SKILL.md), and the principles). the table below is for when you want one directly:

```
/how do we cancel runs? do we have an n+1 when we look up every run to cancel?
```

```
/interrogate review this pr.
```

<details>
<summary>all skills</summary>

| skill | use it when |
|---|---|
| [poteto-mode](./skills/poteto-mode/SKILL.md) | default entry point for any non-trivial task. |
| [poteto-help](./skills/poteto-help/SKILL.md) | you're new to pstack, or unsure which skill, playbook, or principle fits. finds out what you're trying to do, answers that part, and hands you a prompt to type. runs only when you type `/poteto-help`. |
| [in-your-own-words](./skills/in-your-own-words/SKILL.md) | you want the agent to play back your goal and the problem before it starts. runs only when you type `/in-your-own-words`. |
| [sharpen](./skills/sharpen/SKILL.md) | you want a prompt made deeper, not bigger, before you send it: what a top professional would do that you didn't ask for, the raw material they'd start from, their methods and tools, and an outside check that the result is right. hands back the rewritten prompt and leaves your choices open. doesn't do the task. runs only when you type `/sharpen`. |
| [how](./skills/how/SKILL.md) | you want a walkthrough of how a subsystem works. |
| [why](./skills/why/SKILL.md) | you want to know why something was built this way. discovers accessible sources at run time and queries each evidence category in parallel (source control, issue tracker, long-form docs, real-time chat, infra observability, error tracking, analytics warehouse). |
| [recall](./skills/recall/SKILL.md) | you're starting or resuming work and want your recent context on a topic rebuilt from your own chat history and the shared record, handed back as a tight current-state brief. |
| [ketchup](./skills/ketchup/SKILL.md) | you want what changed in this chat since your last message, in plain words and small visuals, with every item waiting on you listed and decidable from the reply alone, even when that makes the reply long. |
| [ketchup-video](./skills/ketchup-video/SKILL.md) | you want the [ketchup](skills/ketchup/SKILL.md) catch-up as a short subtitled video of slides, with the calls waiting on you as text under it. |
| [blast-radius](./skills/blast-radius/SKILL.md) | you have a small-looking change and want to know what else it could break, with the one fact it's safe because of proven by running code, not asserted. |
| [architect](./skills/architect/SKILL.md) | you're about to write code that crosses a function boundary and want the caller's usage, types, and module shape settled first. |
| [codebase-dic](./skills/codebase-dic/SKILL.md) | look up the shared vocabulary for deep modules, dependency seams, and tests at the interface. |
| [arena](./skills/arena/SKILL.md) | you want N parallel attempts at the same thing, then to grab the best parts of each. |
| [swarm](./skills/swarm/SKILL.md) | you want N parallel workers across different slices or races, then one aggregated report. |
| [interrogate](./skills/interrogate/SKILL.md) | you have a diff and want different models to try to break it, keeping only findings a run proves. |
| [automate-me](./skills/automate-me/SKILL.md) | you want your own `-mode` skill, drafted from how you've actually worked. |
| [make-bot-ui](./skills/make-bot-ui/SKILL.md) | you want a page or dashboard whose buttons wake a Grok Bot over a webhook, including the sender-key handoff and Tailscale. |
| [grilling](./skills/grilling/SKILL.md) | work through a design question with the operator, one decision at a time. |
| [domain-modeling](./skills/domain-modeling/SKILL.md) | sharpen the project's terms and record settled meanings and architectural decisions. |
| [research](./skills/research/SKILL.md) | investigate a question against primary sources and return a cited report. |
| [to-spec](./skills/to-spec/SKILL.md) | turn an existing discussion or map into a spec on its GitHub work issue. |
| [to-tickets](./skills/to-tickets/SKILL.md) | open or update a GitHub work issue, or split agreed scope into independently verifiable tickets. |
| [big-pics-little-words](./skills/big-pics-little-words/SKILL.md) | explain a subject with large visuals and enough text to understand the details. |
| [html](./skills/html/SKILL.md) | build a self-contained HTML artifact. use [html-wireframe](./skills/html-wireframe/SKILL.md) for layout, [html-prototype](./skills/html-prototype/SKILL.md) for a mockup or interactive prototype, [html-plan](./skills/html-plan/SKILL.md) for an HTML plan, or [html-diagram](./skills/html-diagram/SKILL.md) for relationships. |
| [design-artifact](./skills/design-artifact/SKILL.md) | choose the visual direction of an HTML artifact. |
| [setup-pstack](./skills/setup-pstack/SKILL.md) | you want to pick which models pstack uses per role. detects your models and writes a config rule. |
| [reflect](./skills/reflect/SKILL.md) | a long task landed and you want the recipe captured as a skill edit. |
| [correct](./skills/correct/SKILL.md) | you keep correcting agents for the same mistakes. mines history for mistake classes, fixes each at the highest level that works (architecture, then types, lint, and ci, then tests, with docs last), and keeps a table pairing each rule with what enforces it. |
| [teach](./skills/teach/SKILL.md) | you want to actually understand a change or subsystem, not just have it summarized. runs how + why and weaves one plain explanation, built up diagram by diagram. |
| [tdd](./skills/tdd/SKILL.md) | you're fixing a bug and there's a cheap local test path. write the failing test first, then the fix. |
| [benchmark-checklist](./skills/benchmark-checklist/SKILL.md) | you ran a benchmark or measured a speedup or regression. vets the number (limiter, tuning, errors, repeat runs, end-to-end relevance) before you report or act on it. |
| [no-comments](./skills/no-comments/SKILL.md) | strip comments before review; spawns Comment Sicko, fixes accepted findings, offers encodings for claimed constraints. |
| [typescript-best-practices](./skills/typescript-best-practices/SKILL.md) | you're reading or editing typescript. grounds the type-system-discipline principle in syntax. |
| [figure-it-out](./skills/figure-it-out/SKILL.md) | no bundled playbook fits. designs a rigorous, auditable playbook for the task. |
| [show-me-your-work](./skills/show-me-your-work/SKILL.md) | you want a reviewable decision trail. logs decisions to a tsv you can commit. |
| [create-verification-skill](./skills/create-verification-skill/SKILL.md) | your project has no scripted way to prove app behavior. generates a project-local verify skill with a feature map, for any language or platform. |
| [maintain-verification-skill](./skills/maintain-verification-skill/SKILL.md) | your verify skill's feature map has drifted from the app. source wave + one live pass, at most one PR of proven corrections. |
| [create-formal-verification-skill](./skills/create-formal-verification-skill/SKILL.md) | tests can't reach the case that breaks a race, retry, state machine, parser, or unsafe code. verifies one property with the tool that fits and generates a project-local skill to recheck it on every change. |
| [maintain-formal-verification-skill](./skills/maintain-formal-verification-skill/SKILL.md) | code your formal verification covers has changed since it was last checked. updates the model, harness, or properties to match the code, reruns, and says whether each failure is drift in the verification or a bug in the code. |
| [statechart](./skills/statechart/SKILL.md) | someone who owns the behavior needs to see it, not read a spec. checks a tla+ model, draws what the user sees as a mermaid statechart, marks each state that breaks a rule, and gives the shortest path to each one. |
| [unslop](./skills/unslop/SKILL.md) | you're cleaning up writing. removes AI tells. |
| [bro](./skills/bro/SKILL.md) | you want the last message restated in plain human language, no jargon. |
| [technical-writing](./skills/technical-writing/SKILL.md) | layered doc standard (Diátaxis + Google developer style + STE + Global English) for docs, RFCs, readmes, PR descriptions, commit messages. |

</details>



### examples

mostly i type [poteto-mode](./skills/poteto-mode/SKILL.md) at the start of a task and let it route to a playbook. the other skills fire as the steps need them. a few i reach for directly.


<details>
<summary>all the examples</summary>

```
bug fix:           /poteto-mode this pr has a subtle bug where the scroll drifts every 750ms even
                   when idle. repro first, then fix and verify.
perf:              /poteto-mode a big list takes a second or two to load even though we virtualize.
                   run a cpu trace and tell me why.
feature:           /poteto-mode build a small feature behind a feature flag. verify it really works.
prototype:         /poteto-mode build two prototypes of the markdown renderer so we can compare.
                   spawn an agent for each.
multi-phase:       /poteto-mode open source these skills as a plugin. nothing internal leaks, work
                   in a temp dir, show me the dependency graph first.
overnight run:     /poteto-mode i'm going to bed. land the stack even if ci flakes. i want
                   everything merged by morning.
babysit:           /poteto-mode check on pr 123. anything outstanding?
visual parity:     /poteto-mode the row spacing is too tall when this flag is on. the second image
                   is correct. repro and fix until it matches.
figure it out:     /poteto-mode i'm stepping away. migrate every caller from the synchronous store
                   to the new async one, keeping behavior identical. i want to trust it was done
                   right when i'm back.
how:               /how do we cancel runs? do we have an n+1 when we look up every run to cancel?
why:               /why is this feature flag not on yet?
architect:         design this instrumentation to be high signal with no false positives. /architect
                   this first.
arena:             /arena take my prompt to the arena verbatim. i want to compare their proposals
                   with yours.
swarm:             /swarm check every package under packages/ against its check.sh. one worker per
                   package. one report.
interrogate:       /interrogate review this pr.
tdd:               /tdd implement
unslop:            can we unslop and tighten the new changes?
reflect:           /reflect that took too long. capture what we learned so the next run doesn't
                   repeat it.
correct:           /correct
show-me-your-work: /show-me-your-work keep a decision trail i can review when i'm back.
automate-me:       /automate-me
help:              /poteto-help which skill should i use to review this branch?
```

</details>

## the `poteto-agent` and Comment Sicko subagents

[poteto-mode](./skills/poteto-mode/SKILL.md) runs in the chat that receives it. that chat owns the playbook, the todo list, and the work it delegates.

pstack also ships the [`poteto-agent` role](./agents/poteto-agent.md) for delegates the main chat spawns inside a playbook step. it reads [poteto-mode](skills/poteto-mode/SKILL.md) in full, including its inline principles index, before doing any work. a worker without that role does not get those instructions. do not spawn `poteto-agent` to run the playbook itself.

when a playbook calls a skill, that skill assigns its own workers the roles it needs.

pstack also ships [Comment Sicko](./agents/comment-sicko.md), a read-only comment reviewer. usually invoke it through [no-comments](./skills/no-comments/SKILL.md), not directly.

## principles

thirty-two short skills, one principle each. [poteto-mode](skills/poteto-mode/SKILL.md) indexes them inline and reads that index at task start. the standalone files are there so other skills can reference a principle by name, and so the index can point at the full rule for each.

<details>
<summary>all thirty-two principles</summary>

| principle | group | rule |
|---|---|---|
| [principle-laziness-protocol](./skills/principle-laziness-protocol/SKILL.md) | core | Bias toward deletion and the smallest change that solves the problem. |
| [principle-foundational-thinking](./skills/principle-foundational-thinking/SKILL.md) | core | Apply before writing logic: choosing core types and data structures, sequencing scaffold-vs-feature work, asking what concurrent actors share. Get the data structures right so downstream code becomes obvious. |
| [principle-first-principles-thinking](./skills/principle-first-principles-thinking/SKILL.md) | core | Test the requirements and constraints behind an open approach before refining it. |
| [principle-redesign-from-first-principles](./skills/principle-redesign-from-first-principles/SKILL.md) | core | Redesign as if the requirement had been a foundational assumption from day one, instead of bolting it on. |
| [principle-baseline-is-the-contract](./skills/principle-baseline-is-the-contract/SKILL.md) | core | Build from the values, wording, and behavior the decision fixed. A prototype binds the question it settled. |
| [principle-attack-the-premise](./skills/principle-attack-the-premise/SKILL.md) | core | Apply when two or more fixes that share one premise have failed the same gate. Write the premise down and test it directly before you write another fix that assumes it. |
| [principle-subtract-before-you-add](./skills/principle-subtract-before-you-add/SKILL.md) | core | Remove dead weight first. Name the observed failure or requirement that calls for a new guard. |
| [principle-minimize-reader-load](./skills/principle-minimize-reader-load/SKILL.md) | core | Collapse layers that cost more than they save and shrink mutable scope. A helper should earn its place in the caller. |
| [principle-outcome-oriented-execution](./skills/principle-outcome-oriented-execution/SKILL.md) | core | Apply during planned rewrites and migrations with explicit phase boundaries. Converge on the target architecture; don't preserve smooth intermediate states with throwaway compatibility code. |
| [principle-experience-first](./skills/principle-experience-first/SKILL.md) | core | Choose user delight over implementation convenience; ship fewer polished features over more rough ones. |
| [principle-start-from-what-exists](./skills/principle-start-from-what-exists/SKILL.md) | core | Look for working implementations before choosing whether to reuse, extend, or build. |
| [principle-exhaust-the-design-space](./skills/principle-exhaust-the-design-space/SKILL.md) | core | Build 2-3 competing prototypes and compare side by side before committing. |
| [principle-build-the-lever](./skills/principle-build-the-lever/SKILL.md) | core | Apply to any non-trivial work, not just bulk work: edits, migrations, analyses, checks. Build the tool that does it or proves it (codemod, script, generator, or a skill your subagents follow) instead of working by hand. The tool is the artifact a reviewer can rerun. |
| [principle-model-the-domain](./skills/principle-model-the-domain/SKILL.md) | architecture | Encode the domain in a structure instead of scattered conditionals. |
| [principle-boundary-discipline](./skills/principle-boundary-discipline/SKILL.md) | architecture | Validate at the boundary and trust internal types. Catch errors where the code can recover or translate them. |
| [principle-type-system-discipline](./skills/principle-type-system-discipline/SKILL.md) | architecture | Make illegal states unrepresentable, brand semantic primitives, parse external data at boundaries, exhaust variants, derive from authoritative schemas. |
| [principle-make-operations-idempotent](./skills/principle-make-operations-idempotent/SKILL.md) | architecture | Converge to the same end state regardless of partial prior runs. |
| [principle-migrate-callers-then-delete-legacy-apis](./skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | architecture | Migrate callers and delete the old API in the same wave instead of preserving compatibility layers. |
| [principle-separate-before-serializing-shared-state](./skills/principle-separate-before-serializing-shared-state/SKILL.md) | architecture | Eliminate the sharing first; serialize structurally only when one shared writer is a real invariant. |
| [principle-read-before-you-conclude](./skills/principle-read-before-you-conclude/SKILL.md) | verification | Read the source and callers a claim or edit depends on, and label what you inferred. |
| [principle-prove-it-works](./skills/principle-prove-it-works/SKILL.md) | verification | Before acting on a finding or declaring work done, check the claim against the current artifact and the path or state it depends on. |
| [principle-fix-root-causes](./skills/principle-fix-root-causes/SKILL.md) | verification | Test competing causes against the reproduction. Trace a failing check to the implementation or the check itself. |
| [principle-sequence-verifiable-units](./skills/principle-sequence-verifiable-units/SKILL.md) | verification | Check each unit before the next. A repro commit proves the expected failure and the fix proves the pass. |
| [principle-test-behavior-not-implementation](./skills/principle-test-behavior-not-implementation/SKILL.md) | verification | Apply when you write, change, or keep a test. Assert what the code's users can observe, so the test fails when that behavior breaks and keeps passing when only the internals change. |
| [principle-explain-the-number](./skills/principle-explain-the-number/SKILL.md) | verification | Find the limiter for a performance number. For an eval, check what each trial did and how far the claim holds. |
| [principle-guard-the-context-window](./skills/principle-guard-the-context-window/SKILL.md) | delegation | Read the excerpt you need or delegate the bulk reading. A subagent returns only its findings and their sources to its parent agent. |
| [principle-never-block-on-the-human](./skills/principle-never-block-on-the-human/SKILL.md) | delegation | Make reversible engineering decisions and continue independent work while a required decision waits. |
| [principle-encode-lessons-in-structure](./skills/principle-encode-lessons-in-structure/SKILL.md) | meta | Remove the opportunity for a recurring mistake, or enforce the rule where it occurs. |
| [principle-write-for-where-it-is-read](./skills/principle-write-for-where-it-is-read/SKILL.md) | meta | Write for the recipient, the task, and the context they will have when the work reaches them. |
| [principle-anchor-every-reference](./skills/principle-anchor-every-reference/SKILL.md) | meta | Give each reference its source or glossary name and enough context to identify it where it appears. |
| [principle-everything-at-hand](./skills/principle-everything-at-hand/SKILL.md) | meta | Label marks where people read them and keep the views they need to compare together at the same scale. |
| [principle-files-describe-the-present](./skills/principle-files-describe-the-present/SKILL.md) | meta | Describe what is true now. Record changes in the files whose subject is the change. |

</details>

## bundled skill dependencies

Each link opens the instructions bundled with this copy.

- From [Cursor Team Kit](https://github.com/cursor/plugins/tree/5866df557357d005b3c0c9d3da0d9e739b4bdde3/cursor-team-kit), [control-cli](./skills/control-cli/SKILL.md) drives CLIs and TUIs, [control-ui](./skills/control-ui/SKILL.md) drives browser and Electron UIs, and [deslop](./skills/deslop/SKILL.md) cleans the diff before commit. [Team Kit license](./licenses/cursor-team-kit.txt)
- [Wayfinder](./skills/poteto-mode/playbooks/wayfinder.md), [Improve codebase architecture](./skills/poteto-mode/playbooks/improve-codebase-architecture.md), [codebase-dic](./skills/codebase-dic/SKILL.md), the [Prototype methods](./skills/poteto-mode/playbooks/prototype.md), [grilling](./skills/grilling/SKILL.md), [domain-modeling](./skills/domain-modeling/SKILL.md), [research](./skills/research/SKILL.md), [to-spec](./skills/to-spec/SKILL.md) and [to-tickets](./skills/to-tickets/SKILL.md) adapt Matt Pocock's skills through MMW v5 Cloud. [Matt Pocock skills license](./licenses/mattpocock-skills.txt)
- From Cursor's built-in skills, [create-skill](./skills/create-skill/SKILL.md) authors skills.
- The HTML skills come from MMW v5 Cloud. [to-spec](./skills/to-spec/SKILL.md) uses [big-pics-little-words](./skills/big-pics-little-words/SKILL.md) to present the whole spec in HTML. [ketchup](./skills/ketchup/SKILL.md) uses [html](./skills/html/SKILL.md) for charts. [Plannotator license](./skills/html/LICENSE)

Overnight runs need a watcher or timer that can wake the agent. Inside [poteto-mode](skills/poteto-mode/SKILL.md), PR-status requests go to the [Babysit playbook](./skills/poteto-mode/playbooks/babysit.md). For app verification, use the project's `verify-<app>` for the target surface. Use [verify-this](./skills/verify-this/SKILL.md) only when no project verification skill matches.

## when do i need a spec, a plan, or tickets?

ask for [Wayfinder](./skills/poteto-mode/playbooks/wayfinder.md) to chart a direction across sessions or resume from its map or a decision ticket. once the questions are settled, give the map to [to-spec](./skills/to-spec/SKILL.md) to write the spec.

use [to-spec](./skills/to-spec/SKILL.md) to record the agreed behavior. [multi-phase plan](./skills/poteto-mode/playbooks/multi-phase-plan.md) describes what each phase should achieve, what it depends on, and how to verify it. [to-tickets](./skills/to-tickets/SKILL.md#split) splits that plan into independently assignable tickets with acceptance criteria and direct blockers. you can also request tickets directly from an agreed spec.

for a standalone problem with one outcome, reuse the original issue as the ticket. the spec issue is the direct parent of the plan issue and each execution ticket. each ticket drawn from the plan links to it. once you authorize execution, the agent writing the code receives its ticket. each code ticket gets its own PR. the PR links to the ticket, and the ticket records the PR URL. the [issue template](./skills/to-tickets/SKILL.md#issue-template) covers the first report through the verified result.

## make it yours

[poteto-mode](skills/poteto-mode/SKILL.md) is my style. you may not want exactly that.

type [automate-me](./skills/automate-me/SKILL.md). it mines your recent transcripts, drafts a `<your-name>-mode` skill from how you've actually worked, and routes through pstack underneath. you keep pstack as the base and end up with your own routing skill alongside [poteto-mode](skills/poteto-mode/SKILL.md).

models are configurable too. type [setup-pstack](./skills/setup-pstack/SKILL.md). it detects the models you have access to and saves a user-level rule mapping each role (code, judgment, the review panels) to a model. skills read it when assigning those roles.

rerun [setup-pstack](skills/setup-pstack/SKILL.md) to change a role or your reasoning budget. the rule applies to new sessions.

## automations

pstack also ships a dormant [benny automation pack](./automations/benny/). benny triages slack issue reports, then reproduces and fixes confirmed bugs with real ui evidence. its files are not registered as slash skills.

to set it up, give your agent [`FOR_AGENTS.md`](./automations/benny/FOR_AGENTS.md). setup copies the pack into the target repository at `.cursor/automations/benny/`, enables pstack there for shared skills, and keeps user configuration outside the copied pack. the deployment target is Cursor Automations.

## license

MIT
