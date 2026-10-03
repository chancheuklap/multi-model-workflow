# Decide at phase boundaries

A **phase** is a chunk of work inside a session: the grilling, the implementation, the QA. The definition is fuzzy on purpose: a phase ends when you think *"ok, we're done with that"*.

At a phase boundary, choose what happens to the session's context: continue, clear, hand off, send the task to a subagent, or compact. The **phase boundary** is the gap between two phases, and it is the only place this decision belongs. Mid-phase there is no decision to make: continue, or split the work that's left into subagents. Compacting mid-phase makes the agent lose the thread.

**Why:** Every move except **Continue** turns a **primary source** into a **secondary source**: the session as it happened, replaced by a summary of it. You only pay the lossiness when staying costs more than it saves.

Emptying a session's context and compressing it into a summary both exist on every host, under a different name on each; use the one your host gives you.

**Pattern:** Work top to bottom at the boundary. The first **yes** wins.
- **Can you continue in this session?** Two things make the answer yes: the next phase needs this phase as a **primary source**, or you have enough [smart zone](https://www.aihero.dev/ai-coding-dictionary/smart-zone) left (~150k tokens) for the next phase to fit. Grilling → implementation is the standard yes: the implementation wants the reasoning verbatim, not a summary of it. Continue costs nothing and loses nothing, so rule it out before anything else.
- **Is the context irrelevant to what comes next?** Is everything in this session (the exploration, the decisions, the dead ends) disposable? If so, **clear it**. It is the cheapest move on the board: it takes no time and hands back the whole window. Clearing also isn't terminal where the host keeps the old session resumable.

  The cost of getting this wrong is one-way. Clear a *relevant* context and you lose the **why** behind what you built, and no amount of reading the diff back gets it returned.
- **Do you need to hand off?** The `handoff` skill is narrow. You need it only when you are:
  - swapping to a **new host**,
  - moving to a **new directory** or repo,
  - sending the work to a **colleague**,
  - or forking a side task you found **mid-phase** without derailing what you're doing.

  That list is the whole clause. What the `handoff` skill buys is **portability**: a file that travels. If nothing is travelling, you don't need it.
- **Can the task be done AFK?** Is it scoped tightly enough to run with you away from the keyboard, no steering? Then send it to a **subagent** and leave this session untouched. Automated review is the standard case: the agent reads the diff and reports, and you aren't needed while it does.
- **Otherwise, compact.** Relevant context, same host, same directory, and you need to stay in the loop: this is where the questions above land, and they land here often. Pass the compaction an instruction ("we're going to QA this area") so the summary keeps what the next phase needs.
