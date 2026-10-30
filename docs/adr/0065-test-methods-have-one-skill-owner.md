---
date: 2026-10-30
amends: []
---

# Common testing judgments and methods belong to test-audit

The owner requested one place to iterate testing rules across MMW-consuming repositories, then approved the advisor's narrowed implementation on 2026-10-30 in [#1454](https://github.com/chancheuklap/multi-model-workflow/issues/1454). `test-audit` owns the common testing judgments and task-specific methods. TDD remains its writing method. The independent tdd, Test Behavior, Not Implementation and Run the Smallest Test Set skills are retired after their callers migrate.

## Considered Options

- Keep thin tdd and testing principles beside test-audit. Rejected because maintaining one testing behavior would still require choosing among several component homes.
- Put every method into one large file. Rejected because writing, reviewing, diagnosing failures and coordinating an audit are different tasks. Shared judgments stay in SKILL.md; explicit pointers load branch methods before their actions.
- Add an audit runner, permanent test registry or another preservation review. Rejected because native configuration, existing tickets and the existing independent Tests axis already supply those responsibilities.

## Consequences

Playbooks retain task order and authority. Product verification skills retain their run recipes and product facts. Native runners, scripts/check, verify-ticket and dispatch retain execution and evidence responsibilities. The upstream import and its adaptations are recorded in Writing for Agents' UPSTREAM.md.

ADRs 0048, 0045, 0060 and 0061 continue to hold. Whole-product maintenance remains owner-requested, frozen acceptance uses the existing contract correction route, and open-e2e may finish with explicit unfinished work. Draft command validation may accept a future test that does not exist yet; the worker's testing method and independent review establish behavioral-red evidence. These are different claims, so consolidating testing rules adds no draft-time proof gate.
