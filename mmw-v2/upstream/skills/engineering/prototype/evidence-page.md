# Evidence Page

The static HTML page an experiment writes at the end of every run (step 4 of [EXP.md](EXP.md)). Read this when writing the generator.

## Two shapes

The question picks the shape; both share the same header.

- **Comparison grid** — for comparing approaches. One row per sample; one column per approach, the untouched input first, column order fixed across the whole page. Each row opens with a one-line stat for that sample.
- **Catalogue** — for summarising outputs or an annotated set. A summary table at the top; below it one block per item with its attributes and thumbnails.

## Sections, in order

1. **Header** — `<title>` and `<h1>` carry the issue and the round so several open tabs stay distinguishable. Under it: the question and the bar, the run parameters, the run time, the commit.
2. **Legend** — every colour, box style, and marker the page uses, before any of them appears.
3. **Summary table** — one row per approach, one column per measure the bar names. No verdict column: the page reports, the `README.md` judges.
4. **Body** — the grid or the catalogue.
5. **How it decided** — the rules the approach applied, one line each, naming the file and function in the leaf directory that implements it, so a reader can map what they see back to code.

A section may open with a one-line *what to look for* note. It points the eye; it does not state the result.

## Presentation

- One file plus its media directory. Plain HTML and CSS, inlined; no framework, no external requests. Media referenced by relative path so the output directory can be zipped or moved whole.
- Dark ground, one accent colour: outlines and overlays read better against it, and the page is obviously not the product.
- Every media cell is captioned: sample, approach, time point.
- Video: `controls preload="none"`; a row fits on one screen, so three to five columns at most.
- Numbers in tables: `font-variant-numeric: tabular-nums`, right-aligned.
- Long sample names are kept, not truncated — they are how the user recognises the sample.

## Skeleton

Embed in the generator and fill the slots; the rest of the page is rows of `.row` inside `.sample` blocks.

```html
<!doctype html>
<meta charset="utf-8">
<title>{{issue}} · {{round}} · evidence</title>
<style>
  body{margin:24px;background:#121416;color:#e6e6e3;font:14px/1.6 system-ui,sans-serif}
  h1{font-size:20px;margin:0 0 4px}
  .meta{color:#9a9fa4;font-size:12px;margin-bottom:20px}
  .legend{display:flex;gap:16px;flex-wrap:wrap;margin:0 0 20px;padding:10px 12px;border:1px solid #2b2f33;border-radius:6px}
  .legend i{display:inline-block;width:14px;height:14px;border:2px solid currentColor;margin-right:6px;vertical-align:-2px}
  table{border-collapse:collapse;margin:0 0 24px}
  th,td{padding:4px 10px;border-bottom:1px solid #2b2f33;text-align:left}
  td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
  .sample{margin:28px 0 8px}
  .sample h2{font-size:15px;margin:0}
  .stat{color:#9a9fa4;font-size:12px;margin:2px 0 8px}
  .look{color:#c8b458;font-size:12px;margin:0 0 8px}
  .row{display:grid;grid-template-columns:repeat({{columns}},1fr);gap:10px;margin-bottom:12px}
  img,video{width:100%;background:#000;border-radius:4px}
  .cap{color:#8fb8d8;font-size:12px;margin-top:4px}
  .rules li{margin:2px 0}
  code{font:12px ui-monospace,monospace;color:#c9d1d9}
</style>
<h1>{{issue}} · {{round}}</h1>
<p class="meta">{{question}} — bar: {{bar}} · params: {{params}} · run: {{run_time}} · commit: {{commit}}</p>
<div class="legend">{{legend_items}}</div>
<table>{{summary_table}}</table>
{{body}}
<h2>How it decided</h2>
<ul class="rules">{{rules}}</ul>
```
