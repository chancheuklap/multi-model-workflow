# design system — from running code, before any page is drawn

The design system exists before the first page is written. Its source is code that already runs, never a reverse extraction of a rendered product.

## Which code

- **A new product, or a remake that changes the look** — the prototype's winning variant. After the product ships, later changes take the product code as the source.
- **An existing product that keeps its current look** — the style variables and shared components (button, badge, banner, dialog, and the like) already in the product. Extracted values are reviewed before they become the standard; current defects are not copied in as rules. Skip this entry when a design system already exists and those shared components have not changed.

A remake is a new interface that does **not** keep the old look. An interface that keeps the old look is the existing-product case, even if the rest of the product is being rewritten.

## Which path

**React code.** Ask the user to start the design-sync command that ships with Claude Code (its description limits it to a React design system; its product is `_ds_bundle.js`). This skill does not call the write tool that command uses.

**Anything else** (Jinja templates, a plain JavaScript prototype). Follow [template-design-system-readme.md](template-design-system-readme.md): gather `styles.css` and `readme.md` from the code into a scratch directory. The user creates the design system in Claude Design under "Set up your design system" and uploads those two files, once per product. The repository does not keep a second copy: from then on the design system in Claude Design is the source, and a later [pull](pull.md) brings down the bound project's `_ds/` copy.

This class of product is a stretch of HTML plus class names whose look the stylesheet decides. Claude Design, given the same stylesheet and the same class list, writes the same class names. The built-in "Classical" design system is this shape (`readme.md`, `styles.css`, `_ds_manifest.json`; its `_ds_bundle.js` is a 303-byte placeholder). Component preview pages are optional and for people to look at.

## After the values change

If a bound project's `_ds/` copy does not follow a value change, write the new `styles.css` into that project's `_ds/` through MCP, then [pull](pull.md).

`_adherence.oxlintrc.json` is not a check this skill runs: the agent inside Claude Design has no linter, and those rules do not reach CSS in a `.dc.html` `<style>` block.

## Next

[edit pages](edit-pages.md).
