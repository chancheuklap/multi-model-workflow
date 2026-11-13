---
name: ambiguity-scan
description: Review a draft spec, plan, or execution ticket when its author calls for an ambiguity scan.
disable-model-invocation: true
---

# Ambiguity scan

The main chat spawns one fresh, read-only general-purpose subagent for the stage under review. Follow [Subagents](../poteto-mode/SKILL.md#subagents). Use the `judgment and prose` model role from the operator's [model rule](../setup-pstack/SKILL.md#model-rule).

Give the reviewer the operator's goal, the work issue, the draft and its sources. Send only the matching stage brief below. For a set of tickets drafted together, send the whole set to one reviewer. Have the reviewer return its findings to the main chat. Wait for the report, then resume the calling step.

## Spec

Compare the spec with the original problem, the discussion, and any approved plan or prototype it draws on. Check that it states the user's problem, gives the agreed outcomes in the user stories, and preserves scope limits and decisions about implementation and testing. Flag any open product choice the draft treats as settled. Check that the author marks engineering choices made while drafting as "this spec's decision".

## Plan

Compare the plan with the agreed spec or design. Check that it preserves the scope and constraints. For each agreed outcome, look for the phase that covers it or the evidence the plan cites for existing behavior. In each phase, check that `Depends on` names any prerequisites, `Build` states the planned work, and `Verify` describes a check for the result in `You see`.

## Ticket

Compare each ticket with its share of the agreed work in the plan, spec, original issue, or discussion. Check that it preserves the agreed decisions, names one deliverable and its scope, and pairs each acceptance check with its expected result. Check that any direct blocker is named along with the prerequisite result it supplies. Across a batch, flag remaining work that no ticket covers or that more than one ticket claims.
