import assert from "node:assert/strict";
import test from "node:test";

import {taskListView} from "../../board/page/tasks.mjs";

function ticket(overrides = {}) {
  const fold = {
    children: {}, sessions: [], landed: false, returned: false, bounced: false,
    outcome: null, unreadable: [], passed: false, review: null, verdict: null, waiting: null,
    ...overrides.fold,
  };
  return {n: 1, state: "open", blocked: [], children: [], events: [], ...overrides, fold};
}

const worker = (started_at = "2026-01-01T00:00:00Z") => ({kind: "worker", live: true, started_at});

function task(n, kind, title, tickets) {
  return {n, kind, title, specs: [{n: n + 1, tickets}]};
}

test("the selected task is marked on and the others are not", () => {
  const rows = taskListView([
    task(98, "wayfinder", "落地流水线改造", [ticket({fold: {sessions: [worker()]}})]),
    task(77, "grilling", "交接包比对", [ticket({fold: {landed: true}})]),
  ], 98).rows;
  assert.equal(rows[0].cls, "task on");
  assert.equal(rows[0].titleCls, "task-title on");
  assert.equal(rows[1].cls, "task");
  assert.equal(rows[1].titleCls, "task-title");
});

test("the lamp and progress follow the task's tickets", () => {
  const view = taskListView([
    task(98, "wayfinder", "落地流水线改造", [
      ticket({fold: {children: {2: {child: 2, kind: "decision"}}}, children: [{number: 2, state: "OPEN"}]}),
      ticket({fold: {landed: true}}),
      ticket(),
    ]),
    task(77, "grilling", "交接包比对", [ticket({n: 8, fold: {landed: true}})]),
    task(101, "grilling", "子 issue 五种改名", [ticket(), ticket(), ticket()]),
  ], 98);
  assert.equal(view.count, 3);
  assert.equal(view.empty, false);
  assert.equal(view.rows[0].lightCls, "light orange");
  assert.equal(view.rows[0].lightWord, "需要你");
  assert.equal(view.rows[0].meta, "#98 · wayfinder");
  assert.equal(view.rows[0].count, "1/3 落地");
  assert.equal(view.rows[1].lightCls, "light ink");
  assert.equal(view.rows[1].count, "1/1 落地");
  assert.equal(view.rows[1].barStyle.width, "100%");
  assert.equal(view.rows[2].lightCls, "light hollow");
  assert.equal(view.rows[2].count, "0/3 落地");
  assert.equal(view.rows[2].barStyle.width, "0%");
});

test("no map tickets is the empty list", () => {
  const view = taskListView([], null);
  assert.equal(view.count, 0);
  assert.equal(view.empty, true);
  assert.deepEqual(view.rows, []);
});
