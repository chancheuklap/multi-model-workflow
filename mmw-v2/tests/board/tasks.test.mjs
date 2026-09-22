import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

import {taskListView} from "../../board/page/tasks.mjs";

function exampleScene(name) {
  const context = {window: {}};
  const source = fs.readFileSync(
    new URL(`../../../prototypes/task-board/example-data/board-${name}.js`, import.meta.url),
    "utf8",
  );
  vm.runInNewContext(source, context);
  return context.window.BOARD_SCENES[name];
}

test("the selected task is marked on and the others are not", () => {
  const scene = exampleScene("morning");
  const rows = taskListView(scene.payload.tasks, scene.select.task).rows;
  assert.equal(rows[0].cls, "task on");
  assert.equal(rows[1].cls, "task");
});

test("the lamp and progress follow the task's tickets", () => {
  const scene = exampleScene("morning");
  const view = taskListView(scene.payload.tasks, scene.select.task);
  assert.equal(view.count, 3);
  assert.equal(view.empty, false);
  assert.equal(view.rows[0].lampCls, "lamp orange");
  assert.equal(view.rows[0].lampWord, "needs you");
  assert.equal(view.rows[0].meta, "#98 · map");
  assert.equal(view.rows[0].count, "6/18 landed");
  assert.equal(view.rows[1].lampCls, "lamp ink");
  assert.equal(view.rows[1].count, "3/3 landed");
  assert.equal(view.rows[1].barStyle.width, "100%");
  assert.equal(view.rows[2].lampCls, "lamp hollow");
  assert.equal(view.rows[2].count, "0/3 landed");
  assert.equal(view.rows[2].barStyle.width, "0%");
});

test("no map tickets is the empty list", () => {
  const view = taskListView([], null);
  assert.equal(view.count, 0);
  assert.equal(view.empty, true);
  assert.deepEqual(view.rows, []);
});
