---
name: draw-diagram
description: Settle a diagram's form before drawing it — the reader's question picks the form, the form picks the visual type, and rendering starts only after both. Use whenever a diagram or chart is the deliverable, and whenever a request to visualise, illustrate or show how something works would be answered with one.
---

# Draw Diagram

Two skills own the two halves of a good diagram, and neither knows the other exists.

- **`html-diagram` owns the form.** The question the reader must answer, which of eight shapes answers it, what has to stay visible together, and which rendering medium carries it.
- **`diagram-design` owns the drawing.** Which of its 39 visual types expresses that form, the layout grammar for it, the editorial system it is drawn in, and its own pre-output gate.

Read `html-diagram` first and settle the form. Read `diagram-design` second and draw. Where the two overlap or contradict, the rulings below decide — that is the only thing this skill adds.

## Rulings

**One canvas before two.** `diagram-design` closes its complexity budget with *"If you exceed, split into two diagrams (overview + detail)."* Split last, not first. Over budget, reach first for a type that nests — nested, layers, tree, high-level — and carry the whole subject on one canvas, the budget then binding per level: each band or container stays inside it while the canvas as a whole exceeds it. These types are written for their own canonical subjects and will need bending; a Layers example that draws no connectors between its bands does not mean your connectors come off. Split only when the subject truly holds two separate questions, and say which question each canvas answers.

**Type selection ends with `diagram-design`.** Both skills carry a selection layer. `html-diagram`'s eight forms settle what kind of question is being asked; `diagram-design`'s semantic-pattern and visual-type tables settle which type draws it. The finer instrument makes the final call.

**Inline SVG unless the form breaks it.** `html-diagram` warns against reaching for SVG merely because the output is a diagram, while every primitive, connector rule, budget and template in `diagram-design` is built on inline SVG. Draw inside that system by default. Leave it only when the settled form needs something no visual type can hold — live data at a scale that must be painted, a canvas the reader drives — and name the reason; `diagram-design` then no longer applies and `html-diagram` owns the whole job.

**Style comes from `diagram-design` alone.** `html-diagram` points at a sibling `design-artifact` skill that is not installed here, so that pointer is dead. Palette, type, and composition come from `diagram-design`'s `references/style-guide.md`.

**Take the shipped default style.** `diagram-design` opens by asking whether to customise its style guide to a brand. Answer option **(e)** and proceed with the default, unless the request is for a branded artifact.

**Keep it static.** `diagram-design`'s animation path expects a verifier that ships with its repository rather than with the installed skill. Motion needs an explicit request.

## Completion

Both skills' own gates run and both pass: `diagram-design`'s pre-output checklist plus `python3 scripts/self_check.py <file>` from its own directory, and `html-diagram`'s inspection at wide and narrow widths. Report the form settled, the visual type chosen, and whatever the budget forced out.
