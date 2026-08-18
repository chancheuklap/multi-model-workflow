# Lists

> **这页管什么**：有序、无序、描述式列表各自的用途；平行结构与标点。
>
> 来源：<https://developers.google.com/style/lists> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## List vs table

- Multiple structured properties per item → table.
- Sequential information or a simple collection → list.
- **Don't use a list to show only one item.**

## Types

- **Numbered lists** — sequences where order matters (steps, phases, priorities). Nested sub-lists use lowercase letters or Roman numerals.
- **Bulleted lists** — non-sequential items such as options or examples. **Make it clear whether every item is required.**
- **Description lists** — terms paired with definitions; useful for glossaries (`dl`, `dt`, `dd`).
- **Description lists with run-in headings** — bulleted format highlighting a term followed by an explanation; saves space.

## Introductory sentences

- Precede a list with context, typically a complete sentence.
- Colon when the list follows immediately; period when other material intervenes.
- **Don't split a sentence across the intro and the list items** — the lead-in must be a complete sentence on its own.
- If a heading already provides context, an intro sentence isn't required.

## Parallel structure

Use the same syntax and structure for all items in a given list.

## Capitalization and punctuation

**Numbered, lettered, and bulleted lists:**

- Start items with a capital letter unless case carries meaning.
- End items with punctuation, **except** when an item is a single word, lacks a verb, is entirely in code font, or is entirely link text or a title.
- Fix inconsistent punctuation by parallel construction, or by adding end punctuation uniformly.

**Description lists:**

- Capitalize each term; don't punctuate the term itself.
- Descriptions typically end with a period.

**Run-in heading lists:**

- Capitalize the heading; end it with a period or colon, consistently within the list.
- Text after a period starts capitalized; text after a colon starts lowercase.
- Descriptions following a period end with a period. Following a colon, only if they include a verb or complete thought.
- **Don't use dashes** to separate a term from its description.

## Comma-separated lists in prose

Use serial commas. **Don't close a list with *etc.* or *and so on*** — instead phrase the introduction to signal the list is non-exhaustive.

## Other

- List items may contain multiple paragraphs; use `p` elements, not `br`.
- Nonstandard numbering uses the `reversed` attribute; avoid manual `value` setting.
