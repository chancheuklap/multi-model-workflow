# HTML formatting

> **这页管什么**：文档源码的缩进、行宽、大小写约定。
>
> 来源：<https://developers.google.com/style/html-formatting> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Base standard

Follow the Google HTML/CSS Style Guide, with one exception: **don't leave out optional elements.**

## General conventions

Also apply to YAML and Markdown files:

- **No tabs** — spaces only.
- **Indent by two spaces** per level.
- Use all-lowercase for elements and attributes.
- No trailing spaces at end of line, except as needed for Markdown.

## Line length

- **Break lines at 80 characters**, with exceptions.
- Meta element content at the top of a file must be on a single line, regardless of length.
- For long URLs in links, put the URL on its own line paired with the `href` attribute.

## Code snippets in `<pre>`

- Target the same 80-character break point.
- If a file already uses a different consistent line length, match that file rather than reformatting it.
- **Line breaks must never alter the code's meaning.** If unsure about a language's syntax, ask someone who knows it.
