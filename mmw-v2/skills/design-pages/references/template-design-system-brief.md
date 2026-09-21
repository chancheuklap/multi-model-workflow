# Design system brief

What the user pastes into Claude Design to have it build the design system ([design-system.md](design-system.md), **Which path**). Claude Design's own design-system instructions supply everything else; the brief names the sources, the inventory, and the rules MMW adds. Fill every `<…>` from the code this design system is built from and leave none in the saved `design-system-brief.md`. It is written in English, the language of those instructions.

```markdown
Build this design system with your full design-system instructions, from the attached codebase. Where this brief adds a rule, follow both.

## Product and sources

<Product name>: <one sentence on what it is and who uses it>.
Source: <repository URL or attached folder>, the code under <paths>. Styles: <stylesheet paths>. Fonts: <font file paths>. Icons: <where they come from>.

## Component inventory

Build exactly these families, each from the file named, and no others (anything else goes under "Intentional additions" with a reason):

| Family | Source | Root markup | Parts that carry an id |
| --- | --- | --- | --- |
| <Family> | <file>:<line> | `<element class="…">` | <part>, <part> |

## UI kits

One kit for <surface>, recreating these screens from the components: <screen>, <screen>. Also write one HTML file per region below, first line `<!-- @startingPoint section="<surface>" subtitle="<one line>" viewport="<W>x<H>" -->`, showing that region alone at that size:

| Region | Size | What it shows |
| --- | --- | --- |
| <region> | <W>x<H> | <one line> |

## Rules this design system adds

1. Each component renders the same DOM the source renders: the same element types, class names and nesting. Its look comes from the source's own CSS rules, carried in a stylesheet `styles.css` imports; JSX adds no styling of its own.
2. Each component accepts a `data-ui` prop, sets it on its root element, and sets `data-ui="<that value>.<part>"` on each part the inventory lists for it.
3. Copy every numeric value exactly from the source. Copy the font files listed above; never substitute a font.
4. When you finish, list each inventory family with the component names you built for it, and anything you could not build.
```
