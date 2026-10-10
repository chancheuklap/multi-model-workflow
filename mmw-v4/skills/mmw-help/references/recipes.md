# Prompts worth copying

Swap in the real paths, skills, and done checks. Informal wording works.

## Understand

- `read <thread>. restate the underlying issue in your own words, in plain english.`
- `investigate why <symptom>. give me what we know, what data you used, and your best hypotheses. don't change any code yet.`
- `use /how to understand <subsystem>. then use /why to find out why it broke recently.`
- `/recall my work on <topic> from last week, then read <issue>.`
- `/teach me why you implemented it this way and not <other way>. what did you trade off?`
- `take over this branch. read the decision log, find what's done, and continue. don't redo finished work.`

## Build

- Bug: `<symptom>. repro first, then fix and verify.`
- Bug in an app: `repro this with /verify-<app>. if it repros on the project branch, fix it and show me a video as proof.`
- Bug with a cheap test: `repro <bug> first. if there's a cheap test path, /tdd it. then fix and rerun.`
- Feature: `add <behavior>. <current output> stays byte-identical. verify both.`
- Refactor: `move <code> into one module, zero behavior change. record the current output first and prove it's unchanged after.`
- Perf: `<operation> takes <time> on <fixture>. trace it, fix the measured cause, show me before and after.`

## Design and plan

- `prototype a few options for <feature>. take screenshots or videos for me to compare.`
- `we need <feature>. /architect it first, and answer open questions with prototypes. let me review before proceeding.`
- `write a tutorial for how i would use <new package> first. then /teach me why it beats the current one.`
- `get the advisor's second opinion on this thread and our approach.`
- `turn this design into a spec, then cut it into tickets.`
- `spec the migration of <library> to <target>. the result must match the original exactly, bugs included.`

## Review and ship

- `use code-review on the whole branch. don't change anything yet. no nitpicks unless it's a real bug or regression.` Read the refutations too.
- `/swarm check every package under <dir> against its check script. one worker per package. one report.`
- A change the session wrote ends in Shared closing on its own: one pull request, merged when you say yes.
- `run spec #<n> tonight.` Run a night works the spec's tickets unattended and opens one pull request for the morning.

## Away and back

- `im going to bed. run spec #<n> tonight. don't ask me before committing.` The tickets' criteria are the done checks; write them before you leave.
- `/show-me-your-work catch me up on what you did last night.` Read its Attention section first.
- `/reflect capture what we learned so the next run doesn't repeat it.` Approve only edits that change a future decision.
- `/bro` restates the last reply in plain words.
