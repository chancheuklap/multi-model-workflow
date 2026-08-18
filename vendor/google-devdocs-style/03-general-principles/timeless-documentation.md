# Timeless documentation

> **这页管什么**：别写会过期的词。寿命长的文档（ADR、术语表）尤其适用。
>
> 来源：<https://developers.google.com/style/timeless-documentation> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Principle

Describe the current state of the product without anchoring to a point in time. Timeless writing focuses on how the product works right now — not on how it changed from previous versions.

Benefits: less maintenance to keep docs current; no assumption that the reader knows older versions.

## Examples

| Avoid | Use instead |
| --- | --- |
| "These **new** subcommands let you interact with HTTP load balancing." | "These subcommands let you…" |
| "…aren't **currently** supported" | "…aren't supported" |
| "The emulator **now** supports the following filters" | "The emulator supports…" |

## Four categories of problematic language

1. **Words implying promises or strategy** — *eventually* can accidentally reveal roadmap plans.
2. **Words already implied by context** — docs are assumed current, so *currently* is redundant.
3. **Words that expire quickly** — *soon*, *latest*.
4. **Words assuming prior context** — if you must use *new*, pair it with a specific reference: "The January 14, 2021 release of BigQuery includes a new resource panel."

## The list to avoid in product docs

`as of this writing` · `currently` · `does not yet` · `eventually` · `existing` · `future, in the future` · `latest` · `new, newer` · `now` · `old, older` · `presently, at present` · `soon`

## Exceptions

Time-bound language is fine in dated material (blog posts) and in step-by-step instructions describing a transitional state — for example, a VM going offline soon after a shutdown command.
