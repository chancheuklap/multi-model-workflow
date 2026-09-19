# Design system `readme.md`

The filename must be `readme.md`. Claude Design embeds this file, whole, into the `design-system-guide` block of the system prompt. Any other name leaves that block as a one-line instruction to list files and read "the README or base.md".

Write only visual style: which classes to use, which stylesheet to link, the visual rules, and a class-name table with a short markup example for each component. Do not put automation conventions here — page prefixes, `scene` props, `data-ui` ids. Claude Design treats the design system as visual reference; markup rules placed here carry little weight. Those conventions live in the project `CLAUDE.md`.

Fill every heading from the code this design system is built from. Leave no placeholder in the file that is uploaded.

```markdown
# <product> design system

Link `styles.css` on every page.

## Classes in use

- Layout: …
- Type: …
- Colour: …

## Visual rules

- Colour, type, space, radius, elevation — one short rule each, naming the class or variable.

## Components

| Component | Class names | Markup |
| --- | --- | --- |
| Button | `.btn` `.btn-primary` `.btn-quiet` | `<button class="btn btn-primary">…</button>` |
| Badge | `.badge` `.badge-ok` | `<span class="badge badge-ok">…</span>` |
| Banner | `.banner` `.banner-warn` | `<div class="banner banner-warn">…</div>` |
| Field | `.field` `.field-label` | `<label class="field"><span class="field-label">…</span><input></label>` |
```
