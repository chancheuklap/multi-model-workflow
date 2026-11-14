---
name: principle-explain-the-number
description: "Apply before you measure, trust, or report a performance number or an eval result. Find the limiter for performance. For an eval, check what each trial actually ran and which conclusions hold across trials."
---

# Explain the Number

- **Write the decision before you run.** Name the result that would change a decision, and the noise floor. Stop when the run-to-run spread is larger than the effect.
- **For a performance number, ask "why not double?"** Name the resource or code path that bounds the result, such as a core, a lock, the disk, the network, or the load generator itself. Get it from a profile or from system counters taken during a run, then map it to source. A guess from reading the code is not a limiter. If you cannot say why the number is not twice as good, you do not know what you measured.
- **List what else the number could be measuring, and rule out each one with evidence.** The usual suspects are errors, skipped or cached work, code that never ran, an untuned side (one left on default settings), noise, and a piece too small to matter end to end.
- **Keep the evidence with the number.** Put the run count, the spread, and the conditions in the notes or a linked artifact. For performance, include the limiter. A single run supports only a single-run observation.

For a performance number, run the full procedure with the [benchmark-checklist](../benchmark-checklist/SKILL.md) skill. For an eval result, read each trial's output. Check claims about which instructions a candidate followed against its execution record. Limit the conclusion to the scenarios and models the trials cover.

You skipped this when a run started without the result that would change a decision, when a comparison has no run count or spread, when a performance claim has no named limiter, or when the time saved is larger than the time the changed piece took.

Distinct from [principle-prove-it-works](../principle-prove-it-works/SKILL.md), which checks that an output is real.
