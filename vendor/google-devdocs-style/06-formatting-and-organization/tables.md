# Tables

> **这页管什么**：什么时候用表格而不是列表；表格前必须有一句完整的介绍。
>
> 来源：<https://developers.google.com/style/tables> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Table vs list

- **Single-unit items** (language names, steps) → numbered, lettered, or bulleted list.
- **Paired data** (term/definition) → description list, or in some contexts a table.
- **Three or more related pieces of data per item** (parameter name, data type, description) → table.

## When NOT to use tables

- Not for page layout — use CSS.
- Single-row content usually isn't a good fit.
- Convert single-column tables to lists.
- Don't use tables to format code snippets.
- Don't split a long one-dimensional list into multiple columns just to save space.
- **Avoid placing tables inside numbered procedures.**

## Introducing tables

- **Precede every table with a complete sentence describing its purpose** — screen readers may not announce tables.
- Colon if the table follows immediately, period if other content intervenes.
- Refer to position as "the following table" or "the preceding table".
- Never place a table in the middle of a sentence.

## Captions

- A single table doesn't require a caption; place it near its referring text.
- Multiple tables in close proximity each need a caption, using `caption` as the table's first child.
- Format: "Table NUMBER." followed by a sentence-case description, no ending period.

## Column headers

- Sentence case, concise.
- **No ending punctuation.**
- Apply `th` only to the first row and first column; add `scope` as needed.

## Formatting

- No styling on the table element itself.
- Don't use visual cues alone to indicate headers — use `th`.
- **Don't merge cells** (`colspan`/`rowspan`).
- Sort rows logically, or alphabetically if there's no logical order.
- Split long or complex tables into separate tables.
- Never convey information through images or symbols alone in cells.

## Other

- Cells may contain multiple paragraphs; use `p`, not `br`.
- Avoid footnotes in tables; if used, place them immediately after.
- Use responsive CSS.
- Avoid linking directly to tables — reference them by number.
