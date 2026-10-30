# Export to PNG / SVG

Convert a generated diagram HTML file into a portable `.svg` and/or `.png` next to it. **Manual only — never run unprompted.**

## Trigger

Load this file when:

- The user invokes `/diagram-design:export-diagram <html-file>` (the plugin's slash command — defined in `commands/export-diagram.md` at the repo root).
- The user asks in natural language to export, save, rasterize, convert, or download a diagram in `.svg` or `.png` form. Typical phrasings:
  - "export this as PNG"
  - "save as SVG"
  - "give me a PNG of that diagram"
  - "rasterize it"
  - "convert to png and svg"

The slash command is a thin wrapper that delegates here — both paths run the same procedure below.

## Scope

Both formats are **diagram-only** — just the `<svg>` node. Editorial wrappers (header, summary cards, footer in `-full` variants) are intentionally dropped: the export deliverable is the diagram itself, suitable for Figma, slides, social cards, or blog images.

The SVG-only export keeps the source `<title>` and `<desc>` with the diagram. Their per-diagram and per-variant prefixed IDs keep accessible names unique when several figures share a page.

Inlining several exported SVGs in one host document also requires namespaced `<defs>` IDs (markers, patterns, gradients, filters, clip paths, masks, symbols). The export procedure prefixes those IDs with the source file slug and rewrites matching `url(#…)` / `href="#…"` references, so a light figure next to its `-dark` twin does not silently share arrowheads. The accessible-name guarantee alone is not enough.

If the user explicitly asks for "a screenshot of the whole page including the cards", that's a different request — fall back to a normal full-page screenshot via the user's OS or browser.

## SVG export procedure

**Prefer the packaged helper.** From this skill's directory run:

```
python3 scripts/export_svg.py <html-file> [<out.svg>] [--system-fonts]
```

The packaged helper owns the transform. Run it rather than reconstructing its parser from a prose recipe.

The helper preserves nested SVG content, conditional CSS, root selectors, keyframes and inherited typography. It namespaces definitions and references, normalizes HTML syntax for XML, and preserves the diagram's accessible title and description. Unsupported CSS bindings fail before output is written.

Use `--system-fonts` for an SVG without the Google Fonts import. This keeps the file offline and uses the installed font stacks. The default includes the font import.

### Caveat to surface to the user

Tools that don't fetch remote fonts at import time (offline Illustrator, some Figma import paths, older SVG viewers) will substitute typography. The SVG renders correctly in any modern browser. For pixel-perfect portability, recommend the PNG export.

## PNG export procedure

Render **the original HTML** (not the extracted SVG) and screenshot only the `<svg>` element's bounding box. This keeps font loading reliable (already wired in the source HTML) while satisfying the "diagram only" rule. The PNG always has a **transparent background** (`omit_background=True`) so it can be placed on any slide or doc colour without a white halo. For motion-enabled HTML, append `?motion=static`, await `document.fonts.ready`, and assert the motion root has `data-frame="static"` before capture; never export at an arbitrary wall-clock delay.

### Detection

Before running anything, verify Playwright is installed in the Python interpreter
you will use for the export. Try:

```
python3 -c "import playwright"
```

If that fails, try `python -c "import playwright"` (the usual command on
Windows). Use whichever interpreter passes the import for the rasterization
command below. If both imports fail, surface this exact instruction to the user
and stop:

> Playwright is not available. PNG export requires an approved Playwright
> installation and a compatible browser to be provisioned by the host
> environment; the skill never installs runtime dependencies automatically.
> Then ask me to export again.

Don't auto-install. The user asked for one feature, not a system change.

### Rasterize

Write the snippet below to a temp file and run it with the interpreter that
passed detection: `python3 <tmp.py> <src.html> <out.png>` or
`python <tmp.py> <src.html> <out.png>`:

```python
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
import sys, pathlib

src, out = sys.argv[1], sys.argv[2]
scale = int(sys.argv[3]) if len(sys.argv) > 3 else 2

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(device_scale_factor=scale)
    page.goto(f"file://{pathlib.Path(src).resolve()}", wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PlaywrightTimeoutError:
        # proxied networks may stall webfont subrequests past any deadline;
        # cancel the outstanding load so the capture below can't block on it again
        page.evaluate("window.stop()")
        page.wait_for_timeout(4000)
        print("warning: webfont request stalled - captured with fallback typography; the PNG may not match the intended fonts", file=sys.stderr)
    svg = page.locator("svg").first
    # Release every clipping ancestor (local scroller, overflow:hidden chrome)
    # so an SVG wider than its frame is captured whole.
    svg.evaluate("el => { for (let a = el.parentElement; a; a = a.parentElement) a.style.setProperty('overflow', 'visible', 'important'); }")
    svg.screenshot(path=out, omit_background=True)
    browser.close()
```

If the `networkidle` wait times out (a stalled font or stylesheet behind a proxy), the snippet cancels the outstanding load with `window.stop()` and captures with fallback typography, printing a warning to stderr — pass that warning on to the user. Any other error propagates and fails the export normally.

Default `device_scale_factor=2` for crisp output. Accept `1` for compact assets or `3` for print/retina hero use, passed as a third CLI arg.

The overflow release matters for the wide presets. `min-width` equals the viewBox width (see [`output-spec.md`](output-spec.md)), so a `doc-wide` or `slide-16x9` SVG is 1280px inside a 1200px frame, and its `.diagram-container` scroller clips the last 80px on screen. The screenshot covers the SVG's box but not what an ancestor clipped, so without the release the PNG comes out full size with a blank right edge. This is the screen-side counterpart of the templates' `@media print` rule.

### Output naming

`example-architecture.html` → `example-architecture.png`, written next to the source. Honour explicit user-provided paths.

## Sizing the export

The PNG's pixel dimensions are the SVG's `viewBox` × `device_scale_factor`. So the size decision was already made when the diagram was drawn — see [`output-spec.md` §2](output-spec.md) for the presets. Export only picks the multiplier.

| Destination | Scale | Result from a 1280×720 `viewBox` |
|---|---|---|
| Docs, README, wiki | 2 | 2560×1440 |
| Slide deck (projected) | 2 | 2560×1440 |
| Print / PDF handout | 3 | 3840×2160 |
| Inline thumbnail, email | 1 | 1280×720 |

### Hitting an exact pixel size

When the user needs specific dimensions (an OG card at exactly 1200×630, a slide image at 1920×1080), compute the scale factor instead of guessing — Playwright accepts fractional values:

```
scale = target_width / viewBox_width
```

A 960-wide `viewBox` at a 1200px target is `scale=1.25`. Two rules:

- **Never scale below 1** to hit a small target — that soft-focuses the type. Redraw at a smaller preset instead.
- **Never scale past 4** — beyond that you're upscaling a layout that was designed for a smaller canvas; redraw at `slide-16x9` or a print preset.

If the target aspect ratio doesn't match the `viewBox` aspect ratio, say so and offer to redraw at the matching preset. Padding or cropping a finished diagram to fit a frame is not an export operation — it breaks the 40px safe margin.

## Edge cases

- **Source is `assets/index.html`** (the gallery, multiple SVGs in one file): refuse the export and ask the user which specific diagram file they meant. Don't guess.
- **No `<svg>` block found**: the source isn't a diagram file. Tell the user; don't write anything.
- **Surrounding HTML matters to the user**: they want cards/header in the image. Tell them this skill exports diagrams only, and recommend a browser-based full-page screenshot (or a separate PDF print).
- **Source is missing fonts at runtime**: Playwright will substitute, the screenshot will look off. Check that the source HTML has the `<link href="...fonts.googleapis.com...">` tag in `<head>`. If absent, the file isn't from a current template — fix the source rather than working around it in export.

## What this command never does

- Modifies the source HTML.
- Adds export buttons or `<script>` tags. Static diagrams remain script-free; an already motion-enabled source may retain the scoped controller from [`animation.md`](animation.md), but export never injects another controller.
- Auto-emits `.svg` or `.png` alongside HTML generation. Manual on every call.
- Embeds an HTML wrapper (cards, headers) into the SVG via `foreignObject`. Too fragile across renderers.
