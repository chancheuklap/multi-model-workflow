---
name: system-map
description: Map something that already exists — a feature, a repository, a workflow, a skill, a plugin — onto one diagram holding the whole of it. Use when asked to visualise, diagram or chart an existing system, to show how its parts connect, or to find its dead ends and its redundancy.
---

# System Map

A reader asks for a map because prose made them hold the system in their head and they could not. The map succeeds when they see the whole of it at once and can point at the part that is wrong.

So the drawing is the last step, not the first. Survey the system, mark its faults, then draw — and draw it on **one canvas**, because a reader holding two canvases in their head is back where they started.

Two vendored upstream skills do the drawing. They sit next to this file under `vendor/`; resolve its absolute path once and read them from there. They know nothing about this workflow, so §3 carries the rulings that bind them.

## 1. Survey

Fix the boundary first. Name the entry point; everything it reaches while it runs is inside. What runs later — triggered by whatever this system installed, configured or scheduled — is outside. Write the outside down as excluded rather than drawing it.

Then read the inside end to end. Take the row closest to what you were handed, and say which row you took:

| Handed | Read |
| --- | --- |
| A repository or feature | Entry points, then every module they reach; the config that wires them |
| A workflow or pipeline | Every stage, its trigger, and the artifact it hands the next stage |
| A skill | Its `SKILL.md` in full, every reference it points at, every script it calls |
| A plugin | Its manifest, every skill and command it ships, the hooks it installs |

Come out with two lists: every **node** (a part that acts or holds state) and every **edge** (one part reaching another, labelled with what actually crosses).

Two nodes that always travel together are one node — collapse them now, while you can still see why.

The survey is complete when every node on your list has its inbound and outbound edges written down, and you have opened every file the table sends you to. Say how many you opened.

## 2. Mark the faults

Faults are what the reader came for. Walk the two lists and tag:

- **Dead end** — a node with inbound edges and no outbound one, where the flow was supposed to continue.
- **Orphan** — a node nothing reaches. Confirm against the filesystem before tagging; a name you failed to grep for is not an orphan.
- **Redundancy** — two nodes doing one job, or two edges carrying one thing.
- **Unlabelled edge** — a connection you could not name what crosses. This is a fault in the system or a gap in your survey; say which.

Carry every tag into the drawing as a visible mark. A fault you found and left off the canvas is a fault the reader will not find.

## 3. Draw

Read the two upstream skills in this order. Each owns a different decision, and where they overlap the rulings below settle it.

1. `vendor/html-diagram/SKILL.md` — owns **whether and how**: the question the reader must answer, and the rendering method that answers it.
2. `vendor/diagram-design/SKILL.md` — owns **which and what it looks like**: the visual type, its layout grammar, and the editorial system.

Four rulings, each overriding what the upstream file says:

**One canvas.** `diagram-design` reads *"Above 9 nodes, it's probably two diagrams."* Here, above nine nodes reach for a type that nests — nested, layers, or high-level — and hold the system on one canvas. Take the closest of the three and bend it: each is written for its own canonical subject, and Layers in particular draws no connectors between its bands at all. Your §1 edges go on the canvas whatever the type's own example omits. Its density budget then binds per **level** — each self-contained visual region, one band or one container, stays inside the budget on its own while the whole canvas exceeds it.

**Type selection is `diagram-design`'s.** Both files carry a selection layer. Use `html-diagram` to decide that a diagram is the right answer at all and what to render it with; take the type itself from `diagram-design`'s semantic-pattern and visual-type tables, which are the finer instrument.

**Style comes from `diagram-design` alone.** `html-diagram` points at a sibling `design-artifact` skill. That skill is deliberately not vendored here and the pointer is dead — palette, type and composition come from `diagram-design`'s `references/style-guide.md`.

**Take the shipped default style.** `diagram-design` opens by asking whether to customise the style guide to a brand. Answer option **(e)**, proceed with the default, unless the reader asked for a branded artifact. A map is read once to understand something, not shipped to a client.

Keep the map static. The animation path's verifier is the one script this vendored copy leaves behind.

## Completion

The map is done when all four hold:

- Every node and edge from §1 is on the canvas, and every fault from §2 carries a visible mark. Near-identical edges may collapse into one connector under a labelled key naming each target — drawn once, none dropped.
- It is one file, and one canvas inside that file.
- Both mechanical checks pass, run from the `diagram-design` directory: `python3 scripts/verify-geometry.py <file>` reports zero findings, and `python3 scripts/self_check.py <file>` passes.
- The prose beside it carries only what the canvas cannot show — the reason behind a fault, a question the survey could not settle. Sentences restating what the reader can see get deleted.
- You state what you left out and why.
