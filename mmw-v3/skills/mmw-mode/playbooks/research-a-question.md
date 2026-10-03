### Research a question

A research session answers one question that a decision waits on, and its readers come to the answer cold: the session that advances the map links the answer into the map's decisions, and the user reads the closed ticket without this session's context. The temptation is to hand the reading to another agent and pass its summary on; do the reading in this session, so that the session posting the answer is the one that checked each claim against its source. An unchecked claim does not stay in the report: the decision it feeds, and every ticket later cut from that decision, rest on it.

**Entry.**
- **Asked with the user present.** The user asks a question in this session. Start at **Name the decision it feeds** and do the research here with the `research` skill; start no other session for it. Without a research ticket, only **Name the decision it feeds**, **Run the research** and **Commit the report** apply, and **Commit the report** delivers the report through `playbooks/deliver-a-change.md`.
- **Started by `dispatch.sh research <n>`.** The start prompt's pointer `mmw-mode research-a-question#Name the decision it feeds` sends you to **Name the decision it feeds**. You run unattended, in a worktree of your own on the research ticket's `research/<n>` branch.

#### Steps

1. **Name the decision it feeds.** (judgement) Read the research ticket in full, or the user's question when there is none, and name the decision its answer feeds: a decision ticket on a map, a spec's `## Sources`, or an ADR. That decision sets what the report must answer and where the search can stop.
   Done when you can name the decision and the question the report answers for it.
2. **Run the research.** Run the `research` skill's steps in this session; start no other agent for them. A secondary write-up, a Memory record or another agent's summary is a clue: follow each claim to the source that owns it before the report states it. A point no source settles stays open in the report, with what each source says; the likeliest reading is not written as the answer.
   Done when the report file exists, cites a source for each claim, and names each point it leaves open.
3. **Commit the report.** Keep the report where the repository already keeps its research notes, as the `research` skill says. Commit it on the research ticket's `research/<n>` branch and push that branch; it merges into the base branch only on the user's command. Without a research ticket, run `playbooks/deliver-a-change.md` instead, so that the report is never left uncommitted without the user knowing.
   Done when the remote `research/<n>` branch holds the commit with the report, or, without a research ticket, `playbooks/deliver-a-change.md` has delivered it.
4. **Answer on the ticket.** Post a resolution comment on the research ticket: a link to the report file on the `research/<n>` branch, the answer in three sentences, and each point the report leaves open. Then close the ticket. A decision you took with nobody to ask goes into this comment too, as `#### Unattended outlets` says.
   Done when the ticket is closed and its resolution comment links the report file.
5. **Leave the map alone.** Leave the map's body as it is, its Decisions so far included, even though this ticket's pointer is missing from it: the session that advances the map adds the pointer. When two sessions edit one map body, the later save drops what the other wrote, so the map body keeps one writer.
   Done when this session has not edited the map's body.

#### Unattended outlets

Started by `dispatch.sh research <n>`, you have nobody to ask, and a question on the screen blocks the work until someone happens to look. Put no question on the screen: take the option the ticket and the map make most likely, and write the option you took and why into the resolution comment of **Answer on the ticket**, because the session that advances the map and the user read the closed research ticket.

**Reply:** the pushed report, the resolution comment and the closed ticket; without a research ticket, the answer in three sentences with each point left open, the report's path, and how far delivery went.
