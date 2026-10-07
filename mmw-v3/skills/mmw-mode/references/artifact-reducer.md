# The artifact reducer's prompt

Runtime forensics step 2 and Trace forensics step 1 send one subagent with this prompt, `{ARTIFACT}`, `{FORMAT}` and `{SYMPTOM}` filled in, and `{TOOLS}` replaced by the full text of the `mmw-mode` skill's `references/forensics-tools.md`, since the subagent sees nothing of this session and cannot open the mode's files by name.

```
You are reducing one diagnostic artifact to the evidence of its cause. Change no file of the repository, write nothing on the tracker, and run nothing against the product: the artifact is a fixed dataset.

Artifact: {ARTIFACT}
Format: {FORMAT}
Symptom: {SYMPTOM}

Load the artifact with the tool the table below names for its format, into a form you can query, before you read it. The artifact can carry customer data and credentials: quote none of it beyond function names, file paths of the product's own code, and numbers.

{TOOLS}

Then narrow to the cause. For CPU time, the functions and call paths that hold the most samples. For memory, what grows across snapshots and its retainer chain to a GC root; from a single snapshot, only what is largest, marked as a hypothesis. For a hang, the thread stuck on-CPU or blocked, and its wait reason.

Report at most five findings, most likely cause first. For each: what it is (the function with its file and line, the class or object and its retainer path, or the thread and its wait reason), the numbers that single it out (share of samples, retained size and its growth, time blocked), and the query or command that shows it, so it can be rerun. Then one line on what this artifact cannot show (no symbols, sampling too coarse, no paired capture). Nothing else.
```
