# Interface parity

Whether an interface matches the design it was built from is `scripts/visual-parity.py`, next to this skill's `SKILL.md`. It reads the screen contract, puts the product into each scene through the repository's own reach script, opens the scene where the contract says the product shows it, and compares the block of the product that design page *is* against the design page rendered offline from the handoff package — by accessibility tree, by class set, and by pixels, at every viewport the contract names.

Two agents come here. The one **writing** the criterion needs the shape below. The one **reading** a `DIFF` line needs the last section.

## Two levels

The `claude-design-blocks` skill prefixes every page `App · ` or `Component · `, and this script rests on that convention, not on anything the product does. An `App · ` scene compares the whole surface — which components are on it, and what box the layout gives each. A `Component · ` scene compares the block the product gives that one component. Neither replaces the other. A handoff package that holds only whole-page designs makes every scene whole-surface, and the model degrades to that without breaking.

## The mount

Each design page declares, in the contract's `pages`, a **`mount`**: the value of the `data-screen` attribute on the one product element that page is. Its subtree is what the tree reads; its box is what the pixel judge measures. It is not a test hook: it is where "this design page is that block of the product" is written down, and the product carries it as a short stable id. A scene that is a top-level dialog outside that subtree overrides `mount` to the page root's id, or the dialog is invisible to the run.

## Measure the box, declare no size

