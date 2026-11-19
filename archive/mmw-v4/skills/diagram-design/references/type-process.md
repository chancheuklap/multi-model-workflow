# Process

**Best for:** sequential business processes with multiple actors/divisions where the reader needs to see *who* does *what*, *what data* enters and leaves each step, and *which tools* are used — not just the step order. Covers responsibility audits, data-quality gate reviews, cross-divisional handoff maps, and end-to-end workflow documentation.

Prefer swimlane (simpler) when the data types and tools don't matter. Prefer process when each step's input/output payload and responsible team must be legible at a glance.

This type is **parametric** — the inputs schema in §1 drives every coordinate via the formulas in §2. Two generations from the same inputs must produce visually identical SVG. The rule shapes mirror `type-data-flow.md` so color override, IN/OUT chip semantic, and reproducibility checklist read identically across types.

---

## 1. Inputs — the parameter contract

```yaml
lanes:                              # 1..6 horizontal swimlanes (top to bottom)
  - { name: ["RD&E"],                 key: "RDE" }
  - { name: ["IT"],                   key: "IT"  }
  - { name: ["FIELD", "SERVICES"],    key: "FLD" }
  - { name: ["SURVEY", "SERVICES"],   key: "SVY" }
  - { name: ["HOUSEHOLD", "UNIT"],    key: "HHU" }
  - { name: ["COMMS &", "MARKETING"], key: "CMM" }

steps:                              # 1..12 vertical step columns (left to right)
  - { number: "1",  label: "Design"   }
  - { number: "2",  label: "Build"    }
  - { number: "3",  label: "Test", focal: true }       # focal step header chip — accent fill
  - { number: "4",  label: "Train"    }
  # ... up to 12

nodes:                              # explicit per-cell entries; empty cells render nothing
  - { lane: "RDE", step: 0,  title: "Survey design",      sub: "questionnaire · sampling", tool: "Excel · CSPro",
      chips: {in: null,  out: "FL"} }              # first step has no input chip
  - { lane: "IT",  step: 1,  title: "Build app",          sub: "form + validation",        tool: "CSPro · scripts",
      chips: {in: "FL", out: "TB"}, color: "#5a7d9a" }    # slate-blue — data quality concern
  - { lane: "RDE", step: 2, kind: decision, title: "Pilot passed?", focal: true }
  - { lane: "FLD", step: 3,  title: "Train enumerators",  sub: "protocols · safety",       tool: "manual",
      chips: {in: "TB", out: "LS"}, color: "#b85450" }    # rust-red — governance / training
  # ... etc

arrows:                             # explicit edges; styles bind to topology (see §3)
  - { from: {lane: "RDE", step: 0}, to: {lane: "IT",  step: 1}, style: "normal" }
  - { from: {lane: "IT",  step: 1}, to: {lane: "RDE", step: 2}, style: "focal-in" }     # accent — into focal
  - { from: {lane: "RDE", step: 2}, to: {lane: "FLD", step: 3}, style: "focal-out", label: "Yes" }
  - { from: {lane: "RDE", step: 2}, to: {lane: "IT",  step: 1}, style: "return", label: "No: rebuild" }
  # ... etc

dark: false
```

**Reserved field semantics:**
- `lanes[k].key` — the 3-letter role badge text shown inside every node in that lane.
- `lanes[k].name` — 1 or 2 line lane label; uppercase mono.
- `steps[j].focal: true` — exactly **one** step may declare this. Header chip renders in accent.
- `nodes[i].focal: true` — exactly **one** node may declare this. Renders with accent border (§5).
- `nodes[i].chips` — `{in: "<CODE>", out: "<CODE>"}` object (either side `null` to omit). Codes from §8. **Skip** the input chip on the first step's nodes, **skip** the output chip on the last step's nodes (no upstream / downstream).
- `nodes[i].kind` — optional `action` (default), `decision`, or `exit`. A `kind: decision` node selects the next step by condition. A `kind: exit` node ends this process and names the destination in its title. Decision and exit nodes display only their title, without role or data chips, subtitle, or tool.
- `arrows[i].label` — condition on every outgoing decision edge, destination on a non-decision edge into an exit, or reason for a non-decision return.
- `arrows[i].style` — adds `style: return` for an edge back to an earlier step. It takes precedence over focal styling.
- `nodes[i].color` — optional **per-node color override**. Any valid `"#hex"` string; the §4 palette is recommended for cross-diagram consistency.

---

## 2. Layout formulas — deterministic geometry

