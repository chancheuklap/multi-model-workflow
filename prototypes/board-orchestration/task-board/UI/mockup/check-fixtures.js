// Checks the mockup's example data against the pipeline it depicts.
// Usage: node check-fixtures.js <task-board-mockup.html>
// Every rule names where it comes from; one line per violation, exit 1 when there is any.
// The events themselves are already valid: build_fixtures.py writes each with events.build,
// which refuses a payload the vocabulary does not allow. This checks what no single event
// can: their order across a ticket, and across the tickets of a spec.
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const js = html.split('<script>')[1].split('</script>')[0];
const core = js.slice(js.indexOf('/* FIXTURES:BEGIN */'), js.indexOf('/* BOARD:END */'));
const { FIXTURES, Board, SCENES, NOW } = new Function(core + '\nreturn { FIXTURES, Board, SCENES, NOW };')();

const bad = [];
const flag = (scene, n, rule, msg) => bad.push(`${scene} #${n}: [${rule}] ${msg}`);
const min = iso => (new Date(iso) - new Date('2026-09-10T00:00')) / 60000;
const first = (t, name, pred = () => true) => t.events.find(e => e.event === name && pred(e.payload));
const all = (t, name) => t.events.filter(e => e.event === name);
const at = (t, name, pred) => { const e = first(t, name, pred); return e ? min(e.at) : null; };
const run = r => p => p.run === r;
// implement's closing steps, in the order they are written (verify-ticket.py and dispatch.sh).
const ORDER = [
  ['worker.started'], ['ticket.checked', run('self')], ['reviewer.started'], ['reviewer.reported'],
  ['worker.decided'], ['verifier.started'], ['ticket.checked', run('reverify')],
  ['verifier.passed'], ['verifier.failed'], ['ticket.checked', run('repo-checks')],
  ['ticket.passed'], ['ticket.returned'], ['ticket.bounced'], ['ticket.landed'],
];
const label = ([name, pred]) => name + (pred ? `(${['self', 'reverify', 'repo-checks'].find(r => pred({ run: r }))})` : '');

