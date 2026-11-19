### Eval

**You own the experiment design. Plan, blind, run, synthesize.**

**Non-negotiables for blinding:**

- No `eval`, `test`, `judge`, `experiment`, `rubric`, `score`, `compare`, `benchmark`, `candidate`, or `arena` in any directory, file, or prompt the candidate sees.
- The candidate prompt looks like an organic user request. State the goal, not the meta.
- No chain-eliciting cues. Don't ask the candidate to list which skills, principles, or files they applied. Ask for design notes generally and grade chain-following from code shape, not self-report.
- Sanitize directory and slug names. Use project-shaped names a user might pick.
- Don't tell the candidate other candidates exist.
- The judge can know it's judging but sees outputs by sanitized label only, never by variant or model name.
- Comparing two variants: one judge scores both sets in a single pass on one scale, blind to which set each came from.

**Steps:**

1. **Frame.** State what variant is under test and what behavior counts as success. Write the rubric (3-6 concrete criteria) for the judge only. Hold it back from candidates.
2. **Set up sanitized environments.** Per-candidate working dir with the variant in place. Plant any context an organic task would have: a project skeleton, the skills the candidate would naturally read.
3. **Author one organic prompt.** What a user would type. No leakage of what's being measured.
4. **Start N candidates in the background**, each a plain session in its own sanitized dir, started with the host's own command that takes one prompt and exits when the session ends, on this session's model, with the organic prompt as its whole first message. The variant under test sits in that dir's project-level skills directory. A candidate is done when its process exits. Candidates are not sent with the dispatch skill: its `Dispatched:` line, brief and report would tell the candidate it is being tested.
5. **Send one blinded judge** per `references/eval-judge.md`, on this session's model: what the candidates were asked is the organic prompt, the candidates are their dirs by sanitized label. It sees the rubric, never which variant a dir carries.
6. **Verify the chain from transcripts, not self-report.** Read each candidate's session record: where each host keeps it is listed at the head of `scripts/worktree-audit.sh`. Read only the records of the candidates' own dirs. Searching across other projects' records reads private chats from unrelated work. Look at which files each candidate actually opened. Grade chain-following from the files it really read plus the shape of the code, never from the candidate's own claims.
7. **Read every candidate output yourself** end to end. Apply **principle-explain-the-number** using step 6's trial and transcript evidence before drawing a conclusion from the results. Compare to the judge's verdict. Disagreement means a model is biased or the rubric is ambiguous. Synthesize.

**Reply:** variant under test, rubric, per-candidate notes, judge's verdict, your synthesis, and a recommendation for whether to promote the variant.
