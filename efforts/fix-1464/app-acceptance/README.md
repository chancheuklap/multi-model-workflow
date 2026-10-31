# Codex App live workflow acceptance

Candidate: `5e621872d6ad87a8375581bd0065c5f99f174a7f`.

The owner requested a demonstration in the actual MMW repository, without installing the candidate. The coordinating chat used a frozen copy of the candidate scripts and an isolated MMW_HOME. No installed skills, hooks, live model configuration or installed checkout were changed.

## Actual workflow

The original coordinating chat ran `dispatch.sh send worker` for three independent tickets. Each worker ran the unchanged Work a ticket playbook, committed only its identity evidence and used `dispatch.sh send reviewer`. Each independent reviewer shared its worker's ticket worktree, ran the four review axes and posted reviewer.reported. The existing relay queued that report to the worker; a new worker turn consumed it and closed the ticket through verify-ticket.

| Ticket | Worker chat | Reviewer chat | Branch | Result |
|---|---|---|---|---|
| [#1471](https://github.com/chancheuklap/multi-model-workflow/issues/1471#issuecomment-6539977077) | `01a19093-aac0-7b42-8e55-5c75fc742870` | `01a19097-11d8-7cd0-8d8f-96e3de52bc58` | `issue-1471` | CLOSED, ticket.passed |
| [#1472](https://github.com/chancheuklap/multi-model-workflow/issues/1472#issuecomment-6539989448) | `01a19094-1270-7141-84f2-867fa0f0615f` | `01a19097-ccdc-73a3-9346-5d15366ea3d3` | `issue-1472` | CLOSED, ticket.passed |
| [#1473](https://github.com/chancheuklap/multi-model-workflow/issues/1473#issuecomment-6539967207) | `01a19094-851e-7800-a91c-e3691d76ac5d` | `01a19096-5608-7e10-aef9-5a1735bf088d` | `issue-1473` | CLOSED, ticket.passed |

Each ticket worktree is `/Users/cheuklapchan/multi-model-workflow/.worktrees/issue-<ticket>`. The worker and reviewer identities are distinct; all three ticket worktrees and branches are distinct. The six chats remain visible in the Codex sidebar section `MMW 正式演示 · Workers 与 Reviewers`.

## Notification evidence

While the coordinating turn remained active, notifications accumulated in the App's pending-message queue. Reading another chat's status did not consume those notifications. After the coordinating turn ended, this chat received `#1471 child.opened` in a new App turn. That child had already been resolved, so the wake required no repeated work. The relay log separately records reviewer.reported delivery to each worker and ticket.passed delivery to the coordinating chat.

The first two workers found a missing closing quote in their ticket CHECK. The coordinator corrected the ticket source, resolved contract children #1474 and #1475 through dispatch route, and resumed the same workers. Neither the frozen runtime nor the workers' identities were replaced.

## Checks and limits

- `CHECK PASS default: 10 steps in 450s` on the candidate runtime code.
- App adapter unit suite: 15 tests passed. The codexappdispatch isolated integration scenario passed.
- Real App: three worker starts, three worker-dispatched independent reviewer starts, reviewer reports, worker automatic continuation and three ticket.passed closeouts.
- All files in the frozen runtime matched its recorded hashes after the run.
- The review reports cover the workers' identity evidence, not an independent review of all adapter source.
- No candidate installation, promotion to dev/main or release. Installed App hooks and App restart recovery were not accepted by this demonstration.
- Chats, worktrees and ticket branches remain available for inspection; evidence tasks were not landed into the product branch.

The frozen runtime was `/tmp/mmw-app-demo-20261031-1540/toolbox/mmw-v4`; its isolated coordination home was `/tmp/mmw-app-demo-20261031-1540/home`. Local raw evidence is in that run's `evidence/`, including the tracker responses and formal-acceptance.json.
