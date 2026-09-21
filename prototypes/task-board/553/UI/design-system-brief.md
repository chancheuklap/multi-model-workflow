Build this design system with your full design-system instructions, from the attached codebase. Where this brief adds a rule, follow both.

## Product and sources

MMW Task Board: a local web page that shows one repository's planning work (maps, specs, tickets and their sub-issues, read from GitHub) as a canvas, and edits which host, model and effort each coding agent runs on. One person uses it, on their own machine.
Source: https://github.com/chancheuklap/multi-model-workflow (branch `dev`), the code under `mmw-v2/board/page/`. Styles: `mmw-v2/board/page/styles/tokens.css`, `board.css`, `settings.css`, and the page frame in `mmw-v2/board/page/index.html`. Fonts: `mmw-v2/board/page/styles/fonts/*.woff2` (Geist, Geist Mono, Instrument Serif), declared in `tokens.css`. Icons: Lucide (`rotate-cw` and `settings`), inline SVG in `mmw-v2/board/page/topbar.mjs` lines 4–5. There is no logo: the brand is the words "MMW" and "task board" in type.

## Component inventory

Build exactly these families, each from the file named, and no others (anything else goes under "Intentional additions" with a reason):

| Family | Source | Root markup | Parts that carry an id |
| --- | --- | --- | --- |
| Lamp | `board.css` "the lamp"; used in every module | `<span class="lamp orange|green|ink|hollow|none [big|small]">` | (root only) |
| StepPill | `board.css` "the pill"; `canvas.mjs:226`, `detail.mjs:447` | `<span class="pill queued|working|waiting|review|verify|landed [big]">` | (root only) |
| Brand | `topbar.mjs:66` | `<div class="brand">` | mark, name, repo |
| Counter | `topbar.mjs:72` | `<button class="counter [hot]">` or `<span class="counter">` | lamp, label, count, sub |
| ReadState | `topbar.mjs:91` | `<div class="readstate [failed]">` | (root only) |
| IconButton | `topbar.mjs:92` | `<button class="gear [on]">` with `<svg class="gear-icon">` | (root only) |
| ColumnEyebrow | `tasks.mjs:84` | `<div class="col-eyebrow">` | label, count |
| TaskRow | `tasks.mjs:40` | `<button class="task [on]">` | lamp, meta, title, bar, count |
| ContainerCard | `canvas.mjs:191` | `<div class="card [on]">` with `card-hit`, `card-top`, `card-title container`, `card-bar` | open, lamp, num, count, expand, title, bar |
| DecisionCard | `canvas.mjs:217` | `<div class="card [on] [cycle]">` with `card-kind` | open, lamp, num, kind, title |
| TicketCard | `canvas.mjs:226` | `<div class="card [on] [closeout] [cycle]">` with `card-run` | open, lamp, num, phase, title, run |
| Edges | `canvas.mjs:48` | `<svg class="edges">` of `e-trunk`, `e-expand`, `e-block`, `e-beam`, `e-port` paths | (root only) |
| LaneLabel | `canvas.mjs:126` | `<div class="lane-label [warn]">` | (root only) |
| Legend | `canvas.mjs:238` | `<div class="legend">` | walked, flow, blocked, closeout |
| ZoomBar | `canvas.mjs:263` | `<div class="zoom">` | out, level, in, fit |
| CanvasEmpty | `canvas.mjs:292` | `<div class="canvas-empty">` | title, text |
| DetailHead | `detail.mjs:435`, `detail.mjs:506` | `<div class="pv-head">` (ticket) or `<div class="dp-head">` | eyebrow, github, close |
| Origin | `detail.mjs:336`, `detail.mjs:441` | `<div class="dp-origin">` or `<div class="pv-links">` | number, link |
| StatusLine | `detail.mjs:447`, `detail.mjs:512` | `<div class="va-status">` or `<div class="dp-status">` | lamp, status, phase, elapsed |
| RunBox | `detail.mjs:373` | `<div class="pv-run">` or `<p class="pv-none">` | grade, model, key, value |
| NeedsYou | `detail.mjs:455` | `<div class="pv-why">` | title, item |
| Section | `detail.mjs:318`, `detail.mjs:367` | `<section class="dp-section">` or `<section class="pv-sec">` | title, count |
| RelationRow | `detail.mjs:304`, `detail.mjs:346` | `<button class="rel">` or `<button class="pv-rel [hold]">` | lamp, number, title, where, phase, state, hold |
| EventBlock | `detail.mjs:410`, `detail.mjs:397`, `detail.mjs:388` | `<div class="va-block [warn]">` with `va-bhead`, `va-body`, `va-ev`, `pv-detail` | toggle, chev, phase, summary, time, event, event-time, event-name, event-text, event-detail |
| SubIssueRow | `detail.mjs:473` | `<div class="pv-rel">` with `pv-kind [hot]` | lamp, number, title, kind |
| CountSummary | `detail.mjs:485` | `<div class="lamps-count">` and `<div class="phases-count">` | lamp-count, phase-count |
| DetailEmpty | `detail.mjs:548` | `<div class="dp-empty">` | title, text |
| Sheet | `settings.mjs:178`, `settings.mjs:185` | `<div class="scrim board">` holding `<div class="sheet">` with `sheet-head`, `sheet-body`, `sheet-foot` | eyebrow, title, intro, close, status, status-note, cancel, save |
| SetBlock | `settings.mjs:209` | `<section class="set-block [ruled]">` with `set-block-head` | title |
| ScanStatus | `settings.mjs:212` | `<span class="scan">` with `spin` or a `linkbtn` | scanning, scanned, rescan |
| HostChip | `settings.mjs:221` | `<span class="hs [missing|silent|down|unlaunchable]">` | name, state |
| Select | `settings.mjs:10` | `<select class="sel [changed|bad]">` | (root only) |
| RoleRow | `settings.mjs:225`, `settings.mjs:248` | `<div class="role">` or `<div class="runner-row">` | agent, what, host, model, effort, problem |
| ProblemLine | `settings.mjs:22` | `<div class="role-bad">` with `hatch` | (root only) |
| RefusedBanner | `settings.mjs:204` | `<div class="refused">` | text, reread |
| Button | `settings.mjs:273` | `<button class="btn [primary]">` or `<button class="linkbtn">` | (root only) |

## UI kits

One kit for the task board, recreating these screens from the components: the board after a night (top bar, task list, canvas with an expanded spec, the detail column on a ticket that needs the owner), and the same board with the settings sheet open. Also write one HTML file per region below, first line `<!-- @startingPoint section="Task board" subtitle="<one line>" viewport="<W>x<H>" -->`, showing that region alone at that size:

| Region | Size | What it shows |
| --- | --- | --- |
| 顶栏 | 1440x52 | the top bar with all four counters and the read time |
| 任务列表 | 236x848 | three tasks, one selected |
| 画布 | 864x848 | a map with decision tickets and a spec expanded into its tickets and blocking curves |
| 详情 | 340x848 | a ticket that needs the owner, with its event history |
| 本机配置 | 1440x900 | the settings sheet over a dimmed board |

## Rules this design system adds

1. Each component renders the same DOM the source renders: the same element types, class names and nesting. Its look comes from the source's own CSS rules, carried in a stylesheet `styles.css` imports; JSX adds no styling of its own.
2. Each component accepts a `data-ui` prop, sets it on its root element, and sets `data-ui="<that value>.<part>"` on each part the inventory lists for it.
3. Copy every numeric value exactly from the source. Copy the font files listed above; never substitute a font.
4. When you finish, list each inventory family with the component names you built for it, and anything you could not build.
