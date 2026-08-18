# Procedures

> **这页管什么**：**给人照着做的步骤怎么写。** wizard 技能可以整页照搬。
>
> 来源：<https://developers.google.com/style/procedures> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Introductory sentences

- Introduce a procedure with context not already in the heading; don't restate it.
- End with a colon if the procedure follows immediately, a period if other material comes between.
- An imperative statement is fine, but **never a partial sentence completed by the numbered steps**.
- Recommended: "To customize the buttons, follow these steps:"
- Not recommended: "To customize the buttons:"

## Single-step procedures

Write as one sentence, formatted as a **bulleted** item, not numbered.

## Sub-steps

Lowercase letters for sub-steps; lowercase Roman numerals for sub-sub-steps. A step introducing sub-steps ends in a colon or period.

## Order of components within one step

1. Describe the action.
2. List the command, if needed.
3. Explain placeholders.
4. Explain the command further, if needed.
5. List command output, if needed.
6. Explain the result in a separate paragraph.

## One action per step

Generally use one step per action. Sequential menu selections may be combined with `>`: "Click **Next > Finish**." Split steps that become unwieldy.

## Multiple procedures for the same task

Document a single accessible procedure when possible. If several methods must be shown, separate them by page, heading, or tab. Prioritize procedures that are keyboard-completable, shortest, and use a familiar language.

## Repetitive procedures

Don't repeat a procedure — reference or link to it. "Create a user as you did in the previous step."

## Optional steps

Start with `Optional` followed by a colon.

- Recommended: "**Optional:** Type an arbitrary string…"
- Not recommended: "(Optional) Type an arbitrary string…"

## Steps that state location

**State where an action occurs before describing the action.**

- Recommended: "In the Google Cloud console, go to the **Monitoring** page."

If procedures span multiple headings, restate the context each time.

## Steps with goals

State the goal before the action, usually with a *To…* structure.

- "To start a new document, click **File > New > Document**."

If *To…* might imply the step is optional, use a colon instead: "Start a new document: click **File > New > Document**."

## Steps with results or justifications

State the action first, then the result, in the same paragraph.

- "Click **Run**. The query results appear after the query runs."
- "Store the private key in a secure location. You need it later."

## Summary of remaining rules

- Steps start with an imperative verb and use complete sentences.
- Maintain parallel structure and consistent verb form across steps.
- **Avoid directional language** (*above*, *below*) for accessibility and localization.
- **Never use *please*.**
- **Avoid "run the following command"** — describe what the command accomplishes.
- Combine an Enter keypress into the same step as the triggering action.
- Don't reference keyboard shortcuts.
- When multiple methods exist, **give only the best way**.
- **List prerequisites in advance** so readers can prepare before starting.
- Keep the number of steps minimal, and address **one reader decision per step**.
