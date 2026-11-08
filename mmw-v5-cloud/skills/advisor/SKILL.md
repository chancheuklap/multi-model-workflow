---
name: advisor
description: "Independent second opinion whenever the user asks or the agent judges that another perspective would help with a decision, an approach, or its understanding. Useful for consequential choices, repeated failures, uncertain assumptions, and disputed interpretations at any stage."
---

# Advisor

You are the caller seeking an independent opinion. Keep your assigned role. The Advisor is a fresh agent that holds none of your context and reads the code itself, using the user's advisor model row. It is available at any stage, including outside a night or ticket.

## Decide whether to consult

When the user asks for the Advisor, proceed to the brief. Otherwise, decide whether an independent perspective would help enough to justify the consultation. Consider the cost of being wrong, uncertainty in your understanding, and whether your own investigation can settle the question. These are judgement calls, not workflow prerequisites or mandatory checkpoints.

When consulting again, include the new question, changed evidence, or the user's request for another opinion. Reading this page is not a consultation.

Done when you have identified the decision that needs an independent opinion, or returned to your task without a consultation.

## Write the brief and send it

Write the complete assignment to a temporary file. Open it with: "You are the Advisor. Read the installed dispatch skill and its references/advisor.md, then advise on the decision below. Return your answer to the caller."

Name the repository, code version, relevant uncommitted changes, and approved baselines. Include these five parts:

1. The recent user/assistant exchange, quoted.
2. Your current understanding of the problem.
3. The constraints you believe bind.
4. The options you weighed, and which way you are leaning.
5. The file paths you believe are relevant.

The test for the brief: a stranger with only this and the repository can reconstruct the decision. For a problem that resisted repeated attempts, each attempt and what it produced is the core of the evidence. Make the named sources available to the Advisor through the host's checkout or readable references.

Your framing is the thing under review, so the brief leaves the Advisor's work to the Advisor. Leave out the list of what to check, the file you would have it skip, the conclusion you expect confirmed, and the narrowing of "which option" down to one option's details.

Use the installed **dispatch** skill's Runtime section to resolve DISPATCH, then run `bash DISPATCH spawn advisor --prompt FILE --host HOST`. Send its card to a **FRESH AGENT** as dispatch describes. The assigned agent follows the Advisor role reference; this skill remains the caller's procedure.

Wait for the answer before acting on the decision. Continue independent work if there is any. A question resumes the same Advisor agent with the missing information.

Done when the Advisor has returned its answer, or you have reported why the consultation could not complete. A missing answer is not agreement.

## Use the answer and resume

The answer is advice, not a ruling: you still own the decision. Take it, or set it aside with a reason you can state. Record consequential decisions and their evidence where the next reader will look, such as the existing ticket or PR.

Keep approved baselines and authorization fixed. Pass `For the owner` to the owner as it stands. In a night, a Worker returns that section through the Coordinator. Use the current role's problem procedure for conflicts, cross-ticket effects, or decisions outside your authority; consultation does not delay a required report.

Done when you have handled the advice within your authority or returned the unresolved decision to its owner. Continue the task or conversation from which you consulted the Advisor.
