### Write a spec and tickets

**You own the batch the night will build. The user owns every product call.**

This playbook turns what the user has in mind into a batch a night can build with nobody there to ask: a published spec, and tickets that pass lint. Once the batch is published, a worker reads its ticket and the spec sections the ticket names, and whatever those leave open, the worker settles alone. **Interview** decides the batch: every branch of the design tree you did not put to the user becomes a decision made at night by someone who cannot ask. The temptation is to start writing as soon as the idea sounds clear to you; ask the whole frontier first.

**Entry.**
- **Routed from mode `## Playbooks`.** Start where **Where you are.** says.
- **Handed a design, a verdict or a fix.** A UI design from **Design a UI**, a verdict from **Prototype**, and a fix from **Bug fix** that needs several sessions each start at **Write the spec**.
- **Handed a triaged issue.** An issue from **Triage an issue** starts at **Split into several specs when it is several**, as an issue triaged `ready-for-agent` does by any other route.
- **Unattended.** This playbook runs with the user present. An unattended session that reaches it records the product question where its role records a decision (mode `## Autonomy`) and stops.

**Where you are.** Take the first line whose fact holds. Read each fact from the tracker, the repository and the user's message, never from this session's memory (**principle-resume-from-durable-state**).
- The spec is published and has no tickets → **Cut the tickets**.
- The spec's tickets are published and `--lint` reports no `ERROR` → **Hand to the night**.
- A map's `## Specs` section, or a first spec's `## Further Notes`, lists a spec with no link yet → **Split into several specs when it is several**.
- A cleared map, an issue triaged `ready-for-agent`, or a retro proposal the user approved → **Split into several specs when it is several**.
- A winning UI variant is recorded and `prototypes/<effort>/claude-design/` does not exist → **Design a UI**.
- `pull-report.md` is committed beside a pulled design package and there is no `screen-contract.yaml` → **Design a UI**.
- The user's message brings a decision already settled, and no spec exists → **Decide who checks**.
- The user brings back a filled questionnaire → **Interview**.
- Anything else → **Interview**.

#### Steps

1. **Interview.** Interview the user with the `grilling` skill, and write each term and hard decision down as the `domain-modeling` skill says; a session the user started with `/grill-with-docs` is already in this step. What is written down is all that a session resuming this playbook, and every worker of the night, will know of it. A fact from outside the repository comes first-hand, through the `research` skill. When the idea is a fix for something that has failed twice under one premise, question that premise before refining the fix (**principle-attack-the-premise**). `#### Session boundaries` holds from here through **Cut the tickets**.
   Done when the `grilling` skill's frontier is empty and the user has confirmed that you share one understanding.
2. **Settle runnable questions.** If a question needs a runnable answer (state, business logic, a UI you have to see, a library or approach you have to run), run **Prototype**. Run the prototype in this session when it fits the smart zone: it lives under `prototypes/` in this checkout, and it needs the grilling as its source. When it does not fit, follow `#### Session boundaries`. **A UI question's answer goes on, not back.** A winning UI variant goes to **Design a UI**, which returns to **Write the spec**.
   Done when every open question can be answered in conversation, or has a prototype whose leaf `README.md` records its verdict.
3. **Ask the one who knows.** A decision blocked on knowledge that lives in someone else's head goes to the `to-questionnaire` skill; then end your turn. The filled questionnaire brings the session back to **Interview**.
   Done when no decision waits on someone else's knowledge, or the questionnaire is with the user and your turn has ended.
4. **Decide who checks.** (judgement) Decide whether this is a multi-session build. In this repository the answer also decides who checks the work: the **Yes** path gives every ticket acceptance criteria a script runs, a reviewer in its own session, and a closed ticket as the record; the **No** path has none of these. Take **No** only for a change small enough that the user will check it directly. On **No**, run **Make a small change**, and this playbook ends here.
   Done when the user has heard which path the change takes and why.
5. **Split into several specs when it is several.** Judge whether what you have read is one spec or several by the rule in the `to-spec` skill's `## Process`. Several, or a reference that already carries a **spec division**: `#### Several specs from one reference`.
   Done when what you have read is one spec, or the division is written where that section says and the user has confirmed it.
