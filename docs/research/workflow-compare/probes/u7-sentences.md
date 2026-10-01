# U-7 sentences

One row per row of `docs/research/workflow-compare/reports/N10-mmw-routing-and-invocation.md` section 3.2 whose starting point is a sentence a person types. `before` names the entry the skill set of `6d9cf01c` offers for that starting point (the first skill of the N10 `到达` column); `after` names the entry after B1: `mmw:<slug>` is the `mmw` skill together with `playbooks/<slug>.md`, a bare name is a skill reached through the `mmw` routing list. `check_u7.py` and `run_u7.py` read this table.

| id | N10 row | before | after | sentence |
| --- | --- | --- | --- | --- |
| S01 | 1 | grill-with-docs | mmw:write-a-spec-and-tickets | I have an idea for this repository: the task board should show how long each ticket has waited in its queue. Help me work out what exactly to build. |
| S02 | 2 | wayfinder | mmw:map-a-large-effort | I want to rebuild our whole release pipeline so that it ships to three app stores, and I cannot see the way there yet. Plan it with me. |
| S03 | 3 | triage | mmw:triage-an-issue | Issue #57 was opened by someone outside the team and nobody has judged it yet. Triage it. |
| S04 | 4 | prototype | mmw:prototype | I cannot decide whether the board should poll or use server-sent events. Build something small we can run to settle it. |
| S05 | 5 | design-pages | mmw:design-a-ui | The second UI sketch from the prototype won. Take it into Claude Design and turn it into the real pages. |
| S06 | 6 | to-spec | mmw:write-a-spec-and-tickets | We have agreed on the change: tickets get a priority field and the board sorts by it. Write it up as a spec and break it into tickets. |
| S07 | 7 | dispatch | dispatch | Run spec #12 tonight. |
| S08 | 12 | implement | implement | Pick up ticket #42 yourself and implement it. |
| S09 | 14 | advisor | advisor | Before we commit to it, get a second opinion: should the board store its events in SQLite or in JSON lines? |
| S10 | 16 | exe-release | exe-release | Ship it: build an installer from the current branch. |
| S11 | 17 | handoff | handoff | I need to hand this session over to another agent on a different host. Write the handoff. |

Rows of section 3.2 that no person types, so no sentence: 8 (`advance` starts a worker), 9 (a worker starts its reviewer), 10 (the reviewer's report wakes the worker), 11 (a worker's `--closeout` wakes the orchestrator), 13 (`summary` records `spec.closed`), 15 (a worker started by `advance` is about to write a page ticket's code).
