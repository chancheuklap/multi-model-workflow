### Write a spec and tickets

**You own the batch the night will build. The user owns every product call.**

This playbook turns what the user has in mind into a batch a night can build with nobody there to ask: a published spec, and tickets that pass lint. Once the batch is published, a worker reads its ticket and the spec sections the ticket names, and whatever those leave open, the worker settles alone. **Interview** decides the batch: every branch of the design tree you did not put to the user becomes a decision made at night by someone who cannot ask. The temptation is to start writing as soon as the idea sounds clear to you; ask the whole frontier first.

**Entry.** A fix that `playbooks/bug-fix.md` found needs several sessions starts at **Write the spec**, with the cause and the feedback loop as its source. A change that `playbooks/make-a-small-change.md` found needs several sessions starts at **Interview**, with what that session found as its source. Any other entry starts where **Where you are** says.

**Where you are.** Take the first line whose fact holds. Read each fact from the tracker, the repository and the user's message, never from this session's memory.
- The spec is published and has no tickets → **Cut the tickets**.
- A map's `## Specs` section, or a first spec's `## Further Notes`, lists a spec with no link yet → **Write the spec**.
- The spec's tickets are published and `--lint` reports no `ERROR` → **Hand over**.
- A cleared map → **Write the spec**.
- The user's message brings a decision already settled, and no spec exists → **Decide who checks**.
- The user brings back a filled questionnaire → **Interview**.
- Anything else → **Interview**.

#### Steps

1. **Interview.** Interview the user with the `grilling` skill, and write each term and hard decision down as the `domain-modeling` skill says. What is written down is all that a session resuming this playbook, and every worker of the night, will know of it. A fact from outside the repository comes first-hand, through the `research` skill. When the idea is a fix for something that has failed twice under one premise, question that premise before refining the fix (`principles/principle-attack-the-premise.md`). `#### Session boundaries` holds from here through **Cut the tickets**.
   Done when the `grilling` skill's frontier is empty and the user has confirmed that you share one understanding.
2. **Settle runnable questions.** If a question needs a runnable answer (state, business logic, a UI you have to see, a library or approach you have to run), build a prototype with the `prototype` skill in this session, with the grilling as its source. When it does not fit the smart zone, follow `#### Session boundaries`.
   Done when every open question can be answered in conversation, or has a prototype whose leaf `README.md` records its verdict.
3. **Ask the one who knows.** A decision blocked on knowledge that lives in someone else's head goes to the `to-questionnaire` skill; then end your turn. The filled questionnaire brings the session back to **Interview**.
   Done when no decision waits on someone else's knowledge, or the questionnaire is with the user and your turn has ended.
4. **Decide who checks.** (judgement) Decide whether this is a multi-session build. The answer also decides who checks the work: the **Yes** path gives every ticket acceptance criteria a script runs, a reviewer in its own session, and a closed ticket as the record; the **No** path has none of these. Take **No** only for a change small enough that the user will check it directly. On **No**, run `playbooks/make-a-small-change.md`, and this playbook ends here.
   Done when the user has heard which path the change takes and why.
5. **Write the spec.** Run the `to-spec` skill on what **Interview** settled, or on the reference the user gave.
   Done when the spec is published and `--publish` exited 0, or, for a published spec that had to change, the completion criterion of the `to-spec` skill's `references/revising-a-spec.md` holds.
6. **Cut the tickets.** Run the `to-tickets` skill on the spec's issue number.
   Done when every ticket the user approved is published under the spec, with its labels and its blocking edges, and `--lint` on the spec reports no `ERROR`.
7. **Hand over.** Tell the user the spec's number, and that its tickets are ready for a night. When the night opens is the user's call: this session starts nothing.
   Done when the user has the spec's number, and this session has started no worker.

#### Session boundaries

Keep **Interview** through **Cut the tickets** in **one unbroken context window**, so the grilling, the spec and the tickets all build on the same thinking; each worker of the night then starts fresh from its ticket. When the session nears the end of its smart zone before **Cut the tickets**, decide at the nearest phase boundary as `principles/principle-decide-at-phase-boundaries.md` says.

When the host compressed the session in the middle of a phase, confirm with the user each decision the summary carries that `CONTEXT.md` and the ADRs do not, before **Write the spec**. A spec written from that summary states a decision the summary flattened as settled.

Ending your turn to wait for a questionnaire keeps this window when the filled questionnaire comes back into this same session. When it comes back in a new session, that session finds its place by **Where you are**, reads what `CONTEXT.md` and the ADRs record from **Interview**, and confirms with the user each earlier decision it cannot find there before **Write the spec**.

**Reply:** the spec's link; each ticket's number and worker grade; the last `--lint` result; the product questions still waiting on the user. On the **No** path of **Decide who checks**, the path the change takes and why, instead.
