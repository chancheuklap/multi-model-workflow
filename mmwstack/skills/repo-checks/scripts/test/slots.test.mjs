import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { cpus } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { cleanConfig, fixture } from './fixture.mjs';

const quote = value => `'${value.replaceAll("'", "'\\''")}'`;
const command = source => `${quote(process.execPath)} -e ${quote(source)}`;
const cpuCap = Math.max(1, Math.min(4, Math.floor(cpus().length / 2)));

function cacheDir(f) {
  return process.platform === 'darwin'
    ? join(f.home, 'Library/Caches/repo-checks/locks')
    : join(f.env.XDG_CACHE_HOME, 'repo-checks/locks');
}

function setup(t, configure) {
  const f = fixture(t);
  const c = cleanConfig();
  c.checks[0].run = command('console.log("checked")');
  configure(c, f);
  f.config(c);
  f.commit('Configure counting slot fixture');
  return { f, c };
}

async function waitUntil(predicate, message, timeout = 10_000) {
  const deadline = Date.now() + timeout;
  while (!predicate()) {
    if (Date.now() > deadline) throw new Error(message);
    await new Promise(resolve => setTimeout(resolve, 20));
  }
}

test('omitted perRunMax defaults to max and caps same-run and cross-run concurrency', async t => {
  const slotName = `default-cap-${Date.now()}`;
  const { f } = setup(t, c => {
    c.slots = { [slotName]: { max: 2 } };
    c.checks = Array.from({ length: 4 }, (_, i) => ({
      ...c.checks[0],
      id: `job${i}`,
      slot: slotName,
      run: command('console.log(JSON.stringify({ event: "start", time: Date.now() })); setTimeout(() => console.log(JSON.stringify({ event: "end", time: Date.now() })), 350)'),
    }));
  });
  const result = f.cli('--all', '--json');
  assert.equal(result.status, 0, result.stdout + result.stderr);
  const facts = JSON.parse(result.stdout);
  assert.equal(facts.summary.passed, 4);
  const events = facts.results
    .flatMap(item => readFileSync(item.log, 'utf8').trim().split('\n').map(JSON.parse))
    .sort((a, b) => a.time - b.time);
  let active = 0;
  let peak = 0;
  for (const event of events) {
    active += event.event === 'start' ? 1 : -1;
    peak = Math.max(peak, active);
  }
  const expectedPeak = Math.min(2, cpuCap);
  assert.equal(peak, expectedPeak, JSON.stringify({ peak, expectedPeak, events }));
  assert.equal(active, 0);

  const blocker = setup(t, (c, bf) => {
    c.slots = { [slotName]: { max: 2 } };
    c.checks = Array.from({ length: 2 }, (_, i) => ({
      ...c.checks[0],
      id: `hold${i}`,
      slot: slotName,
      timeout_s: 30,
      run: command(`
        const fs = require('node:fs');
        fs.writeFileSync(${JSON.stringify(join(bf.home, `held-${i}`))}, '1');
        const poll = setInterval(() => {
          if (fs.existsSync(${JSON.stringify(join(bf.home, 'release-default'))})) clearInterval(poll);
        }, 20);
      `),
    }));
  }).f;

  const contender = setup(t, c => {
    c.slots = { [slotName]: { max: 2 } };
    c.checks = [{
      ...c.checks[0],
      id: 'waiter',
      slot: slotName,
      timeout_s: 20,
      run: command('console.log("contender-entered")'),
    }];
  }).f;

  const expectedHeld = Math.min(2, cpuCap);
  const holdRun = blocker.start(['--all']);
  try {
    await waitUntil(
      () => Array.from({ length: 2 }, (_, i) => existsSync(join(blocker.home, `held-${i}`))).filter(Boolean).length === expectedHeld,
      'Expected blocker to hold counting slots',
    );
    if (expectedHeld === 2) {
      const waitRun = contender.start(['--all'], {
        env: { ...contender.env, HOME: blocker.home, XDG_CACHE_HOME: blocker.env.XDG_CACHE_HOME },
      });
      await waitRun.until(new RegExp(`WAIT ${slotName}`), 10_000);
      writeFileSync(join(blocker.home, 'release-default'), '1');
      const done = await waitRun.done;
      assert.equal(done.status, 0, done.stdout + done.stderr);
      assert.ok(done.stdout.indexOf(`WAIT ${slotName}`) < done.stdout.indexOf('PASS waiter'));
    } else {
      writeFileSync(join(blocker.home, 'release-default'), '1');
    }
  } finally {
    writeFileSync(join(blocker.home, 'release-default'), '1');
  }
  assert.equal((await holdRun.done).status, 0);
});

