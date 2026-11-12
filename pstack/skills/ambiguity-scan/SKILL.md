---
name: ambiguity-scan
description: Review a draft spec, plan, or execution ticket when its author calls for an ambiguity scan.
disable-model-invocation: true
---

# Ambiguity scan

The main chat spawns one fresh, read-only [`poteto-agent`](../../agents/poteto-agent.md) for the stage under review. Follow [Subagents](../poteto-mode/SKILL.md#subagents). Use the `judgment and prose` model role from the operator's [model rule](../setup-pstack/SKILL.md#model-rule).

Give the reviewer the absolute path to the bundled `poteto-mode/SKILL.md` in its environment, the operator's goal, the work issue, the draft and its sources. Send only the matching stage brief below. For a set of tickets drafted together, send the whole set to one reviewer. Have the reviewer return its findings to the main chat. When the brief is empty, it reports that the criteria for that stage are pending. Wait for the report, then resume the calling step.

## Spec

## Plan

## Ticket