6. **Write the spec.** Run the `to-spec` skill; with a division, it writes the one spec the division names next. When the source is a triaged issue, write a spec, or extend a published one through the `to-spec` skill's `references/revising-a-spec.md`, citing the issue as a source; close the issue with a comment linking that spec.
   Done when `--publish` has exited 0 for a new spec, or, for an extended one, the completion criterion of `references/revising-a-spec.md` holds; and, for a triaged issue, the issue is closed with a comment linking the spec.
7. **Cut the tickets.** Run the `to-tickets` skill on the spec's issue number. Its ambiguity scan goes to a subagent that did not draft the batch (**principle-a-second-reader-judges**). The session that drafted the tickets reads its own assumptions back as settled.
   Done when every ticket the user approved is published under the spec, with its labels and its blocking edges.
8. **Lint the batch.** Run the `verify-ticket` skill's `python3 scripts/verify-ticket.py <spec> --lint`, and fix what it reports (**principle-silence-is-never-a-pass**). Count its `LINT` lines against the batch: a lint that read the wrong batch prints nothing about this one, and reads exactly like a clean one.
   Done when `--lint` on the spec exits 0, it printed a `LINT` line for every ticket of the batch, and every `WARN` has been looked at and either fixed or kept on purpose.
9. **Hand to the night.** When the batch is a spec's night run, hand over to **Run a night**; one ticket outside a night goes to **Land one ticket**. When the night opens is the user's call: tell them which playbook runs the batch, and open nothing yourself.
   Done when the user has the spec's number and the playbook that runs its batch, and this session has written no `spec.opened`.

#### Session boundaries

Keep **Interview** through **Cut the tickets** in **one unbroken context window** (don't compact or clear until after **Cut the tickets** has run) so the grilling, spec, and tickets all build on the same thinking. Each worker of the night then starts fresh, working from its ticket.

The limit on this is the **[smart zone](https://www.aihero.dev/ai-coding-dictionary/smart-zone)**: the window (~150k tokens on state-of-the-art models) within which the model still reasons sharply. If a session approaches it before **Cut the tickets**, don't push on degraded; compress the session into a summary at the nearest phase boundary and carry on from it (**principle-decide-at-phase-boundaries**).

Emptying a session's context and compressing it into a summary both exist on every host, under a different name on each; use the one your host gives you.

When the host compressed the session in the middle of a phase, confirm with the user each decision the summary carries that `CONTEXT.md` and the ADRs do not, before **Write the spec**. Compacting mid-phase makes the agent lose the thread (**principle-decide-at-phase-boundaries**). A spec written from that summary states a decision the summary flattened as settled.

Ending your turn to wait for a questionnaire keeps this window when the filled questionnaire comes back into this same session. When it comes back in a new session, that session finds its place through **Where you are.**, reads what `CONTEXT.md` and the ADRs record from **Interview**, and confirms with the user each earlier decision it cannot find there before **Write the spec**.

#### Several specs from one reference

When what you have read is several specs, this is a judgement you hand to the user: list each spec's name, the decisions it covers by ticket name, the order they go in, and why the line falls there. Once the user confirms, write the division back to the map as a `## Specs` section, one line per spec: name, the decision tickets it covers, its position in the order, and its spec link once published. Then write the first spec only; publish it, fill its link into that line, and stop; tell the user to run **Write a spec and tickets** against the map again for the next one. When the map already carries a `## Specs` section, skip the judgement and write the first spec on it that has no link yet.

When the reference is not a map (an issue, a URL, a file, or the conversation itself), there is no map to write the division back to. Write it into the first spec's `## Further Notes` instead: one line per spec, saying what it is called, what it covers, its position in the order, and its link once published. Publish that first spec and stop; tell the user to run **Write a spec and tickets** next time with this spec's issue number. When the reference is a spec whose `## Further Notes` carries a division, write the first spec on it that has no link yet, and fill the link into its line through the `to-spec` skill's `references/revising-a-spec.md`, since that spec is already published. When every line has a link, tell the user the division is fully written and stop.

Stopping ends the specs this session writes; the spec it wrote still goes on to **Cut the tickets**.

**Reply:** the spec's link; each ticket's number and worker grade; the last `--lint` result; the product questions still waiting on the user. On the **No** path of **Decide who checks**, the path the change takes and why, instead.
