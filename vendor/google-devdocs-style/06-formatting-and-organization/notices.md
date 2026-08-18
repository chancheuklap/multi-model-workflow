# Notes and other notices

> **这页管什么**：**Note / Caution / Warning 的分级，以及绝不能塞进 note 的东西。** 读者会跳过 notice。
>
> 来源：<https://developers.google.com/style/notices> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## General principles

- Notices set apart important information outside the main text flow.
- **Readers skip elements on the page, including notices, that are outside their focus of interest.**
- If unsure whether something warrants a notice, draft it as regular text first, then decide.
- Avoid overuse: when you use multiple notices on a page, they lose their visual distinctiveness.
- Avoid stacking notices back-to-back. If it seems unavoidable, the content should probably be reorganized.

## The four types

1. **Note** — an ordinary aside or tip; useful but not critical.
2. **Caution** — tells the reader to proceed carefully.
3. **Warning** — stronger than caution: "Don't do this", or an irreversible action (permanent data loss, security risk, financial loss).
4. **Success** — confirms a successful action. **Don't use in ordinary static pages** — interactive or dynamic content only.

## When to use a Note — all three must hold

- The information is relevant but **not necessary** — the reader can skip it and still succeed.
- Interrupting the reader isn't disruptive; it doesn't divert them onto a different path.
- The content isn't a natural continuation, result, or pointer already part of the surrounding flow.

## When NOT to use a Note

- **Not** for cross-references.
- **Not** for prerequisites or earlier steps — that information comes before the step.
- **Not** to replace or contain a procedural step.
- **Not** for information the reader needs in order to succeed.
- **Not** for content already in flow with the preceding text, such as an expected result.

## Formatting

Use the site's standard notice styling. Rendered examples follow a **Bold label: sentence** pattern.

```html
<aside class="note"><b>Note:</b> All VPC networks include firewall rules.</aside>
```
