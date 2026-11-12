# Chart reference
Read for every chart, plot, part-to-whole view, or parallel timeline.
Do not hand-author static SVG chart marks.
## D3 runtime

Use D3 for every chart. Enable D3 through the inline renderer's documented runtime when it supplies one. Otherwise embed the D3 code the chart uses in the HTML. Embed the data and keep the chart offline.

## Cartesian structure

One `.vis-column` holds `figure.vis-chart-figure` and its drawing script. Inside the figure, put one `.vis-chart-meta` (with `.vis-chart-meta-copy`: `h3` title, then one short muted metric label) immediately before `svg.vis-chart[role="img"]`.
Measure the plot container on first paint and on resize. Once it has a usable size, clear the plot, create the scales, lay out the axes and grid, then draw the marks. Reserve space for labels and margins and put the grid on the quantitative axis.

## Choose the chart
- One current value: `.vis-card.vis-stat-card`, never a one-bar chart. One ratio against a limit: `.vis-gauge` or a linear meter, not a two-slice pie.
- Compare magnitude: bars; ranked categories: horizontal bars, descending. Two-dimensional grid: heatmap.
- Time series: line; area only when filled magnitude matters. Distribution: histogram, box plot, or strip plot. Correlation: scatter.
- Range or interval: range bar, dumbbell, or band. Above and below a baseline: diverging bars.
- Part-to-whole: stacked bars before a donut. Allocation over time: one stacked chart per period on a shared scale. Parallel work: aligned lanes on one time axis.
- More than seven important classes: a table or small multiples, not more hues.
## Color
- Use one accent, usually `.vis-orange`, for one series. For `n` series, take the first `n` of `.vis-orange`, `.vis-blue`, `.vis-purple`, `.vis-green`, `.vis-yellow`, `.vis-brown` in order.
- Do not use `.vis-fg` as a fill on stacked or part-to-whole marks.
- Current versus baseline: `.vis-fg` and one accent. Gain/loss: `.vis-success` and `.vis-danger`, `.vis-fg` totals.
- `.vis-tone-secondary` and `.vis-tone-tertiary` only lighten or darken the same series.
- Axes, grids, values, and labels stay neutral. Never use `--primary`, `--accent`, `color-mix()`, or hardcoded colors on marks. Do not recolor a category on filter, sort, or selection.
## Marks
- `.vis-chart` only on the SVG; `.vis-mark` on filled marks; `.vis-line.vis-data-series` on data lines; `.vis-fill-20` on area, range, uncertainty, and box fills; `.vis-track` for muted geometry; `.vis-label` for in-plot text; `.vis-reference-guide` or `.vis-hover-guide` for dashed guides. Use `r=4` for fixed-radius circles, including line-chart points and hover markers. Do not apply it to radius-encoded marks.
- Tone classes (`.vis-orange`, `.vis-fg`, `.vis-tone-secondary`, and the rest) and `.vis-fill-20` are modifiers. They set no color on their own; a shape must also carry `.vis-mark`, `.vis-line`, or `.vis-label` to receive it. A shape with only a tone class keeps the SVG default black fill.
- Bars: at most 32px thick, centered in the band. Grouped bars share a cluster up to 32px wide. Leave 4px between adjacent bars and divide the remaining width equally. Stacked segments use `.vis-segment-gap`.
- Horizontal bars: reserve room for the widest category label and use height `(row count × 40) + 80`.
- Histogram: bins from samples, each bar spans its full numeric bin; draw from zero to the bin count.
- Area and radar: one `path.vis-mark.vis-fill-20` in the series tone plus a matching `.vis-line.vis-data-series` boundary in the same tone. An uncertainty or forecast band takes the tone of the series it belongs to; do not introduce a second hue for the band. Stacked area and streamgraph: opaque `.vis-mark.vis-segment-gap` fills, no strokes.
- Dumbbell: `line.vis-mark.vis-data-series` with solid endpoint fills. Box plot: box `.vis-mark.vis-fg.vis-fill-20`; median, whiskers, and caps `.vis-mark.vis-line.vis-data-series`.
- Donut: `pie().padAngle(0.02).sort(null)`, inner radius near 55–60%; center holds `text.vis-stat-value` and one `.vis-label`.
- Treemap: `d3.treemap().paddingInner(2)`, opaque group hues, light cell labels. Heatmap: two band scales and one foreground (`.vis-fg`) opacity scale; use orange only for one deliberate emphasis, never as the sequential scale; give in-cell labels an explicit `fill` of `var(--background)` over strong cells and `var(--foreground)` over faint cells.
- Parallel timeline: one time scale for axis, grid, lanes, and bars.
## Domains, ticks, and labels
- Derive numeric domains from all observations, uncertainty, and references; include zero only when the comparison needs it. Pad scatter domains so the largest mark fits.
- Write axis titles as readable words with units, such as `duration (s)`. Compact ticks at or above 1,000 (`2.5k`). One `Intl.NumberFormat` per quantity.
- Keep every label inside the SVG with at least 4px between labels. Fix collisions by anchoring inward, moving along the free axis, or reducing ticks; never remove requested labels or drop below 11px. Never use a dual axis.
- Directly label up to four series; otherwise one `.vis-legend` of `<span class="vis-legend-item"><span class="vis-swatch vis-orange"></span>Read</span>` below `.vis-chart-meta-copy`. No legend for one series; never both a legend and direct labels.
## Interaction
- Show the mark's label and value on hover or focus. Use the mark or a transparent target at least 32px across.
- Multi-series line or area uses one cross-series hover, built in this order:
  1. Append one full-plot transparent `rect[data-chart-hover-overlay="cross-series"]` last, so it sits above every mark.
  2. On pointer move, clamp the cursor x to the plot, invert it through the x scale, and interpolate every visible series between its two surrounding observations. Do not snap to the nearest sample.
  3. Draw one `line.vis-hover-guide[data-chart-hover-guide]` from the top to the bottom of the plot at the clamped x, and one `circle[data-chart-hover-marker]` (`r=4`) per visible series at its interpolated y.
  4. Show one `.vis-tooltip.vis-chart-tooltip` near the cursor: `.vis-tooltip-context` holds the x value, then one `.vis-tooltip-row` (`.vis-tooltip-label`, `.vis-tooltip-value`) per series in legend order.
  5. On pointer leave, hide the guide, markers, and tooltip. Legend toggles (`button.vis-legend-item[aria-pressed]`) hide a series' line, marker, and tooltip row together.
- Static legends use `span.vis-legend-item`; selection uses `button.vis-legend-item[aria-pressed]`.
