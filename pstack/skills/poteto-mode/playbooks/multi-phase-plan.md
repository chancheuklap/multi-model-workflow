### Multi-phase plan

**You own the plan, not the code. The plan is a checklist an owner runs box by box and the operator audits from the evidence.** The plan is the deliverable. Do not implement.

Start from the work issue and its agreed spec, or the agreed design in the discussion. Read the supplied spec and decision comments in full. Take the goal from Problem Statement and Solution, the outcomes from User Stories, and the constraints from Implementation Decisions, Testing Decisions, Out of Scope and Further Notes. Carry forward the prototype when it fixed a product decision.

1. When the change is one or two files with an obvious approach, skip the plan. Say so. If tickets were also requested, return the agreed scope to [to-tickets](../../to-tickets/SKILL.md). Otherwise stop.
2. Settle open questions by prototype before you write. Run the [Prototype playbook](prototype.md) for each. Keep each prototype on a throwaway branch. In Appendix A, record the branch and commit SHA with the screenshots, observed output, or timing that answers the question. Ask the operator only about a product or preference call that no run can settle. Give options (the [principle-never-block-on-the-human](../../principle-never-block-on-the-human/SKILL.md) principle skill).
   If a prototype changes an agreed product decision, record the evidence on the work issue and settle it with the operator. If the decision came from a [published spec](../../to-spec/SKILL.md#publish), update that spec before planning from it.
3. Explore with `poteto-agent` subagents and an explicit model per the Subagents section (the [principle-guard-the-context-window](../../principle-guard-the-context-window/SKILL.md) principle skill). Pick each subagent's reasoning level and fast or standard speed for the job, per the Subagents section. Each returns file pointers, conventions, test commands, and entry points. No inlined dumps.
   Compare each agreed outcome with the current implementation at its test seam. Record the evidence for behavior already in place. Plan the changes needed to close the remaining gaps.
4. Copy the skeleton below into the plan file and fill every placeholder. Unless the operator names a path, write the file under `docs/` in the coordinator's shared artifact store. Keep every heading and every sub-block in the order shown. One section per phase. Put the outcomes in the order their prerequisites allow, with evidence for each (the [principle-sequence-verifiable-units](../../principle-sequence-verifiable-units/SKILL.md) principle skill). Name the execution playbook in **How to read this**. Pick `playbooks/autopilot-full.md` when the run may merge. Pick `playbooks/autopilot-stack.md` when the operator lands the PRs. A standing program takes `playbooks/orchestrate.md`.
   In each phase, name the user stories or outcomes it delivers or enables. Use **Depends on** for the prerequisite results, **Build** for the changes that implement the agreed decisions, and **You see** for the results. Copy each user story's expected result sentence unchanged. In **Verify**, specify the check using its test seam, approved prototype, or measurement baseline. For preparatory work, name what it enables and how to prove the prerequisite is ready.
5. Write under [technical-writing](../../technical-writing/SKILL.md) in full, then [unslop](../../unslop/SKILL.md). The body is one Diátaxis mode, how-to. Appendices hold explanation and reference. Each heading states the task or the finding. No long dashes. No mid-sentence colons.
6. Run `node <poteto-mode-dir>/scripts/check-plan.mjs <plan.md>` using this skill's directory and fix every line it prints (the [principle-encode-lessons-in-structure](../../principle-encode-lessons-in-structure/SKILL.md) principle skill).
   Account for every in-scope outcome with the phase that delivers it or evidence that it already works. Check the plan against the spec's scope boundaries. Run [ambiguity-scan](../../ambiguity-scan/SKILL.md) at the **Plan** stage on the complete plan. If the scan changes the plan, rerun the checker, not the scan, on the version you hand back.
7. Hand back. For a draft-only request, return the checked file and the script's output. Otherwise use [to-tickets](../../to-tickets/SKILL.md#open) to publish the checked plan as a direct sub-issue of its spec. If tickets were requested, give [to-tickets](../../to-tickets/SKILL.md#split) the plan issue to split its remaining work and publish the approved tickets. Post the plan issue URL and the script's output, then stop. Execution starts on the operator's explicit go, under the execution playbook the plan names.

**Verification.** Plan how to prove each outcome on the real surface (the [principle-prove-it-works](../../principle-prove-it-works/SKILL.md) principle skill). Name the scenario, the artifact to save and its pass predicate. For performance, name the metric, the interleaved probe, the trunk baseline measured first, and the rule with the number that fails. For an interaction change, name the screenshots and video the operator reviews. The execution checklist below applies those checks to the PR opened for each code ticket.

**Verification skill.** Choose the project's `verify-<app>` for each affected surface. Use [verify-this](../../verify-this/SKILL.md) only where no project verification skill matches. For an outcome that touches two surfaces, cover both. Name the selected skill and how to drive the surface in **Verify**. Record a surface you cannot exercise as a risk in Appendix C.

````markdown
# <Program> plan

<Under ten lines. What changes, for whom, the rule the program enforces, and the outcomes in phase order. Link the source spec or agreed design.>

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `<poteto-mode-dir>/playbooks/<execution playbook>.md`. <Who merges, and which changes the operator reserves for review.>

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on the operator's explicit go.
- [ ] Read these from trunk at program start. Re-read them at every tick. Fill in each source repository's trunk ref and tracked paths.
  - [ ] `git show origin/main:pstack/skills/poteto-mode/playbooks/<execution playbook>.md`
  - [ ] `git show origin/main:pstack/skills/swarm/SKILL.md`
  - [ ] `git show origin/main:<tracked SKILL.md path for the selected verification skill>`
  - [ ] `git show origin/main:pstack/skills/poteto-mode/playbooks/opening-a-pr.md`
  - [ ] `git show origin/main:pstack/skills/<each other leaf skill the program uses>`
- [ ] On the operator's go, schedule an hourly audit with the prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk. Audit the operation against it and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a merge, a stuck agent and the action taken, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table, the merged list, or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
- [ ] On the operator's hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] Use the spec's execution tickets that link to this plan. If the tickets have yet to be published, use `to-tickets` to split the checked plan and publish the approved tickets.
- [ ] On the operator's go, assign a PR owner to each code ticket that can start. Give the owner the ticket URL, its acceptance criteria and the relevant plan material. Include the existing PR URL if work has already started on that PR.
- [ ] Follow the tickets' direct blockers. Independent changes branch from trunk. When the execution playbook stacks a change on work already available on another branch, use that branch as the base.
- [ ] Hold the file boundaries and the operator's review gates for the assigned work.

### PR mechanics, for every PR

- [ ] Resolve the forge once per **Opening a PR** and use it throughout the run.
- [ ] Open the ticket's PR ready on its intended base and link the two records, per **Opening a PR**. A stack child targets its parent branch.
- [ ] Run the repo's lint and typecheck once before the PR-facing push. Push with hooks on.
- [ ] Run `/deslop` before each commit and `/no-comments` before review.
- [ ] Triage every Bugbot and security-reviewer comment per `<poteto-mode-dir>/references/bugbot-triage.md`.
- [ ] Rebase onto current trunk before the code-ready report and babysit. Keep that merge base in fix rounds. Rebase again only at merge prep, on a `git merge-tree` conflict with trunk, on a CI failure that comes from a change on trunk, or when a known concurrent change to the same files lands.

### Verdict and merge, for every PR

For each code ticket, use its acceptance criteria and the relevant phase checks to fill the unit, live and perf boxes in the decision trail for its actual PR. Give each verifier the PR URL and the commit it must check.

- [ ] Unit. Run the named tests at the committed head and save the results.
- [ ] A full swarm runs once, at the code-ready head. Another full swarm runs only for new behavior, a redesign, or a large new diff. A rebase, a merge-conflict resolution, or a minor fix gets a single verifier at the new head, and a wording-only change gets none. Run each full swarm per the `swarm` skill. One gates lane. The live and perf lanes below. Two or more audit lanes, each with its own focus, that read the diff and the receipts and distrust the PR body. The root audits the receipts in the merge-ready report before the verdict.
- [ ] Live. Run ten lanes on the configured swarm workers model at the PR head. Give each a concrete scenario, a screenshot to save and a pass predicate. Run the regression lane on the same load-bearing scenario at trunk and head. If trunk lacks the feature, record that and gate the behavior the diff adds plus the end state the user waits for.
- [ ] Perf. Record the metric, interleaved probe, trunk baseline and failure rule. Measure both sides when comparable. Otherwise set absolute budgets for the new work and the user-visible end state.
- [ ] For an interaction change, post the screenshots and a 30 to 60 second video in chat. Stop at merge-ready and wait for the operator's approval.
- [ ] Judge every finding by the execution playbook's blocking rule. The verdict is clean when none blocks. A failure on trunk behavior in a lane marked `Regression lane against trunk.` is recorded against trunk and does not block the PR. A new head gets a fresh verdict, except for results that stay valid under the patch-id rule in `<poteto-mode-dir>/playbooks/shipping.md`.
- [ ] <The merge or handoff rule from the execution playbook, with the patch-id rule from `<poteto-mode-dir>/playbooks/shipping.md`.>

### Boot recipe, for every live lane

Each live lane runs on its own remote machine at the PR head. Use the verification skill named in **Verify** for the lane's surface.

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] <Start the backend and the surface. Wait for ready.>
- [ ] <Deliver input only through the user-facing driver named in Verify. Name the read-only diagnostics.>
- [ ] Save every screenshot to `/tmp/swarm-<pr-id>/worker-<n>/<slug>.png` and return links or paths the operator can open.

## Phase 1. <Goal as a verb phrase>

**Depends on.** <The result that must be available first, or None.>

**Files.**

- [ ] <The files this phase changes and why.>

**Build.**

- [ ] <One change. Name the symbol and the file. Identify the user story or outcome it enables.>

**You see.**

- [ ] <One observable result, with the exact log line or screen state. Copy the user story's expected result sentence unchanged when one exists.>

**Verify.**

- [ ] <The check to run, what passes and where to find its evidence. Name the test case, live scenario or performance probe that proves this result. For a live check, name the selected verification skill and the driver command.>

**Review gate.** <None. Or name the operator's decision.>

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

<Each open question a prototype answered, with the branch, the SHA, and the artifact links. Each question that stays unproven.>

## Appendix B. Alternatives rejected

<Each approach weighed and why it lost.>

## Appendix C. Risks

<Each risk with the outcome it affects and what to watch.>

## Appendix D. Links and reading list

<Docs to read before editing. Which changes need the `how` and `interrogate` skills. The trail per the `show-me-your-work` skill.>
````

**Reply:** the plan issue URL or draft path, the phases, their prerequisites and review gates, what the prototypes proved and what stays unproven, and the check script's output.
