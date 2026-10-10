### Investigation

**You own the answer. Plan, route, write.**

Investigation requests are read-only. They produce a cited explanation or a recommendation, not a code change.

1. Route through the **how** skill. For motivation questions, also route through the **why** skill. For a question whose answer lives outside the repo (documentation, third-party APIs, specs, knowledge bases), route through the **research** skill.
2. Throughput checkpoint stays one line: `throughput checkpoint: n/a, read-only investigation`.
3. Produce the `how`-shaped output (Overview / Key Concepts / How It Works / Where Things Live / Gotchas), or a recommendation with a tradeoffs table if the request is a decision between alternatives. Form the recommendation per **principle-first-principles-thinking**. Every claim about a file rests on reading it; one that rests on an unread part is labeled inferred (**principle-read-before-you-conclude**).
4. Apply the **unslop** skill to the reply.

The output goes where the caller needs it. Asked by the user, it is the reply. Resolving a Research ticket on a wayfinder map, it is one Markdown file citing each claim's source, pushed to a `research/<name>` branch that is never merged, with a link commented on the ticket; that push is the only write. Dispatched by the **grilling** skill to find a fact, it goes back to grilling.

No PR, no babysit, no `architect` unless the investigation precedes a code change. If it does, hand back to the user and re-route to Bug fix or Feature.

**Reply:** the investigation output. For "are we sure?" answers, include your real judgment with reasons. Push back if the premise is wrong (see Autonomy).
