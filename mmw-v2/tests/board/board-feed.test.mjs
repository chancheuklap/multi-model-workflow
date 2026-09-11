import assert from "node:assert/strict";
import test from "node:test";
import {startBoardFeed} from "../../board/page/board-feed.mjs";

test("feed reads on open and every minute only while visible", async () => {
  let visible = false;
  let reads = 0;
  let tick;
  let period;
  const feed = startBoardFeed({
    read: async () => ++reads,
    isVisible: () => visible,
    onData: () => {},
    setTimer(callback, milliseconds) { tick = callback; period = milliseconds; return 7; },
    clearTimer() {},
  });
  await Promise.resolve();
  assert.equal(reads, 1);
  assert.equal(period, 60000);
  tick();
  await Promise.resolve();
  assert.equal(reads, 1);
  visible = true;
  tick();
  await Promise.resolve();
  assert.equal(reads, 2);
  feed.stop();
});
