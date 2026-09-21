# MMW task board design system

The MMW task board is a local web page for one person: it reads one repository's planning work from GitHub (a map, its decision tickets, its specs, their tickets and the sub-issues those open) and draws it as a canvas, with a sheet that sets which host, model and effort each coding agent runs on. This design system is that page's look and its parts, rebuilt from the page's own code.

## How to use it

- Link `styles.css` on every page. It only imports: tokens (`tokens/`), the font faces (`fonts/`), and one stylesheet per component group (`components/<group>/<group>.css`).
- Load `_ds_bundle.js` and mount components as `window.MMWTaskBoard2_34b698.<Name>` (in a Design Components page: `<x-import component-from-global-scope="MMWTaskBoard2_34b698.<Name>" …>`). Each renders exactly the markup and classes the product renders, so a page built from them and the product compare element to element.
- Give each component a `data-ui` id; it puts that id on its root and `<id>.<part>` on its parts.
- Take every colour and family from the variables; the component stylesheets carry the product's exact pixel values.

## Sources

- Code: https://github.com/chancheuklap/multi-model-workflow, `mmw-v2/board/page/` (branch `dev`): `topbar.mjs`, `tasks.mjs`, `canvas.mjs`, `detail.mjs`, `settings.mjs` for markup; `styles/tokens.css`, `styles/board.css`, `styles/settings.css` and `index.html` for styles; `styles/fonts/` for the font files.
- Behaviour and wording: the task board spec, issue #318 of that repository.

## CONTENT FUNDAMENTALS

- Two languages on purpose. Pipeline vocabulary stays English and lower case where it is a name from the tracker or the event log: lamp words (`needs you`, `running`, `queued`, `done`), step names (`queued`, `working`, `waiting`, `review`, `verify`, `landed`), event names in sentence case (`Worker started`, `Merge bounced`). Everything that explains or instructs is Chinese: `读 GitHub 失败 · 下面是 07:12 的数据（28 分钟前）`, `这台机器上没装 grok 的 CLI（grok），换一个这台机器有的`.
- Statements, not chat: no "you" addressed except where the owner must act (`只有你能拍板`). No emoji, no exclamation marks.
- Numbers and ids are literal: `#133`, `6/18 landed`, `1h02m`, `07:39`. Separators are ` · ` with spaces.
- A problem line says what is wrong and what to do, in one sentence: `Paseo 服务没开，问不到 claude 的 model；先开 Paseo，或者把 runner 换回 orca 或 herdr`.

## VISUAL FOUNDATIONS

- **Colour.** Paper and ink: grounds `--paper` #f3f3f1, `--canvas` #ebecee, `--panel` #fff; text `--ink` #2d3142 down to `--ghost`. Orange (`--orange` #eb6c36) means only "needs you" and appears nowhere else; green (`--led-green` #22a06b) means only "running", on the lamp and on a moving blocking line alike; red (`--led-red` #c9304f) is a blocked line. Selection is an ink outline, never orange. The settings sheet uses no lamp colour.
- **Type.** Geist for text (13px body, 1.45), Geist Mono for numbers, ids, times and small uppercase eyebrows (9–11.5px), Instrument Serif italic only for the brand name and empty-state titles.
- **Space.** Columns pad 18–24px across; sections are separated by a `--rule-2` hairline with 12–16px above. The canvas is a 28px dot grid.
- **Backgrounds.** Flat colour only; no images, no gradients except the hatching below.
- **Borders and radius.** 1px `--rule` borders; cards 10px, the sheet 12px, buttons, blocks and fields 6–8px; lamps, pills and counters fully round.
- **Shadows.** Panels are flat. Only the selected card, the zoom bar and the settings sheet cast a shadow.
- **Hover and press.** Hover darkens a border or text one step toward ink; the needs-you counter tints orange. There is no separate pressed colour. Keyboard focus is a 2px `--focus` outline.
- **Stale or refused values** are hatched ink (diagonal stripes, ink border): a failed GitHub read, a cell `start` would refuse, a refused save.
- **Motion.** The only moving thing is the green beam travelling a running blocking line; with reduced motion it is a still bright green line.
- **Cards.** White, 1px border, 10px radius, a lamp and number on top, the title largest, a mono run line at the bottom; a ticket opened in the closing pass has a slate bar on its inner left edge.

## ICONOGRAPHY

Two icons, both from Lucide as the product inlines them: `rotate-cw` (read GitHub now) and `settings` (the settings sheet), 15px, 1.8 stroke, `currentColor` (`assets/icons/`). Everything else is typographic: lamps are dots, the expand control is `▸`/`▾`, close is `×`, links end in `↗`. No emoji.

## Index

- `styles.css`, `tokens/colors.css`, `tokens/typography.css`, `tokens/fonts.css`, `fonts/` (Geist, Geist Mono, Instrument Serif).
- `components/status/` Lamp, StepPill · `components/topbar/` Brand, Counter, ReadState, IconButton · `components/tasks/` ColumnEyebrow, TaskRow, TasksEmpty · `components/canvas/` ContainerCard, DecisionCard, TicketCard, Edges, LaneLabel, Legend, ZoomBar, CanvasEmpty · `components/detail/` DetailHead, DetailTitle, Origin, StatusLine, RunBox, NeedsYou, Section, RelationRow, NoneNote, EventBlock, EventRow, SubIssueRow, LampCounts, PhaseCounts, GithubButton, DetailEmpty · `components/settings/` Sheet, RefusedBanner, SetBlock, ScanStatus, HostChip, Select, ProblemList, RoleRow, RunnerRow, RolesTable, SetNote, CodeText, Button · `components/frame/` the page frame classes (`app-shell`, `app-top`, `app-slot`, `app-sheet`) and `.board`.
- `guidelines/` foundation cards: colours, type, spacing, brand.
- `ui_kits/task-board/` the board after a night, the board with settings open, and one starting point per region (`TopBar`, `TaskList`, `Canvas`, `Detail`, `Settings`).
- `assets/icons/`, `SKILL.md`.

## Intentional additions

- `CodeText`, `SetNote`, `RolesTable`, `NoneNote`, `DetailTitle`, `GithubButton`: the product writes these as inline elements inside larger render functions rather than as separate helpers; they are split out so a page can place them, and render the same element and class the product does.
- `data-ui` on every component: an acceptance id, not visual; the product carries none.
