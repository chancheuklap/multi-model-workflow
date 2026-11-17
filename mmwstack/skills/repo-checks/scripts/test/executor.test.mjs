import assert from 'node:assert/strict';
import test from 'node:test';
import { cpus } from 'node:os';
import { appendFileSync, chmodSync, copyFileSync, existsSync, readFileSync, readdirSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { cleanConfig, fixture } from './fixture.mjs';

const quote = value => `'${value.replaceAll("'", "'\\''")}'`;
const command = source => `${quote(process.execPath)} -e ${quote(source)}`;
function setup(t, configure) {
  const f = fixture(t);
  const c = cleanConfig();
  c.checks[0].run = command('console.log("checked")');
  configure(c, f);
  f.config(c);
  f.commit('Configure executor');
  return { f, c };
}
function json(f, args = ['--all'], expected = 0) {
  const r = f.cli(...args, '--json');
  assert.equal(r.status, expected, r.stdout + r.stderr);
  return JSON.parse(r.stdout);
}

test('six sleeping checks overlap within the CPU execution cap and retain selection order', t => {
  const { f } = setup(t, c => {
    c.checks = Array.from({ length: 6 }, (_, i) => ({
      ...c.checks[0], id: `check${i}`,
      run: command('console.log(JSON.stringify({event:"start",time:Date.now()})); setTimeout(() => console.log(JSON.stringify({event:"end",time:Date.now()})), 350)'),
    }));
  });
  const facts = json(f);
  assert.deepEqual(facts.results.map(x => x.id), ['check0', 'check1', 'check2', 'check3', 'check4', 'check5']);
  const events = facts.results.flatMap(x => readFileSync(x.log, 'utf8').trim().split('\n').map(JSON.parse)).sort((a,b) => a.time-b.time);
  let active = 0;
  let peak = 0;
  for (const e of events) { active += e.event === 'start' ? 1 : -1; peak = Math.max(peak, active); }
  const cap = Math.max(1, Math.min(4, Math.floor(cpus().length / 2)));
  assert.ok(peak <= cap, `peak=${peak}, cap=${cap}`);
  assert.equal(peak, cap);
  assert.equal(active, 0);
  t.diagnostic(JSON.stringify({ peak, cap, events }));
});

test('retry reruns only the failing check once and reports recovery', t => {
  const { f } = setup(t, (c, f) => {
    const counter = join(f.home, 'attempts');
    c.checks[0].retry = 1;
    c.checks[0].run = command(`const fs=require('node:fs'); const p=${JSON.stringify(counter)}; const n=fs.existsSync(p)?Number(fs.readFileSync(p)):0; fs.writeFileSync(p,String(n+1)); process.exit(n===0?1:0)`);
    c.checks.push({ ...c.checks[0], id: 'sibling', retry: 0, run: command('console.log("sibling")') });
  });
  const r = f.cli('--all');
  assert.equal(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /PASS unit [\d.]+s \(recovered on retry\)/);
  assert.equal(readFileSync(join(f.home, 'attempts'), 'utf8'), '2');
  assert.equal((r.stdout.match(/^PASS sibling /gm) ?? []).length, 1);
});

test('timeout fails with reason timeout and kills descendants before finishing', async t => {
  const { f } = setup(t, (c, f) => {
    c.checks[0].timeout_s = 0.35;
    c.checks[0].run = command(`const {spawn}=require('node:child_process'); spawn(process.execPath,['-e',${JSON.stringify(`setTimeout(()=>require('node:fs').writeFileSync(${JSON.stringify(join(f.home, 'escaped'))},"bad"),900)`)}],{stdio:'ignore'}); setTimeout(()=>{},10000)`);
  });
  const facts = json(f, ['--all'], 1);
  assert.equal(facts.results[0].status, 'failed');
  assert.equal(facts.results[0].reason, 'timeout');
  assert.match(f.cli('--all').stdout, /FAIL unit [\d.]+s log=.*\ntimeout/);
  await new Promise(resolve => setTimeout(resolve, 1100));
  assert.equal(existsSync(join(f.home, 'escaped')), false);
});

test('machine locks serialize separate repositories while waiters leave slots available', async t => {
  const lock = `shared-${Date.now()}`;
  const { f } = setup(t, c => {
    c.checks[0].lock = lock;
    c.checks[0].run = command('console.log("started"); setTimeout(()=>console.log("finished"),1500)');
  });
  const other = setup(t, c => {
    c.checks = [
      { ...c.checks[0], id: 'locked', lock, run: command('console.log("second")') },
      ...Array.from({length: 5}, (_, i) => ({ ...c.checks[0], id:`free${i}`, run: command('console.log("free")') })),
    ];
  }).f;
  const first = f.start(['--all']);
  await first.until(/SELECT unit/);
  await new Promise(resolve => setTimeout(resolve, 250));
  const second = other.start(['--all'], { env: { ...other.env, HOME: f.home, XDG_CACHE_HOME: f.env.XDG_CACHE_HOME } });
  await second.until(new RegExp(`WAIT ${lock}`));
  await second.until(/PASS free4/);
  assert.equal(first.child.exitCode, null, 'Unlocked work must finish while the resource is still held');
  const a = await first.done;
  const b = await second.done;
  assert.equal(a.status, 0, a.stdout + a.stderr);
  assert.equal(b.status, 0, b.stdout + b.stderr);
  assert.ok(b.stdout.indexOf(`WAIT ${lock}`) < b.stdout.indexOf('PASS locked'));
  assert.match(b.stdout, /SUMMARY 6 selected, 6 passed/);
});

test('live lock wait timeout is blocked exit 2 and names the process holder', async t => {
  const { f, c } = setup(t, c => {
    c.checks[0].lock = 'live-timeout';
    c.checks[0].run = command('setTimeout(()=>{},1200)');
  });
  const first = f.start(['--all']);
  await first.until(/SELECT/);
  await new Promise(resolve => setTimeout(resolve, 250));
  c.checks[0].timeout_s = 0.2;
  f.config(c);
  const r = await f.start(['--all', '--json']).done;
  assert.equal(r.status, 2, r.stdout + r.stderr);
  const facts = JSON.parse(r.stdout);
  assert.equal(facts.summary.blocked, 1);
  assert.equal(facts.results[0].status, 'blocked');
  assert.match(facts.results[0].reason, /live-timeout.*pid.*start/i);
  assert.match(r.stderr, /WAIT live-timeout/);
  assert.equal((await first.done).status, 0);
});

test('outer engine death leaves the supervisor lock valid until its child finishes', async t => {
  const marker = 'owner-death';
  const { f } = setup(t, (c, f) => {
    c.checks[0].lock = marker;
    c.checks[0].run = command(`console.log("child started"); require('node:fs').writeFileSync(${JSON.stringify(join(f.home,'child-started'))},String(process.pid)); setTimeout(()=>{},1400)`);
  });
  const first = f.start(['--all']);
  await first.until(/SELECT/);
  const deadline = Date.now()+5000;
  while (!existsSync(join(f.home, 'child-started')) && Date.now()<deadline) await new Promise(resolve=>setTimeout(resolve,20));
  assert.ok(existsSync(join(f.home, 'child-started')));
  const pid = Number(readFileSync(join(f.home,'child-started')));
  first.child.kill('SIGKILL');
  await first.done;
  assert.doesNotThrow(()=>process.kill(pid,0));
  const second = f.start(['--all']);
  await second.until(/WAIT owner-death/);
  const r = await second.done;
  assert.equal(r.status, 0, r.stdout+r.stderr);
  t.diagnostic('Outer CLI killed while the command PID remained alive; second CLI waited and passed.');
});

test('an empty lock left between token deletion and rmdir is recoverable', async t => {
  const { f } = setup(t, c => { c.checks[0].lock = 'empty-crash'; c.checks[0].run = command('setTimeout(()=>{},400)'); });
  const first = f.start(['--all']);
  await first.until(/SELECT/);
  await new Promise(resolve=>setTimeout(resolve,200));
  const cache = process.platform === 'darwin' ? join(f.home,'Library/Caches/repo-checks/locks') : join(f.env.XDG_CACHE_HOME,'repo-checks/locks');
  const canonical = readdirSync(cache).find(name => !name.startsWith('.'));
  assert.ok(canonical);
  assert.equal((await first.done).status,0);
  mkdirSync(join(cache,canonical));
  f.write('README.md', 'A dirty tree requires actual execution instead of reuse.\n');
  const r = f.cli('--all');
  assert.equal(r.status,0,r.stdout+r.stderr);
  assert.doesNotMatch(r.stdout, /\(reused\)/);
  assert.equal(existsSync(join(cache, canonical)), false);
});

test('SIGINT stops the running check, its process group and its lock', async t => {
  const { f } = setup(t, (c, f) => {
    c.checks[0].lock = 'interrupt-lock';
    c.checks[0].run = command(`require('node:fs').writeFileSync(${JSON.stringify(join(f.home,'check-pid'))},String(process.pid));setTimeout(()=>{},30000)`);
  });
  const active = f.start(['--all']);
  await active.until(/SELECT unit/);
  const deadline = Date.now() + 10000;
  while (!existsSync(join(f.home,'check-pid')) && Date.now() < deadline) await new Promise(resolve=>setTimeout(resolve,20));
  const pid = Number(readFileSync(join(f.home,'check-pid'),'utf8'));
  assert.doesNotThrow(()=>process.kill(pid,0));
  active.child.kill('SIGINT');
  const r = await active.done;
  assert.equal(r.status, 130, r.stdout+r.stderr);
  const cache = process.platform==='darwin' ? join(f.home,'Library/Caches/repo-checks/locks') : join(f.env.XDG_CACHE_HOME,'repo-checks/locks');
  const gone = Date.now()+5000;
  while (Date.now() < gone) {
    try { process.kill(pid,0); await new Promise(resolve=>setTimeout(resolve,20)); }
    catch { break; }
  }
  assert.throws(()=>process.kill(pid,0),{code:'ESRCH'});
  const free = Date.now()+5000;
  while (readdirSync(cache).some(name=>!name.startsWith('.')) && Date.now() < free) await new Promise(resolve=>setTimeout(resolve,20));
  assert.deepEqual(readdirSync(cache).filter(name=>!name.startsWith('.')),[]);
});

test('SIGINT never retries a check or leaves its lock blocking the next run', async t => {
  const { f } = setup(t, (c, f) => {
    c.checks[0].retry = 1;
    c.checks[0].lock = 'interrupt-retry-lock';
    c.checks[0].run = `echo $$ >> ${quote(join(f.home, 'pids'))}; if [ ! -f ${quote(join(f.home, 'fast'))} ]; then sleep 30 & echo $! >> ${quote(join(f.home, 'pids'))}; wait; fi`;
  });
  const pids = () => readFileSync(join(f.home, 'pids'), 'utf8').trim().split('\n').map(Number);
  const active = f.start(['--all']);
  try {
    await active.until(/SELECT unit/);
    const deadline = Date.now() + 10000;
    while ((!existsSync(join(f.home, 'pids')) || pids().length < 2) && Date.now() < deadline) {
      await new Promise(resolve => setTimeout(resolve, 20));
    }
    assert.equal(pids().length, 2);
    await new Promise(resolve => setTimeout(resolve, 1000));
    active.child.kill('SIGINT');
    const result = await active.done;
    assert.equal(result.status, 130, result.stdout + result.stderr);
    for (const pid of pids()) assert.throws(() => process.kill(pid, 0), { code: 'ESRCH' });
    const cache = process.platform === 'darwin'
      ? join(f.home, 'Library/Caches/repo-checks/locks')
      : join(f.env.XDG_CACHE_HOME, 'repo-checks/locks');
    assert.deepEqual(readdirSync(cache).filter(name => !name.startsWith('.')), []);
    assert.equal(pids().length, 2, 'An interrupted attempt must not be retried');
    f.write('../home/fast', '');
    const next = f.cli('--all');
    assert.equal(next.status, 0, next.stdout + next.stderr);
    assert.doesNotMatch(next.stdout, /WAIT /);
    assert.ok(next.elapsed_ms < 3000, `Next run took ${next.elapsed_ms} ms`);
    assert.equal(pids().length, 3);
  } finally {
    if (existsSync(join(f.home, 'pids'))) for (const pid of pids()) {
      try { process.kill(pid, 'SIGKILL'); }
      catch (error) { if (error.code !== 'ESRCH') throw error; }
    }
  }
});

test('prepare runs before needs, rechecks its lease and hashes stamp paths and bytes', async t => {
  const { f, c } = setup(t, (c, f) => {
    f.write('.gitignore', 'installed/\n');
    f.write('deps/one.lock', 'same bytes');
    c.prepare = {
      stamps: ['deps/*.lock', 'missing.lock'],
      run: command(`const fs=require('node:fs'); fs.appendFileSync(${JSON.stringify(join(f.home,'prepares'))},'prepare\\n'); setTimeout(()=>{fs.mkdirSync('installed',{recursive:true}); fs.writeFileSync('installed/ready','yes')},250)`),
    };
    c.checks[0].needs = ['path:installed/ready'];
    c.checks[0].run = command(`if(!require('node:fs').existsSync('installed/ready')) process.exit(9); console.log("ready")`);
  });
  const a = f.start(['--all', '--json']);
  const b = f.start(['--all', '--json']);
  for (const r of await Promise.all([a.done,b.done])) assert.equal(r.status,0,r.stdout+r.stderr);
  assert.equal(readFileSync(join(f.home,'prepares'),'utf8'), 'prepare\n');
  assert.ok(json(f).preparation_stamp);
  f.write('deps/one.lock','changed bytes');
  json(f);
  f.write('deps/two.lock','changed bytes');
  rmSync(join(f.repo,'deps/one.lock'));
  json(f);
  f.write('missing.lock','appeared');
  json(f);
  rmSync(join(f.repo,'installed'),{recursive:true});
  json(f);
  assert.equal(readFileSync(join(f.home,'prepares'),'utf8'), 'prepare\n'.repeat(5));
  assert.ok(c.prepare);
});

test('failed preparation blocks checks and never persists a successful stamp', t => {
  const { f, c } = setup(t, (c, f) => {
    c.prepare = { stamps:['README.md'], run: command(`console.error("install broke"); process.exit(4)`) };
    c.checks[0].run = command(`require('node:fs').writeFileSync(${JSON.stringify(join(f.home,'check-ran'))},"bad")`);
  });
  for (let i=0;i<2;i++) {
    const facts = json(f,['--all'],2);
    assert.equal(facts.results[0].status,'blocked');
    assert.match(readFileSync(facts.results[0].log,'utf8'),/install broke/);
    assert.equal(facts.preparation_stamp,null);
    assert.equal(existsSync(join(f.home,'check-ran')),false);
  }
  assert.match(f.cli('--all').stdout,/SUMMARY 1 selected, 0 passed, 0 failed, 1 skipped\n$/);
  c.prepare.run = command('console.log("installed")');
  f.config(c);
  assert.equal(json(f).results[0].status,'passed');
});

test('reuse requires clean tree and unchanged command config and engine source', t => {
  const { f, c } = setup(t, () => {});
  const engine = join(f.home,'check.mjs');
  copyFileSync(new URL('../check.mjs',import.meta.url),engine);
  copyFileSync(new URL('../checks.schema.json',import.meta.url),join(f.home,'checks.schema.json'));
  f.write('scripts/check',`#!/bin/sh\nexec ${quote(process.execPath)} ${quote(engine)} "$@"\n`);
  f.commit();
  assert.equal(json(f).results[0].reused,false);
  assert.equal(json(f).results[0].reused,true);
  assert.match(f.cli('--all').stdout,/PASS unit [\d.]+s \(reused\)/);
  f.write('README.md','dirty');
  assert.equal(json(f).results[0].reused,false);
  f.commit();
  assert.equal(json(f).results[0].reused,false);
  assert.equal(json(f).results[0].reused,true);
  c.inert.push('docs/**');
  f.config(c); f.commit();
  assert.equal(json(f).results[0].reused,false);
  c.checks[0].run = command('console.log("new command")');
  f.config(c); f.commit();
  assert.equal(json(f).results[0].reused,false);
  assert.equal(json(f).results[0].reused,true);
  appendFileSync(engine,'\n');
  assert.equal(json(f).results[0].reused,false);
});

test('whole coverage reuses its current whole command for narrow selection but narrow never covers whole', t => {
  for (const identical of [false,true]) {
    const { f } = setup(t,(c,f)=>{
      Object.assign(c.checks[0],{
        inputs:[],sources:['src/**'],select:command('console.log(JSON.stringify(["test/a.test.mjs"]))'),
        run:command('console.log("narrow")'),
        run_all:command(identical ? 'console.log("narrow")' : 'console.log("whole")'),
      });
      f.write('test/a.test.mjs','fixture');
    });
    f.git('push','origin','main');
    f.write('src/a.js','changed'); f.commit();
    assert.equal(json(f,[]).results[0].reused,false);
    assert.equal(json(f,[]).results[0].reused,true);
    assert.equal(json(f).results[0].reused,false);
    const narrow = json(f,[]);
    assert.equal(narrow.results[0].reused,true);
    assert.equal(narrow.results[0].scope.kind,'narrowed');
    assert.equal(narrow.results[0].reused_from.coverage.kind,'whole');
  }
});

test('needs are checked before reuse and identity drift prevents reusable evidence', async t => {
  const { f, c } = setup(t,(c,f)=>{
    f.write('.gitignore','installed\n');
    f.write('installed','ready');
    c.checks[0].needs=['path:installed'];
    c.checks[0].run=command('setTimeout(()=>console.log("done"),500)');
  });
  assert.equal(json(f).results[0].status,'passed');
  rmSync(join(f.repo,'installed'));
  const missing=json(f,['--all'],2);
  assert.equal(missing.results[0].status,'skipped');
  f.write('installed','ready');
  c.checks[0].run=command(`require('node:fs').writeFileSync(${JSON.stringify(join(f.home,'started'))},"yes"); setTimeout(()=>console.log("changed"),1500)`);
  f.config(c); f.commit();
  const active=f.start(['--all','--json']);
  const started=Date.now()+10000;
  while(!existsSync(join(f.home,'started'))&&Date.now()<started) await new Promise(resolve=>setTimeout(resolve,20));
  assert.ok(existsSync(join(f.home,'started')),'check started before the tree changed');
  f.write('README.md','changed during execution');
  const r=await active.done;
  assert.equal(r.status,0,r.stdout+r.stderr);
  const facts=JSON.parse(r.stdout);
  assert.equal(facts.results[0].reusable,false);
  assert.equal(facts.reuse_eligible,false);
  f.write('README.md','Fixture repository.\n');
  assert.equal(json(f).results[0].reused,false);
});

test('RUNNING is live within 20 seconds during a real 22 second check and JSON stays one object', async t => {
  const { f }=setup(t,(c,f)=>{
    c.checks[0].timeout_s=30;
    c.checks[0].run=command(`require('node:fs').writeFileSync(${JSON.stringify(join(f.home,'started-at'))},String(Date.now())); setTimeout(()=>console.log("finished"),22000)`);
  });
  const active=f.start(['--all','--json']);
  await active.until(/RUNNING unit [\d.]+s/,45000);
  assert.equal(active.child.exitCode,null);
  assert.equal(active.lines.filter(x=>x.stream==='stdout').length,0);
  const progress=active.lines.find(x=>x.text.includes('RUNNING unit'));
  const start=Number(readFileSync(join(f.home,'started-at')));
  assert.ok(progress.time-start<=20000,`First heartbeat after ${progress.time-start}ms`);
  const r=await active.done;
  assert.equal(r.status,0,r.stdout+r.stderr);
  const facts=JSON.parse(r.stdout);
  assert.equal(facts.results[0].status,'passed');
  assert.ok(facts.results[0].seconds>=22);
  assert.ok(facts.events.some(e=>e.type==='RUNNING'));
  assert.ok(Date.now()-progress.time<=20000);
  t.diagnostic(JSON.stringify({first_heartbeat_ms:progress.time-start,check_seconds:facts.results[0].seconds}));
});

test('60 real runs retain 50 immutable records and 20 completed log sets without pruning an active run', async t => {
  const { f }=setup(t,(c,f)=>{
    c.checks[0].timeout_s=40;
    c.checks[0].run=command(`require('node:fs').writeFileSync(${JSON.stringify(join(f.home,'retention-started'))},"yes"); setTimeout(()=>console.log("finished"),Number(process.env.RETENTION_DELAY ?? 5))`);
  });
  const active=f.start(['--all','--json'],{env:{...f.env,RETENTION_DELAY:'30000'}});
  const deadline=Date.now()+5000;
  while(!existsSync(join(f.home,'retention-started'))&&Date.now()<deadline) await new Promise(resolve=>setTimeout(resolve,20));
  assert.ok(existsSync(join(f.home,'retention-started')));
  let facts;
  let immutable;
  for(let i=0;i<60;i++) {
    facts=json(f);
    if(i===40) immutable={path:facts.storage.record,bytes:readFileSync(facts.storage.record,'utf8')};
  }
  assert.equal(readFileSync(immutable.path,'utf8'),immutable.bytes);
  const records=join(facts.storage.worktree_dir,'records');
  const logs=join(facts.storage.worktree_dir,'logs');
  assert.equal(readdirSync(records).filter(x=>x.endsWith('.json')).length,50);
  assert.equal(readdirSync(logs).length,21);
  assert.equal(active.child.exitCode,null);
  assert.equal(f.git('status','--porcelain'),'');
  const r=await active.done;
  assert.equal(r.status,0,r.stdout+r.stderr);
  const slow=JSON.parse(r.stdout);
  assert.match(readFileSync(slow.results[0].log,'utf8'),/finished/);
  assert.equal(readdirSync(records).filter(x=>x.endsWith('.json')).length,50);
  assert.equal(readdirSync(logs).length,20);
  assert.equal(f.git('status','--porcelain'),'');
  t.diagnostic('61 completed CLI runs; 50 immutable records; 20 log sets; active logs survived pruning; git status empty.');
});

test('selector timeout bounds its process tree and is excluded from selection timing', async t => {
  const { f }=setup(t,(c,f)=>{
    Object.assign(c.checks[0],{
      inputs:[],sources:['src/**'],timeout_s:0.2,
      select:command(`require('node:child_process').spawn(process.execPath,['-e',${JSON.stringify(`setTimeout(()=>require('node:fs').writeFileSync(${JSON.stringify(join(f.home,'selector-escaped'))},"bad"),700)`)}],{stdio:'ignore'}); setTimeout(()=>console.log(JSON.stringify(["test/a.test.mjs"])),1200)`),
    });
  });
  f.git('push','origin','main');
  f.write('src/a.js','changed');
  const facts=json(f,[],2);
  assert.ok(facts.events.some(x=>x.type==='ERROR'&&/selector.*timeout/i.test(x.message)));
  assert.ok(facts.timing.selector_ms>=200);
  assert.equal(facts.results.length,0);
  await new Promise(resolve=>setTimeout(resolve,800));
  assert.equal(existsSync(join(f.home,'selector-escaped')),false);
});

test('stale lock reapers serialize racing CLIs after the recorded holder dies', async t => {
  const { f } = setup(t,(c,f)=>{
    c.checks[0].lock='stale-race';
    c.checks[0].run=command(`const fs=require('node:fs'); fs.writeFileSync(${JSON.stringify(join(f.home,'holder-child'))},JSON.stringify({pid:process.pid,parent:process.ppid})); console.log(JSON.stringify({event:"start",time:Date.now()})); setTimeout(()=>console.log(JSON.stringify({event:"end",time:Date.now()})),450)`);
  });
  const first=f.start(['--all']);
  const pidfile=join(f.home,'holder-child');
  const deadline=Date.now()+5000;
  while(!existsSync(pidfile)&&Date.now()<deadline) await new Promise(resolve=>setTimeout(resolve,20));
  assert.ok(existsSync(pidfile));
  const child=JSON.parse(readFileSync(pidfile,'utf8'));
  const cache=process.platform==='darwin' ? join(f.home,'Library/Caches/repo-checks/locks') : join(f.env.XDG_CACHE_HOME,'repo-checks/locks');
  const canonical=readdirSync(cache).find(name=>!name.startsWith('.'));
  const owner=JSON.parse(readFileSync(join(cache,canonical,readdirSync(join(cache,canonical))[0])));
  assert.equal(typeof owner.start,'string');
  assert.equal(typeof owner.nonce,'string');
  process.kill(owner.pid,'SIGKILL');
  for(const pid of new Set([child.pid,child.parent])) {
    try { process.kill(pid,'SIGKILL'); } catch(error) { if(error.code!=='ESRCH') throw error; }
  }
  assert.equal((await first.done).status,70);
  const racing=Array.from({length:6},()=>f.start(['--all','--json']));
  const results=await Promise.all(racing.map(run=>run.done));
  const events=[];
  for(const r of results) {
    assert.equal(r.status,0,r.stdout+r.stderr);
    const facts=JSON.parse(r.stdout);
    events.push(...readFileSync(facts.results[0].log,'utf8').trim().split('\n').map(JSON.parse));
  }
  events.sort((a,b)=>a.time-b.time);
  let active=0;
  for(const event of events) {
    active+=event.event==='start'?1:-1;
    assert.ok(active>=0&&active<=1,JSON.stringify(events));
  }
  assert.equal(active,0);
  t.diagnostic('Six CLI contenders reclaimed the dead holder token without overlapping commands.');
});

test('same lock name prevents overlap in linked worktrees sharing one common git directory', async t => {
  const { f }=setup(t,c=>{
    c.checks[0].lock='linked-database';
    c.checks[0].run=command('console.log(JSON.stringify({event:"start",time:Date.now()})); setTimeout(()=>console.log(JSON.stringify({event:"end",time:Date.now()})),2000)');
  });
  const linked=join(f.root,'linked');
  f.git('worktree','add','-b','linked-check',linked,'HEAD');
  const cache=process.platform==='darwin' ? join(f.home,'Library/Caches/repo-checks/locks') : join(f.env.XDG_CACHE_HOME,'repo-checks/locks');
  const held=()=>existsSync(cache)&&readdirSync(cache).some(name=>!name.startsWith('.'));
  const a=f.start(['--all','--json']);
  const lockDeadline=Date.now()+10000;
  while(!held()&&Date.now()<lockDeadline) await new Promise(resolve=>setTimeout(resolve,20));
  assert.ok(held(),'holder published its lock before the waiter started');
  const b=f.start(['--all','--json'],{repo:linked});
  await b.until(/WAIT linked-database/,10000);
  const events=[];
  for(const r of await Promise.all([a.done,b.done])) {
    assert.equal(r.status,0,r.stdout+r.stderr);
    const facts=JSON.parse(r.stdout);
    events.push(...readFileSync(facts.results[0].log,'utf8').trim().split('\n').map(JSON.parse));
  }
  events.sort((a,b)=>a.time-b.time);
  assert.deepEqual(events.map(x=>x.event),['start','end','start','end']);
});

test('configuration and engine identity describe the bytes loaded before a delayed fetch', async t => {
  for (const change of ['config', 'engine']) {
    const { f, c } = setup(t, () => {});
    const engine = join(f.home, 'check.mjs');
    copyFileSync(new URL('../check.mjs', import.meta.url), engine);
    copyFileSync(new URL('../checks.schema.json', import.meta.url), join(f.home, 'checks.schema.json'));
    f.write('scripts/check', `#!/bin/sh\nexec ${quote(process.execPath)} ${quote(engine)} "$@"\n`);
    f.commit();
    const uploadpack = join(f.home, 'uploadpack');
    const marker = join(f.home, 'fetch-started');
    appendFileSync(uploadpack, `#!${process.execPath}\nrequire('node:fs').writeFileSync(${JSON.stringify(marker)},"yes"); setTimeout(()=>{const c=require('node:child_process').spawn('git-upload-pack',process.argv.slice(2),{stdio:'inherit'});c.on('exit',code=>process.exit(code))},600);\n`);
    chmodSync(uploadpack, 0o755);
    f.git('config', 'remote.origin.uploadpack', quote(uploadpack));
    const active = f.start(['--all', '--json']);
    const deadline = Date.now() + 5000;
    while (!existsSync(marker) && Date.now() < deadline) await new Promise(resolve => setTimeout(resolve, 20));
    assert.ok(existsSync(marker));
    if (change === 'config') {
      c.inert.push('docs/**');
      f.config(c);
      f.commit();
    } else appendFileSync(engine, '\n');
    const r = await active.done;
    assert.equal(r.status, 0, r.stdout + r.stderr);
    const facts = JSON.parse(r.stdout);
    assert.equal(facts.reuse_eligible, false, change);
    assert.equal(facts.results[0].reusable, false, change);
  }
});

test('a lock waiter whose outer CLI dies removes its unpublished token directory', async t => {
  const { f } = setup(t, c => {
    c.checks[0].lock = 'cancel-waiter';
    c.checks[0].run = command('setTimeout(()=>{},1200)');
  });
  const first = f.start(['--all']);
  await first.until(/SELECT/);
  await new Promise(resolve => setTimeout(resolve, 200));
  const waiter = f.start(['--all']);
  await waiter.until(/WAIT cancel-waiter/);
  waiter.child.kill('SIGKILL');
  await waiter.done;
  const cache = process.platform === 'darwin' ? join(f.home, 'Library/Caches/repo-checks/locks') : join(f.env.XDG_CACHE_HOME, 'repo-checks/locks');
  const deadline = Date.now() + 600;
  while (readdirSync(cache).some(name => name.startsWith('.')) && Date.now() < deadline) await new Promise(resolve => setTimeout(resolve, 20));
  assert.deepEqual(readdirSync(cache).filter(name => name.startsWith('.')), []);
  assert.equal((await first.done).status, 0);
});
