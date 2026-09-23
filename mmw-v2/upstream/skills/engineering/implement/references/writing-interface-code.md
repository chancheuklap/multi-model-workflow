# Writing interface code

Read this file when the ticket's **Read first** lists a screen contract. An interface ticket has two baselines, each binding its own domain: the design package binds look and verbatim copy; the screen contract binds what each control calls, which field feeds each shown value, what state follows, what failure shows, and timing. A statement of the design package about the second domain is a reference the contract has already adopted or overridden, so the two never compete. A `contract` child for a screen-contract row that does not fit also names the alignment ticket, since that is where the row is rewritten.

## Resolve `<ui-acceptance scripts>` once

`<ui-acceptance scripts>` in every command below is the `scripts/` directory of the `ui-acceptance` skill. Resolve it from that skill's own `SKILL.md`. The path differs by machine and by host.

## Before the first line

Read the screen-contract rows this ticket owns.

Then take the design side's values (the design package's pages as the story judge renders them). `--contract` is the screen contract **Read first** names; `--pages` is the `pages` mounts this ticket owns; `--out` is a directory `mktemp` makes:

```
uv run <ui-acceptance scripts>/story-parity.py --contract … --pages … --render-only --out <mktemp directory>
```

`--render-only` needs no product. It writes screenshots under `--out/media` and, for each scene and viewport, the facts of every `data-ui` id (text, size, position, style) to `--out/values/<mount>/<scene>-<WxH>.json`. Write the product to those values. What the JSON holds is the ui-acceptance skill's `references/story-parity.md` under **The two sides**.

**Done when** every owned scene has a screenshot and a values file in that directory.

## Write the product

Build the component and its story page as the ui-acceptance skill's `references/story-parity.md` **The story page the product serves** says: where `[data-story-root]` and the `data-ui` ids go, and what the story adapter takes.

In the same pass write that page's story adapter and a four-column boundary test for each owned row. The four-column boundary test asserts `calls`, `shows`, `next` and `on_failure` of one row.

**The story criterion is the exception to red before green.** The `tdd` skill writes one failing test and then only the code that passes it, and calls tests written ahead of the code **Horizontal slicing**, because they verify imagined behaviour. Element parity compares two rendered sides, so the story criterion has nothing to compare until the component renders, and its expected values are not imagined: they are the design side's, taken in the step above. So the component comes first here, written to those values. Each owned row's four-column boundary test is still its own red-green slice inside this pass, at the seam this ticket's **Seam** names: write it against the row, watch it fail, wire that row, watch it pass.

When the design system was built from code that already runs, the design page already uses the product's class names: copy them.

**Done when** the component, its story adapter and its four-column boundary tests exist.

## Fix in place

Run the ticket's story criterion. A `DIFF` line names one `data-ui` id and one property, with its design and product values. Before changing the product to the design value, check that the design value itself is plausible: against the same-role elements beside it and the design system's scale. A value that is clearly wrong is not copied; it goes to **When the design side is the defect** below. Otherwise that id and property are the complete repair. Fix them, run again. The loop stays on this machine.

The pixel difference image is evidence, not a verdict: change the named id and property. Fonts, line heights and renderer flags stay as they are. How many rounds a criterion gets, and the `ABANDON:` line when none is in sight, are closing step 1's.

When the review's Spec axis reports a `Missing` that names one of this ticket's screen-contract rows, the closing comment names that row id too: beside the commit that fixed it, or under `Sub-issues opened:`.

**Done when** the story criterion prints no `DIFF` line, or closing step 1 has recorded that it is abandoned.

## When the design side is the defect

A design value that is clearly wrong (a metric number and the label beside it both 13px), a fix that must break another place on the design page, a design page missing a control this ticket must build, or a flow that does not match the screen contract, is a `contract` child. The criterion it blocks stays red: closing step 1 records it with the `ABANDON:` line, `stuck` pointing at that child, and the ticket ends as `HANDOFF REQUIRED`. Keep working the rest of this ticket.

```
<engine> <n> --sub-issue contract <file>
```

The file's first line is the child issue's title: the Claude Design page and the value that does not hold. The next line is:

由 design-pages 技能的 references/pull.md 处理：在能调用 Claude Design MCP 工具的会话里，在 Claude Design 里改，再 pull

Leave the design package as it is: **pull** of the design-pages skill is what writes it.

**Done when** the child is open and the rest of this ticket is still being worked.

## One code path

The story page's data comes only from the story adapter reading scene data. No request path of the product chooses its projection by whether a data source is present, by a query parameter, or by a build switch.
