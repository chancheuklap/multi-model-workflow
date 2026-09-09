# Interface parity

Whether a product story matches the design page it was built from is
`scripts/story-parity.py`, next to this skill's `SKILL.md`. It reads the screen
contract and `scenes.json`, starts the product's story service from
`.mmw/target.json`'s `stories` command (which prints `origin`), opens
`<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`, and compares that render
with the design page rendered offline from the handoff package — by accessibility
tree and by pixels, at every viewport the contract names. The class set is not
compared.

Three agents come here. The one **building** the story page and its adapter needs the
next section. The one **writing** the criterion needs the shape below it. The one
**reading** a `DIFF` line needs the last section.

## The story page the product serves

One ticket builds this and every later interface ticket copies it: the contract
ticket, whose `## Owns` covers `.mmw/stories/`. Five things make a story page one this
judge can read, and none of them is visible from a `DIFF` line months later.

- **`.mmw/target.json`'s `stories` command brings the service up and prints its
  `origin`**, the same shape `start` and `discover` have. The judge runs it, reads that
  one line, and stops the service when it finishes. Nothing else tells it where the
  pages are.
- **The address carries the whole request.** The judge opens
  `<origin>/?page=<mount>&scene=<name>&viewport=<WxH>` and nothing else: `page` is the
  screen contract's `pages.<page>.mount`, `scene` is a name from `scenes.json`,
  `viewport` is `WIDTHxHEIGHT`. A page that needs a route, a login or a click first is
  a page this judge cannot reach.
- **`[data-story-root]` sits on the root of the design page's own block** — not on a
  wrapper around it, not on a child inside it. That element's box is what the pixel
  judge measures and what the accessibility tree is walked from, so a wrapper adds
  padding the design side does not have and a child cuts the comparison short. A run
  that cannot find it stops with `no visible [data-story-root] at <url>`.
- **The adapter puts the component in the scene from `scenes.json`.** Each scene entry
  carries `data` (`{state, vals}`, written by the handoff run's
  `export_scene_data.py`); the adapter maps those fields onto the presentational
  component's props, and the screen contract's `shows` column for each row says which
  field feeds which displayed value. The `code-review` Spec axis checks that mapping
  against the contract, field by field.
- **Nothing else runs.** No backend, no seed, no route, no controlled clock: the page
  puts the component in the scene by itself. A story page that reaches for the product's
  data layer is a page whose result depends on what happens to be in it.

`--render-only` renders the design side of a scene into a directory with no product at
all, which is what you look at while building the product side.

## Two sides

The **story page** is the product's. It renders the presentational component at
`[data-story-root]`. That element's box is what the pixel judge measures. No
backend, no seed, no route, no controlled clock: the page itself puts the
component in the scene.

The **design page** is the handoff package, served by the existing baseline server
and wrapper page. `#dc-root` is pinned to the box `[data-story-root]` measured
(`frame_box`). `retired_ids` are hidden on this side only; `volatile_values` are
masked on both. `navigate` still moves the design page's clock 200 ms of virtual
time after each load, so `support.js`'s readiness poll fires.

`--pages` names the `pages.<page>.mount` values of the non-`App · ` design pages
this ticket owns. Every scene of the contract whose page declares one of them is
compared. `--scenes` narrows that to a subset.

## Pixels

Both screenshots are shrunk by 4 (each cell the average of a 4×4 block), and each
cell is then compared with the other image's cells sampled at every sub-cell
origin: a cell counts as differing only when no sub-cell alignment explains it.
The share that still differs is held to `--max-pct`, 5% by default.

The alignment is not a loosening, it is what makes the number mean what its name
says. Shrinking by 4 does not remove offsets under 4 pixels — a line of text
moving into or out of a cell changes that cell's average by about 64, far past the
16 the comparison tolerates. With the alignment a 2 px shift is 0.0%; a shift of
a whole cell or more still fails; a block of the wrong colour still fails; a
shift laid on top of a real difference does not absolve it.

A `DIFF` line prints both numbers — `pixel 9.0% > 3.0% (unaligned 10.8%)`. Both
high is drawn wrong; only the unaligned one high is merely out of position.

The tree is the main judge and walks the whole subtree under `[data-story-root]`
and `#dc-root`, below the fold included. Pixels see only that box intersected with
the viewport.

A display value the seed must not write is declared under the contract's
`volatile_values`; both judges replace that node with one token before comparing.

## The criterion, in one shape

Nobody types this command. It is written onto the ticket as a criterion, and a
run of `verify-ticket.py` hands it to a shell months later with no model in
between. The script is named bare — `verify-ticket.py` puts this skill's
`scripts/` on that shell's `PATH` (its `--tools`) — and nothing else on the line
can go stale:

```
CHECK: story-parity.py --contract docs/specs/<effort>/screen-contract.yaml --pages <id,id>
EXPECT: STORY OK <passed>/<total>
```

`--pages` names the `pages.<page>.mount` values this ticket owns.
`<total>` is scenes × viewports. The pixel threshold is the script's default; a
ticket names `--max-pct` only when its scenes are known to need another number,
and says why beside the criterion.

`--render-only` renders the design side of the selected scenes into `--out` with
no product at all, so a worker can look at what it is building.

## Reading what it printed

Three exit codes.

- **`0`**, one line `STORY OK <passed>/<total> pixel<=<worst>%`: every scene
  matched at every viewport. The number is the largest pixel share any pair had;
  the `EXPECT` above matches it as a prefix, and a difference under the threshold
  is on record without being a failure.
- **`1`**: one `DIFF` line per failing scene and viewport.
- **`2`** with `NEGATIVE CONTROL FAILED`: the run's own control was not caught —
  the baseline server was made to serve, at the first scene's own address, that
  scene with an error banner in the bytes it sends, the story page was captured
  again, and the two compared equal, which means the product-side capture read
  the design's server; nothing this run says about parity can be trusted, and no
  story conclusion is printed at all. Exit 2 also when the `stories` command does
  not come up, when a story page is 404, or when `--pages` names a mount the
  contract does not declare, with the reason on stderr.

A failure line reads
`DIFF <scene> <viewport> <pct>% (unaligned <pct>%) — <reasons>`, and the reasons
after the dash are where the failure is named. A tree difference brings lines out
under it: `baseline`, `impl`, `only in baseline`, `only in impl`, each node with
`(in <ancestor>)` when it sits under a named one. A pixel failure ends the line
with `around: <role "name">, …`, the product's elements under the differing area,
smallest first: that is the component to open.

What to fix is what the line names: the tree lines, the elements after `around:`.
A `DIFF` that names nothing you have not already fixed is not something to chase
by changing fonts, line heights or renderer flags; run the criterion once more
after the named fixes and take the result.

`--out <dir>` keeps the screenshots, the trees and the differing-pixel pictures
for the user to look at.
