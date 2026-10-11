# Retired playbooks

Block 6 of the v4 design (page 11) took these out of the mmw-mode skill, and page 15 took out Shared closing. Each file is kept here unchanged, so it can be read or copied back; nothing routes to it and no check reads it.

| What | Was | Replaced by |
| --- | --- | --- |
| `opening-a-pr.md` | Opening a PR, as pstack wrote it | Opening a PR is back in `skills/mmw-mode/playbooks/opening-a-pr.md`, rewritten from this file and run by One ticket and Run a night step 6. This copy stays as pstack wrote it |
| `shared-closing.md` | Shared closing, which replaced Opening a PR for a change the session wrote itself | Every change now goes through a ticket a worker builds. Its steps went to: proving it, the verification step of each playbook, run by One ticket step 4; cleaning the comments and the commit rules, Work a ticket; having it read, the reviewer Work a ticket sends; merging the latest project branch, One ticket step 5; opening and handing over the pull request, Opening a PR |
| `babysit.md`, `shipping.md` | Babysit, Shipping | A night's pull request: Run a night's steps 6 and 7, with `finish` refusing while the pull request has a red or pending check or an unresolved review thread. A day's pull request: merged with `gh pr merge` on the owner's yes |
| `autonomous-run.md`, `orchestrate.md`, `autopilot-full.md`, `autopilot-stack.md`, `multi-phase-plan.md` | Autonomous run, Orchestrate, Autopilot-full, Autopilot-stack, Multi-phase plan | The pipeline: To spec, To tickets, then Run a night |
| `scripts/orch/`, `scripts/watch-pr/`, `scripts/package.json`, `scripts/bun.lock`, `scripts/bootstrap.ts` | The tools of Orchestrate, Babysit and Shipping, and the installer of their packages | Nothing; their playbooks are gone |
| `scripts/check-plan.mjs` | Multi-phase plan's plan check | Nothing; its playbook is gone |
| `../retired-skills/interrogate/` | The interrogate skill | The code-review skill: its Correctness axis carries interrogate's correctness, root-cause and security questions, and its Standards axis the four structural ones |