test('max 4 with perRunMax 2 holds at most 2 slots in Process A while Process B enters immediately', async t => {
  const slotName = `headroom-${Date.now()}`;
  const { f: repoA } = setup(t, (c, f) => {
    c.slots = { [slotName]: { max: 4, perRunMax: 2 } };
    c.checks = Array.from({ length: 4 }, (_, i) => ({
      ...c.checks[0],
      id: `a${i}`,
      slot: slotName,
      timeout_s: 30,
      run: command(`
        const fs = require('node:fs');
        const path = require('node:path');
        fs.writeFileSync(path.join(process.env.HOME, 'a-started-${i}'), String(Date.now()));
        console.log(JSON.stringify({ id: 'a${i}', event: 'start', time: Date.now() }));
        const poll = setInterval(() => {
          if (fs.existsSync(path.join(process.env.HOME, 'release-a'))) {
            clearInterval(poll);
            console.log(JSON.stringify({ id: 'a${i}', event: 'end', time: Date.now() }));
          }
        }, 20);
      `),
    }));
  });

  const { f: repoB } = setup(t, c => {
    c.slots = { [slotName]: { max: 4, perRunMax: 2 } };
    c.checks = Array.from({ length: 2 }, (_, i) => ({
      ...c.checks[0],
      id: `b${i}`,
      slot: slotName,
      timeout_s: 15,
      run: command(`console.log(JSON.stringify({ id: 'b${i}', time: Date.now() }))`),
    }));
  });

  const startedCount = () => Array.from({ length: 4 }, (_, i) => existsSync(join(repoA.home, `a-started-${i}`))).filter(Boolean).length;
  const expectedA = Math.min(2, cpuCap);
  const procA = repoA.start(['--all', '--json']);
  try {
    await waitUntil(() => startedCount() >= expectedA, 'Expected Process A to acquire its perRunMax slots');
    await new Promise(resolve => setTimeout(resolve, 300));
    assert.ok(startedCount() <= 2, `Process A exceeded perRunMax=2 before release: ${startedCount()}`);

    const procB = repoB.start(['--all', '--json'], {
      env: { ...repoB.env, HOME: repoA.home, XDG_CACHE_HOME: repoA.env.XDG_CACHE_HOME },
    });
    const bDone = await procB.done;
    assert.equal(bDone.status, 0, bDone.stdout + bDone.stderr);
    assert.doesNotMatch(bDone.stderr, new RegExp(`WAIT ${slotName}`));
    const bFacts = JSON.parse(bDone.stdout);
    assert.equal(bFacts.summary.passed, 2);
    assert.equal(bFacts.events.some(event => event.type === 'WAIT'), false);
    assert.equal(existsSync(join(repoA.home, 'release-a')), false, 'Process B must finish before Process A drains');
    assert.ok(startedCount() <= 2, `Process A exceeded perRunMax=2 while Process B ran: ${startedCount()}`);
  } finally {
    writeFileSync(join(repoA.home, 'release-a'), '1');
  }

  const aDone = await procA.done;
  assert.equal(aDone.status, 0, aDone.stdout + aDone.stderr);
  const aFacts = JSON.parse(aDone.stdout);
  assert.equal(aFacts.summary.passed, 4);
  const aEvents = aFacts.results
    .flatMap(item => readFileSync(item.log, 'utf8').trim().split('\n').map(JSON.parse))
    .sort((a, b) => a.time - b.time);
  let active = 0;
  let peak = 0;
  for (const event of aEvents) {
    active += event.event === 'start' ? 1 : -1;
    peak = Math.max(peak, active);
  }
  assert.ok(peak <= 2, `Process A peak concurrency ${peak} exceeded perRunMax=2`);
  assert.equal(peak, expectedA);
  t.diagnostic(JSON.stringify({ max: 4, perRunMax: 2, processAPeak: peak, processBPassedBeforeADrain: true }));
});

