# Porting — a mockup into Claude Design

MCP tools: `mcp__claude-design__get_claude_design_prompt` (the Design Components format), `DesignSync` (writing files into the project), `mcp__claude-design__create_support_js` (the runtime), and `mcp__claude-design__render_preview` (a `serve_url` for inspecting what was uploaded). Confirm all four are callable before anything else. If one is missing, stop and tell the user this session cannot reach Claude Design, and which tool is absent.

A Claude Design project refines every page against a design system. Before the first upload, check whether the consuming repository has a `DESIGN.md`; if it has none, run the `create-design-md` skill to write one from that repository, then upload it in Claude Design under "Create new design system". This is once per project, not once per port: every interface designed afterwards holds to that system.

The mockup becomes a set of **components**, each a root-level `<name>.dc.html` page in the project. A component owns its state, exposes a `scene` enum prop — one value per state, and those values are the page's scene names — so the Tweaks panel can switch states, and reports cross-component actions through callback props; opened on its own, a callback falls back to a toast. Two layers compose them: **app pages** (`dc-import` each component, hold global state, wire callbacks) and an **overview** page in canvas mode.

Why components rather than one page per screen: the mockup's page-level JavaScript state machine ported into one logic class mixes every UI defect into a single file; a component is small enough to inspect state by state in the Tweaks panel and click button by button, and the wiring is added only at composition.

Read the Design Components format first: `mcp__claude-design__get_claude_design_prompt` returns the rules for `<x-dc>`, `helmet`, `sc-if` / `sc-for`, `{{ }}` template holes, `data-props`, and `dc-import`. This skill does not restate them.

## Working directory

One local directory; every script runs inside it, and its layout mirrors the project root:

```
work/
  mk.py            # copied from this skill's scripts/ (deadsweep.py expects it here)
  src/<name>.py    # one per component; annotated minimal example: scripts/example.src.py
  styles/*.css     # tokens plus the mockup's original CSS
  data/fixtures.js # window.<FX> = {...}; DC_FX names the global (default FIXTURES), DC_FX_FILE the path (default data/fixtures.js)
  <name>.dc.html   # mk.py output
```

Upload with the DesignSync tool (its description targets design-system projects, but it writes to an ordinary project as well): `list_files` → `finalize_plan` (declare `writes` as globs: `*.dc.html`, `styles/*.css`, `data/*.js`; pass `deletes: []` — the call fails without it; set `localDir` to `work/`) → `write_files` with `localPath` **and `mimeType`** (`text/html`, `text/css`, `text/javascript`); without `mimeType` CSS and JS are served as `text/plain` and rejected. One plan accepts repeated writes until it expires.

Verify remotely with `scripts/serve.sh`: split the `serve_url` returned by `mcp__claude-design__render_preview` into `BASE` and `TOK` and paste them in. The token is project-scoped and valid for every file for about one hour; once it expires the page renders the Claude sign-in screen and every screenshot is wrong — refresh the token first. The `serve_url` goes only to scripts and browser tools; the user receives `open_url`.

## Procedure

