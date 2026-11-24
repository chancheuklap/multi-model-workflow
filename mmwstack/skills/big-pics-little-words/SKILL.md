---
name: big-pics-little-words
description: "Default entry for standalone HTML artifacts and visual explanations (diagrams, plans, reports, explainers, wireframes, mockups, prototypes). Sole implicit HTML router; delegates to html and its specialists. Not for app code or specialized skill HTML."
---

Before shaping the artifact, use [principle-write-for-where-it-is-read](../principle-write-for-where-it-is-read/SKILL.md), [principle-everything-at-hand](../principle-everything-at-hand/SKILL.md), and [principle-anchor-every-reference](../principle-anchor-every-reference/SKILL.md).

When describing supplied files or an existing system, use [principle-read-before-you-conclude](../principle-read-before-you-conclude/SKILL.md) before deciding what the artifact says.

When working from approved wording, decisions, or designs, use [principle-baseline-is-the-contract](../principle-baseline-is-the-contract/SKILL.md) before changing their presentation.

Before interpreting or presenting measured results or numerical comparisons, use [principle-explain-the-number](../principle-explain-the-number/SKILL.md) for the numbers.

## Visual craft

Show the subject with large, legible visuals and only the plain words needed to understand the details. Avoid jargon and explain as if the viewer is new here.

- **Flowcharts and logic.** Draw steps, branches, or parts as rich flowcharts with detailed, light-tinted nodes and distinct shapes, borders, and line styles per kind and state. Keep rows to at most 4 or 5 nodes so the chart reads clearly unzoomed.
- **Legends.** Above any multi-style HTML or SVG diagram, place a one-row horizontal inline-flex legend of miniature swatches, short line segments, and labels. Never build a legend from dummy nodes or a table.
- **Review pages.** A page the user reviews repeatedly keeps the skeleton that [html](../html/SKILL.md#review-pages) sets.
- **Imagery.** Use real-world pictures, icons, or visuals selectively when they add clarity. Avoid lazy decorative filler.

## Build and deliver

Open and follow [html](../html/SKILL.md) to route to the narrowest specialist (`html-diagram`, `html-plan`, `html-wireframe`, `html-prototype`, `design-artifact`) and build one self-contained `.html` file. Leave specialized-format HTML owned by another skill (such as `make-bot-ui` or `improve-codebase-architecture`'s report scaffold) to that skill.

Write a newly generated, unsaved HTML artifact to the OS temp directory and open it in the host's built-in browser when available so the operator can inspect and annotate it directly. Ask whether to archive it on first generation; if an archive skill is installed (such as `sync-html-artifact`), invoke it once approved and update the saved entry on later iterations without asking again.
