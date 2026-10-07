# Story parity

`story-parity.py`, the **story oracle**, compares a product story with the Claude Design
page it was built from, element by element, by `data-ui` id.

Two agents use this page. An agent building a story reads **The story page the product
serves**. An agent fixing a `DIFF` line reads **The DIFF line**. An agent whose run
exited 2 reads **When the oracle cannot judge**.

## The story page the product serves

The contract ticket builds the **story service** (the server that `.mmw/target.json`'s
`stories` command brings up) under `.mmw/stories/`; later page
tickets add one story adapter per design page.

- `.mmw/target.json`'s `stories` command starts the service in the foreground and
  prints `origin=<url>`. The oracle starts that command with `MMW_AUTOMATION=1` and
  ends the command and all descendants it started. A story uses a machine-chosen
  port and no lease.
- The oracle opens
  `<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`. `mount` comes from the
  screen contract's `pages`; `name` comes from `scenes.json`. `Component · ` and `App · `
  pages use the same request and comparison.
- `[data-story-root]` is on the product component's own root element. That same
  element carries the `data-ui` id on the design page's root. It is not a wrapper
  around the component and not a child inside it.
- Every other product element being compared carries the same `data-ui` id as the
  corresponding element on the design page. Repeated component instances may reuse
  an id; the oracle pairs them in document order.
- The adapter takes the scene's **scene data** and maps it to the product
  component. Scene data is the `data` field of the scene's `scenes.json` entry:
  the displayed text keyed by `data-ui` id, nested where one id contains another,
  `_text` holding a node's own text, a list where an id repeats. When the screen contract
  declares `scenes.<name>.input`, the adapter takes that value from the design
  package file instead, with the input's `with` fields
  merged over it: it is what the design page
  itself drew the scene from, so lamp colours, layout and other state that the
  displayed text does not carry reach the product component too. No backend, seed,
  route or alternate preview projection runs. After a click the region enters the
  scene the screen-contract row's `next` names, and the adapter draws that scene's own
  input: a scene stands for a state, so the clicked object needs no data of its own.

## The two sides

The product side is the subtree rooted at `[data-story-root]`. The design side is
the design package's page, rendered offline in the same screen-contract viewport window;
`#dc-root` keeps the size the design page renders at in that window.
Both browser contexts take `locale` from the screen contract. Neither side reads a live clock: the
design side keeps its paused clock, and the product's time values come from scene
data. Both sides are read as rendered. The oracle does not hide controls or replace
display values.

For each `[data-ui]` element, the common reader records these facts in document
order:

| field | fact |
| --- | --- |
| `id` | `data-ui`; repeated values become `<id>#<n>`, from 1, and a lone match on the other side becomes `<id>#1` |
| `disabled` | true for a control matching `:disabled` or carrying `aria-disabled="true"`; recorded for the skeleton's `disabled_in`, not compared |
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

The oracle's comparison is **element parity**. The same id on each side is one
pair. Repeated ids pair in document order. An id only on the design side is
`missing`; one only on the product side is `extra`.

If either paired element is not visible, the oracle compares only `visible`. It does
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
images are supporting evidence, not another verdict. Fix the product component, not
the story page: the story page only puts the real component into a scene, so a style
or wrapper added there closes the `DIFF` while the product stays wrong. `--out <dir>`
keeps both screenshots, their pixel difference image and the ARIA capture.

## When the oracle cannot judge

Exit 2. The output is not a `DIFF` line and does not contain `STORY OK`.

The story service exits, or prints no origin within its wait. The oracle prints that
service's last 15 output lines, one per line, then a refusal. The log lines stay
outside the refusal, because the refusal is capped at 256 characters and the real
error is often not the first line.

The design page throws, or `#dc-root` never becomes visible. The oracle prints four
lines, `scene`, `file`, `url` and `error`, then a refusal. The refusal says the design
page failed and the product was not compared. The next step is a contract child,
`verify-ticket.py <n> --sub-issue contract <file>`. A throw inside a timer on the
paused clock is reported as a console error with a stack. That is still this refusal.
A one-line `console.error` string is not.

Anything else compare did not expect, such as a navigation timeout, is the same exit
2. It is not exit 1. Exit 1 is a real `DIFF` line.

A design page that throws nothing and renders no `data-ui` element prints one stdout
line, `read 0 data-ui elements at <url> screenshot <path>`, and exits 2. `<url>` is
the design page. `<path>` is the design screenshot under `--out`. This is not
`NEGATIVE CONTROL FAILED`.

## Console errors

A design-page console error that is not an uncaught exception is printed and written
to `--out/media/<scene>-<W>x<H>-console.txt`. The verdict is unchanged. There is no
`--console-errors` flag.

## Element facts on disk

Each compared pair writes `--out/media/<scene>-<W>x<H>-elements.json`. The file has
two arrays, `design` and `product`. Each item is one `[data-ui]` element, and the
fields are the table in **The two sides**. The file sits next to that pair's
screenshots. `--render-only` still writes
`--out/values/<mount>/<scene>-<W>x<H>.json` and does not write this file.

## Negative controls

Once per run, after a design page has rendered at least one `data-ui` element, the
oracle proves it can see a changed style and a missing id. When it cannot, it exits 2
with `NEGATIVE CONTROL FAILED`. A design page with no `data-ui` element takes the
zero-count line in **When the oracle cannot judge** and does not reach this gate.
