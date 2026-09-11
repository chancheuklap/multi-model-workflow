import assert from "node:assert/strict";
import test from "node:test";

import {canvasView, stillEdges} from "../../board/page/canvas.mjs";
import {defaultExpanded} from "../../board/page/board-logic.mjs";

function ticket(overrides = {}) {
  const fold = {
    children: {}, sessions: [], landed: false, returned: false, bounced: false,
    outcome: null, unreadable: [], passed: false, review: null, verdict: null, waiting: null,
    ...overrides.fold,
  };
  return {n: 1, title: "ticket", state: "open", blocked: [], children: [], events: [], ...overrides, fold};
}

const worker = (started_at = "2026-01-01T00:00:00Z") => ({kind: "worker", live: true, started_at});

test("no task is the empty canvas", () => {
  const view = canvasView(null, null, [], true);
  assert.equal(view.hasTask, false);
  assert.equal(view.noTask, true);
  assert.equal(view.layout, null);
  assert.equal(view.svg, "");
});

test("a ticket card shows its lamp, step pill and run line", () => {
  const running = ticket({
    n: 2, title: "折叠接入中继",
    fold: {sessions: [{...worker(), host: "grok", model: "grok 4.6", effort: "xhigh"}]},
  });
  const landed = ticket({n: 3, title: "中继进程骨架", fold: {landed: true, worker: {host: "claude", model: "opus 5", effort: "high"}}});
  const stopped = ticket({
    n: 4, title: "回收冲突告警",
    fold: {
      sessions: [{kind: "worker", live: true, started_at: "2026-01-01T00:00:00Z", host: "grok", model: "grok 4.6", effort: "high"}],
      children: {8: {child: 8, kind: "fault"}},
    },
    children: [{number: 8, state: "OPEN"}],
    events: [{event: "worker.started", payload: {}}, {event: "child.opened", payload: {kind: "fault", child: 8}}],
  });
  const queued = ticket({n: 5, title: "尚未派发的票"});
  const closeout = ticket({n: 6, title: "中继日志轮转", closeout: {from: 1, child: 9}, fold: {landed: true}});
  const task = {
    n: 1, kind: "wayfinder", title: "落地流水线改造", decisions: [],
    specs: [{n: 10, title: "唤醒回路", tickets: [running, landed, stopped, queued, closeout]}],
  };
  const view = canvasView(task, 2, [1, 10], true);
  const byN = Object.fromEntries(view.tickets.map(item => [item.n, item]));
  assert.equal(byN[2].lightCls, "light green");
  assert.equal(byN[2].pillCls, "pill working");
  assert.equal(byN[2].cls, "card on");
  assert.equal(byN[2].run, "grok · grok 4.6 · xhigh");
  assert.equal(byN[3].lightCls, "light ink");
  assert.equal(byN[3].step, "landed");
  assert.equal(byN[4].lightCls, "light orange");
  assert.equal(byN[4].runCls, "card-run flag");
  assert.match(byN[4].run, /已停下/);
  assert.equal(byN[5].step, "queued");
  assert.equal(byN[5].run, "尚未派发");
  assert.match(byN[6].cls, /\bcloseout\b/);
  const spec = view.containers.find(item => item.n === 10);
  assert.equal(spec.lightCls, "light orange");
  assert.equal(spec.chev, "▾");
  assert.equal(spec.toggleLabel, "收起 #10");
  const map = view.containers.find(item => item.n === 1);
  assert.equal(map.titleCls, "card-title map");
  assert.equal(map.num, "#1 · wayfinder");
});

test("a collapsed spec hides its tickets and the chevron says expand", () => {
  const task = {
    n: 1, kind: "wayfinder", title: "map", decisions: [],
    specs: [{n: 10, title: "spec", tickets: [ticket({n: 2}), ticket({n: 3})]}],
  };
  const closed = canvasView(task, null, [1], true);
  assert.equal(closed.tickets.length, 0);
  assert.equal(closed.containers.find(item => item.n === 10).chev, "▸");
  assert.equal(closed.containers.find(item => item.n === 10).toggleLabel, "展开 #10");
  const open = canvasView(task, null, [1, 10], true);
  assert.equal(open.tickets.length, 2);
  assert.equal(open.containers.find(item => item.n === 10).chev, "▾");
});