test('global max across concurrent processes blocks waiters on timeout with exit 2 and holder details', async t => {
  const slotName = `sat-${Date.now()}`;
  const holder1 = setup(t, c => {
    c.slots = { [slotName]: { max: 2, perRunMax: 2 } };
    c.checks = [{
      ...c.checks[0],
      id: 'h1',
      slot: slotName,
      timeout_s: 30,
      run: command(`
        const fs = require('node:fs');
        const path = require('node:path');
        fs.writeFileSync(path.join(process.env.HOME, 'h1-held'), '1');
        const poll = setInterval(() => {
          if (fs.existsSync(path.join(process.env.HOME, 'release-sat'))) clearInterval(poll);
        }, 20);
      `),
    }];
  }).f;

  const holder2 = setup(t, c => {
    c.slots = { [slotName]: { max: 2, perRunMax: 2 } };
    c.checks = [{
      ...c.checks[0],
      id: 'h2',
      slot: slotName,
      timeout_s: 30,
      run: command(`
        const fs = require('node:fs');
        const path = require('node:path');
        fs.writeFileSync(path.join(process.env.HOME, 'h2-held'), '1');
        const poll = setInterval(() => {
          if (fs.existsSync(path.join(process.env.HOME, 'release-sat'))) clearInterval(poll);
        }, 20);
      `),
    }];
  }).f;

  const timedOut = setup(t, c => {
    c.slots = { [slotName]: { max: 2, perRunMax: 2 } };
    c.checks = [{
      ...c.checks[0],
      id: 'blocked-check',
      slot: slotName,
      timeout_s: 0.25,
      run: command('console.log("should-not-run")'),
    }];
  }).f;

  const patient = setup(t, c => {
    c.slots = { [slotName]: { max: 2, perRunMax: 2 } };
    c.checks = [{
      ...c.checks[0],
      id: 'patient-check',
      slot: slotName,
      timeout_s: 20,
      run: command('console.log("patient-ran")'),
    }];
  }).f;

  const sharedEnv = { ...holder1.env };
  const p1 = holder1.start(['--all'], { env: sharedEnv });
  const p2 = holder2.start(['--all'], { env: { ...holder2.env, HOME: holder1.home, XDG_CACHE_HOME: holder1.env.XDG_CACHE_HOME } });
  let p3;
  try {
    await waitUntil(
      () => existsSync(join(holder1.home, 'h1-held')) && existsSync(join(holder1.home, 'h2-held')),
      'Expected both cross-process holders to acquire max=2 slots',
    );
    const blockedRun = await timedOut.start(['--all', '--json'], {
      env: { ...timedOut.env, HOME: holder1.home, XDG_CACHE_HOME: holder1.env.XDG_CACHE_HOME },
    }).done;
    assert.equal(blockedRun.status, 2, blockedRun.stdout + blockedRun.stderr);
    assert.match(blockedRun.stderr, new RegExp(`WAIT ${slotName}`));
    const blockedFacts = JSON.parse(blockedRun.stdout);
    assert.equal(blockedFacts.summary.blocked, 1);
    assert.equal(blockedFacts.results[0].status, 'blocked');
    assert.match(blockedFacts.results[0].reason, new RegExp(`${slotName}.*2 max.*pid=.*start=`));

    p3 = patient.start(['--all', '--json'], {
      env: { ...patient.env, HOME: holder1.home, XDG_CACHE_HOME: holder1.env.XDG_CACHE_HOME },
    });
    await p3.until(new RegExp(`WAIT ${slotName}`), 10_000);
  } finally {
    writeFileSync(join(holder1.home, 'release-sat'), '1');
  }

  assert.equal((await p1.done).status, 0);
  assert.equal((await p2.done).status, 0);
  const p3Done = await p3.done;
  assert.equal(p3Done.status, 0, p3Done.stdout + p3Done.stderr);
  assert.equal(JSON.parse(p3Done.stdout).results[0].status, 'passed');
});

