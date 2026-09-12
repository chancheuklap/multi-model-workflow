import assert from "node:assert/strict";
import test from "node:test";
import {Board, defaultExpanded} from "../../board/page/board-logic.mjs";

function ticket(overrides = {}) {
  const fold = {
    children: {}, sessions: [], landed: false, returned: false, bounced: false,
    outcome: null, unreadable: [], passed: false, review: null, verdict: null, waiting: null,
    ...overrides.fold,
  };
  return {n: 1, state: "open", blocked: [], children: [], events: [], ...overrides, fold};
}

const worker = (started_at = "2026-01-01T00:00:00Z") => ({kind: "worker", live: true, started_at});

test("lamp is orange for an open decision, fault or contract child", () => {
  for (const kind of ["decision", "fault", "contract"]) {
    const value = ticket({fold: {children: {2: {child: 2, kind}}}, children: [{number: 2, state: "OPEN"}]});
    assert.equal(Board.light(value), "orange");
  }
  for (const kind of ["finding", "deferred"]) {
    const value = ticket({fold: {children: {2: {child: 2, kind}}}, children: [{number: 2, state: "OPEN"}]});
    assert.equal(Board.light(value), "hollow");
  }
  const closed = ticket({fold: {children: {2: {child: 2, kind: "decision"}}}, children: [{number: 2, state: "CLOSED"}]});
  assert.equal(Board.light(closed), "hollow");
});

test("lamp is orange for a returned or bounced ticket until a worker starts again", () => {
  const earlier = {...worker(), live: false, ended_by: "ticket.returned"};
  const returned = ticket({fold: {returned: true, outcome: {at: "2026-01-01T01:00:00Z"}, sessions: [earlier]}});
  assert.equal(Board.light(returned), "orange");
  returned.fold.sessions.push(worker("2026-01-01T02:00:00Z"));
  assert.equal(Board.light(returned), "green");

  const bounced = ticket({fold: {bounced: true, sessions: [{...earlier, ended_by: "ticket.bounced"}]},
    events: [{event: "ticket.bounced", at: "2026-01-01T01:00:00Z",
      payload: {reason: "checks", into: "main", commit: "abcdef012345",
        commands: [{command: "bash checks.sh", output: ["first line", "last line"]}]}}]});
  assert.equal(Board.light(bounced), "orange");
  assert.match(Board.why(bounced)[0].text, /bash checks\.sh：first line \/ last line/);
  bounced.fold.sessions.push(worker("2026-01-01T02:00:00Z"));
  assert.equal(Board.light(bounced), "green");
});

test("lamp is green while held, ink when landed, hollow otherwise", () => {
  assert.equal(Board.light(ticket({fold: {sessions: [worker()]}})), "green");
  assert.equal(Board.light(ticket({fold: {claim_hold: true, held: true}})), "green");
  assert.equal(Board.runLine(ticket({fold: {claim_hold: true, held: true}})).text, "已认领 · 待派发");
  assert.equal(Board.light(ticket({fold: {landed: true}})), "ink");
  assert.equal(Board.light(ticket()), "hollow");
});

test("a fault opened after the newest start or resume stops the ticket", () => {
  const blocker = ticket({state: "closed", blocker_hold: "", fold: {passed: false}});
  const stopped = ticket({
    fold: {sessions: [worker()], children: {8: {child: 8, kind: "fault"}}},
    children: [{number: 8, state: "OPEN"}],
    events: [
      {event: "worker.started", payload: {}},
      {event: "child.opened", payload: {kind: "fault", child: 8}},
    ],
  });
  assert.equal(Board.running(stopped), false);
  assert.equal(Board.light(stopped), "orange");
  assert.equal(Board.edgeState(blocker, stopped), "done");

  stopped.events.push({event: "worker.resumed", payload: {}});
  assert.equal(Board.running(stopped), true);
  assert.equal(Board.edgeState(blocker, stopped), "flow");
});

test("step follows who still holds the ticket", () => {
  assert.equal(Board.step(ticket()), "queued");
  assert.equal(Board.step(ticket({fold: {sessions: [worker()]}})), "working");
  assert.equal(Board.step(ticket({fold: {sessions: [worker()], waiting: {at: "2026-01-01T00:00:00Z"}}})), "waiting");
  assert.equal(Board.step(ticket({fold: {sessions: [worker(), {kind: "reviewer", live: true}]}})), "review");
  assert.equal(Board.step(ticket({fold: {sessions: [worker(), {kind: "verifier", live: true}]}})), "verify");
  assert.equal(Board.step(ticket({fold: {sessions: [worker()], verdict: {event: "verifier.passed"}}})), "verify");
  assert.equal(Board.step(ticket({fold: {landed: true}})), "landed");
});

