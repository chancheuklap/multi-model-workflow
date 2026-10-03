# Checks for upstream text

For text inside an upstream subtree, or adapted from one. These apply on top of `references/checks.md`.

An **upstream skill** (one kept in an upstream subtree, or adapted from one) enters the set as its authors wrote it. The set's work is to connect it to the workflow: what reaches it, what it hands on, which repository rule it must obey. Its text changes only where the change alters what the agent does: a step, their order, where or with what it works, what it produces or hands over. A rewording for style, clarity or the set's voice is a finding, fixed by restoring the upstream text.

- Diff the skill against upstream (the squash-commit command is in `mmw-v2/merge-notes/README.md`). A pstack file imported into a skill is recorded instead as a row of that skill's `imports.tsv`: its `source` and `commit` give the upstream text, and its `mechanical` and `judgement` columns are its merge-note. Every changed paragraph maps to a merge-note entry stating the behaviour it changes. A paragraph with no entry, or whose entry states only wording, goes back to upstream's text. A skill adapted from upstream without a merge-note is a finding.
- The merge-note's entries agree with each other and with the current text. An entry that still states a replaced rule is a finding: the next upstream pull would restore that rule.
- Connect outside the upstream text first: in the set's own skills, in a reference file added beside the upstream ones, in the line a caller reads. An upstream sentence changes only when an agent reading it would act wrongly in this workflow even with the connecting text in place.
- Checks on style (completion-criterion lines, the shape of a description, vocabulary preferences) apply to the set's own text. Upstream sentences are judged on whether they work in the workflow.
- When fewer than half of a skill's lines are upstream's, it is reviewed as the set's own text. Its upstream original remains the measure of length: an addition earns its words by a judgement the workflow needs that upstream did not.
