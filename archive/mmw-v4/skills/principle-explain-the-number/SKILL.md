---
name: principle-explain-the-number
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Explain the Number

Before measuring, and before trusting, reporting or acting on the result, establish what work it measures and what conclusion the evidence supports.

- Before the run, name the decision and the result that would change it, including the smallest meaningful difference and expected variation.
- State the claim and its scope. Evidence about one component or scenario supports that case until broader runs establish more.
- Rule out alternative explanations with evidence: errors, skipped or cached work, code that never ran, an unfair comparison, noise, or a piece too small to matter to the whole task.
- Keep the evidence with the number, including the run count, spread and conditions. A single run supports only a single-run observation. Judge a claimed difference against variation across trials.
- For an eval result, check that each trial did the task and reached the behavior being judged. Use the actual trial and transcript evidence, and distinguish a scenario-specific result from a claim across tasks or models.

The **benchmark-checklist** skill owns the performance measurement procedure, including profiling the resource limiter, tuning comparisons and repeated runs. Agent evals need evidence of task execution and a supported conclusion, not a CPU or I/O limiter by default.

Distinct from **principle-prove-it-works**, which checks that an output is real.
