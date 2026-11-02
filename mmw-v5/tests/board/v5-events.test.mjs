import assert from 'node:assert/strict';
import test from 'node:test';
import {Board, describeEvent} from '../../board/page/board-logic.mjs';
import {fromBoard} from '../../board/page/detail.mjs';

test('plain V5 completion identifies the output without claiming criterion counts', () => {
  const event = describeEvent({event: 'ticket.passed', payload: {commit: 'abc1234abcd', into: 'batch'}});
  assert.match(event.text, /abc1234/);
  assert.doesNotMatch(event.text, /criteria met/);
});

test('a completion awaiting landing keeps its existing verify phase', () => {
  const ticket = {state: 'closed', children: [], events: [{event:'ticket.passed', payload:{}}],
    fold: {landed:false, passed:true, children:{}, sessions:[{kind:'worker',live:true}]}};
  assert.equal(Board.phase(ticket), 'verify');
});

test('a review report names the actual comparison without assuming reviewer axes', () => {
  const event = describeEvent({event:'reviewer.reported', payload:{base:'aaaaaaa1',head:'bbbbbbb2'}});
  assert.match(event.text, /aaaaaaa/);
  assert.match(event.text, /bbbbbbb/);
  assert.doesNotMatch(event.text, /three-axis/);
});

test('an explicit independent ticket target is shown as Ticket opened', () => {
  const event=describeEvent({event:'ticket.opened',payload:{into:'batch'}});
  assert.equal(event.name,'Ticket opened');
  assert.match(event.text,/batch/);
});

test('a standalone Spec ticket does not invent a Map parent', () => {
  const ticket={n:61,title:'First ticket',state:'open',blocked:[],children:[],events:[],
    fold:{children:{},sessions:[],landed:false,returned:false,bounced:false,worker:null}};
  const spec={n:60,title:'Standalone Spec',tickets:[ticket]};
  const detail=fromBoard({repo:'fixture/board',tasks:[{n:60,kind:'spec',decisions:[],specs:[spec]}]},61);
  assert.deepEqual(detail.links,[{label:'spec #60',n:60}]);
});


import {readFileSync} from 'node:fs';
const feeds=JSON.parse(readFileSync(new URL('./v5-event-feed.json',import.meta.url)));
const firstTicket=feed=>feed.tasks.flatMap(task=>task.specs).flatMap(spec=>spec.tickets)[0];
for (const name of ['ticket.returned-then-start-same-second','ticket.bounced-then-start-same-second']) {
  test(`${name}: a newer worker ends the old result by comment order`,()=>{
    const ticket=firstTicket(feeds[name]);
    assert.equal(Board.handedBack(ticket),false);
    assert.equal(Board.bounce(ticket),null);
    assert.equal(Board.running(ticket),true);
    assert.equal(Board.lamp(ticket),'green');
  });
}
test('unreadable event after landing is visible as needs you until repaired',()=>{
  const bad=firstTicket(feeds['landed-with-unreadable-event']);
  assert.equal(Board.done(bad),false);
  assert.equal(Board.lamp(bad),'orange');
  assert.match(Board.why(bad)[0].text,/comment/);
  const repaired=firstTicket(feeds['landed-after-comment-repair']);
  assert.equal(Board.done(repaired),true);
  assert.equal(Board.lamp(repaired),'ink');
});

test('a reopened ticket with historical landing is not done',()=>{
  assert.equal(Board.done({state:'open',blocker_hold:'open',fold:{landed:true}}),false);
});