for (const key of SCENES) {
  const sc = FIXTURES[key];
  if (sc.select.node != null && !sc.tasks.some(task => [task.n, ...task.decisions.map(d => d.n), ...task.specs.flatMap(s => [s.n, ...s.tickets.map(t => t.n)])].includes(sc.select.node)))
    flag(key, sc.select.node, 'select', 'the scene selects a card that is not in it');
  for (const task of sc.tasks) {
    // Wayfinder: a decision ticket closes only after its blockers have (docs/agents/issue-tracker.md).
    const dn = Object.fromEntries(task.decisions.map(d => [d.n, d]));
    for (const d of task.decisions) for (const b of d.blocked)
      if (d.state === 'closed' && dn[b] && dn[b].state !== 'closed') flag(key, d.n, 'decision-order', `closed while its blocker #${b} is open`);
    for (const spec of task.specs) {
      const byN = Object.fromEntries(spec.tickets.map(t => [t.n, t]));
      const specStarted = spec.tickets.some(t => first(t, 'worker.started'));
      const g = Board.graph(spec.tickets);
      for (const t of spec.tickets) {
        const f = t.fold, n = t.n;
        const S = first(t, 'worker.started');
        for (const e of t.events) if (min(e.at) > min(NOW)) flag(key, n, 'time', `${e.event} at ${e.at} is after the board read the tracker`);
        if (S) for (const e of t.events) if (min(e.at) < min(S.at)) flag(key, n, 'time', `${e.event} at ${e.at} comes before its worker started`);
        const missing = t.blocked.filter(b => !byN[b]);
        const blockers = t.blocked.filter(b => byN[b]);
        const landedAt = b => at(byN[b], 'ticket.landed');
        // #315 §10: the frontier holds no ticket with an unlanded blocker.
        if (S) {
          for (const b of blockers) {
            const L = landedAt(b);
            if (L == null || L > min(S.at)) flag(key, n, 'frontier', `started ${S.at.slice(11)} while blocker #${b} had not landed`);
          }
          if (missing.length) flag(key, n, 'frontier', `started although blocker ${missing.map(b => '#' + b).join(', ')} cannot be read`);
        }
        // #316 §5 + #315 §9: advance dispatches what a landing unblocks in the same run, with no cap on workers.
        const unlockAt = blockers.length ? Math.max(...blockers.map(b => landedAt(b) ?? Infinity)) : null;
        const origin = t.closeout ? byN[t.closeout.from] : null;
        const born = origin ? first(origin, 'child.closed', p => p.child === t.closeout.child && p.became === n) : null;
        if (t.closeout && !born) flag(key, n, 'child', `marked as opened in #${t.closeout.from}'s closing pass, but no child.closed there made it`);
        const readyAt = Math.max(unlockAt ?? -Infinity, born ? min(born.at) : -Infinity);
        if (S && isFinite(readyAt) && min(S.at) - readyAt > 5) flag(key, n, 'dispatch', `ready at ${Math.round(readyAt)}m but started ${Math.round(min(S.at) - readyAt)} minutes later`);
        if (!S && specStarted && !g.cyclic.has(n) && !missing.length && isFinite(readyAt) && readyAt <= min(NOW))
          flag(key, n, 'dispatch', 'every blocker has landed and nothing dispatched it');
        if (!S && specStarted && !blockers.length && !missing.length && !g.cyclic.has(n)) flag(key, n, 'dispatch', 'a root of a started spec was never dispatched');
        // implement, closing steps, in order.
        let last = -Infinity, lastName = '';
        for (const step of ORDER) {
          const x = at(t, ...step);
          if (x == null) continue;
          if (x < last) flag(key, n, 'closing-order', `${label(step)} comes before ${lastName}`);
          last = x; lastName = label(step);
        }
        const has = (name, pred) => !!first(t, name, pred);
        const needs = [
          ['reviewer.started', 'ticket.checked(self)', has('reviewer.started'), has('ticket.checked', run('self'))],
          ['reviewer.reported', 'reviewer.started', has('reviewer.reported'), has('reviewer.started')],
          ['ticket.checked(reverify)', 'verifier.started', has('ticket.checked', run('reverify')), has('verifier.started')],
          ['a verdict', 'verifier.started', has('verifier.passed') || has('verifier.failed'), has('verifier.started')],
          ['worker.decided', 'reviewer.reported', has('worker.decided'), has('reviewer.reported')],
          ['verifier.started', 'worker.decided', has('verifier.started'), has('worker.decided')],
          ['a verdict', 'ticket.checked(reverify)', has('verifier.passed') || has('verifier.failed'), has('ticket.checked', run('reverify'))],
          ['ticket.passed', 'verifier.passed', has('ticket.passed'), has('verifier.passed')],
          ['ticket.passed', 'ticket.checked(repo-checks)', has('ticket.passed'), has('ticket.checked', run('repo-checks'))],
          ['ticket.landed', 'ticket.passed', has('ticket.landed'), has('ticket.passed')],
          ['ticket.bounced', 'ticket.passed', has('ticket.bounced'), has('ticket.passed')],
        ];
        for (const [a, b, hasA, hasB] of needs) if (hasA && !hasB) flag(key, n, 'closing-steps', `${a} without ${b}`);
        if (all(t, 'worker.decided').length > 1) flag(key, n, 'closing-steps', 'more than one DECISIONS comment');
        // verify-ticket.py --verdict: a pass needs the newest reverify to be `met`.
        const reverify = first(t, 'ticket.checked', run('reverify'));
        if (has('verifier.passed') && reverify && reverify.payload.result !== 'met') flag(key, n, 'verdict', `verifier.passed on a reverify whose result is ${reverify.payload.result}`);
        // implement: only a `failed` or `stuck` criterion turns a ticket back.
        const back = first(t, 'ticket.returned');
        if (back && !(back.payload.abandoned || []).some(a => ['failed', 'stuck'].includes(a.kind)))
          flag(key, n, 'handoff', 'handed back without a failed or stuck criterion');
        if (f.landed && f.sessions.some(s => s.live)) flag(key, n, 'hold', 'landed but a session still holds it');
        // #337 §8: the worker merges the base branch in before its review, so a passed ticket
        // fails to land only when another ticket of its spec landed after it started; and the
        // bounce ends every hold on it (events.py ENDS_EVERY_HOLD).
        const bounce = first(t, 'ticket.bounced');
        if (bounce && S && !spec.tickets.some(o => o !== t && landedAt(o.n) != null && landedAt(o.n) > min(S.at) && landedAt(o.n) <= min(bounce.at)))
          flag(key, n, 'bounce', 'did not land although no other ticket of its spec landed while it was worked');
        if (f.bounced && f.sessions.some(s => s.live && s.started_at <= bounce.at)) flag(key, n, 'hold', 'did not land but a session from before still holds it');
        // Children: opened while the worker works; a finding only after the review reported;
        // routed by main only on the closing pass, after the ticket passed or came back.
        const closedOut = at(t, 'ticket.passed') ?? at(t, 'ticket.returned');
        for (const e of all(t, 'child.opened')) {
          if (!S) flag(key, n, 'child', `#${e.payload.child} opened on a ticket no worker started`);
          if (e.payload.kind === 'finding' && !(at(t, 'reviewer.reported') <= min(e.at))) flag(key, n, 'child', `finding #${e.payload.child} opened before the review reported`);
        }
        for (const e of all(t, 'child.closed')) {
          if (closedOut == null || min(e.at) < closedOut) flag(key, n, 'child', `#${e.payload.child} routed before the closing pass`);
          if (e.payload.resolution === 'became-ticket') {
            const nt = byN[e.payload.became];
            if (!nt) flag(key, n, 'child', `#${e.payload.child} became #${e.payload.became}, which is not in the spec`);
            else if (!nt.closeout || nt.closeout.from !== n) flag(key, n, 'child', `#${e.payload.became} is not marked as opened in #${n}'s closing pass`);
          }
        }
        // A fault stops the agent where it is (#315 §3, implement: "then stop") until the main
        // agent fixes the cause and resumes it (dispatch's references/night.md, `worker.resumed`).
        const fault = t.events.find(e => e.event === 'child.opened' && e.payload.kind === 'fault');
        const resumed = fault && t.events.find(e => e.event === 'worker.resumed' && min(e.at) >= min(fault.at));
        if (fault) for (const e of t.events) if (e.actor !== 'main' && min(e.at) > min(fault.at) && !(resumed && min(e.at) >= min(resumed.at)))
          flag(key, n, 'fault', `${e.event} after the fault stopped the worker`);
        // #315 §9: a run waits for a slot before it runs; the fold's `waiting` is that wait.
        if (f.waiting && !f.sessions.some(s => s.live)) flag(key, n, 'slot', 'waits for a slot with no live worker');
        if (g.cyclic.has(n) && key !== 'bad-data') flag(key, n, 'bad-data', 'a blocking cycle outside the bad-data scene');
        if (missing.length && key !== 'bad-data') flag(key, n, 'bad-data', 'a blocker outside the tree outside the bad-data scene');
      }
    }
  }
}
if (bad.length) { console.log(bad.join('\n')); console.log(`${bad.length} violations`); process.exit(1); }
console.log('the example data obeys every rule checked');
