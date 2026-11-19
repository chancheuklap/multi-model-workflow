### Investigation

**You own the answer. Plan, route, write.**

Investigation requests are read-only. They produce a cited explanation or a recommendation, not a code change.

1. Route a question about this repository through the **how** skill, and for motivation questions also through the **why** skill. Route a question about the world outside the repository to one researcher: write the question and what the owner wants it for to a file, and run `dispatch.sh brief researcher <file>`; the researcher leads with the **research** skill. When sessions are started, end your turn until the relay wakes you with `brief <batch> done`; on that wake, follow the **dispatch** skill's `## On waking`, then the next step, and close the batch once its answer is used.
2. Produce the `how`-shaped output (Overview / Key Concepts / How It Works / Where Things Live / Gotchas), the researcher's answer checked against its cited sources, or a recommendation with a tradeoffs table if the request is a decision between alternatives.
3. Apply the **unslop** skill to the reply.

No commit and no ticket. If the investigation precedes a code change, hand back to the owner and re-route to Bug fix or Make a small change, or, when the change needs a decision of the owner's, to Write a spec.

**Reply:** the investigation output, written to the owner per **Writing the reply**: what the thing does and why, and what that means for the product, not a walk through the code, since `how` writes for an engineer and the owner does not read code. For "are we sure?" answers, include your real judgment with reasons. Push back if the premise is wrong (see Autonomy).
