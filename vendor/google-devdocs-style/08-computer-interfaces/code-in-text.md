# Code in text

> **这页管什么**：哪些东西要用代码字体，哪些不要；代码名不能当英文动词或复数。
>
> 来源：<https://developers.google.com/style/code-in-text> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Purpose

Code font signals verbatim entry, shows text boundaries, and separates entities from surrounding text. Use `<code>` or backticks.

## Items that get code font

Attribute names and values, class names, command output, command-line utility names, data types, database elements, DNS record types, HTML/XML element names, enum names, environment variables, filenames and paths, folders and directories, HTTP content-type values, HTTP status codes, HTTP verbs, IAM role names, IP addresses, language keywords, method and function names, namespace aliases, placeholder variables, package names, port numbers, query parameters, and strings used in commands.

**Don't put quotation marks around code** unless the quotation marks are part of the code.

## Items that do NOT get code font

- Domain names in general reference
- Product, service, and organization names
- URLs meant for browser navigation

## Conditional

- **Boolean values** — code font for the literal value, plain font when referring to the evaluation as true or false.
- **Command-line utility names** — code font for the command, regular font for the software (GCC the compiler vs `gcc` the command).
- **Email addresses** — code font only when used as input or output.

## UI elements

When a UI element also qualifies for code font, apply both code font and bold.

## Pluralizing and inflecting — one of the strictest rules

**Don't use code elements as if they were English verbs or nouns**, and don't inflect them for plural or possessive.

Add a plain-English noun after the code term and inflect that noun instead — "send a `POST` request", not treating `POST` as an action.

## Method names

Omit the class name prefix unless needed for clarity — "its `get` method".

## HTTP status codes

Call them *status codes* (not response or error codes), keep the number and name in code font, and use `2xx` notation or an explicit range.
