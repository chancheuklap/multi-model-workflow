# Prompts worth copying

Swap in the real paths, skills, and done checks. Informal wording works.

## Understand

- `/mmw-mode read <thread>. restate the underlying issue in your own words, in plain english.`
- `/bro <long or messy ask>`
- `/reframe <your rough description or files>`
- `/sharpen <the prompt you're about to send>`
- `/mmw-mode investigate why <symptom>. give me what we know, what data you used, and your best hypotheses. don't change any code yet.`
- `use /how to understand <subsystem>. then use /why to find out why it broke recently.`
- `/recall my work on <topic> from last week, then read <issue>.`
- `/teach me why you implemented it this way and not <other way>. what did you trade off?`
- `/mmw-mode take over this branch. read the decision log, find what's done, and continue. don't redo finished work.`

## Build

- Bug: `/mmw-mode <symptom>. repro first, then fix and verify.`
- Bug in an app: `/mmw-mode repro this with /verify-<app>. if it repros on main, fix it and show me a video as proof.`
- Bug with a cheap test: `/mmw-mode repro <bug> first. if there's a cheap test path, /write-tests it. then fix and rerun.`
- Feature: `/mmw-mode add <behavior>. <current output> stays byte-identical. verify both.`
- Refactor: `/mmw-mode move <code> into one module, zero behavior change. record the current output first and prove it's unchanged after.`
- Perf: `/mmw-mode <operation> takes <time> on <fixture>. trace it, fix the measured cause, show me before and after.`

## Design and plan

- `/mmw-mode prototype a few options for <feature>. take screenshots or videos for me to compare.`
- `/mmw-mode we need <feature>. /architect it first, and answer open questions with prototypes. let me review before proceeding.`
- `/mmw-mode write a tutorial for how i would use <new package> first. then /teach me why it beats the current one.`
- `ask /arena for a second opinion on this thread and our approach.`
- `/advisor should we keep the queue in memory or move it into the database?` The configured advisor returns an independent verdict. Say `advisor on` to have it consulted before major decisions and when the agent is stuck.
- `/mmw-mode turn this design into a plan. show each phase's outcome, dependencies, and verification steps.`
- `/mmw-mode plan the migration of <library> to <target>. include visual regression checks for each phase. the result must match the original exactly, bugs included.`

## Review and ship

- `/create-formal-verification-skill prove <property> holds in <module>, even when <steps> interleave or retry.` After merges or refactors in that code: `/maintain-formal-verification-skill`.
- `Check every package under <dir> against its check script. one worker per package. one report.`
- `/mmw-mode open the pr. small ordered commits, evidence in the description.`
- `/mmw-mode babysit this pr. get it green.` For status only: `/mmw-mode check on pr <number>. anything outstanding?`
- `/mmw-mode land the stack.`
- `/mmw-mode code review project/<name>.` One review of the finished branch and one fix pass, then it stops.

## Away and back

- `/mmw-mode im going to bed. <goal> in a fresh worktree off <base>. done means <checks>. keep a decision log. don't ask me before committing. keep checking until done. if you're truly stuck after a few hours, stop and write up why.`
- `/show-me-your-work catch me up on what you did last night.` Read its Attention section first.
- `/ketchup` catches you up on this chat since your last message and lists every call that waits on you.
- `/mmw-mode full autopilot on this queue. each item is independent.`
- `/mmw-mode autopilot these changes, but don't merge. i'll land them.`
- `/correct retro on this session. capture durable lessons in skills or repo checks.` Approve only edits that change a future decision.
- `/bro` restates your goal, then restates the last reply in plain words. Say what you need, such as `/bro what changed while I was away`, and it hands off to the matching skill.
