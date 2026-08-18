# Prescriptive documentation

> **这页管什么**：**最该借的一页。** 别给读者一堆选项，告诉他们该做什么；以及 must / can / might / should 各自的准确含义。
>
> 来源：<https://developers.google.com/style/prescriptive-documentation> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## What it means

Prescriptive (opinionated) documentation **recommends a way** to achieve a task. It tells the reader what to do instead of giving them a list of options to choose from. When a task has several possible approaches, commit to recommending one.

## Why

It reduces reader confusion on complex tasks with multiple possible solutions.

## What it affects

- **Document purpose and structure** — content and headings organized around a clear, specific purpose.
- **Scenarios and procedures** — examples reflect the use cases most likely relevant to the readers, not exhaustive edge cases.
- **Sample commands** — commands and arguments accomplish the task for the most common use case.

## Modal verbs — the core table

**Generally avoid `should`.** It creates ambiguity and uncertainty for readers.

| Intent | Use |
| --- | --- |
| Required action | `must`, or rewrite as a direct imperative ("Do the following before you continue") |
| Recommended action | "We recommend…" / "Google recommends…". `should` is acceptable only for a widely-accepted recommendation, as in "You should use a strong password" |
| Optional action | `can` — "You can also use approach B" |
| Expected outcome | State it directly and factually — "The process returns 10 items" |
| Possible outcome | `might` or `can` — "The process can take about 30 minutes" |
| Describing state | Don't write "The value should be true". Clarify whether the reader must act, a system performs the action, or a condition triggers a next step |

Related word-list verdicts: `may` — reserve for official policy or legal considerations; for possibility use `can` or `might`, for permission use `can`. `could` — avoid; use `can`.

## Examples

- Recommended: "Ensure that the Share Button conforms to our min-max size guidelines."
- Not recommended: "The Share Button should conform to our min-max size guidelines."

- Recommended: "Whether it's a brand new project or an existing one, perform the following steps."
- Not recommended: "Whether it's a brand new project or an existing one, here's what you should do."

Direct imperatives and factual statements beat softer phrasing built around *should*.
