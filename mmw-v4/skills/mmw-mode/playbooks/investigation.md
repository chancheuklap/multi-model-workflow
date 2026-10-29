### Investigation

**You own the answer. Plan, route, write.**

Investigation requests are read-only. They produce a cited explanation or a recommendation, not a code change.

1. Route through the **how** skill. For motivation questions, also route through the **why** skill. For a question whose answer lives outside the repo (documentation, third-party APIs, specs, knowledge bases), send one researcher: a brief with `## Task` the question, `## Known` what you already know, `## For` what the user wants the answer for. Send it with `dispatch.sh send researcher --follow "the research skill" <brief>` of the **dispatch** skill and end your turn. Woken by `brief <batch> done`, follow the dispatch skill's `## On waking`, and check the answer against the sources it cites before you use it.
2. Throughput checkpoint stays one line: `throughput checkpoint: n/a, read-only investigation`.
3. For a question the owner asked directly, draw the `how` output, and for a motivation question the `why` output, as one page, as the **how** skill's `## Step 4. Present` and the **why** skill's `## Step 5. Present` say, and give the conclusion and page location in the reply. With both on one page, the `how` output is drawn as the current shape that the `why` output sets beside the earlier one, not as a second picture. For a decision between alternatives, show the alternatives side by side on that page, and give the recommendation and reasons in the reply, so the owner compares the options in one view. Form the recommendation per **principle-first-principles-thinking**. For a question handed over by another playbook or skill, return the `how`-shaped output, or the `why` output, as text. Every claim about a file follows **principle-read-before-you-conclude**. A claim that a value is, or is not, overwritten, reset or kept names every place that writes it, startup paths included, found by searching for its writers rather than by reading one function's description. A claim that two values agree says what makes them agree; agreement a mechanism forces is not evidence that either value is right.
4. Apply the **unslop** skill to the reply.

For a question the owner asked, the reply gives the conclusion and page location. When a playbook or skill handed you the question instead of the owner (a fact the **grilling** skill needs, a research ticket of a map), the output goes back to that step as one Markdown file that names the question and opens with `## Answer`, at most three sentences a reader can act on. It goes in your temporary directory unless that step names a place.

No PR and no sketch. When the investigation precedes a code change, hand back to the user and re-route to Bug fix or Feature.

**Reply:** the investigation output. For "are we sure?" answers, include your real judgment with reasons. Push back if the premise is wrong (see Autonomy).
