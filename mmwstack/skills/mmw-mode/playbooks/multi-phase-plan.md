### Multi-phase plan

**You own the plan, not the code. The plan is a checklist an owner runs box by box and the operator audits from the evidence.** The plan is the deliverable. Do not implement.

Start from the work issue and its agreed spec, or the agreed design in the discussion. Read the supplied spec and decision comments in full. Take the goal from Problem Statement and Solution, the outcomes from User Stories, and the constraints from Implementation Decisions, Testing Decisions, Out of Scope and Further Notes. Carry forward the prototype when it fixed a product decision.

1. When the change is one or two files with an obvious approach, skip the plan. Say so. If tickets were also requested, return the agreed scope to [to-tickets](../../to-tickets/SKILL.md). Otherwise stop.
2. Settle open questions by prototype before you write. Run the [Prototype playbook](prototype.md) for each. Keep each prototype on a throwaway branch. In Appendix A, record the branch and commit SHA with the screenshots, observed output, or timing that answers the question. Ask the operator only about a product or preference call that no run can settle. Give options (the [principle-never-block-on-the-human](../../principle-never-block-on-the-human/SKILL.md) principle skill).
   If a prototype changes an agreed product decision, record the evidence on the work issue and settle it with the operator. If the decision came from a [published spec](../../to-spec/SKILL.md#publish), update that spec before planning from it.
3. Locate the relevant files, conventions, test commands, and entry points.
   Compare each agreed outcome with the current implementation at its test seam. Record the evidence for behavior already in place. Plan the changes needed to close the remaining gaps.
4. Copy the skeleton below into the plan file and fill every placeholder. Unless the operator names a path, write the file under `docs/` in the coordinator's shared artifact store. Keep every heading and every sub-block in the order shown. One section per phase. Put the outcomes in the order their prerequisites allow, with evidence for each (the [principle-sequence-verifiable-units](../../principle-sequence-verifiable-units/SKILL.md) principle skill). Name the execution playbook in **How to read this**. Pick `playbooks/autopilot-full.md` when the run may merge. Pick `playbooks/autopilot-stack.md` when the operator lands the PRs.
   In each phase, name the user stories or outcomes it delivers or enables. Use **Depends on** for the prerequisite results, **Build** for the changes that implement the agreed decisions, and **You see** for the results. Copy each user story's expected result sentence unchanged. In **Verify**, specify the check using its test seam, approved prototype, or measurement baseline. For preparatory work, name what it enables and how to prove the prerequisite is ready.
5. Write under [technical-writing](../../technical-writing/SKILL.md) in full, then [unslop](../../unslop/SKILL.md). The body is one Diátaxis mode, how-to. Appendices hold explanation and reference. Each heading states the task or the finding. No long dashes. No mid-sentence colons.
6. Run `node <mmw-mode-dir>/scripts/check-plan.mjs <plan.md>` using this skill's directory and fix every line it prints (the [principle-encode-lessons-in-structure](../../principle-encode-lessons-in-structure/SKILL.md) principle skill).
   Account for every in-scope outcome with the phase that delivers it or evidence that it already works. Check the plan against the spec's scope boundaries. Run [ambiguity-scan](../../ambiguity-scan/SKILL.md) at the **Plan** stage on the complete plan. If the scan changes the plan, rerun the checker, not the scan, on the version you hand back.
7. Hand back. For a draft-only request, return the checked file and the script's output. Otherwise use [to-tickets](../../to-tickets/SKILL.md#open) to publish the checked plan as a direct sub-issue of its spec. If tickets were requested, give [to-tickets](../../to-tickets/SKILL.md#split) the plan issue to split its remaining work and publish the approved tickets. Post the plan issue URL and the script's output, then stop. Execution starts on the operator's explicit go, under the execution playbook the plan names.

**Verification.** Plan how to prove each outcome on the real surface (the [principle-prove-it-works](../../principle-prove-it-works/SKILL.md) principle skill). Name the scenario, the artifact to save and its pass predicate. For performance, name the metric, the interleaved probe, the trunk baseline measured first, and the rule with the number that fails. For an interaction change, name the screenshots and video the operator reviews. The named execution playbook applies those checks to the PR opened for each code ticket.

**Verification skill.** Choose the project's `verify-<app>` for each affected surface. Use [verify-this](../../verify-this/SKILL.md) only where no project verification skill matches. For an outcome that touches two surfaces, cover both. Name the selected skill and how to drive the surface in **Verify**. Record a surface you cannot exercise as a risk in Appendix C.

````markdown
# <Program> plan

<Under ten lines. What changes, for whom, the rule the program enforces, and the outcomes in phase order. Link the source spec or agreed design.>

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Execution follows `<mmw-mode-dir>/playbooks/<execution playbook>.md` with the project-specific parameters in **Execution setup** below.

Tests alone are not sufficient verification. Check each applicable unit, live, and perf requirement against its evidence.

## Execution setup

- [ ] Set the target trunk to `project/<slug>` (`git fetch origin && git push origin origin/<integration>:refs/heads/project/<slug>`) or to `<integration>` directly when running `playbooks/autopilot-stack.md`.
- [ ] Run `<mmw-mode-dir>/playbooks/<execution playbook>.md` (`autopilot-full.md` or `autopilot-stack.md`) against that trunk once the operator gives explicit go. Under `autopilot-stack.md`, follow `playbooks/autopilot-stack.md` so each dependent phase branches directly off its parent PR's verified branch until the full stack is verified.
- [ ] <Name the operator review gates and handoff point (`project/<slug>` merge and `/code-review project/<slug>` before integration merge, or handing the verified `autopilot-stack.md` stack to the operator once).>

### Boot recipe

The coordinator dispatches a fresh, read-only PR verifier independent of the author in the task's execution environment. Once the coder has stopped and its worktree is clean at the exact pushed PR head SHA (`git status` empty and `HEAD` matching the PR `headRefOid`), assign the verifier to inspect that same worktree; create a separate local worktree or cloud workspace when the coder is still concurrently modifying that worktree or when the cloud environment requires one. Isolate ports and runtime data when verifiers share a machine, or run conflicting checks in sequence. Use the verification skill named in **Verify** for each affected surface.

- [ ] Confirm the verifier's assigned worktree or cloud workspace is clean at `<head SHA>` (or run `git fetch origin <head-branch> && git checkout <head SHA>` in a separate workspace).
- [ ] <Start the backend and the surface. Wait for ready.>
- [ ] <Deliver input only through the user-facing driver named in Verify. Name the read-only diagnostics.>
- [ ] Save the evidence for each scenario at the location named in the ticket or plan and return links or paths the operator can open.

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
- [ ] Hand the verified `autopilot-stack.md` stack to the operator once, or stop after every `project/<slug>` PR merges for `/code-review project/<slug>` and final integration merge.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

<Each open question a prototype answered, with the branch, the SHA, and the artifact links. Each question that stays unproven.>

## Appendix B. Alternatives rejected

<Each approach weighed and why it lost.>

## Appendix C. Risks

<Each risk with the outcome it affects and what to watch.>

## Appendix D. Links and reading list

<Docs to read before editing. The trail per the `show-me-your-work` skill.>
````

**Reply:** the plan issue URL or draft path, the phases, their prerequisites and review gates, what the prototypes proved and what stays unproven, and the check script's output.
