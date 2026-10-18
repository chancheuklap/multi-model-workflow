---
name: arena
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Arena

When the **prototype** skill's UI branch calls this skill, follow its `UI.md` for scoring, selection, and what to keep, including the exception to "Then remove `candidates/`" under `## Outputs`.

Fan out N parallel designs of the same task, each from its own angle. Read every candidate end to end. Pick the strongest as the base. Graft the best ideas from the others into it. Verify the synthesized result.

## Phase A: Frame

The N candidates receive the same task, so the task is the contract. Each candidate is a session of the dispatch skill's `candidate` role, all on one model, so their differences come from their angles, not from their models.

1. State the artifact each candidate is producing.
2. Derive the rubric. State what success looks like for *this* task, then turn it into 3-6 concrete gradeable criteria. The rubric is the picker's tool in Phases C and D. Candidates only see the task.
3. Give each candidate its angle. When the caller gives constraints, each candidate takes one. Otherwise set N angles yourself, each a different shape of the whole design, not a point fix inside one shape. N is the number of angles.
4. Assign output paths. Each candidate writes only its own directory `candidates/<n>/`, under where the caller keeps the result (under the **prototype** skill, the leaf `SKETCH/`), per the **separate-before-serializing-shared-state** principle skill.

## Phase B: Fan out

Write one brief per candidate: `## Task` the task and this candidate's angle, with the artifact and a short rationale to produce, the rationale naming the alternatives it considered and what it rejected; the artifact stays in its output directory, and the one file it reports is the `README.md` there, which carries the rationale; `## Known` the path to the shared grounding and its output directory; `## For` N designs compared against each other, where the differences are the signal. The rubric stays out of every brief. Send them all with one `dispatch.sh send candidate --follow "the brief" <brief>...` of the **dispatch** skill, or, when the **architect** skill sent you here, with `dispatch.sh send candidate --follow "the architect skill's references/runner-prompt.md" <brief>...`, and end your turn. Woken by `brief <batch> done`, follow the dispatch skill's `## On waking`.

If a candidate is lost or produces no output, proceed with N-1 and note the dropout in the synthesis record.

## Phase C: Score

Read every candidate end to end before scoring. Score each against the rubric criterion by criterion, not on holistic feel, and write the scores down before Phase D.

## Phase D: Pick

Pick the base a future maintainer can extend most easily without breaking invariants. When two feel tied, prefer the cleaner boundary or smaller API, per the Laziness Protocol.

Record the pick and the reason in a short synthesis note alongside the base artifact.

## Phase E: Graft

Walk each losing candidate once more for what is worth porting into the base, usually one or two things per candidate, not most of it. Fold each graft in by hand, per the **redesign-from-first-principles** principle skill, so the result stays coherent under one mental model. Don't paste mechanically.

If the candidates converge on one shape, that is strong agreement. Note it and ship the consensus shape. No graft is needed. If they wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase F: Verify

Verify the synthesized artifact like any other output, per the **prove-it-works** principle skill. If verification finds a problem the arena missed, either Phase A was wrong (re-frame and re-run) or a candidate caught it and you missed the graft (go back to Phase E). Don't paper over it.

## Outputs

One synthesized artifact, with a short synthesis note alongside naming the base and why, each graft with its source candidate, what was rejected and why, any convergence or dropouts, and the verification result. Then remove `candidates/`: what was taken and what was rejected lives in the note.
