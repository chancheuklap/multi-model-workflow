# Page project `CLAUDE.md`

Write the block below, unchanged, into the Claude Design project root as `CLAUDE.md`. It instructs the agent inside that project, not you: that agent reads it on every conversation and sees nothing of this repository.

```markdown
# Page conventions

These conventions are what the repository reads back from this project when the design is pulled. Everything else about how pages are designed is open.

## Page names

Draw one state per page, and include that state in the page name.

## Semantic markup

Use `<a href>` for navigation, `aria-expanded` for collapsible controls, `role` for popup menus, and `aria-label` for icon-only buttons.

## Copy

Every word shown on a page is the final copy.

## Decisions

Record decisions made while drawing in the project-root `设计决策记录.md`, one per line, marked `已确认` or `待确认`. Put each line under `## <n>` for the current task sheet.

## Files

A page loads only files inside this project, with the design system copy under `_ds/`. It loads no product code: its look comes from the design system and its own markup.

## `tasks/<n>.md`

`tasks/<n>.md` is the work the repository's agent has set for this project. `开始 <n>` selects that sheet; `继续` resumes the sheet already in progress in this conversation. If no sheet is selected, ask which ticket to continue. Do what the selected sheet says, tick each item as you finish it, and ask the user where a choice is unclear. It never overrides `CLAUDE.md`.
```
