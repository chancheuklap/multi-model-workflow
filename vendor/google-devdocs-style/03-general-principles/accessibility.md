# Writing accessibly

> **这页管什么**：方向词、链接文字、alt 文本、颜色不能单独承载信息。
>
> 来源：<https://developers.google.com/style/accessibility> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Directional language

Avoid *above*, *below*, *right-hand side* — they fail for accessibility and localization. Use *earlier*, *preceding*, or *following*.

- Recommended: "In the preceding diagram, clients run jobs on multi-team or single-team clusters."

If a UI element is hard to locate, provide a screenshot rather than describing its position.

## Link text

- Link text must make sense when read out of context.
- Never use *click here* or *read this document* as link text.
- Use *see* when referring to links and cross-references.
- If a link triggers unexpected behavior (download, new tab, jump to section), explain that behavior.
- Avoid placing links directly adjacent to each other.

## Alt text and images

- Provide an `alt` attribute for every image.
- Decorative images get empty alt text.
- Don't introduce new information solely through images.
- **Never use images of text, code, or terminal output.**
- Prefer SVG over PNG.

## Color-only meaning

- Don't rely on color, size, or location as the primary way of communicating information.
- If color or icon indicates state, pair it with a text label change.
- Refer to UI elements by label, not visual description — "Notifications", not "the bell icon".

## Structure for screen readers

- Use semantic tagging; prefer native HTML elements.
- Avoid unnecessary font formatting — screen readers describe text modifications explicitly.
- Maintain heading hierarchy without skipping levels.
- No empty headings.
- Avoid camel case and all caps — some screen readers read letters individually.
- Minimize reliance on punctuation for meaning; not all punctuation is read.
- Introduce tables and interactive elements in preceding text — screen readers don't always pre-announce them.
- Use proper table markup (`th`, `scope`, `headers`); avoid merged cells.
- Ensure full keyboard navigability.
- Never use `visibility:hidden` or `display:none` for content.
- Content must remain understandable without sound, images, color, and punctuation.