```
n_steps          = len(steps)
n_lanes          = len(lanes)
node_w           = max(100, chinese_content_w, decision_content_w)
node_h           = 80 if any Han text else 64
label_col_w      = max(140, ceil4(longest lane-label line width + 16)) if Han lane labels else 140
header_h         = 44 if Han step labels else 36
step_slot_w(j)   = max(node_w + 2*pad(j) if D(j) else node_w + 12,
                       ceil4(text_w(steps[j].label) + 16))
lane_h(k)        = max(node_h + 16, node_h + 2*(16 + pitch*L(k))) if L(k) else node_h + 16
right_pad        = 28
has_color_row    = any(node.color or step.color or lane.color in inputs)
legend_h         = (124 if has_color_row else 100) if Han legend labels else (100 if has_color_row else 80)
lanes_bottom     = header_h + sum(lane_h(k) for k in lanes)
return_strip_h   = 16 + pitch*R if R else 0
viewBox_w        = label_col_w + sum(step_slot_w(j) for j in steps) + right_pad
viewBox_h        = lanes_bottom + return_strip_h + legend_h

chip_y           = 8
chip_w           = 16
chip_h           = 16
chip_rx          = 8
lane_y_top(k)    = header_h + sum(lane_h(t) for t < k)
lane_y_mid(k)    = lane_y_top(k) + lane_h(k)/2
lane_label_x     = label_col_w / 2
step_cx(j)       = label_col_w + sum(step_slot_w(t) for t < j) + pad(j) + node_w/2
node_x(j)        = step_cx(j) - node_w/2
node_y(k)        = lane_y_top(k) + (lane_h(k) - node_h)/2
legend_y_top     = lanes_bottom + return_strip_h
legend_row_y(r)  = legend_y_top + (20 + 24*r if Han legend labels else 16 + 21*r)
return_y(q)     = lanes_bottom + 16 + pitch*q
```

### 2.0 Branch and Chinese geometry

The formulas use the text metrics, shape sizes, and local track counts defined here. A Latin process without decisions or returns uses 100×64 nodes, 112px step slots, and 80px lanes.

**Chinese text.** Follow `style-guide.md` `### Traditional Chinese labels`, including its Simplified Chinese rules. Chinese titles and labels use 12px, the minimum allowed size. Titles keep semibold weight. Traditional Chinese names use `'Geist', 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif`. Simplified Chinese names use `'Geist', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif`. Chinese labels use 12px sans, weight 500, no tracking, and no uppercase transform. Technical values stay Latin mono. Chinese prose in the subtitle or tool slot uses the same 12px sans treatment.

Let `text_w(t)` use the style-guide width budget at the text's rendered size. Count every wide or full-width character as 1em, nonspacing marks as zero, and all other characters at the face's Latin advance. Round structural dimensions up to a multiple of 4 with `ceil4(v) = 4 * ceil(v / 4)`.

- `chinese_content_w = ceil4(max(text_w(t) for all node titles, subtitles, and tools) + 16)` with any Han text, or 0 without it. Titles remain one line. With Han text, title, subtitle, and tool baselines are `node_y + 28`, `+44`, and `+60`. Data chips sit at `node_y + node_h - 10`. The output chip's x is `node_x + node_w - 20` in every size.
- Two-line Han lane labels use baselines `lane_y_mid - 4` and `lane_y_mid + 12`. Han step labels use baseline 36. Numbered chips keep their Latin positions.
- `decision_content_w = ceil4(2 * (longest decision-title width + 16))` if decisions exist, or 0 otherwise. Let `cx = step_cx(j)` and `cy = lane_y_mid(k)`. A decision's bounding box has height `node_h` and width `node_w`. Its vertices are `(cx, cy-node_h/2)`, `(cx+node_w/2, cy)`, `(cx, cy+node_h/2)`, and `(cx-node_w/2, cy)`. An exit uses an ellipse centered at `(cx, cy)` with radii `node_w/2` and `node_h/2`. Center both titles vertically with `dominant-baseline="middle"`.

**Branch corridors.** Special edges are decision edges and returns. `D(j)` counts their endpoints in step column `j`. Number those endpoints from 0 in arrow input order within that column, source before destination if both are in the same column. Reverse only the source ranks among returns from the same node, as §3.3 defines. For each edge, `s` is its source endpoint's rank and `d` its destination endpoint's rank. `L(k)` counts special edges originating in lane `k`. Their source-lane rank `l` starts at 0 in input order. These local counts allocate space only where an edge needs it.

Let `mask_w(label) = ceil4(text_w(label) + 8)`. Mask height is 16px for Chinese and 12px for Latin. `pitch = max(12, tallest special-edge mask height + 8)`. For a column with special endpoints, `pad(j) = 24 + pitch*D(j) + ceil4(widest incident mask width / 2)`. Otherwise `pad(j) = 8`. Empty maxima are zero. The two endpoint pads leave room for the full label mask even on an adjacent-step branch with the largest local ranks.

