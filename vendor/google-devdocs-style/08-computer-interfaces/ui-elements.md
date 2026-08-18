# UI elements and interaction

> **这页管什么**：UI 元素怎么称呼、哪个动词配哪个控件、粗体规则。
>
> 来源：<https://developers.google.com/style/ui-elements> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## General approach

**State instructions in terms of what the reader should accomplish, rather than focusing on the widgets and gestures.** When UI specifics matter for clarity, name elements explicitly.

## Bolding and naming

- **Put a UI element's name in bold** — `b` or `**`, not code font (unless it also qualifies for code font).
- Don't bold official product or feature names unless they directly label an on-page element.
- Provide surrounding context when naming an element outside a procedure.
- Follow on-page capitalization; convert all-caps or inconsistent labels to sentence case.
- **Don't use UI element names as verbs or nouns** — not "Name the account", but "In the **Name** field, enter an account name".
- Avoid slang like *hamburger icon* or *zippy*.
- Omit trailing ellipses from element labels — "Browse", not "Browse …".
- **Avoid directional language** — use a screenshot instead if needed.

## Element terminology

| Use | Not |
| --- | --- |
| window (full app window or modular sub-window) | page |
| page (web pages, console subpages) | window |
| dialog | pop-up window |
| pane, panel | section, area, column |
| section (labeled grouping within a window or pane) | — |
| command (for a menu item) | choice, menu item, option |
| navigation menu | navigation bar/pane/panel/window |
| the **LABEL** tab | — |
| box (text box); field in Google Cloud/Workspace contexts | — |
| the **LABEL** list, the **LABEL** box | — |
| checkbox: **select** / **clear**; state is *selected* / *not selected* | check / uncheck |
| expander arrow, expandable section | expando, zippy |

**Toggle**: don't use as a verb. Describe the resulting action, or state the toggle's target position.

**Radio button**: refer to it by its label or the group label, not the mechanism.

## Icons and buttons

- Use the button's label text — "Click **OK**", not "Click the 'OK' button".
- If an icon has a tooltip, include the tooltip name plus the icon before the label.
- If unsure of an icon's name, inspect its ARIA attributes.

## Verbs for interaction

Approved: *Click*, *Choose*, *Drag*, *Enable*, *Enter, type*, *Go to*, *Hold the pointer over*, *Press*, *Select*, *Tap*, *Turn on, turn off*. Use each per its word-list definition rather than interchangeably.

## Keyboard keys

- Use `<kbd>` (or monospace) for key presses; `code` formatting for literal typed input.
- Capitalize letter keys — "press Control+S".
- **Spell out modifier key names** (Command, Control, Option, Shift) — no symbols.
- Format combinations as `MODIFIER+KEY_NAME`, including Shift combos.
- Spell out ambiguous characters (comma, hyphen, period, plus).
- Cross-platform: Windows/Linux first, macOS in parentheses.
- Use *press* for key actions; *enter* or *type* for text input.

## Prepositions

**in** with dialogs, fields, lists, menus, panes, windows. **on** with pages, tabs, toolbars.
