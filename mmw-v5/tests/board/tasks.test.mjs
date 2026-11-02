import assert from "node:assert/strict";
import test from "node:test";

import {render, taskListView} from "../../board/page/tasks.mjs";
import {installDom} from "./fake-dom.mjs";

test("the selected task is marked on and the others are not", () => {
  const tasks = [
    {n: 98, specs: []},
    {n: 99, specs: []},
    {n: 100, specs: []},
  ];
  const rows = taskListView(tasks, 98).rows;
  assert.equal(rows[0].cls, "task on");
  assert.equal(rows[1].cls, "task");
});

test("the lamp and progress follow the task's tickets", () => {
  const tasks = [
    {n: 98, kind: "map", specs: [{tickets: [
      {blocker_hold: "", events: [], fold: {children: {}, sessions: []}},
      {blocker_hold: "", events: [], fold: {children: {}, sessions: []}},
      {blocker_hold: "", events: [], fold: {children: {}, sessions: []}},
      {blocker_hold: "", events: [], fold: {children: {}, sessions: []}},
      {blocker_hold: "", events: [], fold: {children: {}, sessions: []}},
      {blocker_hold: "", events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {1: {kind: "decision"}}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
    ]}]},
    {n: 99, kind: "map", specs: [{tickets: [
      {blocker_hold: "", events: [], fold: {children: {}, sessions: []}},
      {blocker_hold: "", events: [], fold: {children: {}, sessions: []}},
      {blocker_hold: "", events: [], fold: {children: {}, sessions: []}},
    ]}]},
    {n: 100, kind: "map", specs: [{tickets: [
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
      {events: [], fold: {children: {}, sessions: []}},
    ]}]},
  ];
  const view = taskListView(tasks, 98);
  assert.equal(view.count, 3);
  assert.equal(view.empty, false);
  assert.equal(view.rows[0].lampCls, "lamp orange");
  assert.equal(view.rows[0].lampWord, "needs you");
  assert.equal(view.rows[0].meta, "#98 · map");
  assert.equal(view.rows[0].count, "6/18 landed");
  assert.equal(view.rows[0].barStyle.width, "33.3%");
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

test("the task list is named Maps & specs", () => {
  const {document} = installDom();
  const host = document.createElement("div");
  const root = render(host, {tasks: []});
  assert.equal(root.getAttribute("aria-label"), "Maps & specs");
});
