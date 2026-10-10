# Retired playbooks

Block 6 of the v4 design (page 11) took these out of the mmw-mode skill. Each file is kept here unchanged, so it can be read or copied back; nothing routes to it and no check reads it.

| What | Was | Replaced by |
| --- | --- | --- |
| `opening-a-pr.md` | Opening a PR | The Shared closing playbook (`skills/mmw-mode/playbooks/shared-closing.md`) and its `#### The pull request`, which carries this file's PRs, Titles, Descriptions and Readiness text |
| `babysit.md`, `shipping.md` | Babysit, Shipping | A night's pull request: Run a night's steps 6 and 7, with `finish` refusing while the pull request has a red or pending check or an unresolved review thread. A day's pull request: merged with `gh pr merge` on the owner's yes |
| `autonomous-run.md`, `orchestrate.md`, `autopilot-full.md`, `autopilot-stack.md`, `multi-phase-plan.md` | Autonomous run, Orchestrate, Autopilot-full, Autopilot-stack, Multi-phase plan | The pipeline: To spec, To tickets, then Run a night |
| `scripts/orch/`, `scripts/watch-pr/`, `scripts/package.json`, `scripts/bun.lock`, `scripts/bootstrap.ts` | The tools of Orchestrate, Babysit and Shipping, and the installer of their packages | Nothing; their playbooks are gone |
| `scripts/check-plan.mjs` | Multi-phase plan's plan check | Nothing; its playbook is gone |
| `../retired-skills/interrogate/` | The interrogate skill | The code-review skill: its Correctness axis carries interrogate's correctness, root-cause and security questions, and its Standards axis the four structural ones |
