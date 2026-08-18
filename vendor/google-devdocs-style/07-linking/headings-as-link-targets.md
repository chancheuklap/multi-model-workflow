# Headings as link targets

> **这页管什么**：锚点怎么写，改标题时怎么不弄断旧链接。
>
> 来源：<https://developers.google.com/style/headings-targets> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Why custom anchors

Some CMSs auto-generate anchors, but a custom anchor is recommended when you want a shorter link, expect frequent linking, or plan to revise the heading text. **The auto-generated anchor changes when you revise the heading, breaking existing links.**

## In HTML

- Preferred: wrap the heading in a `section` element with an `id`.
- Alternative: an `a` element with a `name` attribute.
- Putting the `id` directly on the heading tag is *acceptable*, not preferred.
- Anchor text: lowercase letters, hyphens between words.

## In Markdown

Append `{: #ID_OF_ANCHOR }` to the end of the heading line. `{: id='…' }` is only *acceptable*. Same casing and hyphenation rules.

## Revising headings

- If the heading changes and its anchor was auto-generated, **add a custom anchor** to prevent broken links.
- If it already has a custom anchor, leave it — unless it contains a term you want to remove.
- When revising, reuse the **original** ID string so old links keep working. Retrieve it by inspecting the heading on the published page.

## Changing an existing custom anchor

Update any links using the old anchor. Old anchor links still land on the page, but not the specific section.
