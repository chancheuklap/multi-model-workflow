# 解释 HTML

An `/mmw-wait-what` visualisation is a **re-pitch in pictures**. The diagrams carry the weight. Prose is sparse, in ASD-STE100 Simplified Technical English, and uses the domain docs' canonical terms. If a diagram needs a paragraph to be understood, redraw the diagram.

It is not a prototype and not Logic HTML. If they need to push buttons through a state model, go back to [SKILL.md](SKILL.md) and invoke `/mmw-prototype`.

Render it as a single self-contained HTML file. Tailwind and Mermaid both come from CDNs. Mermaid handles graph-shaped diagrams reliably; hand-built divs and inline SVG handle the more editorial visuals (cross-sections, mass, emphasis). Mix the two — don't lean on Mermaid for everything, it'll start to look generic.

Cover what they named — the last message, or a document from this conversation or the repo. Same terms as the source. Do not invent jargon, abbreviations, or code names. User wording, leaf, ADR, and code in conflict: show the conflict. Do not photocopy the source into boxes.

## Scaffold

Set `lang` on `<html>` to the language of the canonical terms on the page.

```html
<!doctype html>
<html lang="zh">
  <head>
    <meta charset="utf-8" />
    <title>{{what this re-pitches}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
      mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
    </script>
    <style>
      /* small custom layer for things Tailwind doesn't cover cleanly:
         emphasis strokes, faded internals, hand-drawn-feeling arrow heads */
      .fade { opacity: 0.4; }
      .hit { stroke: #dc2626; stroke-width: 2px; }
    </style>
  </head>
  <body class="bg-stone-50 text-slate-900 font-sans">
    <main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
      <header>...</header>
      <section id="pitch" class="space-y-10">...</section>
    </main>
  </body>
</html>
```

## Header

What this re-pitches (document name, or "last message"), and the date. A compact legend only when the diagrams use symbols the labels don't already say. No introduction paragraph — straight into the pictures.

## One article per idea

Each idea the reader must see is one `<article>`:

- **Title** — short. Names the idea, not the file heading you copied.
- **Diagram** — the centrepiece. Pick a pattern below.
- **One sentence** under it, only if the picture still needs a caption. Often it doesn't.
- **Wins / stakes** — bullets, ≤6 words each, only when the point is a contrast or a cost.

No paragraphs of explanation. One figure that shows the whole relation beats a gallery of fragments. A concrete walk-through of one real case beats an abstract cloud of boxes.

## Diagram patterns

Pick the pattern that fits what they didn't get. Mix them. Don't make every diagram look the same — variety is part of the point.

### Mermaid graph (the workhorse for relationships)

Use a Mermaid `flowchart` or `graph` when the point is "A hangs off B, C blocks D, and look at the mess." Wrap it in a Tailwind-styled card so it doesn't feel parachuted in. Style with `classDef` to colour the thing they missed.

```html
<div class="rounded-lg border border-slate-200 bg-white p-4">
  <pre class="mermaid">
    flowchart TD
      S[shared understanding] --> Spec[spec]
      Spec --> T1[path ticket]
      Spec --> T2[save ticket]
      T1 --> T2
      classDef hit stroke:#dc2626,stroke-width:2px;
      class T2 hit
  </pre>
</div>
```

### Mermaid sequence (a process over time)

Use a sequence diagram when the point is order: a request and its replies, a grilling round, a save then a publish. "Before: six turns. After: one." lives here.

### Hand-built boxes-and-arrows (when Mermaid's layout fights you)

Ideas as `<div>`s with borders and labels. Arrows as inline SVG `<line>` or `<path>` elements positioned absolutely over a relative container. Reach for this when one box must feel heavy and the others faded — Mermaid won't render that with the right weight.

### Cross-section (good for a stack of steps)

Stack horizontal bands (`h-12 border-l-4`) to show layers a thing passes through. Before: six thin layers each doing nothing. After: one thick band labelled with the consolidated responsibility. Same pattern for a pipeline, a review sequence, or a path shape.

### Two-column compare (good for "this vs that")

Two columns, side by side. Last pitch vs this re-pitch. Option A vs option B. Current vs proposed. Keep each column's diagram ~320px tall so they sit without scrolling.

### Tree (good for hang-offs)

A design tree, blocking tickets, a Context Map of leaves. Root at the top or left. Open questions faded. Settled nodes solid. Do not flatten a tree into a numbered list and call it a diagram.

### Mass (good for "this part is huge")

Two rectangles — one for the part that looks small in prose, one for the part that actually dominates. Before: they look even. After: the real mass is obvious. Use this when the last pitch hid proportion.

### Static state map (not clickable)

States as boxes, transitions as arrows, the current state marked. The reader looks; they do not drive it. Driving it is Logic HTML.

## Style guidance

- Lean editorial, not corporate-dashboard. Generous whitespace. Serif optional for headings (`font-serif` works well with stone/slate).
- Colour sparingly: one accent (emerald or indigo) plus red for the thing they missed and amber for a conflict.
- Keep diagrams ~320px tall so a compare sits side by side without scrolling.
- Use `text-xs uppercase tracking-wider` for labels inside diagrams — they should read as schematic, not as UI.
- The only scripts are the Tailwind CDN and the Mermaid ESM import. The page is otherwise static — no app code, no interactivity beyond Mermaid's own rendering.

## Tone

Plain STE100. Canonical terms from the domain docs `mmw domain path` printed. Concision is not an excuse to drift.

If a sentence could be a bullet, make it a bullet. If a bullet could be cut, cut it. No hedging, no throat-clearing, no "it's worth noting that…".

## Write and open

A named repo file: write `<stem>.html` beside it. That path already holds something else: `<stem>-explained.html`.

Last message, or anything that is not a repo file: write to the OS temp directory. Resolve the temp dir from `$TMPDIR`, falling back to `/tmp` (or `%TEMP%` on Windows). File name `mmw-wait-what-<timestamp>.html`.

Open it — `open <path>` on macOS, `xdg-open <path>` on Linux, `start <path>` on Windows — and tell them the absolute path.

The host can render an HTML fragment in the conversation: do that only when the named range is small enough that one compact figure covers it. Otherwise write the full file. Do not paste fragment source as text.