The mount element is never pinned. The viewport is (the driver pushes a device-metrics override for every entry of the contract's `viewports`); the product lays the element out as it will; the element's box after that — `getBoundingClientRect()` — is what the design's `#dc-root` is pinned to for that scene. The two come out the same size by construction and no number appears in the contract. This rests on the porting convention that a ported component fills its container (`#dc-root > * { height:100% }`): the design renders at whatever box the product gives that component — a component under a 46 px title bar renders at 1440×854, a shell header at 1440×46 with its standalone padding collapsed. On a responsive target the measured width may land in a media query other than the design's default; that is correct, not a defect — the design is rendered at the width the product actually gives — and is not something to "fix".

`viewports` come from the handoff package README (the design size and the declared minimum). A viewport on a breakpoint of the package's stylesheets compares two reflows and verifies nothing; the contract lint refuses it.

## Three judges, two ranges — a written decision

The **accessibility tree** is the main judge: the sequence of named nodes in reading order — a button and its name, a heading and its text, a line of copy, a checkbox and its state — each with its nearest named ancestor, over the **whole subtree** under the mount, below the fold included. Unnamed wrappers and landmark names are not in it, so a product page that nests things in `list` and `article` where the component page had `generic` is the same tree; a button that moved out of its dialog is not. A node missing, added, renamed, given another role or another named ancestor fails the scene, and the `DIFF` line prints which.

The **class set** of the subtree is the second judge. The stylesheets are copied from the handoff package byte for byte, so with the tree equal a wrong colour or gap on the right element can only be the wrong class name — which the tree cannot see and a pixel share cannot name. A class one side lacks fails the scene and names the element wearing it.

A display value the seed must not write — a wallet balance belonging to an external account, not a difference to hide — is declared on the contract as `volatile_values`: each entry is a `page`, a `trigger` (role and accessible name, the same shape as `retired_ids`), and one line of `reason`. Before either judge compares, both sides replace that node's text with one token: the tree name becomes `<volatile>`, and the pixel judge paints the node's box the same solid colour. Different numbers then compare equal. The lint prints every entry on every run and warns when the trigger is not in that page's target tree.

**Pixels** are the third, for a block that did not render or came out the wrong size. They see only the mount element's box **intersected with the viewport**, the baseline pinned to that same intersection; below the fold is the tree's alone. Both screenshots are shrunk by 4 (each cell the average of a 4×4 block) before they are compared, which removes glyph rendering and offsets under 4 pixels; the share of cells that still differ is held to `--max-pct`, 3% by default. What 3% lets through is for the class set and for the user looking at `--out`, not for another round of fixing.

That the three judges have different ranges is a decision written here, not an accident: the tree is the main judge, so what is below the fold is judged by the main judge. The other road — scrolling both sides in step and comparing screen by screen — would pin the baseline to the scroll height, rendering the design at a height no App page ever drew.

## The clock

Every page runs under a paused fake clock the driver moves forward in 200 ms of virtual time after each navigation and each `open` step, stepping further only until the next `open` control, and after the chain the mount element, appears. The readiness poll of `support.js` (50 ms) fires, a focus effect on `requestAnimationFrame` fires, and none of the package's own timers — an 1800 ms auto-advance, a 2600 ms auto-recover, a 2400 ms toast — ever does. Animations are off through reduced motion on both sides. Nothing about "wait for it to settle" is in the contract.

## Reaching a scene

The product is brought up by the run, not by the worker: `.mmw/target.json`'s `start` is run when `ready` finds nothing answering ([targets/README.md](targets/README.md)). The contract's `scenes` say how: `reach`, the mechanisms the repository's reach script runs before the scene (idempotent, once per scene); the page's `route`, filled from the `KEY=VALUE` lines that script prints; then `open`, the row ids performed on the page, ending on a row whose `next` is the scene. Writes in `open` are fine — the next scene's `reach` puts the state back. A renderer that poses itself from fixtures to satisfy any of this is the failure this pipeline exists to catch. A scene whose `reach` names a mechanism nobody builds fails on the first night; the contract lint refuses it before then.

What kind of product this is, and how it is attached, readied, addressed, released, seeded and read, is the contract's `target.kind` and the reference file under [targets/](targets/README.md). Addresses are never on the criterion: they come from the repository's `.mmw/target.json`.

## The criterion, in one shape

Nobody types this command. It is written onto the ticket as a criterion, and a run of `verify-ticket.py` hands it to a shell months later with no model in between. So it carries a path written out in full, and nothing else that could go stale:

```
CHECK: uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py --contract docs/specs/<effort>/screen-contract.yaml --mount <id,id>
EXPECT: PARITY OK <passed>/<total>
```

`--mount` names the `data-screen` values this ticket owns; every scene of the contract whose page (or whose own override) declares one of them is compared. `<total>` is scenes × viewports. Scenes belong to tickets by mount; when one page's scenes are split between two tickets, each adds `--scenes <name,name>`, a subset of what its mounts derive — the one way to split, and `verify-ticket --lint` checks that across the batch every scene of the contract is covered exactly once. When mounts collide (a target without component pages, where every scene is whole-surface), scenes belong by `route` instead.

The pixel threshold is not on the line: it is the script's default, so that loosening or tightening it is one edit to the script and not one to every ticket already published. A ticket names `--max-pct` only when its scenes are known to need another number, and says why beside the criterion.

**That path stays literal, and stays exactly this one.** Everywhere else an agent reaches a script in this skill by resolving it from the skill's own location, because an agent knows where its host put the skill. A shell does not. `~/.agents/skills` is the install location `mmw-v2/install.sh` creates unconditionally on every machine, for every host, which makes it the one path a ticket can name and still run a year later on another checkout. Writing the resolved absolute path of your own machine into a ticket breaks it for every other machine; writing a placeholder breaks it immediately.

On an electron target the run borrows the application's own window, because Electron exposes one page over its debugging port and refuses to open another. While a run is going the window switches between the viewports being compared; when it ends — however it ends — the window is given back at its own size, with its own clock, on its own page. A window that stays small after a run is a bug in the driver, not a diagnosis to make.

Three more modes. `--addressing` is the contract ticket's criterion: for every scene under `--mount` (`--mount all` for every mount the contract declares), run its `reach`, fill its `route`, navigate, walk its `open` chain, and assert the mount element is there — the whole addressing model proved against an empty surface, printing `ADDRESSING OK <n>/<n>`, or one `UNREACHABLE <scene> — <why>` per scene that failed and then `ADDRESSING <reached>/<n> — <k> unreachable`; no baseline, no comparison. A scene unreachable only at an `open` step names the row whose control is missing: on an empty surface that is the row's own ticket still to land, and the tally is what the contract ticket reports. The other two are not for a criterion: `--render-only` renders the design side of the selected scenes into `--out` with no product at all, so a worker can look at what it is building; `--shows-perturbation` reseeds every scene with values other than `data/fixtures.js` and requires every scene whose rows declare `shows` to read differently — a value that stays the same is hard coded or fed from the wrong field.

## Reading what it printed

Three exit codes.

- **`0`**, one line `PARITY OK <passed>/<total> pixel<=<worst>%`: every scene matched at every viewport. The number is the largest pixel share any pair had; the `EXPECT` above matches it as a prefix, and a difference under the threshold is on record without being a failure.
- **`1`**: one `DIFF` line per failing scene and viewport.
- **`2`** with `NEGATIVE CONTROL FAILED`: the run's own control was not caught — the baseline server was made to serve, at the first scene's own address, that scene with an error banner in the bytes it sends, the product was captured again, and the two compared equal, which means the product-side capture read the design's server; nothing this run says about parity can be trusted, and no parity conclusion is printed at all. Exit 2 also when the product is not ready or a scene cannot be reached, with the reason on stderr.

A failure line reads `DIFF <scene> <viewport> <pct>% box=… — <reasons>`, and the reasons after the dash are where the failure is named. A tree difference brings lines out under it: `baseline`, `impl`, `only in baseline`, `only in impl`, each node with `(in <ancestor>)` when it sits under a named one. A class difference brings `class only in baseline <name> (on <element>)` and its mirror. A pixel failure ends the line with `around: <role "name">, …`, the product's elements under the differing area, smallest first: that is the component to open. A size difference or a console error prints the `DIFF` line alone.

What to fix is what the line names: the tree lines, the class names, the elements after `around:`, the console error. A `DIFF` that names nothing you have not already fixed is not something to chase by changing fonts, line heights or renderer flags; run the criterion once more after the named fixes and take the result.

`--out <dir>` keeps the screenshots, the trees and the differing-pixel pictures for the user to look at.
