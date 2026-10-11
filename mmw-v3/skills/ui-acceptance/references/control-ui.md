# Control UI

Use local browser automation to verify UI behavior with evidence. First reuse the repo's own Playwright, browser, or Electron harness if it exists. The product is brought up by `start` inside the lease, and the address is what `discover` prints.

## What It Is Used For

- Reproducing UI bugs that depend on real browser focus, keyboard input, scrolling, resizing, or rendering.
- Verifying visual or accessibility changes with screenshots and snapshots.
- Checking local web, IDE, or Electron behavior before shipping.
- Capturing console logs, network logs, CPU profiles, traces, or heap snapshots.
- Creating before/after evidence.

## Setup Pattern

1. Start the product with `start` inside the lease. A journey does this through `journey.py`. A probe that is not a journey runs that same `start` through the lease command in **Five rules while the product is running**, and passes `--product <product>`; then it runs `doctor` the same way. After you change the product's code, run `stop` and `start` again before you look: `start` leaves a product it already started as it is, so the old code would still be running.
2. Discover existing local harnesses: Playwright tests, Cypress specs, Storybook, browser scripts, Electron launch scripts, or snapshot tools.
3. For a web app, connect to the address `discover` printed. The key `origin` arrives uppercased as `ORIGIN`.
4. For Electron or another Chromium app, `start` passes `--remote-debugging-port` from this product's port segment and `--user-data-dir` under `MMW_DATA_DIR`. `discover` prints `cdp`, which arrives as `CDP`. Connect with `connectOverCDP`.
5. Select the correct page by stable app markers, not by tab order alone.
6. Prefer accessibility roles, labels, and stable `data-*` selectors over coordinates.

Write screenshots, traces and logs under `.scratch/` in the worktree. A journey writes them in `MMW_EVIDENCE_DIR`.

## Generic Web Harness

Use the repo's installed browser tooling when possible. If the repo already has Playwright, a minimal one-off probe looks like:

```javascript
import { chromium } from "playwright";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto(process.env.ORIGIN);
await page.getByRole("button", { name: /submit/i }).click();
await page.screenshot({ path: ".scratch/ui-harness-after.png", fullPage: true });
await browser.close();
```

`browser.close()` here closes the browser this probe launched. The product stays up until `stop`.

Do not add Playwright as a project dependency just for this probe unless the user asks. Prefer existing dev dependencies or external browser tools already available in the environment.

## Generic CDP Harness

For Electron or a Chromium app whose `start` passed `--remote-debugging-port` from this product's port segment, connect over CDP to the `CDP` address.

```javascript
import { chromium } from "playwright";

const browser = await chromium.connectOverCDP(process.env.CDP);
const pages = browser.contexts().flatMap((context) => context.pages());
let page;
for (const candidate of pages) {
  if (await candidate.locator("<app-root-selector>").count()) {
    page = candidate;
    break;
  }
}

if (!page) {
  console.log(await Promise.all(pages.map(async (p) => ({
    title: await p.title(),
    url: p.url(),
  }))));
  throw new Error("No matching app page found");
}

await page.screenshot({ path: ".scratch/ui-harness-cdp.png", fullPage: true });
await browser.close();
```

`browser.close()` disconnects this client and leaves the application running. `stop` ends the application.

Replace `<app-root-selector>` with a stable marker from the current repo, such as a root app node, landmark, or product-specific `data-*` attribute.

## Interaction Loop

1. Capture a page snapshot or screenshot before acting.
2. Choose a target from the latest page structure.
3. Perform exactly one structural action: click, type, keypress, drag, scroll, navigate, or resize.
4. Capture a fresh snapshot/screenshot.
5. Verify the expected state change.
6. Save artifacts for before/after comparisons when the user asked for proof.

## CDP Capabilities

Use raw CDP only when higher-level browser APIs are insufficient:

- Performance: CPU profiles, traces, paint flashing, FPS meter, layout shift inspection.
- Memory: heap snapshots and forced GC for leak investigations.
- Network: request blocking, throttling, cache disablement, request/response logs.
- Rendering: viewport changes, color scheme emulation, reduced motion, accessibility checks.
- Debugging: console streaming, exception capture, DOM snapshots.

## Page Selection

When multiple app windows/tabs share a debug port:

- Prefer a positive marker for the surface under test, such as an app root selector.
- Use a negative marker to avoid the wrong surface when necessary.
- If no page matches, list available page titles and URLs instead of guessing.

## Guardrails

- Do not rely on stale element references after navigation or structural changes.
- Avoid coordinate clicks unless a fresh screenshot was captured immediately before the click.
- Keep test data local and disposable.
- Do not store screenshots or heap snapshots from privacy-sensitive workspaces unless the user explicitly agrees.
- Do not hard-code selectors or script paths from another repository. The address is the one `discover` printed, `ORIGIN` or `CDP`. Discover the current repo's local app markers.
- End the product with its `stop`. That ends what this run's `start` started. Disconnect the browser client when the probe is finished.