test('stale counting-slot leases from killed holders are reclaimed without exceeding max', async t => {
  const slotName = `stale-${Date.now()}`;
  const { f } = setup(t, c => {
    c.slots = { [slotName]: { max: 2, perRunMax: 2 } };
    c.checks = Array.from({ length: 2 }, (_, i) => ({
      ...c.checks[0],
      id: `stale${i}`,
      slot: slotName,
      run: command(`
        const fs = require('node:fs');
        const path = require('node:path');
        fs.writeFileSync(path.join(process.env.HOME, 'child-${i}.json'), JSON.stringify({ pid: process.pid, ppid: process.ppid }));
        setTimeout(() => {}, 30000);
      `),
    }));
  });

  const expectedKilled = Math.min(2, cpuCap);
  const deadRun = f.start(['--all']);
  await waitUntil(
    () => Array.from({ length: 2 }, (_, i) => existsSync(join(f.home, `child-${i}.json`))).filter(Boolean).length === expectedKilled,
    'Expected stale holder child PIDs to be written',
  );
  const cache = cacheDir(f);
  const slotDirs = readdirSync(cache).filter(name => !name.startsWith('.'));
  assert.equal(slotDirs.length, 1);
  const slotFolder = join(cache, slotDirs[0]);
  const leaseDirs = readdirSync(slotFolder).filter(name => !name.startsWith('.'));
  assert.equal(leaseDirs.length, expectedKilled);
  for (const leaseDir of leaseDirs) {
    const tokenFile = readdirSync(join(slotFolder, leaseDir))[0];
    const owner = JSON.parse(readFileSync(join(slotFolder, leaseDir, tokenFile), 'utf8'));
    assert.equal(typeof owner.start, 'string');
    assert.equal(typeof owner.nonce, 'string');
    try { process.kill(owner.pid, 'SIGKILL'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
  }
  for (let i = 0; i < 2; i++) {
    const pidFile = join(f.home, `child-${i}.json`);
    if (!existsSync(pidFile)) continue;
    const child = JSON.parse(readFileSync(pidFile, 'utf8'));
    for (const pid of [child.pid, child.ppid]) {
      try { process.kill(pid, 'SIGKILL'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
    }
  }
  assert.equal((await deadRun.done).status, 70);

  const contender = setup(t, c => {
    c.slots = { [slotName]: { max: 2, perRunMax: 2 } };
    c.checks = [{
      ...c.checks[0],
      id: 'reclaimer',
      slot: slotName,
      run: command('console.log(JSON.stringify({ event: "start", time: Date.now() })); setTimeout(() => console.log(JSON.stringify({ event: "end", time: Date.now() })), 350)'),
    }];
  }).f;

  const racers = Array.from({ length: 4 }, () => contender.start(['--all', '--json'], {
    env: { ...contender.env, HOME: f.home, XDG_CACHE_HOME: f.env.XDG_CACHE_HOME },
  }));
  const results = await Promise.all(racers.map(r => r.done));
  const events = [];
  for (const r of results) {
    assert.equal(r.status, 0, r.stdout + r.stderr);
    const facts = JSON.parse(r.stdout);
    events.push(...readFileSync(facts.results[0].log, 'utf8').trim().split('\n').map(JSON.parse));
  }
  events.sort((a, b) => a.time - b.time);
  let active = 0;
  let peak = 0;
  for (const event of events) {
    active += event.event === 'start' ? 1 : -1;
    assert.ok(active >= 0 && active <= 2, JSON.stringify(events));
    peak = Math.max(peak, active);
  }
  assert.equal(active, 0);
  assert.equal(peak, 2);
  assert.deepEqual(readdirSync(cache).filter(name => !name.startsWith('.')), []);
});

test('SIGINT cleans up waiting and held counting-slot lease directories', async t => {
  const slotName = `sigint-${Date.now()}`;
  const { f } = setup(t, (c, f) => {
    c.slots = { [slotName]: { max: 1 } };
    c.checks = [{
      ...c.checks[0],
      id: 'holder',
      slot: slotName,
      run: command(`require('node:fs').writeFileSync(${JSON.stringify(join(f.home, 'sigint-held'))}, String(process.pid)); setTimeout(() => {}, 30000)`),
    }];
  });
  const waiterRepo = setup(t, c => {
    c.slots = { [slotName]: { max: 1 } };
    c.checks = [{
      ...c.checks[0],
      id: 'waiter',
      slot: slotName,
      run: command('console.log("ran")'),
    }];
  }).f;

  const active = f.start(['--all']);
  t.after(() => { try { active.child.kill('SIGKILL'); } catch {} });
  await waitUntil(() => existsSync(join(f.home, 'sigint-held')), 'Expected holder to enter slot');
  const waiter = waiterRepo.start(['--all'], {
    env: { ...waiterRepo.env, HOME: f.home, XDG_CACHE_HOME: f.env.XDG_CACHE_HOME },
  });
  t.after(() => { try { waiter.child.kill('SIGKILL'); } catch {} });
  await waiter.until(new RegExp(`WAIT ${slotName}`), 10_000);
  waiter.child.kill('SIGINT');
  assert.equal((await waiter.done).status, 130);

  active.child.kill('SIGINT');
  assert.equal((await active.done).status, 130);

  const cache = cacheDir(f);
  await waitUntil(() => readdirSync(cache).length === 0, 'Expected cache locks dir to be completely clean');
  assert.deepEqual(readdirSync(cache), []);
  const next = waiterRepo.start(['--all'], {
    env: { ...waiterRepo.env, HOME: f.home, XDG_CACHE_HOME: f.env.XDG_CACHE_HOME },
  });
  const nextDone = await next.done;
  assert.equal(nextDone.status, 0, nextDone.stdout + nextDone.stderr);
  assert.doesNotMatch(nextDone.stdout, /WAIT /);
});
