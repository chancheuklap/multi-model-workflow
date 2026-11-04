import {Board} from "../../board/page/board-logic.mjs";
import {taskListView} from "../../board/page/tasks.mjs";

const failures = [];
const check = (name, actual, expected) => {
  if (actual !== expected) failures.push(`${name}: ${JSON.stringify(actual)} !== ${JSON.stringify(expected)}`);
};

const ticket = (extra) => ({
  landed: false,
  state: "open",
  labels: [],
  pr: null,
  into: "night/spec-4",
  blocker_hold: "open",
  blocked: [],
  events: [],
  fold: {landed: false, held: false, sessions: [], children: {}},
  ...extra,
});

const draft = ticket({
  labels: ["needs-triage", "junior-worker"],
  pr: {state: "open", draft: true, body: "fix the door"},
});
check("draft phase", Board.phase(draft), "working");
check("draft lamp", Board.lamp(draft), "orange");
check("draft run", Board.runLine(draft).text, "");
check("draft why", Board.why(draft)[0].text, "fix the door");
check("draft not running", Board.running(draft), false);

const human = ticket({labels: ["ready-for-human"]});
check("human phase", Board.phase(human), "queued");
check("human lamp", Board.lamp(human), "orange");
check("human run", Board.runLine(human).text, "not dispatched");
check("human why", Board.why(human)[0].text, "ready-for-human");

const bare = ticket({labels: ["needs-triage"]});
check("bare why", Board.why(bare)[0].text, "needs-triage");

const landed = ticket({
  landed: true,
  into: "night/spec-4",
  blocker_hold: "",
  fold: {landed: true, held: false, sessions: [], children: {}},
  pr: {state: "closed", draft: false, merged_at: "2026-11-04T00:00:00Z", body: "done"},
});
check("landed phase", Board.phase(landed), "landed");
check("landed lamp", Board.lamp(landed), "ink");
check("landed run", Board.runLine(landed).text, "merged into night/spec-4");
check("landed done", Board.done(landed), true);
check("elapsed", Board.elapsed(landed), "");

const landedAsk = ticket({
  landed: true,
  labels: ["needs-triage"],
  fold: {landed: true, held: false, sessions: [], children: {}},
  pr: {state: "closed", draft: false, merged_at: "2026-11-04T00:00:00Z", body: "look again"},
});
check("landed ask phase", Board.phase(landedAsk), "landed");
check("landed ask lamp", Board.lamp(landedAsk), "orange");

const closed = ticket({state: "closed"});
check("closed phase", Board.phase(closed), "");
check("closed lamp", Board.lamp(closed), "hollow");
check("closed run", Board.runLine(closed).text, "closed unpassed");
check("closed not done", Board.done(closed), false);

const ready = ticket({pr: {state: "open", draft: false, body: "report"}});
check("ready phase", Board.phase(ready), "verify");
check("ready lamp", Board.lamp(ready), "hollow");
check("ready run", Board.runLine(ready).text, "");

const idle = ticket({});
check("idle phase", Board.phase(idle), "queued");
check("idle lamp", Board.lamp(idle), "hollow");
check("idle run", Board.runLine(idle).text, "not dispatched");

const rows = taskListView([{
  n: 4, kind: "spec", title: "Spec", deliveryLine: "delivery PR #81",
  decisions: [],
  specs: [{tickets: [landed, idle]}],
}], null);
check("row count", rows.rows[0].count, "1/2 landed · delivery PR #81");
check("row meta", rows.rows[0].meta, "#4 · spec");

const map = taskListView([{
  n: 1, kind: "migration", title: "Map", decisions: [], specs: [{tickets: []}],
}], null);
check("map count", map.rows[0].count, "0/0 landed");
check("map meta", map.rows[0].meta, "#1 · migration");

const layout = Board.layout({
  n: 9, kind: "ticket", title: "Solo", state: "open", decisions: [],
  specs: [{n: 9, tickets: [{n: 9, title: "Solo", blocked: []}]}],
}, new Set());
check("solo nodes", layout.nodes.length, 1);
check("solo type", layout.nodes[0].type, "ticket");
check("solo id", layout.nodes[0].id, 9);

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("phase ok");
