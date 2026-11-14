### Code review

**You own one review of one project branch and the single fix pass after it.** The operator names the branch once the tickets of its spec have landed on it. Distinct from Interrogate, which tries to break any diff with runs, and from Babysit, which drives one PR.

1. Run the [code-review](../../code-review/SKILL.md) skill on the branch. It returns the reviewed commit and the checked findings, each marked a hard finding or a judgement call.
2. Repair once. Record the in-scope hard findings on one execution ticket with [to-tickets](../../to-tickets/SKILL.md#open). Deliver the repair through the playbook that fits the work, in one PR whose base is the project branch. Record why any hard finding stays unrepaired. Record each unrelated defect as its own ticket and leave it. A judgement call is not a code change. Report each one with the finding, your judgment and your recommendation. Run the checks that target each correction.
3. Stop. Do not run the skill or any reviewer again, not even to confirm the repair. A second review needs a new request from the operator. Merging the project branch into trunk is the operator's decision.

**Reply:** the reviewed commit. Then for each axis the supported findings, the dropped findings with reasons, what stayed unverified, and the judgement calls. Then the corrections made after the reviewed commit, with their PR and targeted checks.
