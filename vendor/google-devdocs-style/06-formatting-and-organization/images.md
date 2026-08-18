# Figures and other images

> **这页管什么**：什么时候该放图；alt 文本、截图、图注的规则。
>
> 来源：<https://developers.google.com/style/images> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## When to use images

- Only for useful visual explanations of information that is otherwise difficult to express with words.
- For screenshots, be discreet — only capture UIs important to the discussion.
- **Never use images for text, code samples, or terminal output.**
- Avoid image maps.

## Creating and saving

- Prefer SVG for diagrams (stays sharp when zoomed); otherwise PNG.
- Never use a transparent background.
- For animation, avoid animated GIFs — use MP4.
- Be consistent within a doc set on OS and visual style.
- Crop screenshots to relevant information only.
- **Never include PII.** Obscure it with a 100%-opacity solid overlay — not blur or mosaic, which can be reversed. Flatten layered formats on export.
- Use descriptive filenames.

## Introducing images

Precede most images with an introductory complete sentence, ending in a colon (immediately before) or period (if other content intervenes). Screenshots that immediately follow procedural UI text don't need one.

## Alt text

- Concise and context-aware, not a literal description.
- Empty `alt=""` for decorative images or those restating adjacent text.
- The attribute is **required** even when empty — otherwise screen readers may read the filename.
- Avoid "Image of…"; include punctuation for screen-reader pausing; keep it consistent for repeated images; avoid all caps; use full sentences or noun phrases; stay at **155 characters or less**.
- For complex images, pair a brief alt summary with a fuller text description elsewhere.

## Captions

- Optional, as are figure numbers.
- If numbered: "**Figure NUMBER.** DESCRIPTION." Complete sentences with end punctuation.
- **Never use spatial references** like "the image above" — refer to numbered figures by number.
- Don't embed the caption's wording inside the referencing sentence.

## Figure descriptions

Body text conveying the same information as the figure. Use one when the caption doesn't capture the figure's purpose. **Any new information must appear in text, not solely in the image.**

## Text in figures

- Avoid embedding explanatory text in screenshots — hurts accessibility, searchability, and localization cost.
- Keep any in-image text brief; follow sentence case.
- Don't put captions or descriptions inside the image.
- Don't invent new abbreviations to save space.

## High-resolution

Use `srcset` alongside `src`. `src` points to the standard-resolution image. The 2x image must be exactly twice the width and height (±1px). Never upscale to fake a 2x. Set explicit `width`, never `height`.

## Layout

Don't position images with `style` attributes. Avoid oversized or undersized images. Never center images. Never nest an `img` inside a `p`.