For each special edge, `src_gap_x = node_x(src_step) + node_w + 8 + pitch*s`, `src_left_x = node_x(src_step) - 8 - pitch*s`, `dst_gap_x = node_x(dst_step) - 8 - pitch*d`, `upper_y = node_y(src_lane) - 8 - pitch*l`, and `lower_y = node_y(src_lane) + node_h + 8 + pitch*l`. `R` counts return edges. Number them from `q=0` in input order for the fixed strip below every swimlane and above the legend. §2 defines that strip's coordinates and height.

### 2.1 Background structure

- Paper fill across full viewBox.
- Dot pattern: 22×22 grid, `circle r=0.8`, `fill rgba(45,49,66,0.10)`. Opacity 0.55.
- Alternating lane tints: odd-indexed lanes (0, 2, …) receive `rgba(45,49,66,0.018)` fill from `x=label_col_w` to `viewBox_w`.
- Lane dividers: horizontal hairlines at every `lane_y_top(k)` at `lanes_bottom`, and at `legend_y_top`; stroke `rgba(45,49,66,0.12)` width 0.8.
- Label column right border: vertical hairline at `x = label_col_w`, stroke `rgba(45,49,66,0.20)` width 1, from `y = header_h` to `y = legend_y_top`.

### 2.2 Step header chip + label

Per step `j`:

```
chip_w(j)        = 20 if len(step.number) >= 2 else 16
chip_x(j)        = step_cx(j) - chip_w(j)/2
number_anchor    = (step_cx(j), chip_y + 11)
label_anchor     = (step_cx(j), 32)              # 8-px gap below chip
```

**Chip** (the numbered pill at the top of each column):
- Default fill: `rgba(45,49,66,0.12)`, number text ink.
- Focal fill: `rgba(191,69,32,0.20)`, number text accent (§5).
- Per-step `color` override (§4): replaces the fill with `rgba(C, 0.20)` and the number fill with `C`.

**Label** (the uppercase mono text below the chip):
- Renders `steps[j].label` (uppercased), anchored at `label_anchor`.
- Font: Geist Mono 6 px, weight 500, `letter-spacing="0.12em"`, `text-anchor="middle"`.
- Default fill: muted (`#4f5d75` light / `#bfc0c0` dark).
- Focal fill: accent (`#bf4520` light / `#f08a59` dark).
- Per-step `color` override: fill = `C` (matches the chip number color).
- Keep labels short (≤ 9 chars). Long labels truncate; if you need more, abbreviate.

### 2.3 Lane labels

One or two-line mono label, all uppercase, letter-spacing 0.08em, font-size 8, fill muted. Centered at `(lane_label_x, lane_y_mid(k))`:
- Single-line: anchored at `(lane_label_x, lane_y_mid(k) + 4)`
- Two-line: lines at `(lane_label_x, lane_y_mid(k) - 4)` and `(lane_label_x, lane_y_mid(k) + 4)`

Per-lane `color` override (§4): replaces the label fill with `C` and the lane stripe tint with `rgba(C, 0.04)`.

### 2.4 Node content layout (Latin action defaults, 100×64 rect)

```
role_chip          rect 14×10 at (node_x+4, node_y+4),  rx=2
role_chip_text     centered at (node_x+11, node_y+12), font-size=6, weight=600
                                                                # text = lanes[k].key (3-letter lane code)
title              centered at (step_cx(j), node_y+26),  font-size=9 sans semibold
in→out             centered at (step_cx(j), node_y+40),  font-size=6.5 mono muted
tool               centered at (step_cx(j), node_y+52),  font-size=6.5 mono soft
data chip IN       rect 16×8 at (node_x+4,   node_y+54), rx=2      # payload entering
data chip OUT      rect 16×8 at (node_x+80,  node_y+54), rx=2      # payload leaving
```

**Role chip text rule:** the badge inside each node renders `lanes[k].key` where `k` is the node's lane index — **not** the step number (the step number already lives in the column header chip at the top, §2.2). Showing the lane key as the node badge gives each node a self-contained "who" identifier that survives when a single node is excerpted out of context. Mirrors the same rule in `type-data-flow.md` §2.4.

Empty cells (no node entry) render **nothing**. No placeholder rect, no role chip, no label.

**Chip-vs-tool-text collision rule:** chips sit at `node_y + 54..62`; tool text baseline is at `node_y + 52`. If a node has a two-line title (rare), increase node_h to 72 OR omit the chips for that node. Default behaviour: omit chips on collision.

---

## 3. Connector rules (mandatory)

Styles bind to topology. Connectors drawn **before** all node shapes (z-order rule).

