---
name: arena
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Arena

Fan out N parallel designs of the same task, each from its own angle. Read every candidate end to end. Pick the strongest as the base. Graft the best ideas from the others into it. Verify the synthesized result.

## Phase A: Frame

The N candidates receive the same task, so the task is the contract. Each candidate is a session of the dispatch skill's `candidate` role, all on one model, so their differences come from their angles, not from their models.

1. State the artifact each candidate is producing.
2. When the caller hands the pick to the owner, there is no rubric and Phase C is skipped. Otherwise, take the caller's rubric, or derive it. State what success looks like for *this* task, then turn it into 3-6 concrete gradeable criteria. The rubric is the picker's tool in Phases C and D. Candidates only see the task.
3. Give each candidate its angle. When the caller gives constraints, each candidate takes one. Otherwise set N angles yourself, each a different shape of the whole design, not a point fix inside one shape. N is the number of angles.
4. Assign output paths. Each candidate writes its artifact only in its own directory `candidates/<n>/`, under where the caller keeps the result, per **principle-separate-before-serializing-shared-state**.

## Phase B: Fan out

Write one brief per candidate: `## Task` the task, this candidate's angle, and the artifact shaped per the files the caller names; `## Known` the path to the shared grounding and its output directory; `## For` N designs compared against each other, where the differences are the signal. The rubric that ranks candidates stays out of the brief; a Done criterion every candidate must meet is part of the task. Send them all with one `dispatch.sh send candidate --follow "the arena skill's references/candidate.md" <brief>...` of the **dispatch** skill.

If a candidate is lost or produces no output, proceed with N-1 and note the dropout in the synthesis record.

## Phase C: Score

When the caller hands the pick to the owner, skip this phase. Otherwise, read every candidate end to end before scoring. Score each against the rubric criterion by criterion, not on holistic feel, and write the scores down before Phase D.

## Phase D: Pick

When the caller hands the pick to the owner, show the owner every candidate and take the owner's pick and combination as the base. Otherwise, pick the base a future maintainer can extend most easily without breaking invariants. When two feel tied, prefer the cleaner boundary or smaller API, per **principle-laziness-protocol**.

Record the pick and the reason in the synthesis note.

## Phase E: Graft

When the owner picked, graft only the parts the owner selected. Otherwise, walk each losing candidate once more for what is worth porting into the base, usually one or two things per candidate, not most of it. Fold each graft in by hand, per **principle-redesign-from-first-principles**, so the result stays coherent under one mental model. Don't paste mechanically.

If the candidates converge on one shape, that is strong agreement. Note it and ship the consensus shape. No graft is needed. If they wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase F: Verify

Verify the synthesized artifact like any other output, per **principle-prove-it-works**. If verification finds a problem the arena missed, either Phase A was wrong (re-frame and re-run) or a candidate caught it and you missed the graft (go back to Phase E). Don't paper over it.

## Outputs

One synthesized artifact, with a short synthesis note naming the base and why, each graft with its source candidate, what was rejected and why, any convergence or dropouts, and the verification result. The caller says where the note goes. Then remove `candidates/`, unless the caller keeps them as reference: what was taken and what was rejected lives in the note.
