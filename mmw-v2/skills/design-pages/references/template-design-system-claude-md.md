# Design system `CLAUDE.md`

Write the block below into the design system project's root as `CLAUDE.md`, with the three fields in `<…>` filled and nothing else changed. It instructs the agent inside Claude Design that builds and later edits the design system; that agent reads it on every conversation and sees nothing of this repository. [design-system.md](design-system.md) says when and how.

- `<product>`: one sentence on what the product is and which screens it has.
- `<source>`: where the code is: the repository URL, the branch, and the directory that holds the front end, with one line on which files decide what (markup and states, stylesheets, page shell). The agent reads it through Claude Design's GitHub connection.
- `<example data>`: where real data for the product's states is (a directory in the same repository, outside the design package), or "none".

```markdown
# What this design system is and where it comes from

This is the design system of <product>. It distils the product's look into one reusable visual vocabulary; every page designed for the product is drawn from it.

## Sources

- Code: <source>. Nothing outside it bears on the interface.
- Example data: <example data>. Use it to see the parts with real content.
- Fonts and icons already in this project are the product's own files; keep them.

The code is read only to find the parts, their states and their values. This design system is organised by part, not by the product's screen regions.

## What it holds

- Variables: colour, type scale, weights, line heights, spacing scale, radius, shadow, borders. Each has a few steps, not one value per use.
- Parts: the reusable elements the code actually renders (for example buttons in each kind, status marks, labels, badges, list rows, card shells, section headings, inputs, notices, links). Each part is one class name with its variants, written as HTML and CSS unless the product is a React component library. Each part has one card showing all its states, including hover, selected, disabled and warning.
- Foundation cards for colour, type, spacing, radius, shadow and the brand mark.
- `readme.md` in Claude Design's usual structure.

It holds no screen regions (a whole title bar, a whole sidebar, a whole dialog: those are pages in the design project), no example data, and no product logic.

## Unification

Every inconsistency in the code is unified into one standard: several ways of writing one part become one part with variants; close values join one step. When it is unclear which value to keep, ask the user.

Each unification is a row of the table headed `Unifications` at the end of `readme.md`: the part or variable; each value the code had, with the class names it was on; the unified value. The product's code is changed to follow this table.

## `task.md`

`task.md` at the project root, when present, is the work the repository's agent has set for this project now. When the user says to start or continue, do what it says, tick each item in it as you finish it, and ask the user where a choice is unclear. It never overrides the rules in this file.

## Done when

- Every card opens on its own and renders with no error.
- Every style value in the code is either the value of a variable or part, or a row of the `Unifications` table saying which step it joined.
```
