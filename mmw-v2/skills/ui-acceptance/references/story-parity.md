# Story parity

`<scripts>/story-parity.py`, the **story judge**, decides whether a product story
matches the Claude Design page it was built from. `<scripts>` is the token defined
by this skill's **Resolve `<scripts>` once** section. The judge reads the screen
contract and the handoff package's `scenes.json`, starts the story service, and
compares every selected scene at every contract viewport by `data-ui` id.

Four agents use this page. An agent taking design facts before implementation uses
**`--render-only`**. An agent building a story reads **The story page the product
serves**. An agent writing a ticket copies **The criterion, in one shape**. An agent
fixing a failure reads **The DIFF line**.

## The story page the product serves

The contract ticket builds the service under `.mmw/stories/`; later interface
tickets add one story adapter per design page.

- `.mmw/target.json`'s `stories` command starts the service in the foreground and
  prints `origin=<url>`. The judge starts that command with `MMW_AUTOMATION=1` and
  ends the command and all descendants it started. A story uses a machine-chosen
  port and no lease.
- The judge opens
  `<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`. `mount` comes from the
  contract's `pages`; `name` comes from `scenes.json`. `Component · ` and `App · `
  pages use the same request and comparison.
- `[data-story-root]` is on the product component's own root element. That same
  element carries `data-screen="<mount>"` and the `data-ui` id on the design page's
  root. It is not a wrapper around the component and not a child inside it.
- Every other product element being compared carries the same `data-ui` id as the
  corresponding element on the design page. Repeated component instances may reuse
  an id; the judge pairs them in document order.
- The adapter takes the scene's `scene data` and maps it to the product
  component. No backend, seed, route or alternate preview projection runs. The
  screen contract's `shows` columns bind the mapping; code review checks that each `shows` name is a property of the component.

## The two sides

The product side is the subtree rooted at `[data-story-root]`. The design side is
the handoff package's page, rendered offline in the same contract `viewports`
window; `#dc-root` keeps the size the design page renders at in that window.
`viewports` is a top-level list of `WIDTHxHEIGHT` entries. `locale` is a top-level
BCP 47 tag (`zh-CN`, `en-US`). Both are required; there is no fallback. The form
is in write-screen-contract `references/screen-contract-format.md` under Top level. Both browser
contexts take `locale` from the contract. Neither side reads a live clock: the
design side keeps its paused clock, and the product's time values come from scene
data. Both sides are read as rendered. The judge does not hide controls or replace
display values.

For each `[data-ui]` element, the common reader records these facts in document
order:

| field | fact |
| --- | --- |
| `id` | `data-ui`; repeated values become `<id>#<n>`, from 1, and a lone match on the other side becomes `<id>#1` |
| `visible` | false for `display: none`, `visibility: hidden`, `opacity: 0`, or a zero width or height |
| `text` | own character data and descendants without `data-ui`, including `span.sc-interp`, with whitespace collapsed |
| `size` | integer `[width, height]` in CSS pixels |
| `ancestor` | nearest `data-ui` ancestor, or null; repeated ids use `<id>#<n>` |
| `offset` | top-left relative to that ancestor, or null |
| `previous` | previous element with the same nearest `data-ui` ancestor, or null; repeated ids use `<id>#<n>` |
| `gap` | `[left − previous.right, top − previous.bottom]`, or null |
| `style` | `font-size`, `font-weight`, `color`, `background-color`, `border-radius` |

Class names, font families, line heights, hover styles and focus styles are not
compared.

## Element parity

The judge's comparison is **element parity**. The same id on each side is one
pair. Repeated ids pair in document order. An id only on the design side is
`missing`; one only on the product side is `extra`.

If either paired element is not visible, the judge compares only `visible`. It does
not report any descendant carrying `data-ui`, so hiding one parent produces one
line. When both are visible it compares `text`, `size`, the five style facts,
`parent`, and `position`:

- Width or height differs only when the difference exceeds 2 px.
- A different nearest `data-ui` ancestor is one `parent` difference. The element's
  offset is not compared in that case.
- On each axis, `position` differs when `offset` differs by more than 2 px and one
  of these is also true: the element has no `previous`; the two sides name different
  `previous` elements; or the same-axis `gap` differs by more than 2 px. This leaves
  a whole top-level block move unreported, reports the parent whose movement carried
  its children, and does not report a later element merely pushed by a taller
  previous element.

Any element difference exits 1. Pixel differences never decide the exit code, but
every scene and viewport still writes its pixel difference image under `--out` as
evidence.

## The criterion, in one shape

The criterion names the judge bare because `verify-ticket.py` puts `<scripts>` on
the shell's `PATH`:

```
CHECK: story-parity.py --contract docs/specs/<effort>/screen-contract.yaml --pages <id,id>
EXPECT: STORY OK <passed>/<total>
```

`--pages` is a comma-separated list of contract mounts. `--scenes` may narrow the
scenes belonging to those mounts. `<total>` is scene × viewport pairs.

## The DIFF line

One fact produces one line:

```
DIFF <mount> <scene> <W>x<H> <data-ui id> <property> design=<value> product=<value>
DIFF <mount> <scene> <W>x<H> <data-ui id> missing
DIFF <mount> <scene> <W>x<H> <data-ui id> extra
```

Repeated ids appear as `<id>#<n>`. `<property>` is `visible`, `text`, `size`,
`position`, `parent`, `font-size`, `font-weight`, `color`, `background-color`, or
`border-radius`. The named id and property are the complete repair target; pixel
images are supporting evidence, not another verdict.

## Negative controls

Once per run, using its first scene and viewport, the judge proves both detection
paths before trusting any result:

1. It adds 7 px to every design-side `data-ui` element's computed font size and
   requires at least one element difference. A product story with no ids therefore
   reaches the ordinary `missing` report instead of making the control itself fail.
2. It removes every product-side `data-ui` attribute and requires at least one
   `missing` difference.

Either control reporting nothing exits 2 with `NEGATIVE CONTROL FAILED` and no
`STORY OK`. A design page with no `data-ui` therefore cannot pass. These controls
prevent accidental cheating caused by an agent following an old implementation
habit; they are not intended to defeat deliberate sabotage.

## `--render-only`

`--render-only` renders only the design side and does not read `.mmw/target.json`.
It writes screenshots under `--out/media` and the element facts from that same
render to:

`--out/values/<mount>/<scene>-<W>x<H>.json`

The JSON array uses the fields in **The two sides** and preserves document order.

## Exit codes

- `0`: one line `STORY OK <passed>/<total>`.
- `1`: one or more lines in **The DIFF line** shape.
- `2`: a negative control failed; the `stories` command did not start; a story page
  404 or other error status; the story page could not be opened; no visible
  `[data-story-root]`; `--pages` is empty or names a mount the contract does not
  declare; `--scenes` names a scene outside the mount; the contract has no
  `viewports` or no `locale`; `volatile_values` is non-empty; a `retired_ids` entry
  carries `trigger`; or the product story page carries `sc-interp`, `data-dc-tpl`,
  `data-dc-script` or `dc-root`. Each refusal names the fact, why, and what to do
  next. `--render-only` applies the same `viewports`, `locale`, `volatile_values`
  and `retired_ids` refusals; Claude Design runtime traces need a product page
  and do not apply.

`--out <dir>` keeps both screenshots, their pixel difference image and the ARIA
capture beside each screenshot. `--render-only` additionally writes the design
facts described above.