| `style` | Stroke | Width | Dash | Marker | When required |
|---|---|---|---|---|---|
| `normal` | `#4f5d75` (muted) | 1.0 | — | `arrow` | Standard data hand-off between steps or actors. Decision branches carry conditions. |
| `focal-in` / `focal-out` | `#bf4520` (accent) | 1.2 | — | `arrow-accent` | Every edge whose endpoint is the focal node (`focal-in`) or origin is the focal node (`focal-out`). |
| `trigger` | `#4f5d75` (muted) | 1.0 | `4,3` | `arrow-sm` | Orchestration trigger (scheduler → tool). Unlabelled unless it leaves a decision or enters an exit. |
| `return` | `#4f5d75` (muted) | 1.0 | `4,3` | `arrow-sm` | Labelled route back to an earlier step, outside the swimlanes (§3.3). |

**Defs block** (required, three markers):

```svg
<defs>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
    <circle cx="11" cy="11" r="0.8" fill="rgba(45,49,66,0.10)"/>
  </pattern>
  <marker id="arrow"        markerWidth="8" markerHeight="6" refX="7" refY="3"   orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#4f5d75"/></marker>
  <marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3"   orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#bf4520"/></marker>
  <marker id="arrow-sm"     markerWidth="6" markerHeight="5" refX="5" refY="2.5" orient="auto"><polygon points="0 0, 6 2.5, 0 5" fill="#4f5d75"/></marker>
</defs>
```

### 3.1 Routing rules (non-negotiable)

**Single-bend right-angle:** exit RIGHT → corridor → enter TOP (↓ destination below) or BOTTOM (↑ destination above).

- Source-side: exit at `(node_x + node_w, lane_y_mid(src_lane))` — node's right edge, vertical center.
- Destination-side: enter at `(step_cx(dst_step), node_y(dst_lane))` for downward, or `(step_cx(dst_step), node_y(dst_lane) + node_h)` for upward.
- Corner radius: 8-px Q-bezier at the bend.
- Same-lane edges (rare — same lane, adjacent steps): horizontal `<line>` from src right to dst left.
- **No diagonals.** Ordinary forward action edges use these ports. Decision branches and returns use §3.3 instead.

```svg
<!-- Downward (destination lane > source lane) -->
<path d="M {rx},{src_cy} H {dst_cx - 8} Q {dst_cx},{src_cy} {dst_cx},{src_cy + 8} V {dst_top}"
      fill="none" stroke="…" stroke-width="…" marker-end="…"/>

<!-- Upward (destination lane < source lane) -->
<path d="M {rx},{src_cy} H {dst_cx - 8} Q {dst_cx},{src_cy} {dst_cx},{src_cy - 8} V {dst_bottom}"
      fill="none" stroke="…" stroke-width="…" marker-end="…"/>

<!-- Same lane (adjacent step) -->
<line x1="{src_right}" y1="{lane_cy}" x2="{dst_left}" y2="{lane_cy}"
      stroke="…" stroke-width="…" marker-end="…"/>
```

- **Z-order:** all `<path>` and `<line>` connectors emitted **before** any node shape.
- **Markers:** exactly one `marker-end` per path. Never `marker-start`.
- **Labels:** ordinary handoffs are unlabelled. Decision branches, exit edges, and returns follow §3.3. Latin labels use 6.5px mono on a paper mask. Chinese labels use §2.0. Masks are 16px tall for Chinese, 12px for Latin, and `ceil4(text_w(label) + 8)` wide.

### 3.2 Crossings

Swap step assignments first when arrows cross or a path would intersect a node. If the process grammar still cannot show the flow without crossings, redraw with containers under the diagram-design skill's `## 7. Layout & Spacing`. Keep the whole subject on one canvas, with detail nested inside or directly beside it.

### 3.3 Branches, exits, and returns

Use the shape and condition-label conventions of `type-flowchart.md` `## Layout conventions`. A step that selects its successor by condition is a diamond with at most three exits. Label every outgoing edge with its condition, including an edge that returns. An edge leaving the process ends at an ellipse whose title names the destination. Exit nodes have no outgoing edges. Use `style: return` and a label for every edge to an earlier step.

For non-return decision edges, assign ports in outgoing input order, first right, second bottom, third top. Returns use separate left-side ports and do not consume these forward ports. Route the right port horizontally to `src_gap_x`, vertically to `lower_y`, horizontally to `dst_gap_x`, vertically to the destination center y, then horizontally into its left vertex or edge. The bottom port goes vertically to `lower_y`, then follows the same route from there. The top port goes vertically to `upper_y`, horizontally to `dst_gap_x`, vertically to the destination center y, then horizontally into its left vertex or edge. These are orthogonal paths with 8px rounded corners. Place the condition label at the midpoint of the horizontal segment at `upper_y` or `lower_y`, with its paper mask.

