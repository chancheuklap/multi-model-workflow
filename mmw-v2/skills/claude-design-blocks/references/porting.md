# Porting — a mockup into Claude Design

`<scripts>` below is resolved by `SKILL.md`'s section **Resolve `<scripts>` once**.

MCP tools: `mcp__claude-design__get_claude_design_prompt` (the Design Components format), `DesignSync` (writing files into the project), `mcp__claude-design__create_support_js` (the runtime), and `mcp__claude-design__render_preview` (a `serve_url` for inspecting what was uploaded). Confirm all four are callable before anything else. If one is missing, stop and tell the user this session cannot reach Claude Design, and which tool is absent.

A Claude Design project refines every page against a design system. Before the first upload, check whether the consuming repository has a `DESIGN.md`; if it has none, run the `create-design-md` skill to write one from that repository, then upload it in Claude Design under "Create new design system". This is once per project, not once per port: every interface designed afterwards holds to that system.

The mockup becomes a set of **components**, each a root-level `<name>.dc.html` page in the project. A component owns its state, exposes a `scene` enum prop — one value per state, and those values are the page's scene names — so the Tweaks panel can switch states, and reports cross-component actions through callback props; opened on its own, a callback falls back to a toast. Two layers compose them: **app pages** (`dc-import` each component, hold global state, wire callbacks) and an **overview** page in canvas mode.

Why components rather than one page per screen: the mockup's page-level JavaScript state machine ported into one logic class mixes every UI defect into a single file; a component is small enough to inspect state by state in the Tweaks panel and click button by button, and the wiring is added only at composition.

Read the Design Components format first: `mcp__claude-design__get_claude_design_prompt` returns the rules for `<x-dc>`, `helmet`, `sc-if` / `sc-for`, `{{ }}` template holes, `data-props`, and `dc-import`. This skill does not restate them.

## Working directory

One local directory, `work/`; every command below runs inside `work/`, and its layout mirrors the project root:

```
work/
  mk.py            # copied from <scripts> (deadsweep.py expects it here)
  serve.sh         # copied from <scripts>; BASE and TOK go in this copy
  src/<name>.py    # one per component; annotated minimal example: <scripts>/example.src.py
  styles/*.css     # tokens plus the mockup's original CSS
  data/fixtures.js # window.<FX> = {...}; DC_FX names the global (default FIXTURES), DC_FX_FILE the path (default data/fixtures.js)
  <name>.dc.html   # mk.py output
```

Upload with the DesignSync tool (its description targets design-system projects, but it writes to an ordinary project as well):

1. `list_files`.
2. `finalize_plan`: declare `writes` as globs (`*.dc.html`, `styles/*.css`, `data/*.js`); pass `deletes: []` — the call fails without it; set `localDir` to `work/`; one plan accepts repeated writes until it expires.
3. `write_files` with `localPath` **and `mimeType`** (`text/html`, `text/css`, `text/javascript`); without `mimeType` CSS and JS are served as `text/plain` and rejected.

Verify remotely with `serve.sh`: copy it out of `<scripts>` into `work/` the way `mk.py` is copied, split the `serve_url` returned by `mcp__claude-design__render_preview` into `BASE` and `TOK`, fill those two into `work/serve.sh`, and `source work/serve.sh`. The values go in that copy: this skill's directory is one symlink shared by every repository on the machine, so a token pasted into `<scripts>/serve.sh` is a credential written into the copy every other run loads. The token is project-scoped and valid for every file for about one hour; once it expires the page renders the Claude sign-in screen and every screenshot is wrong — refresh the token first. The `serve_url` goes only to scripts and browser tools; the user receives `open_url`.

## Procedure

