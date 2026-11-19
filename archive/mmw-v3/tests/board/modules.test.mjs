import assert from "node:assert/strict";
import test from "node:test";

import {api, request} from "../../board/page/api.mjs";
import {mountPage} from "../../board/page/app.mjs";
import {render as topbar} from "../../board/page/topbar.mjs";
import {render as tasks} from "../../board/page/tasks.mjs";
import {render as canvas} from "../../board/page/canvas.mjs";
import {render as detail} from "../../board/page/detail.mjs";
import {render as settings} from "../../board/page/settings.mjs";

test("page modules load directly in Node without a build", () => {
  assert.equal(typeof request, "function");
  assert.equal(typeof api.settings, "function");
  assert.equal(typeof mountPage, "function");
  for (const render of [topbar, tasks, canvas, detail, settings]) {
    assert.equal(typeof render, "function");
  }
});
