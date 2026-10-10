### Investigation

**You own the answer. Plan, route, write.**

Investigation requests are read-only. They produce a cited explanation or a recommendation, not a code change.

1. Route through the **how** skill. For motivation questions, also route through the **why** skill. For a question whose answer lives outside the repo (documentation, third-party APIs, specs, knowledge bases), send one researcher: a brief with `## Task` the question, `## Known` what you already know, `## For` what the user wants the answer for. Send it with `dispatch.sh send researcher <brief>` of the **dispatch** skill and end your turn. Woken by `brief <batch> done`, follow the dispatch skill's `## On waking`, and check the answer against the sources it cites before you use it.
2. Throughput checkpoint stays one line: `throughput checkpoint: n/a, read-only investigation`.
3. Produce the `how`-shaped output (Overview / Key Concepts / How It Works / Where Things Live / Gotchas), or a recommendation with a tradeoffs table if the request is a decision between alternatives. Form the recommendation per **principle-first-principles-thinking**. Every claim about a file rests on reading it; one that rests on an unread part is labeled inferred (**principle-read-before-you-conclude**).
4. Apply the **unslop** skill to the reply.

The output is the reply.

No PR, no `architect` unless the investigation precedes a code change. If it does, hand back to the user and re-route to Bug fix or Feature.

**Reply:** the investigation output. For "are we sure?" answers, include your real judgment with reasons. Push back if the premise is wrong (see Autonomy).