test("a stopped ticket keeps the step it stopped at", () => {
  const returned = ticket({fold: {returned: true, outcome: {at: "2026-01-01T01:00:00Z"}}});
  assert.equal(Board.step(returned), "working");
  const fault = ticket({
    fold: {sessions: [{kind: "reviewer", live: true}], children: {8: {child: 8, kind: "fault"}}},
    children: [{number: 8, state: "OPEN"}],
    events: [{event: "worker.started", payload: {}}, {event: "child.opened", payload: {kind: "fault", child: 8}}],
  });
  assert.equal(Board.step(fault), "review");
  const bounced = ticket({fold: {bounced: true}, events: [{event: "ticket.bounced", at: "2026-01-01T01:00:00Z"}]});
  assert.equal(Board.step(bounced), "verify");
});

test("edge is blocked, flow or done", () => {
  const held = ticket({state: "open", blocker_hold: "open"});
  const released = ticket({state: "closed", blocker_hold: ""});
  assert.equal(Board.edgeState(held, ticket()), "blocked");
  assert.equal(Board.edgeState(released, ticket({fold: {sessions: [worker()]}})), "flow");
  assert.equal(Board.edgeState(released, ticket()), "done");
  assert.equal(Board.edgeState({state: "open"}, ticket(), "decision"), "blocked");
  assert.equal(Board.edgeState({state: "closed"}, ticket(), "decision"), "done");
});

test("a blocker closed without a pass lets go and a passed unlanded one holds", () => {
  assert.equal(Board.released(ticket({state: "closed", blocker_hold: ""})), true);
  assert.equal(Board.released(ticket({state: "closed", blocker_hold: "passed, not landed"})), false);
});

test("layers follow the longest chain and an implied edge is not drawn", () => {
  const graph = Board.graph([{n: 1, blocked: []}, {n: 2, blocked: [1]}, {n: 3, blocked: [1, 2]}]);
  assert.deepEqual([...graph.layer], [[1, 0], [2, 1], [3, 2]]);
  assert.deepEqual(graph.edges.map(edge => [edge.from, edge.to]), [[1, 2], [2, 3]]);
});

test("a blocking cycle goes to the last column with its label", () => {
  const items = [
    ticket({n: 1, blocked: [], blocker_hold: ""}),
    ticket({n: 4, blocked: [1], blocker_hold: ""}),
    ticket({n: 5, blocked: [4], blocker_hold: ""}),
    ticket({n: 2, blocked: [3], blocker_hold: "open"}),
    ticket({n: 3, blocked: [2], blocker_hold: "open"}),
    ticket({n: 6, blocked: [3], blocker_hold: "open"}),
  ];
  const layout = Board.layout({n: 100, decisions: [], specs: [{n: 10, tickets: items}]}, new Set([10]));
  const tickets = layout.nodes.filter(node => node.type === "ticket");
  const at = number => tickets.find(node => node.id === number).x;
  // One column to the right of #5, the last ticket the chain could order.
  const column = at(4) - at(1);
  assert.equal(at(2), at(5) + column);
  assert.deepEqual(layout.edges.filter(edge => edge.cyc).map(edge => [edge.from, edge.to, edge.state]),
    [[3, 2, "blocked"], [2, 3, "blocked"]]);
  assert.equal(tickets.find(node => node.id === 6).cyclic, false);
  assert.equal(layout.edges.find(edge => edge.from === 3 && edge.to === 6).cyc, false);
  assert.equal(layout.labels.find(label => label.warn).text, "阻塞成环 · #2 ⇄ #3 · 排不出先后");
});

test("a blocker outside the container draws no line", () => {
  const graph = Board.graph([{n: 2, blocked: [99]}]);
  assert.deepEqual(graph.edges, []);
});

test("container and decision lamps", () => {
  const hollow = ticket();
  const ink = ticket({fold: {landed: true}});
  const green = ticket({fold: {sessions: [worker()]}});
  const orange = ticket({fold: {children: {2: {child: 2, kind: "decision"}}}});
  assert.equal(Board.aggregate([ink, ink]), "ink");
  assert.equal(Board.aggregate([hollow, ink]), "hollow");
  assert.equal(Board.aggregate([green, ink]), "green");
  assert.equal(Board.aggregate([orange, green]), "orange");
  assert.equal(Board.decisionLight({state: "closed"}), "ink");
  assert.equal(Board.decisionLight({state: "open"}), "hollow");
});

test("default expansion", () => {
  const active = {n: 2, tickets: [ticket({fold: {sessions: [worker()]}})]};
  const done = {n: 3, tickets: [ticket({fold: {landed: true}})]};
  const untouched = {n: 4, tickets: [ticket()]};
  const orange = {n: 5, tickets: [ticket({fold: {children: {8: {child: 8, kind: "decision"}}}})]};
  assert.deepEqual([...defaultExpanded({n: 1, specs: [active, done, untouched, orange]})], [1, 2, 5]);
});