1. **Partition.** Read the input in full and cut it into components by what the user perceives as one region (title bar, list, form, sidebar, group of dialogs). The input comes in either of two shapes:
   - **An HTML mockup**, static or with page-level JavaScript: read its HTML and its JavaScript.
   - **The winning variant of a UI prototype**: framework source files sitting in a leaf directory (`prototypes/<task>/<issue>/UI/`), mounted on a real page behind a `?variant=` search param. Read those source files for the states and the interactions — the render branches, the boolean toggles, the dialogs, the event handlers. Do not read them for CSS or DOM: a framework decides both at runtime, so those come from the rendered page instead (step 2).

   Done when: a written inventory lists, per component, its states (`scene` branches in the source, `hidden` toggles, dialogs) and its cross-component actions (navigation, opening a dialog, mutating another component's state).
2. **Prepare assets.** `mcp__claude-design__create_support_js` writes `support.js` at the project root. Where the CSS and the data come from depends on the input shape:
   - **HTML mockup**: copy its CSS into `styles/` unchanged (faithful port first, refactor later); extract the fixture data and scene tables from its JavaScript into `data/fixtures.js` verbatim.
   - **Prototype leaf directory**: open the real page at `?variant=<winner>` and take the CSS and the DOM from what it renders — collect the rules the browser actually applies (`document.styleSheets`) into `styles/`, and keep the rendered DOM of the variant's subtree as the reference the templates are written against. Take the data from the props the page passes the variant, stub data included, into `data/fixtures.js`. Do this while the prototype's `?variant=` mount is still wired: the scaffolding comes down only after this port.

   When more than one stylesheet carries a `:root` block, merge those tokens into `styles/tokens.css` and leave one copy. In Claude Design each page loads the stylesheets it needs, so conflicting values never meet; the implementation loads them all into one document, where the last file's `:root` wins on every page.
3. **Write components.** One `src/<name>.py` per component; `DC_FX=<fixtures global> python3 mk.py src/<name>.py` builds it (the same `DC_FX` for every component of one mockup). `mk.py` supplies the helmet (which fixes the page root `#dc-root` to the application window size — `DC_FRAME`, default `1440x900` — centred on a grey page, so the editor shows the mockup at its real proportions instead of stretching it across the browser), the toast, backdrop and modal CSS, the fixtures polling, and the base-class methods `init(props)`, `onReady()`, `afterUpdate(prev)`, `cleanup()`, `toast(msg)`, `emit(name, detail, fallback)`, `fx()` — a component writes only its TEMPLATE and, in LOGIC, `init` and `renderVals`.
4. **Verify.** `python3 scripts/mkharness.py <name> '<JSON array of scene values>'` generates `Harness.dc.html` (rename with `DC_HARNESS=<file>`), a test harness whose `<select>` drives the component's `scenario` prop. Upload it, then use `open_page / sel / clk / q / errs / shot` from serve.sh to inspect the DOM per scenario, click every button, and read the screenshots. Done when: `errs` is empty in every scenario and every button produces an observable result (a DOM change or a toast). Finish one component, start the next; compose only after all components pass.
5. **Compose.** An app page is written by hand as a `.dc.html` (it is not a `src/*.py` source, so `mkallharness.py` needs no exclusion list for it); it `dc-import`s the components inside one `<main>`; page-level state chooses which component renders, passes `scenario` and data props, and receives callbacks. The overview page sets `<meta name="design_doc_mode" content="canvas">` in its helmet and follows the canvas rule from `get_claude_design_prompt`: every frame is `position: absolute` directly inside `<x-dc>` (no wrapper element, otherwise the editor gives no pan/zoom), its label carries `data-drags-parent="1"`, and the imported page is scaled with `transform: scale(0.5)` inside a clipped frame. The overview overrides `mk.py`'s fixed root (`html body #dc-root { width: auto; height: auto; overflow: visible; transform: none; }`) because the imported components' helmets mount into its head too; size the import host explicitly (`.ov-scale > .sc-host, .ov-scale > .sc-host > * { width: 1440px; height: 900px; }`) — an app page inside the overview otherwise collapses to its header. Done when: every end-to-end path in the mockup can be clicked through on the app page.
6. **Flatten the CSS.** The Claude Design editor resolves only `.a`, `.a.b`, and `.a .b` selectors (pseudo-classes allowed); a chain like `.card header h2` from the mockup is unreachable to it. Flatten only after every component has passed step 4 — otherwise a regression cannot be attributed to the port or to the flattening:
   1. `python3 scripts/mkallharness.py` generates `Harness.dc.html`, which renders every component in every scene; upload it, open it, and run `playwright-cli --raw eval "$(cat scripts/collect_dom_classes.js)" > domclasses.json`. This records the classes each template element actually renders with, which is how dynamic classes (`class="{{ x }}"`) get resolved.
   2. Install the dependencies (`uv venv && uv pip install beautifulsoup4 soupsieve tinycss2`) and run `python scripts/flatten.py src styles/*.css`. Descendant chains become one new class (`.active-project strong` → `.active-project-strong`) written back into the templates; a state on an ancestor (`.a.on .b`) becomes `.on .b`; a trailing state (`button.on`) becomes `.a-button.on`; a chain whose last segment is a bare element with no matching template element is deleted, because it can only match the `span.sc-interp` wrapper `support.js` adds. Handle the entries the report lists under `manual` by hand, and read the `dropped` list: a dropped rule that styled a real element (e.g. `dialog button`, whose `<dialog>` became `.dc-modal`) is rewritten against the new class, not lost.
   3. `python scripts/deadsweep.py src data/fixtures.js styles/*.css` removes class rules nothing references. **Read the printed deletion list before accepting it**: a feature the mockup marks "not yet available" (a disabled tab, an unreached branch) keeps its underlying code — if no component renders it yet, add a prop that does, so the unreached branch has a scenario of its own. Delete only screens left over from earlier mockup rounds.
   4. Rebuild, upload, and repeat step 4; compare screenshots pixel by pixel with the pre-flattening ones. The only expected differences are places where an accidental match on the wrapper span has been corrected.
7. **Finish.** Delete `Harness.dc.html` and any obsolete pages with the claude-design MCP tools `finalize_plan` (`deletes`) and `delete_files` (with etags); keep `src`, `styles`, and `data` in the consuming repository; give the user the `open_url` of every page.

   A port that started from a prototype leaf directory ends by handing the design off into that same directory: [`handoff.md`](handoff.md).

## Component conventions

- Components live at the **project root**: helmet paths resolve relative to the host page, so a component in a subdirectory loses `./styles/…` the moment it is opened, and a thin wrapper page is neither editable nor has a Tweaks panel.
- Only props declared in `data-props` appear in the Tweaks panel: `scene` uses `editor: "enum"` with `options`; booleans `editor: "boolean"`; text `editor: "text"`.
- Template rules: whole-value attributes `onClick="{{ fn }}"`, `disabled="{{ bool }}"`; `[hidden]` becomes `sc-if`; a `<dialog>` becomes two divs, `.dc-backdrop` and `.dc-modal`; lists use `sc-for` with per-item event closures built in `renderVals`; a dynamic class may be mixed with static ones: `class="base {{ x.cls }}"`.
- A component fills its frame with `height: 100%` on its outermost element in `EXTRA_CSS` (never `100vh`: the frame is smaller than the viewport); `mk.py` sets `#dc-root > * { height: 100% }` — a component that keeps its natural height (a header bar) re-declares that as `height: auto` in `EXTRA_CSS`; `#dc-root` carries `transform: translateZ(0)` so `position: fixed` overlays (backdrop, modal, toast) are contained to the frame. An app page keeps the components at `100%` and lays components out with CSS grid — each `dc-import` renders as a `div.sc-host`.
- `init(props)` runs once before the fixtures arrive: return an empty skeleton when `this.fx()` is empty.
- Choose state names that do not collide with existing `DCLogic` methods (`patch` is shadowed).
- Cross-component actions: `this.emit("onXxx", detail, "→ toast text shown when opened alone")`.
- `support.js` wraps every `{{ }}` text in `span.sc-interp`, so an element selector such as `.x span` matches it by accident — a second reason to flatten the CSS. The wrapper also takes an `<option>`'s text out of its own child text nodes, which is where an `<option>`'s accessible name comes from, so a downloaded page reports its options unnamed.

## Verification pitfalls

- Playwright's `text=` is a substring match and hits headings; target buttons with CSS selectors or `>> nth=0`.
- With multiple matches `click` fails silently (`clk` swallows stderr); count the elements with `q` first.
- `q` takes an expression; wrap statements as `(()=>{…})()`.
- `sel` does not reset a component when the scene is unchanged; switch to another scene first.
- Drag and drop across components: `playwright-cli drag <source> <target>` exercises `dragstart` / `drop`.

## Scripts

[scripts/](../scripts/) — `mk.py`, `mkharness.py`, `mkallharness.py`, `serve.sh`, `collect_dom_classes.js`, `flatten.py`, `deadsweep.py`; `example.src.py` is the component-source template.
