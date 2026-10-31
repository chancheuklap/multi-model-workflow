import assert from "node:assert/strict";
import test from "node:test";
import {startBoardFeed} from "../../board/page/board-feed.mjs";

test("feed schedules from read_at, suspends hidden timers and reads on return", async () => {
  let visible = true;
  let reads = 0;
  let tick, visibility, period;
  const feed = startBoardFeed({
    read: async () => { reads++; return {read_at: '2026-10-31T00:00:00Z'}; },
    isVisible: () => visible,
    onVisibility(callback) { visibility = callback; return () => {}; },
    now: () => Date.parse('2026-10-31T00:00:40Z'),
    setTimer(callback, milliseconds) { tick = callback; period = milliseconds; return 7; },
    clearTimer() {},
  });
  await Promise.resolve();
  assert.equal(reads, 1);
  assert.equal(period, 20000);
  visible = false;
  visibility();
  tick();
  await Promise.resolve();
  assert.equal(reads, 1);
  visible = true;
  visibility();
  await Promise.resolve();
  assert.equal(reads, 2);
  feed.stop();
});

test("manual refresh waits behind a GET and does not overlap it", async () => {
  const releases = [];
  const calls = [];
  const feed = startBoardFeed({
    read: force => { calls.push(force); return new Promise(resolve => releases.push(resolve)); },
    isVisible: () => true,
    setTimer: () => 1,
    clearTimer() {},
  });
  const fresh = feed.refresh?.();
  releases.shift()({read_at: new Date().toISOString(), tasks: ['cached']});
  await Promise.resolve();
  await Promise.resolve();
  assert.deepEqual(calls, [false, true]);
  releases.shift()({read_at: new Date().toISOString(), tasks: ['fresh']});
  assert.deepEqual((await fresh).tasks, ['fresh']);
  feed.stop();
});
