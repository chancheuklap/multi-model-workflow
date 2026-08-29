# ui-gate: can a downloaded Claude Design page be the machine-checked baseline for a UI ticket?

## Question and bar

**Question.** A UI ticket's baseline is the Claude Design project downloaded back into the leaf directory (`.dc.html` + `styles/` + `data/` + `support.js`). Can that baseline be rendered offline, snapshotted, and compared with the product page by two automatic checks — so a worker can run the check itself and nobody has to stop and ask a human?

**Bar.** For the sample (chameleon `App · 商品项目库` vs its React port from `issue-534`), at both viewports:

1. ARIA tree diff, after dropping runtime noise, has 0 changed lines;
2. differing pixels ≤ threshold (default 1%);
3. a deliberately wrong scene (negative control) fails both checks.

## How to run

```sh
uv run prototypes/code-landing/ui-gate/EXP/run.py            # writes .scratch/code-landing/ui-gate/evidence/round-2/
python3 -m http.server 18780 -d .scratch/code-landing/ui-gate/evidence/round-2
open http://127.0.0.1:18780/
```

First run downloads React/ReactDOM/Babel UMD (the three scripts `support.js` loads from unpkg) into `.scratch/code-landing/ui-gate/cdn/` and needs `playwright install chromium-headless-shell` once. After that it is offline.

Samples are copies, not links: `sample/baseline/` = chameleon `claude-design/` + `support.js` read back from the Claude Design project; `sample/impl/` = `issue-534/EXP/react-library/dist`; `sample/mockup/` = the original static mockup (calibration column: `issue-534` measured mockup vs React at 0.000%).

## Legend

- Evidence page columns: baseline · impl · diff. Red on the diff image = a pixel whose RGB differs by > 16/255 on any channel.
- `aria changed` = added + removed lines of `difflib.unified_diff` over the normalised ARIA snapshots; `.aria.diff` links show the lines.
- Pairs: `baseline vs impl` is the gate; `mockup vs impl` and `baseline vs mockup` calibrate the pipeline; `baseline vs wrong` is the negative control (impl at `scenario=library-empty`).

## Rounds

### round-2 — 2026-08-28

Changed since round-1: ARIA normalisation strips the accessible name from landmark roles and hoists a `main` nested inside another `main`; negative-control pair added; server sockets reuse addresses.

| pair | viewport | pixel % | aria changed | console errors |
| --- | --- | --: | --: | --: |
| baseline vs impl | 1440×900 | 0.027 | 0 | 0/0 |
| baseline vs impl | 1180×720 | 0.044 | 0 | 0/0 |
| mockup vs impl | both | 0.000 | 0 | 0/0 |
| baseline vs mockup | both | 0.027 / 0.044 | 0 | 0/0 |
| baseline vs wrong | 1440×900 | 23.439 | 28 | 0/0 |
| baseline vs wrong | 1180×720 | 28.843 | 28 | 0/0 |

Observations:

- The 0.027% is three glyph clusters (`4 个 生成任务` and two arrow icons) rendered with different sub-pixel anti-aliasing; cropping both at 4× shows the same shapes. Not a layout difference.
- `#dc-root` is fixed to 1440×900 by the `.dc.html` helmet; forcing it to the viewport with one injected style rule (`frame_css` in `capture()`) makes the 1180×720 comparison possible without touching the baseline files.
- Raw ARIA trees differ only in wrapping: the app page's `<main>` around the header component (itself a `main`), and the product page's `aria-label` on `<main>`. Both are noise for this question.
- `mockup vs impl` reproduces `issue-534`'s 0.000% exactly, so the pipeline is not introducing differences of its own.
- The wrong scene fails both checks by a wide margin (23–29% pixels, 28 tree lines), so a passing gate is not a check that cannot fail.

### round-1 — 2026-08-28

First run. Offline render worked once the three unpkg scripts were answered from a local cache by a Playwright route. Pixel 0.027% / 0.044%; ARIA changed = 9 at both viewports, all in the two wrapper lines described above. No negative control yet.

## Conclusion

**Yes.** A downloaded Claude Design page is a workable machine-checked baseline: it renders offline (three vendored CDN scripts), its ARIA tree matches the product page's after a three-rule normalisation, and pixel difference is two orders of magnitude below a 1% threshold while a wrong scene is an order of magnitude above it. The two-tier gate — `aria changed == 0` and `pixel % ≤ 1` — separates right from wrong on this sample with no human in the loop.

What the real tool should do differently from this experiment:

- Take `--baseline`, `--impl`, `--scenes` (name → baseline page + impl URL) as arguments; the sample paths here are hard-coded.
- Keep the negative control as a required self-test before trusting a run (`gates.md` "Test negative controls").
- Default threshold 1%, overridable from the spec's Testing Decisions; do not raise it to hide anti-aliasing — 0.03% is what anti-aliasing costs.
- Print `PARITY OK n/n` only on success and exit non-zero otherwise, so it can be a ticket `CHECK:` with `EXPECT: PARITY OK`.

Open: a scene other than the default is switched in Claude Design through props on the Tweaks panel, not through the URL; the experiment compared only the default scene. A tool that needs per-scene baselines must either render each scene page separately or set props before render (`support.js` `parseDataProps`).

## Reusable parts

- `run.py:normalize_aria` + `_hoist_nested_main` — the three normalisation rules; the real tool copies these verbatim.
- `run.py:route_cdn` (inside `main`) + `ensure_cdn` — offline rendering of a `.dc.html` by answering the runtime's unpkg requests from a cache.
- `run.py:capture` — the `#dc-root` targeting and the injected `frame_css` that resizes the Claude Design frame to the viewport.
- `run.py:pixel_diff` — per-channel tolerance 16, percentage, bounding box, red-mask image; unequal sizes count as 100%.
- `run.py:serve` + the `ports` map in `main` — serving each side from its own local port so both are same-origin static pages.

`run.py:write_evidence` is not among them. The comparison-grid page of
`prototype/evidence-page.md` is written for choosing between approaches, so it reports
without a verdict and puts the approaches side by side. A parity gate has already given
its verdict on stdout, and its reader is asking what to change — which the ARIA tree
carries as text. The gate prints those lines under the failing scene and writes the
screenshots to a directory; it builds no page.