For a node's `m` return edges, number them `r=0..m-1` in input order and give each a separate lower-left port. Its y is `cy + 8*(r+1)`. On a diamond its x is `cx - node_w/2 * (1 - 2*abs(y-cy)/node_h)`, and on an action rectangle its x is `node_x`. Exit nodes have no returns. A return leaves this port horizontally to `src_left_x`, then vertically to `return_y(q)`, horizontally to `dst_gap_x`, vertically to the destination center y, then horizontally into its left vertex or edge. For these source departures only, assign the return source ranks in reverse return order within their reserved endpoint ranks, so lower ports use nearer-left tracks. Destination ranks keep input order. The return path stays to the left of the source column, separate from forward departures to its right. Its dashed horizontal return segment stays in the fixed strip outside the swimlanes. Place its label at that segment's midpoint. Return edges keep the muted dashed style even when touching the focal node. Other focal-touching branches retain the accent style. A non-decision edge into an exit uses the ordinary forward routing and puts its destination label at the midpoint of its horizontal segment.

All branch and return paths must clear every node. If tracks cross other connectors, apply §3.2 rather than drawing through a node or dropping a condition. This routing changes only diagrams that declare decisions or returns.

---

## 4. Component color override

Any node, lane, or step accepts an optional `color: "#hex"`. Mirrors `type-data-flow.md` §4 and `type-high-level.md` §3.4 so the rule reads identically across types.

### 4.1 Per-node `color`

Applied to:

| Element | Light | Dark |
|---|---|---|
| Container fill (`rect`) | `rgba(C, 0.06)` | `rgba(C_light, 0.10)` |
| Container stroke | `rgba(C, 0.35)` (stroke-width 1) | `rgba(C_light, 0.45)` |
| Role chip fill | `rgba(C, 0.18)` | `rgba(C_light, 0.22)` |
| Role chip text | `C` | `C_light` |
| Title text | `C` | `C_light` |
| Sub-label (in → out) | **unchanged** (muted) | **unchanged** (muted) |
| Tool label | **unchanged** (soft) | **unchanged** (soft) |
| Data-type chips | **unchanged** | **unchanged** |
| Arrows touching this node | **unchanged** — topology-driven | **unchanged** |

`C_light` = the same hex lightened ~15% for dark-mode contrast (e.g., `#b85450` → `#d97a78`).

### 4.2 Per-step `color`

Replaces the step header chip's fill with `rgba(C, 0.20)` and the chip's number text fill with `C`. The legend's matching step entry uses the same colors.

### 4.3 Per-lane `color`

Replaces the lane stripe tint with `rgba(C, 0.04)` and the lane label text fill with `C`. Use sparingly — lane tints are easy to over-apply.

### 4.4 Rules

- **Never on focal nodes / focal steps.** The accent already carries that signal. A `color` on a focal element is ignored.
- **Never on arrows.** Arrows are topology-driven. If you want a colored edge, pick a different `style` from §3, not a color override.
- **Cap at 3 custom-colored elements** per diagram (nodes + lanes + steps combined), in addition to the focal pair (focal node + focal step header). Above 3 the visual signal starts to fragment.
- **Subtitle and tool labels stay muted** regardless of any component `color`.

### 4.5 Semantic palette (recommended)

Same palette as `type-high-level.md`, `type-dp-integration.md`, `type-data-flow.md`:

- `#b85450` rust-red — Security / Identity / Governance (access control, training, approvals)
- `#5a7d9a` slate-blue — Observability / Quality (data quality gates, validation, monitoring)
- `#7a8c47` olive-green — Data Products / Publication (consumer-ready outputs, releases)
- `#8c6d3f` warm-brown — Backup / DR / Archive

---

## 5. Focal rule

The process diagram has three focal slots, exactly one entry each:

