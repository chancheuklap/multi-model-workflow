# Anthropomorphism

> **这页管什么**：别把软件写成人：用 specifies 不用 tells，用 detects 不用 sees。
>
> 来源：<https://developers.google.com/style/anthropomorphism> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Rule

Don't attribute human qualities to software or hardware.

## Why

It falls under figurative language: less precise, and often harder to understand and translate than direct language.

## Examples

- Recommended: "A Delimiter object **specifies** where to split a string."
- Not recommended: "A Delimiter object **tells** the splitter where a string should be broken."

- Recommended: "The PC **detects** a new device."
- Not recommended: "The PC **sees** a new device."

Avoid verbs implying human communication or perception (*tells*, *sees*) in favour of neutral technical verbs (*specifies*, *detects*).

## MMW note

MMW roles (`worker`, `planner`, `reviewer`) are agents that genuinely act, report, and stop. Describing what they do is not anthropomorphism. This page applies to describing *code*, not agents.
