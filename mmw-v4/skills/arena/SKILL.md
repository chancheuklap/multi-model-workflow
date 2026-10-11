---
name: arena
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Arena

Fan out N parallel designs of the same task, each from its own angle. Read every candidate end to end. Pick the strongest as the base. Graft the best ideas from the others into it. Verify the synthesized result.

## Start

Open a todolist with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Cross-judge
4. Pick
5. Graft
6. Verify

## Phase A: Frame

The N candidates receive the same task, so the task is the contract. Each candidate is a session of the dispatch skill's `candidate` role, all on one model, so their differences come from their angles, not from their models.

1. State the artifact each candidate is producing.
2. Derive the rubric. State what success looks like for *this* task, then turn it into 3-6 concrete gradeable criteria. The rubric is the picker's tool in Phase D. Candidates only see the task.
3. Give each candidate its angle. When the caller gives constraints, each candidate takes one. Otherwise set N angles yourself, each a different shape of the whole design, not a point fix inside one shape. N is the number of angles.
4. Assign output paths. Each candidate writes only its own directory `candidates/<n>/`, under where the caller keeps the result (under the **prototype** skill, the leaf `SKETCH/`), per the **separate-before-serializing-shared-state** principle skill.

## Phase B: Fan out

Write one brief per candidate: `## Task` the task and this candidate's angle, with the artifact and a short rationale to produce, the rationale naming the alternatives it considered and what it rejected; `## Known` the path to the shared grounding and its output directory; `## For` N designs compared against each other, where the differences are the signal. The rubric stays out of every brief. Send them all with one `dispatch.sh send candidate --follow "the brief" <brief>...` of the **dispatch** skill, or, when the **architect** skill sent you here, with `dispatch.sh send candidate --follow "the architect skill's references/runner-prompt.md" <brief>...`, and end your turn. Woken by `brief <batch> done`, follow the dispatch skill's `## On waking`.

If a candidate is lost or produces no output, proceed with N-1 and note the dropout in the synthesis record.

## Phase C: Cross-judge

After every candidate has reported, send one judge: a subagent, as mmw-mode's `## Subagents` says, on this session's model, which only reads. Its piece: score each candidate in <directories> against <rubric>, criterion by criterion, and recommend a base with your reasons. It runs in parallel with your reading in Phase D, never while candidates are still writing. Its worth is that it has not seen the reasoning that framed the task.

## Phase D: Pick a base

Read every candidate end to end before picking.

Score each candidate against the rubric criterion by criterion, not on holistic feel. Compare against the cross-judge. Agreement on the base confirms the pick. Disagreement means one of you is biased or the rubric was ambiguous. Read both rationales before deciding.

Pick the base on which candidate a future maintainer can extend most easily without breaking invariants. Prefer the cleaner boundary or smaller API when two feel tied, per the Laziness Protocol.

Record the pick and the reason in a short synthesis note alongside the base artifact, including the cross-judge's verdict.

## Phase E: Graft

Walk each losing candidate once more and identify what is worth porting into the base. The signal is usually one or two things per candidate, not most of it.

Fold each graft in by hand, per the **redesign-from-first-principles** principle skill. Don't paste mechanically. The result has to remain coherent under one mental model.

Record what was grafted, from which candidate, and what was rejected and why.

When N candidates converge on the same shape, that is a strong agreement signal. Note the convergence in the record and ship the consensus shape. No graft is needed. When N candidates wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase F: Verify

The synthesized artifact has to hold up under the same scrutiny as any other output, per the **prove-it-works** principle skill.

If verification surfaces a problem the arena did not catch, either Phase A was wrong (re-frame and re-run) or one candidate caught it and you missed the graft (go back to Phase E). Don't paper over.

## Outputs

One synthesized artifact. One short synthesis note alongside, naming the base, the grafts (with source candidate), the rejections, the dropouts if any, and the verification result. Then remove `candidates/`: what was taken and what was rejected lives in the note.
