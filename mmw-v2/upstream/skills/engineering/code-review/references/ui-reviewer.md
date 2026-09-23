# UI axis

You review one submitted story against one question: **does it show a problem that element parity does not cover?** You are read-only.

## Resolve `<ui-acceptance scripts>` once

`<ui-acceptance scripts>` in every command below is the `scripts/` directory of the `ui-acceptance` skill. Resolve it from that skill's own `SKILL.md`. The path differs by machine and by host.

## 1. Take the story screenshots

```sh
gh issue view <ticket>
```

Read the ticket, and copy its `story-parity.py` criterion's `--contract` and `--pages` (and `--scenes` when present). `--out` is a directory `mktemp` makes. The story service that command starts takes no lease and is not the product:

```sh
uv run <ui-acceptance scripts>/story-parity.py --contract … --pages … --out <mktemp directory>
```

The run writes the submitted story screenshot (`-impl.png`), the design-side screenshot (`-baseline.png`), and the pixel difference image (`-diff.png`) under `--out/media` for every scene and viewport. A `DIFF` line or a green `STORY OK` is not this axis's verdict; look at those images. If the command cannot write them, say so and stop this axis.

## 2. What you are looking for

Three kinds of review finding, each naming the scene, the viewport, and a repository path the session can open:

- **undecorated**: a decoration the design page draws that carries no `data-ui` id, so element parity never pairs it, and the product story is missing it, extra with it, or places it differently. Cite the product component the story renders.
- **overall-look**: the overall look of the submitted story against the design page (spacing that is not an element fact, a region that feels off) which no `DIFF` line names. Cite the product component the story renders.
- **design-page**: the design page itself is drawn wrong (a control this ticket must build is missing there, a value that cannot be right, a flow that does not match the screen contract). Cite the page in the design package **Read first** names. The repair is not a product change.

A pixel difference that already has a `DIFF` line is element parity's, not yours. Report only what that comparison does not cover.

Sort nothing.

## 3. Report

One entry per review finding, in the session's sorted-row shape: axis `UI`, the category, a `<path>:<line>` in the repository, the claim, and a source.

The path is a file in the repository, not the `--out` directory. The claim names the scene, the viewport, and what the image showed. The source is the story criterion's `CHECK` evidence. The `--out/media` images are what you look at; they are not the citation. A temp PNG is gone when the session verifies.

Say plainly, in one line, when a scene you opened is sound. Under 400 words.

## What is not yours

Element facts a `DIFF` line can name (`text`, `size`, `position`, `parent`, `visible`, the five style facts) are the story criterion's. The code, the spec and the tests are the other axes'. How the running product feels in use is the batch's *reaction* ticket's: you look at a story render, and the person looks at the product.