- **One focal step** (`steps[j].focal: true`) — typically the analytical or decision pivot (Test, Approve, Validate). Header chip and legend chip render in accent.
- **One focal node** (`nodes[i].focal: true`) — the node that *receives* the critical handoff. Accent border + accent role chip + ink title (title text stays ink so it's still readable; only the border + role chip carry the accent).
- **One focal arrow set** (`style: focal-in` and `focal-out`) — edges into and out of the focal node. Accent solid strokes.

If zero or >1 of any focal slot are declared, halt and ask the user.

---

## 6. Dark mode

| Token | Light | Dark |
|---|---|---|
| Paper | `#f5f5f5` | `#2d3142` |
| Ink | `#2d3142` | `#f5f5f5` |
| Muted | `#4f5d75` | `#bfc0c0` |
| Soft | `#5a6580` | `#949eb2` |
| Accent | `#bf4520` | `#f08a59` |
| Dot pattern | `rgba(45,49,66,0.10)` | `rgba(245,245,245,0.10)` |
| Lane tint | `rgba(45,49,66,0.018)` | `rgba(245,245,245,0.025)` |
| Dividers | `rgba(45,49,66,0.12)` | `rgba(245,245,245,0.12)` |
| Label col divider | `rgba(45,49,66,0.20)` | `rgba(245,245,245,0.22)` |
| Default chip fill | `rgba(45,49,66,0.12)` | `rgba(245,245,245,0.12)` |
| Focal chip fill | `rgba(191,69,32,0.20)` | `rgba(240,138,89,0.22)` |
| Default node fill | white | `rgba(245,245,245,0.04)` |
| Default node stroke | `rgba(45,49,66,0.25)` | `rgba(245,245,245,0.20)` |
| Focal node fill | `rgba(191,69,32,0.08)` | `rgba(240,138,89,0.12)` |
| Focal node stroke | `#bf4520` | `#f08a59` |
| Custom component colors | `C` | `C_light` (lighten ~15%) |

---

## 7. Reproducibility checklist (taste gate)

Before emitting SVG, verify **every** item:

1. `viewBox = "0 0 {viewBox_w} {viewBox_h}"` derived via §2.
2. Header and legend strips use §2, including the Chinese and return-strip overrides in §2.0.
3. Every node uses §2 dimensions and anchors, with the shape selected by `kind`. Latin action defaults remain `100×64`.
4. Empty cells render nothing — no placeholder rect, no text.
5. Exactly **one** focal step (`steps[j].focal: true`).
6. Exactly **one** focal node (`nodes[i].focal: true`).
7. Focal-touching arrows use `style: focal-in` / `focal-out` (accent), except returns, which stay muted dashed.
8. All other arrows use `normal`, `trigger`, or `return` as §3 defines. Ordinary handoffs are unlabelled.
9. All arrows emitted before any node shape (z-order rule).
10. Ordinary forward edges use §3.1. Branches and returns use §3.3 and §2.0 tracks. No diagonals or paths through nodes. Q-bezier `r=8` at each bend.
11. Custom component colors ≤ 3 (in addition to the focal pair). Arrows never recolored by component `color`.
12. Subtitle and tool labels stay muted regardless of any component `color`. Input chip skipped on first step's nodes, output chip skipped on last step's nodes.
13. No unlabelled decision branches. Every exit names its destination, and every return is labelled and routed outside the swimlanes.

---

## 8. Data-type chips reference (input + output)

Same catalog as `type-data-flow.md` §8.

- **Input chip** at `(node_x+4, node_y+node_h-10)` — bottom-**left**. Payload entering the node.
- **Output chip** at `(node_x+node_w-20, node_y+node_h-10)` — bottom-**right**. Payload leaving the node.
- Either chip may be omitted (first/last step, unknown payload).

### Chip codes

| Code | Color (light) | Color (dark) | Meaning |
|------|---------------|--------------|---------|
| `LS` | `#7c8f6f` sage | `#9caf8f` | List / assignment / task |
| `DB` | `#5e7a9b` dusty-blue | `#82a0c0` | Dataset / tabular records |
| `TB` | `#b8915a` mustard | `#d3ad7a` | Table (analysis-ready) |
| `FL` | `#9c6b50` rust-brown | `#b88670` | File / document / report |
| `WB` | `#6e6479` slate | `#8d8298` | Web / press / public release |
| N/A | omit chip entirely | — | Unknown or not applicable |

Text inside chip: white, font-size 5, weight 700, mono.

Data-type chip colors are a **separate semantic axis** from the per-node color override (§4). Chip colors describe *payload format*; node color describes *concern type*. A node can have both an `out: TB` mustard chip and a rust-red border simultaneously.

---

## 9. Legend (3- or 4-row strip)

Each row introduced by a category label at `x = label_col_w + 4`. Use `legend_row_y(r)` from §2 for its baseline, starting at `r=0`. The default legend has **3 rows** (`STEPS` / `DATA TYPE` / `FLOW`); when one or more nodes carry a `color` override (§4), add a 4th `CONCERN` row with the height given in §2.

- **Row 1 — `STEPS`** at `legend_row_y(0)`: repeat the header chips with their labels. Focal step keeps accent fill.
- **Row 2 — `DATA TYPE`** at `legend_row_y(1)`: one swatch per chip type actually used in the diagram. Append a small sub-hint in muted mono: `left chip = input · right chip = output`.
- **Row 3 — `CONCERN`** (only when color overrides are present) at `legend_row_y(2)`: one mini-rect per custom color used, with its semantic label.
- **Row 4 — `FLOW`** (position depends on whether `CONCERN` row exists): one segment per arrow style actually used, with marker + label.

---

## 10. Complexity budget

| Dimension | Max |
|---|---|
| Lanes (actors) | 6 |
| Steps | 12 |
| Nodes per lane | Nodes = active steps only — empty cells are invisible |
| Labelled arrows | Required on decision branches, exit edges, and returns; ordinary handoffs unlabelled |
| Data-type chips per node | 2 (input + output) |
| Custom-colored elements (§4) | 3 (in addition to focal node + focal step) |

Above 6 lanes or 12 steps, redraw in a type with containers under the diagram-design skill's `## 7. Layout & Spacing`. Keep the whole subject on one canvas, with detail nested inside or directly beside it.

---

## 11. Anti-patterns

- **Placeholder empty cells** — if an actor doesn't participate in a step, leave the cell empty (no box, no text).
- **Diagonal arrows** — use §3.1 for ordinary forward edges and §3.3 for branches and returns.
- **Wrong ports** — ordinary forward edges exit right and enter top or bottom. Branch and return ports follow §3.3.
- **More than one focal step / focal node** — pick the single most critical operation.
- **Unlabelled lanes** — every swimlane must identify its actor.
- **All arrows the same style** — orchestration triggers must be dashed to distinguish them from data-flow connectors.
- **`color` override on a focal element** — ignored. Accent always wins.
- **Custom-colored arrows** — connectors are topology-driven; `color` on a node never spreads to its edges.
- **Lane tints over-applied** — a tint on every lane reads as decoration, not signal. Apply to ≤1 lane.
- **Data-type chips in a double-line-name node** — skip the chips or shorten the name to one line.
- **Unlabelled decision branches** — every outgoing decision edge carries its condition.
- **Oversized process grammar** — above 6 lanes or 12 steps, use containers on one canvas under the diagram-design skill's `## 7. Layout & Spacing`.

---

## 12. Worked example — full YAML for an extended process variant

The following input block describes an extended process workflow with custom colors and lanes. Every coordinate in the rendered SVG is derivable from this block via §2 + §3 + §4, demonstrating the parametric layout contract end-to-end.

```yaml
# Quarterly survey — end-to-end workflow (extended variant)
# 6 lanes × 11 steps, 1 focal step + 1 focal node + 3 custom-colored nodes

lanes:
  - { name: ["RD&E"],                 key: "RDE" }
  - { name: ["IT"],                   key: "IT"  }
  - { name: ["FIELD", "SERVICES"],    key: "FLD" }
  - { name: ["SURVEY", "SERVICES"],   key: "SVY" }
  - { name: ["HOUSEHOLD", "UNIT"],    key: "HHU" }
  - { name: ["COMMS &", "MARKETING"], key: "CMM" }

steps:
  - { number: "1",  label: "Design"   }
  - { number: "2",  label: "Assign"   }
  - { number: "3",  label: "Collect",  focal: true }    # focal step header chip
  - { number: "4",  label: "Review"   }
  - { number: "5",  label: "Validate" }
  - { number: "6",  label: "Weight"   }
  - { number: "7",  label: "Clean"    }
  - { number: "8",  label: "Tabulate" }
  - { number: "9",  label: "Approve"  }
  - { number: "10", label: "Publish"  }
  - { number: "11", label: "Upload"   }

nodes:
  - { lane: "RDE", step: 0,  title: "Sample Design",     sub: "Census data → Sample",
      tool: "SAS · Survey Solutions",      chips: {in: null, out: "LS"} }                # first step: no input chip
  - { lane: "IT",  step: 1,  title: "Field Assignment",  sub: "Sample → Field tasks",
      tool: "Survey Solutions",            chips: {in: "LS", out: "LS"} }
  - { lane: "FLD", step: 2,  title: "Data Collection",   sub: "→ 10,464 dwellings",
      tool: "Survey Solutions",            chips: {in: "LS", out: "DB"},  focal: true }   # focal node
  - { lane: "SVY", step: 3,  title: "HQ Review",         sub: "Submissions → Approved",
      tool: "Survey Sol. HQ",              chips: {in: "DB", out: "DB"},  color: "#b85450" }   # rust-red · governance
  - { lane: "IT",  step: 4,  title: "Error Checks",      sub: "Approved → Cleaned",
      tool: "SAS · Scripts",               chips: {in: "DB", out: "DB"},  color: "#5a7d9a" }   # slate-blue · data quality
  - { lane: "RDE", step: 5,  title: "Weight Calculation", sub: "Cleaned → Weighted",
      tool: "SAS",                         chips: null }                                  # 2-line title — chips skipped
  - { lane: "HHU", step: 6,  title: "2° Cleaning",       sub: "Weighted → Analysis",
      tool: "SAS · R · SPSS",              chips: {in: "DB", out: "TB"} }
  - { lane: "HHU", step: 7,  title: "Tables + Brief",    sub: "Analysis → Tables",
      tool: "Excel · SAS",                 chips: {in: "TB", out: "FL"} }
  - { lane: "CMM", step: 8,  title: "Stats Review",      sub: "Tables → Approved",
      tool: "Internal review",             chips: {in: "FL", out: "FL"} }
  - { lane: "CMM", step: 9,  title: "Public Release",    sub: "Approved → Public",
      tool: "Press conference",            chips: {in: "FL", out: "WB"}, color: "#7a8c47" }   # olive-green · data products
  - { lane: "IT",  step: 10, title: "Upload NatStat / SDMX", sub: "Results → Published",
      tool: "Web · SDMX API",              chips: null }                                  # 2-line title — chips skipped

arrows:
  - { from: {lane: "RDE", step: 0}, to: {lane: "IT",  step: 1},  style: "normal"    }
  - { from: {lane: "IT",  step: 1}, to: {lane: "FLD", step: 2},  style: "focal-in"  }     # → focal
  - { from: {lane: "FLD", step: 2}, to: {lane: "SVY", step: 3},  style: "focal-out" }     # ← focal
  - { from: {lane: "SVY", step: 3}, to: {lane: "IT",  step: 4},  style: "normal"    }     # upward
  - { from: {lane: "IT",  step: 4}, to: {lane: "RDE", step: 5},  style: "normal"    }     # upward
  - { from: {lane: "RDE", step: 5}, to: {lane: "HHU", step: 6},  style: "normal"    }     # downward, skips 2 lanes
  - { from: {lane: "HHU", step: 6}, to: {lane: "HHU", step: 7},  style: "normal"    }     # same lane
  - { from: {lane: "HHU", step: 7}, to: {lane: "CMM", step: 8},  style: "normal"    }
  - { from: {lane: "CMM", step: 8}, to: {lane: "CMM", step: 9},  style: "normal"    }     # same lane
  - { from: {lane: "CMM", step: 9}, to: {lane: "IT",  step: 10}, style: "normal"    }     # upward, skips 4 lanes

dark: false
```

### 12.1 What this YAML proves

Run §2 of this reference with these inputs:

- `n_lanes = 6`, `n_steps = 11`, `has_color_row = true` (3 nodes carry `color`).
- `viewBox_w = 140 + 11 * 112 + 28 = 1400`. ✓
- `legend_h = 100`, `viewBox_h = 36 + 6 * 80 + 100 = 616`. ✓
- Lane y_top = [36, 116, 196, 276, 356, 436]; lane mid = [76, 156, 236, 316, 396, 476]. ✓
- Step cx = [198, 310, 422, 534, 646, 758, 870, 982, 1094, 1208, 1320] (the 8-px content-area gutter shifts every value by 8 from `140 + j*112 + 50`). ✓
- Node 4 (HQ Review): step=3, lane="SVY" (k=3) → x = 534-50 = 484, y = 276+8 = 284. ✓
- Node 5 (Error Checks): step=4, lane="IT" (k=1) → x = 646-50 = 596, y = 116+8 = 124. ✓
- Node 10 (Public Release): step=9, lane="CMM" (k=5) → x = 1208-50 = 1158, y = 436+8 = 444. ✓

A fresh generation from this YAML produces deterministic coordinates directly from the formula without manual tweaking.

### 12.2 Adapting this YAML to a different process

To document a different process, change only the value of these inputs:

- **Lanes**: rename `lanes[k].name` to your team names; update each `nodes[i].lane` to match. Up to 6 lanes.
- **Steps**: rename `steps[j].label`, move `focal: true` to the step that defines the diagram's central claim. Up to 12 steps.
- **Nodes**: write one entry per `(lane, step)` cell that has work. Leave cells empty (no entry) to render nothing.
- **Colors**: choose `color: "#hex"` on at most 3 nodes (§4 cap). Stick to the recommended palette unless brand demands otherwise.
- **Arrows**: declare every edge explicitly with `style: normal | focal-in | focal-out | trigger | return`, including `label` where §3.3 requires it. The routing rules (§3.1 and §3.3) fill in the geometry.

Everything else — viewBox sizing, chip positions, legend layout, dark-mode token swap — is derivable. The YAML is the **source of truth**; the SVG is one of many possible renderings of it (light/dark/full all derive from the same inputs with different style tokens).

---

## 13. Examples

- `assets/example-process.html` — minimal light (quarterly survey: 11 steps, 6 divisions, data-type chips). Gallery default.
- `assets/example-process-dark.html` — same, dark skin.
- `assets/example-process-full.html` — same, editorial-card frame.
