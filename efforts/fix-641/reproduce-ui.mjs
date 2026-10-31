import assert from "node:assert/strict";
import {readFile, writeFile} from "node:fs/promises";
import {createRequire} from "node:module";
import path from "node:path";

const require = createRequire(path.resolve("tests/e2e/task-board/package.json"));
const {chromium} = require("playwright-core");
const [url, fixtureDirectory, output, scenario] = process.argv.slice(2);
const browser = await chromium.launch({headless: true});
const page = await browser.newPage({viewport: {width: 1440, height: 900}});
page.setDefaultTimeout(10000);
const consoleErrors = [];
page.on("pageerror", error => consoleErrors.push(error.message));
try {
  await page.goto(url);
  await page.getByRole("button", {name: "#11 source ticket", exact: true}).waitFor();
  if (scenario === "landed-edge") {
    const fixturePath = path.join(fixtureDirectory, "scenario.json");
    const data = JSON.parse(await readFile(fixturePath, "utf8"));
    data.tree_active = 1;
    data.comment_active["11"] = 1;
    await writeFile(fixturePath, JSON.stringify(data));
    const response = page.waitForResponse(response =>
      response.url().endsWith("/api/board/refresh") && response.status() === 200);
    await page.getByRole("button", {name: "立刻重读 GitHub", exact: true}).click();
    await response;
    await page.locator('[data-ui="画布.ticket-card"]').filter({hasText: "#11"}).locator(".pill")
      .filter({hasText: "landed"}).waitFor();
    await page.getByRole("button", {name: "#11 source ticket", exact: true}).click();
    const cardPhase = await page.locator('[data-ui="详情.status.phase"]').textContent();
    const blockedEdges = await page.locator(".e-block.blocked").count();
    assert.equal(cardPhase, "landed", "the landing must be read to reach this defect");
    const result = {scenario, passed: blockedEdges === 0, cardPhase, blockedEdges, consoleErrors};
    await page.screenshot({path: path.join(output, scenario + ".png"), fullPage: true});
    await writeFile(path.join(output, scenario + ".json"), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
    process.exitCode = result.passed ? 0 : 1;
  } else {
    await page.getByRole("button", {name: "#11 source ticket", exact: true}).click();
    const currentPhase = await page.locator('[data-ui="详情.status.phase"]').textContent();
    const phases = await page.locator('[data-ui="详情.event-block.phase"]').allTextContents();
    assert.equal(currentPhase, "working", "review must have ended and worker resumed");
    assert.ok(phases.length, "the real detail timeline must be visible");
    const result = {scenario, passed: phases.at(-1) === currentPhase,
      currentPhase, latestEventBlock: phases.at(-1), consoleErrors};
    await page.screenshot({path: path.join(output, scenario + ".png"), fullPage: true});
    await writeFile(path.join(output, scenario + ".json"), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
    process.exitCode = result.passed ? 0 : 1;
  }
  assert.deepEqual(consoleErrors, [], "page errors must not masquerade as a state bug");
} finally {
  await browser.close();
}