test("the default expansion opens orange and green specs and leaves the rest closed", () => {
  const active = ticket({n: 2, fold: {sessions: [worker()]}});
  const done = ticket({n: 3, fold: {landed: true}});
  const task = {
    n: 1, kind: "wayfinder", title: "map", decisions: [],
    specs: [
      {n: 10, title: "active", tickets: [active]},
      {n: 11, title: "done", tickets: [done]},
    ],
  };
  const view = canvasView(task, null, defaultExpanded(task), true);
  assert.ok(view.tickets.some(item => item.n === 2));
  assert.equal(view.tickets.some(item => item.n === 3), false);
  assert.equal(view.containers.find(item => item.n === 10).chev, "▾");
  assert.equal(view.containers.find(item => item.n === 11).chev, "▸");
});

test("reduced motion draws a still beam on a flow edge", () => {
  const blocker = ticket({n: 2, fold: {landed: true}, blocker_hold: ""});
  const running = ticket({
    n: 3, blocked: [2],
    fold: {sessions: [worker()]},
  });
  const task = {
    n: 1, kind: "wayfinder", title: "map", decisions: [],
    specs: [{n: 10, title: "spec", tickets: [blocker, running]}],
  };
  const still = canvasView(task, 3, [1, 10], true);
  assert.match(still.svg, /e-beam still/);
  assert.doesNotMatch(still.svg, /<animate/);
  const moving = canvasView(task, 3, [1, 10], false);
  assert.match(moving.svg, /<g class="e-beam">/);
  assert.match(moving.svg, /<animate/);
  const converted = stillEdges(moving.svg);
  assert.match(converted, /e-beam still/);
  assert.doesNotMatch(converted, /<animate/);
  assert.doesNotMatch(converted, /e-pulse/);
});

test("a selected issue lights the blocking curve that touches it", () => {
  const blocker = ticket({n: 2, fold: {landed: true}, blocker_hold: ""});
  const running = ticket({n: 3, blocked: [2], fold: {sessions: [worker()]}});
  const other = ticket({n: 4, fold: {sessions: [worker()]}});
  const task = {
    n: 1, kind: "wayfinder", title: "map", decisions: [],
    specs: [{n: 10, title: "spec", tickets: [blocker, running, other]}],
  };
  const atBlocked = canvasView(task, 3, [1, 10], true);
  assert.match(atBlocked.svg, /e-block flow hot/);
  const atBlocker = canvasView(task, 2, [1, 10], true);
  assert.match(atBlocker.svg, /e-block flow hot/);
  const atOther = canvasView(task, 4, [1, 10], true);
  assert.doesNotMatch(atOther.svg, /e-block flow hot/);
});

test("a decision in a blocking cycle gets a dashed card", () => {
  const first = {n: 2, title: "a", kind: "grilling", state: "open", blocked: [3]};
  const second = {n: 3, title: "b", kind: "research", state: "open", blocked: [2]};
  const task = {n: 1, kind: "wayfinder", title: "map", decisions: [first, second], specs: []};
  const view = canvasView(task, null, [1], true);
  const cards = view.decisions.filter(item => item.n === 2 || item.n === 3);
  assert.equal(cards.length, 2);
  for (const card of cards) assert.match(card.cls, /\bcycle\b/);
});

test("a spec with no map is the top container, its tickets hang straight off it", () => {
  const spec = {n: 30, title: "lone spec", tickets: [ticket({n: 31, title: "its ticket"})]};
  const task = {n: 30, kind: "spec", title: "lone spec", state: "open", decisions: [], specs: [spec]};
  const view = canvasView(task, null, [...defaultExpanded(task)], true);
  assert.deepEqual(view.containers.map(c => c.n), [30]);
  assert.equal(view.containers[0].num, "#30");
  assert.equal(view.containers[0].titleCls, "card-title");
  assert.deepEqual(view.tickets.map(t => t.n), [31]);
  assert.equal(view.labels.length, 0);
  assert.equal(view.layout.nodes.filter(node => node.id === 30).length, 1);
});
