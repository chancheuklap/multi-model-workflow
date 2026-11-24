### Autopilot-stack

Run the Autopilot-full playbook, stopping at verified PRs for the operator to merge. Target either `project/<slug>` created off the integration branch (`dev` or `main`) as trunk, or target the integration branch directly.

1. **In place of step 5, stop at verified.** Continue stacking and verifying dependent PRs until every PR in the queue is verified and green at its current head, then hand the full verified stack to the operator once. After the handoff, further pushes wait for the operator's go. Once the verified stack handoff to the operator completes, close the queue's `PR owner` sessions via [host dispatch](../references/host-dispatch.md), and force-close any stuck owner on replacement. Every audit prompt names this file, so each tick keeps the stop-at-verified rule.
2. **Stack a PR only when it builds on another PR.** This is the one exception to step 3, whether the stack targets `project/<slug>` or directly targets the integration branch. Once the lower PR reaches its verified head, branch the dependent PR directly off that lower PR's branch in place of trunk per `playbooks/opening-a-pr.md`, and continue stacking until the full stack is verified. In place of step 2's rebase onto trunk, each PR rebases onto its parent PR's branch, and the stack root rebases onto trunk. A new head on the lower PR restacks the PRs above it, and a PR whose `git patch-id` the restack leaves unchanged keeps its verdict.

**Reply:** list each PR with its verdict, in place of what merged.
