# API reference code comments

> **这页管什么**：API 参考注释：类、方法、参数、返回值、异常各自的起句模式。
>
> 来源：<https://developers.google.com/style/api-reference-comments> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Requirements

The API reference **must** describe every class, interface, struct, constant, field, enum, typedef, and method — including parameters, return values, and exceptions thrown.

Strong suggestions:

- Include a short code sample (~5-20 lines) at the top of each unique reference page.
- Put API names, classes, methods, constants, and parameters in code font, linked to their reference page.
- Put string literals in code font with double quotation marks.
- Match class name spelling and capitalization to the actual code.
- **Don't pluralize class names** — "Intent objects", not "Intents".

## Classes, interfaces, structs

- The opening sentence states the purpose, using detail not obvious from the name.
- **Don't repeat the class name** in the first sentence.
- Avoid "this class will/does…".
- **Avoid a period before the sentence actually ends** — some generators cut text at the first period. Write "for example" instead of "e.g."
- Craft the first sentence carefully: doc tools often pull it into summary lists.

## Members (constants and fields)

Keep descriptions minimal; link to any methods that use the constant or field.

## Methods

The first sentence briefly identifies the action; later sentences cover usage, prerequisites, exceptions, and related APIs. Use present tense.

| Method type | Start with |
| --- | --- |
| Operation returning data | An action verb — "Adds a new bird to the ornithology list and returns the ID of the new entry." |
| Boolean getter | "Checks whether…" |
| Non-boolean getter | "Gets the…" |
| Enabling a setting | "Sets the…" |
| Updating | "Updates the…" |
| Deleting | "Deletes the…" |
| Registering | "Registers…" |
| Callback | "Called by…" then "Subclasses implement this method to…" |
| Convenience constructor | "Creates a…" |

## Parameters

- Capitalize the first word and end with a period.
- Non-boolean parameters ideally start with *The* or *A*.
- Boolean parameters that trigger behavior: explain both true and false outcomes.
- Boolean parameters describing state: "True if …; false otherwise."
- Don't put *true* or *false* in code font or quotes in these descriptions.
- For parameters with defaults, explain behavior per value, then state the default with the label "Default:".

## Return values

Keep brief.

- Non-boolean: start with "The…"
- Boolean: "True if …; false otherwise."

## Exceptions

- If the generator auto-inserts "Throws", begin with "If…" — "If no key is assigned."
- Otherwise begin with "Thrown when…"

## Deprecations

Name a replacement, and the version where deprecation began. Only the first sentence appears in summaries, so put the essential replacement there — "Deprecated. Use #CameraPose instead."