1. **Partition.** Read the input in full and cut it into components by what the user perceives as one region (title bar, list, form, sidebar, group of dialogs). The input comes in either of two shapes:
   - **An HTML mockup**, static or with page-level JavaScript: read its HTML and its JavaScript.
   - **The winning variant of a UI prototype**: framework source files sitting in a leaf directory (`prototypes/<task>/<issue>/UI/`), mounted on a real page behind a `?variant=` search param. Read those source files for the states and the interactions — the render branches, the boolean toggles, the dialogs, the event handlers. Do not read them for CSS or DOM: a framework decides both at runtime, so those come from the rendered page instead (step 2).

   Done when: a written inventory lists, per component, its states (`scene` branches in the source, `hidden` toggles, dialogs) and its cross-component actions (navigation, opening a dialog, mutating another component's state).
2. **Prepare assets.** `mcp__claude-design__create_support_js` writes `support.js` at the project root.

   2a. **Input shapes.** Where the CSS and the data come from depends on the input shape:
   - **HTML mockup**: take its CSS into `styles/`; extract the fixture data and scene tables from its JavaScript into `data/fixtures.js` verbatim.
   - **Prototype leaf directory**: open the real page at `?variant=<winner>` and take the CSS and the DOM from what it renders — collect the rules the browser actually applies (`document.styleSheets`) into `styles/`, and keep the rendered DOM of the variant's subtree as the reference the templates are written against. Take the data from the props the page passes the variant, stub data included, into `data/fixtures.js`. Do this while the prototype's `?variant=` mount is still wired: the scaffolding comes down only after this port.

   When more than one stylesheet carries a `:root` block, merge those tokens into `styles/tokens.css` and leave one copy. In Claude Design each page loads the stylesheets it needs, so conflicting values never meet; the implementation loads them all into one document, where the last file's `:root` wins on every page.

   2b. **Selector rewrite.** **The CSS arrives in the editor's terms, not the mockup's.** Claude Design can direct-edit a rule only when its selector is a single class `.a`, a two-class compound `.a.b`, or a two-class descendant `.a .b` (pseudo-classes allowed) — the rule is stated under Styling in what `get_claude_design_prompt` returns. Anything deeper renders correctly and is unreachable from the editor's panel, which is what the project exists for: a page nobody can polish is a port that did not land.

   So rewrite each rule as you bring it over — a descendant chain becomes one class on the element it styles (`.card header h2` → `.card-title`), a state attribute becomes a second class or a prop the template branches on (`.tab[aria-selected="true"]` → `.tab.on`, `[hidden]` → `sc-if`), an id becomes a class. `python3 <scripts>/selector_check.py styles/*.css` names what is left and why.

   Fidelity is not what this trades away: step 4 compares each component against the mockup scene by scene, and that comparison is what the port is held to, not a byte-for-byte stylesheet.
3. **Write components.** One `src/<name>.py` per component; `DC_FX=<fixtures global> python3 mk.py src/<name>.py` builds it (the same `DC_FX` for every component of one mockup). That is the copy in `work/`, not `<scripts>/mk.py`: `deadsweep.py` reads `mk.py` from beside `src/`, and pointing this line at the skill would leave it with nothing to read. `mk.py` supplies the helmet (which fixes the page root `#dc-root` to the application window size — `DC_FRAME`, default `1440x900` — centred on a grey page, so the editor shows the mockup at its real proportions instead of stretching it across the browser), the toast, backdrop and modal CSS, the fixtures polling, and the base-class methods `init(props)`, `onReady()`, `afterUpdate(prev)`, `cleanup()`, `toast(msg)`, `emit(name, detail, fallback)`, `fx()` — a component writes only its TEMPLATE and, in LOGIC, `init` and `renderVals`.
4. **Verify.** `python3 <scripts>/mkharness.py <name> '<JSON array of scene values>'` generates `Harness.dc.html` (rename with `DC_HARNESS=<file>`), a test harness whose `<select>` drives the component's `scene` prop. Upload it, then use `open_page / sel / clk / q / errs / shot` from `work/serve.sh` to inspect the DOM per scene, click every button, and read the screenshots. Done when: `errs` is empty in every scene, every button produces an observable result (a DOM change or a toast), the component reads like the mockup at every scene, and `python3 <scripts>/selector_check.py styles/*.css` exits 0. Finish one component, start the next; compose only after all components pass.
5. **Compose.** An app page is written by hand as a `.dc.html` (not a `src/*.py` source; the handoff export reads the page itself rather than a source); it `dc-import`s the components inside one `<main>`; page-level state chooses which component renders, passes `scene` and data props, and receives callbacks. The overview page sets `<meta name="design_doc_mode" content="canvas">` in its helmet and follows the canvas rule from `get_claude_design_prompt`: every frame is `position: absolute` directly inside `<x-dc>` (no wrapper element, otherwise the editor gives no pan/zoom), its label carries `data-drags-parent="1"`, and the imported page is scaled with `transform: scale(0.5)` inside a clipped frame.

   The overview overrides `mk.py`'s fixed root (`html body #dc-root { width: auto; height: auto; overflow: visible; transform: none; }`) because the imported components' helmets mount into its head too; size the import host explicitly (`.ov-scale > .sc-host, .ov-scale > .sc-host > * { width: 1440px; height: 900px; }`) — an app page inside the overview otherwise collapses to its header. Done when: every end-to-end path in the mockup can be clicked through on the app page.
6. **Sweep and finish.** `python3 <scripts>/deadsweep.py --dry-run src data/fixtures.js styles/*.css` prints the class rules nothing references and writes nothing. **Read that list, then run the same command without `--dry-run`** — the real run rewrites every stylesheet in place, and `work/` need not be under git. What to keep: a feature the mockup marks "not yet available" (a disabled tab, an unreached branch) keeps its underlying code — if no component renders it yet, add a prop that does, so the unreached branch has a scene of its own. Delete only screens left over from earlier mockup rounds. Then delete `Harness.dc.html` and any obsolete pages with the claude-design MCP tools `finalize_plan` (`deletes`) and `delete_files` (with etags); keep `src`, `styles`, and `data` in the consuming repository; give the user the `open_url` of every page.

   A port that started from a prototype leaf directory ends by handing the design off into that same directory: [`handoff.md`](handoff.md).

## Component conventions

- Components live at the **project root**: helmet paths resolve relative to the host page, so a component in a subdirectory loses `./styles/…` the moment it is opened, and a thin wrapper page is neither editable nor has a Tweaks panel.
- Only props declared in `data-props` appear in the Tweaks panel: `scene` uses `editor: "enum"` with `options`; booleans `editor: "boolean"`; text `editor: "text"`.
- One class per element the design touches, named for what the element is (`.card-title`, `.queue-row`), not for where it sits. A state is a second class on the same element (`.tab.on`) or a `sc-if` branch, never an attribute selector: the editor reaches `.a` and `.a.b`, and reaches neither `[aria-selected="true"]` nor a three-level chain. `EXTRA_CSS` is the exception — it glues `dc-import` hosts into a layout (`.wb-app .app > .workspace`), and nobody polishes a host from the panel, so it is not held to this and `selector_check.py` is not pointed at it.
- Template rules: whole-value attributes `onClick="{{ fn }}"`, `disabled="{{ bool }}"`; `[hidden]` becomes `sc-if`; a `<dialog>` becomes two divs, `.dc-backdrop` and `.dc-modal`; lists use `sc-for` with per-item event closures built in `renderVals`; a dynamic class may be mixed with static ones: `class="base {{ x.cls }}"`.
- A component fills its frame with `height: 100%` on its outermost element in `EXTRA_CSS` (never `100vh`: the frame is smaller than the viewport); `mk.py` sets `#dc-root > * { height: 100% }` — a component that keeps its natural height (a header bar) re-declares that as `height: auto` in `EXTRA_CSS`; `#dc-root` carries `transform: translateZ(0)` so `position: fixed` overlays (backdrop, modal, toast) are contained to the frame. An app page keeps the components at `100%` and lays components out with CSS grid — each `dc-import` renders as a `div.sc-host`.
- `init(props)` runs once before the fixtures arrive: return an empty skeleton when `this.fx()` is empty.
- Choose state names that do not collide with existing `DCLogic` methods (`patch` is shadowed).
- Cross-component actions: `this.emit("onXxx", detail, "→ toast text shown when opened alone")`.
- `support.js` wraps every `{{ }}` text in `span.sc-interp`, so an element selector such as `.x span` matches it by accident — a second reason no selector carries an element name. The wrapper also takes an `<option>`'s text out of its own child text nodes, which is where an `<option>`'s accessible name comes from, so a downloaded page reports its options unnamed.

## Verification pitfalls

- Playwright's `text=` is a substring match and hits headings; target buttons with CSS selectors or `>> nth=0`.
- With multiple matches `click` fails silently (`clk` swallows stderr); count the elements with `q` first.
- `q` takes an expression; wrap statements as `(()=>{…})()`.
- `sel` does not reset a component when the scene is unchanged; switch to another scene first.
- Drag and drop across components: `playwright-cli drag <source> <target>` exercises `dragstart` / `drop`.

## Scripts

`<scripts>` ([scripts/](../scripts/)) — `mk.py`, `mkharness.py`, `serve.sh`, `selector_check.py`, `deadsweep.py`; `example.src.py` is the component-source template. `mk.py` and `serve.sh` are copied into `work/` and run from there. Standard library only; nothing here needs `uv`.
