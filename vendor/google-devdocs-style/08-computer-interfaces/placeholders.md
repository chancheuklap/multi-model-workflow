# Placeholder formatting

> **这页管什么**：占位符全大写下划线；多个占位符后面跟 Replace the following: 列表。
>
> 来源：<https://developers.google.com/style/placeholders> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Naming

- **Don't use a single `x` or a series of `x`s** as placeholders; use something informative. (Exception: contexts like HTTP status codes where `xx` is standard.)
- Use **uppercase characters with underscore delimiters** — `API_NAME`, `METHOD_NAME`. Not hyphens, lowercase, or camelCase.
- If uppercase-underscore doesn't suit the context, use an alternative but be internally consistent.
- **Don't use possessive adjectives** — no `MY_API_NAME` or `YOUR_API_NAME`.

## Syntax

- **Inline code placeholder**, HTML: `<code><var>PLACEHOLDER_NAME</var></code>`
- **Inline code placeholder**, Markdown: backticks wrapped in asterisks
- **Inline non-code placeholder**, HTML: `<var>PLACEHOLDER_NAME</var>` only
- **Code blocks**, HTML: `<pre>` with each placeholder in `<var>`
- **Code blocks**, Markdown: a code fence — formatting can't be applied inside a fence
- Brackets, braces, and ellipses that indicate optional or repeatable arguments **don't go inside the `var` element**

## Explaining placeholders

**Explain each placeholder the first time it's used.** Repeat explanations in long documents, with multiple placeholders, or where reading is non-linear.

### One placeholder

"Replace PLACEHOLDER with a description of what the placeholder represents."

### Two or more

Introduce a list with **"Replace the following:"**

- List placeholders **in the order they appear in the command**.
- Format: code + `var` element, then a colon and a description **starting with a lowercase letter**.
- If the description includes an example, introduce it with an em dash or *such as*.

### In output examples

Tag placeholder text in output with `var`. After the output, introduce the list with **"This output includes the following values:"**, in the order they appear.
