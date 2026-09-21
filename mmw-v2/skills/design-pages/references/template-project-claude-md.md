# Design project `CLAUDE.md`

Write the block below, unchanged, into the Claude Design project root as `CLAUDE.md`. It instructs the agent inside that project, not you: that agent reads it on every conversation and sees nothing of this repository. What only you can do with these conventions, such as supplying the prototype's state list, is in [edit-pages.md](edit-pages.md).

```markdown
# Page conventions

This file is the only source of page conventions for this project. The title of a page, the `dc-import` name, and the file name are the same string.

## Page names

Every page name starts with its kind, then ` · ` (space, U+00B7, space), then the name:

| Kind | Prefix | What this page does |
| --- | --- | --- |
| app page | `App · <name>` | compose regions and switch whole-page states |
| component | `Component · <name>` | one region the user sees as a unit |
| overview | `Overview` | pan and zoom over every page at 50% |

Split `Component · ` pages by the regions the user perceives (title bar, list, form, sidebar, a group of dialogs). An `App · ` page only composes those pages and switches states; it does not define interface calls. When the product has no component boundary, one design for the whole page is allowed.

Default Claude Design guidance ("one page, one design, unless the user asks for reusable components"; "do not add props a component does not read") is overridden here.

## `scene`

Every `Component · ` page and every `App · ` page exposes one enum prop named `scene`.

- On a `Component · ` page the values are every state that will be accepted, including combined states.
- On an `App · ` page each value is one whole-page combination that will be accepted.

A feature that is not shipping is not a scene. If it must stay in the file, keep its value in `options` and list it again under `out_of_scope`, a key inside the `scene` prop itself, beside `editor` and `options`: `"scene": {"editor": "enum", "options": ["ready", "empty", "future"], "out_of_scope": ["future"]}`. Those values do not enter `scenes.json` and so do not enter the screen contract.

## `data-ui`

Every control that can be clicked or typed into, and every element whose look will be accepted, carries `data-ui="<region>.<part>"`. Repeated parts in a list share the same id.

The `<region>` is the name of the `Component · ` page the element lives on. That is what lets one region own an id prefix: an App page repeats the ids of the Component pages it composes, so the owner of a prefix can only be found again if every id on a page carries that page's name.

When a page is edited or rewritten, an existing `data-ui` attribute moves with the element that still means that part. It is removed only when that element is deleted.

## Composition

An `App · ` page `dc-import`s `Component · ` pages and passes `scene` down. A child page's `renderVals()` does not return a key named `scene`.

Every page carries `data-screen-label`.

Every `Component · ` page and every `App · ` page declares `$preview` in `data-props`, with `$preview.width` and `$preview.height` as positive integers — the size the page is drawn at. A later pull refuses a page that has `scene` and no `$preview`.

## Style

Use only design-system class names, and only selectors the editor can direct-edit: a single class, a comma pair `.a,.b`, a two-class compound `.a.b`, or a two-class descendant `.a .b` (pseudo-classes allowed).
```
