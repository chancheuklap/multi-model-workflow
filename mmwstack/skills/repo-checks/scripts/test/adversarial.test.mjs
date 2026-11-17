import assert from 'node:assert/strict';
import test from 'node:test';
import { copyFileSync, existsSync, readFileSync, readdirSync, realpathSync, rmdirSync, symlinkSync, unlinkSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { cleanConfig, fixture } from './fixture.mjs';

const quote = value => `'${value.replaceAll("'", "'\\''")}'`;
const command = source => `${quote(process.execPath)} -e ${quote(source)}`;
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(predicate, timeout = 6000) {
  const deadline = Date.now() + timeout;
  while (!predicate()) {
    assert.ok(Date.now() < deadline, 'Observable fixture condition timed out');
    await pause(20);
  }
}
function setup(t, configure) {
  const f = fixture(t);
  const c = cleanConfig();
  c.checks[0].run = command('console.log("checked")');
  configure(c, f);
  f.config(c);
  f.commit('Configure adversarial regression');
  return { f, c };
}
function facts(result, status = 0) {
  assert.equal(result.status, status, result.stdout + result.stderr);
  const value = JSON.parse(result.stdout);
  assert.equal(value.exit_code, status);
  return value;
}
function lockRecord(f) {
  const cache = process.platform === 'darwin'
    ? join(f.home, 'Library/Caches/repo-checks/locks')
    : join(f.env.XDG_CACHE_HOME, 'repo-checks/locks');
  for (const name of readdirSync(cache).filter(name => !name.startsWith('.'))) {
    const directory = join(cache, name);
    for (const token of readdirSync(directory)) return { directory, path: join(directory, token), owner: JSON.parse(readFileSync(join(directory, token))) };
  }
  throw new Error('No published resource lease');
}
const lockOwner = f => lockRecord(f).owner;

test('I1 gitlink changes and dirty submodules cannot be hidden by git configuration', t => {
  const { f } = setup(t, (c, f) => {
    c.inert.push('.gitmodules');
    c.checks[0].inputs = ['vendor/**'];
    f.git('-c', 'protocol.file.allow=always', 'submodule', 'add', join(f.root, 'origin.git'), 'vendor/lib');
  });
  f.git('push', 'origin', 'main');
  f.git('-C', 'vendor/lib', 'fetch', 'origin', 'main');
  f.git('-C', 'vendor/lib', 'checkout', 'FETCH_HEAD');
  f.commit('Advance tracked gitlink');
  f.git('config', 'diff.ignoreSubmodules', 'all');
  f.git('config', 'submodule.vendor/lib.ignore', 'all');
  const selected = facts(f.cli('--json'));
  assert.deepEqual(selected.selection.map(x => x.check.id), ['unit']);
  assert.equal(facts(f.cli('--all', '--json')).results[0].reused, true);
  f.write('vendor/lib/README.md', 'Dirty tracked submodule bytes.\n');
  const dirty = facts(f.cli('--json'));
  assert.equal(dirty.identity.dirty, true);
  assert.equal(dirty.identity_after.dirty, true);
  assert.equal(dirty.results[0].reused, false);
});

for (const kind of ['owner-only', 'device']) test(`I2 protected ${kind} selector is rejected before execution`, t => {
  const { f } = setup(t, (c, f) => {
    const run = command(`require('node:fs').writeFileSync(${JSON.stringify(join(f.home, 'protected-ran'))},"bad");console.log("[]")`);
    Object.assign(c.checks[0], { inputs: [], sources: ['src/**'], select: run });
    c.lanes = [{ id: 'protected', kind, reason: 'Requires the owner.', run_by: 'owner', tests: [], command: run }];
  });
  f.git('push', 'origin', 'main');
  f.write('src/a.js', 'Changed source.');
  const lint = facts(f.cli('lint', '--json'), 1);
  assert.ok(lint.findings.some(x => x.rule === 'protected-command' && x.field.endsWith('.select')));
  facts(f.cli('--json'), 2);
  assert.equal(existsSync(join(f.home, 'protected-ran')), false);
});

for (const [path, section] of [['setup.cfg', 'tool:pytest'], ['tox.ini', 'pytest']]) {
  test(`I3 pytest norecursedirs in ${path} is an exclusion context`, t => {
    const { f } = setup(t, (c, f) => {
      c.inert.push(path);
      f.write(path, `[${section}]\nnorecursedirs =\n    build\n    .worktrees/\n`);
    });
    const lint = facts(f.cli('lint', '--json'), 1);
    assert.ok(lint.findings.some(x => x.path === path && x.marker === '.worktrees/'));
    f.write(path, '[metadata]\nproject_path = .worktrees/\n');
    facts(f.cli('lint', '--json'));
  });
}

for (const id of ['unit,build', '-unit']) test(`I4 schema rejects unaddressable check id ${id}`, t => {
  const { f } = setup(t, c => { c.checks[0].id = id; });
  assert.ok(facts(f.cli('lint', '--json'), 1).findings.some(x => x.field === 'checks[0].id'));
  facts(f.cli('--all', '--json'), 2);
});

test('I5 coordinator death preserves the lease through surviving workload lifetime', async t => {
  const eventsPath = f => join(f.home, 'resource-events');
  const { f } = setup(t, (c, f) => {
    c.checks[0].lock = 'coordinator-death';
    c.checks[0].run = command(`const fs=require('node:fs');const event=e=>fs.appendFileSync(${JSON.stringify(eventsPath(f))},JSON.stringify({e,label:process.env.LABEL,time:Date.now(),pid:process.pid})+"\\n");event("start");setTimeout(()=>event("end"),process.env.LABEL==="A"?1500:50)`);
  });
  const linked = join(f.root, 'linked');
  f.git('worktree', 'add', '-b', 'lease-regression', linked, 'HEAD');
  const a = f.start(['--all', '--json'], { env: { ...f.env, LABEL: 'A' } });
  await until(() => existsSync(eventsPath(f)));
  const owner = lockOwner(f);
  process.kill(owner.pid, 'SIGKILL');
  const b = f.start(['--all', '--json'], { repo: linked, env: { ...f.env, LABEL: 'B' } });
  const [ar, br] = await Promise.all([a.done, b.done]);
  facts(ar, 70);
  facts(br);
  const events = readFileSync(eventsPath(f), 'utf8').trim().split('\n').map(JSON.parse);
  assert.deepEqual(events.map(x => `${x.label}-${x.e}`), ['A-start', 'A-end', 'B-start', 'B-end']);
  assert.ok(owner.workload?.token, 'Workload ownership must be published before the workload starts');
});

test('I5 a stale lease observation cannot delete a newly published retry workload', async t => {
  const { f } = setup(t, (c, f) => {
    c.checks[0].lock = 'retry-handoff';
    c.checks[0].retry = 1;
    c.checks[0].run = command(`const fs=require('node:fs'),p=${JSON.stringify(join(f.home, 'attempt'))};const label=process.env.LABEL;const n=label==="B"?0:(fs.existsSync(p)?Number(fs.readFileSync(p)):0)+1;if(n)fs.writeFileSync(p,String(n));fs.appendFileSync(${JSON.stringify(join(f.home, 'retry-events'))},label+n+"-start\\n");setTimeout(()=>{fs.appendFileSync(${JSON.stringify(join(f.home, 'retry-events'))},label+n+"-end\\n");process.exit(n===1?1:0)},n===2?1500:400)`);
  });
  const linked = join(f.root, 'linked');
  f.git('worktree', 'add', '-b', 'retry-handoff', linked, 'HEAD');
  const first = f.start(['--all', '--json'], { env: { ...f.env, LABEL: 'A' } });
  const events = () => readFileSync(join(f.home, 'retry-events'), 'utf8');
  await until(() => existsSync(join(f.home, 'attempt')));
  const observed = lockRecord(f);
  await until(() => events().includes('A2-start'));
  process.kill(observed.owner.pid, 'SIGKILL');
  try { unlinkSync(observed.path); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  try { rmdirSync(observed.directory); } catch (error) { if (!['ENOENT', 'ENOTEMPTY', 'EEXIST'].includes(error.code)) throw error; }
  const second = f.start(['--all', '--json'], { repo: linked, env: { ...f.env, LABEL: 'B' } });
  const [ar, br] = await Promise.all([first.done, second.done]);
  facts(ar, 70);
  facts(br);
  assert.ok(events().indexOf('A2-end') < events().indexOf('B0-start'), events());
});

for (const timeout of [false, true]) test(`I6 detached descendants cannot outlive ${timeout ? 'timeout' : 'PASS'} and overlap a linked worktree`, async t => {
  const { f } = setup(t, (c, f) => {
    const ready = join(f.home, 'detached-ready');
    c.checks[0].lock = 'detached-lifetime';
    c.checks[0].timeout_s = timeout ? 0.35 : 8;
    c.checks[0].run = command(`
      const fs=require('node:fs');
      if(process.env.LABEL==="B") fs.writeFileSync(${JSON.stringify(join(f.home, 'B-start'))},String(Date.now()));
      else {
        require('node:child_process').spawn(process.execPath,['-e',${JSON.stringify(`const fs=require('node:fs');fs.writeFileSync(${JSON.stringify(ready)},String(process.pid));setTimeout(()=>fs.writeFileSync(${JSON.stringify(join(f.home, 'escaped'))},String(Date.now())),1000)`)}],{detached:true,stdio:'ignore'}).unref();
        const timer=setInterval(()=>{if(fs.existsSync(${JSON.stringify(ready)})){clearInterval(timer);${timeout ? 'setTimeout(()=>{},10000)' : ''}}},10);
      }`);
  });
  const linked = join(f.root, 'linked');
  f.git('worktree', 'add', '-b', 'detached-regression', linked, 'HEAD');
  const a = facts(await f.start(['--all', '--json'], { env: { ...f.env, LABEL: 'A' } }).done, timeout ? 1 : 0);
  assert.equal(a.results[0].reason, timeout ? 'timeout' : null);
  facts(await f.start(['--all', '--json'], { repo: linked, env: { ...f.env, LABEL: 'B' } }).done);
  await pause(1150);
  assert.equal(existsSync(join(f.home, 'escaped')), false, 'Detached workload must terminate before resource release');
});

for (const failure of ['supervisor-death', 'log-disappearance']) test(`I7 ${failure} preserves all terminal outcomes and writes one final record`, async t => {
  const { f } = setup(t, (c, f) => {
    const base = c.checks[0];
    c.checks = [
      { ...base, id: 'passed', run: command('console.log("early pass")') },
      { ...base, id: 'failed', run: command('console.log("early fail");process.exit(7)') },
      { ...base, id: 'internal', lock: 'mixed-error', run: command(`const fs=require('node:fs');fs.writeFileSync(${JSON.stringify(join(f.home, 'internal-ready'))},"yes");console.log("DELETE ME");setTimeout(()=>{${failure === 'log-disappearance' ? `const path=require('node:path');const root=".git/repo-checks";for(const wt of fs.readdirSync(root))for(const set of fs.readdirSync(path.join(root,wt,"logs")))for(const file of fs.readdirSync(path.join(root,wt,"logs",set))){const p=path.join(root,wt,"logs",set,file);if(file.endsWith(".log")&&fs.readFileSync(p,"utf8").includes("DELETE ME"))fs.unlinkSync(p)}` : ''}},450)`) },
      { ...base, id: 'later', run: command(`setTimeout(()=>{require('node:fs').writeFileSync(${JSON.stringify(join(f.home, 'later-ended'))},"yes");console.log("later passed")},1000)`) },
    ];
  });
  const active = f.start(['--all', '--json']);
  await until(() => existsSync(join(f.home, 'internal-ready')));
  if (failure === 'supervisor-death') process.kill(lockOwner(f).pid, 'SIGKILL');
  const value = facts(await active.done, 70);
  assert.ok(existsSync(join(f.home, 'later-ended')), 'Final JSON must follow the last sibling terminal outcome');
  assert.deepEqual(value.results.map(x => [x.id, x.status]), [
    ['passed', 'passed'], ['failed', 'failed'], ['internal', 'internal-error'], ['later', 'passed'],
  ]);
  assert.equal(value.summary.selected, 4);
  assert.equal(value.summary.passed, 2);
  assert.equal(value.summary.failed, 1);
  assert.equal(value.summary['internal-error'], 1);
  assert.ok(existsSync(value.storage.record));
  assert.deepEqual(JSON.parse(readFileSync(value.storage.record)), value);
  assert.match(readFileSync(value.results[3].log, 'utf8'), /later passed/);
});

test('I8 symlink stamp hashes consumed bytes and cannot reuse stale dependencies', t => {
  const { f } = setup(t, (c, f) => {
    f.write('.gitignore', 'installed\nreal-lock\n');
    f.write('real-lock', 'old\n');
    symlinkSync('real-lock', join(f.repo, 'package-lock.json'));
    c.prepare = { stamps: ['package-lock.json'], run: command('const fs=require("node:fs");fs.writeFileSync("installed",fs.readFileSync("package-lock.json"))') };
    c.checks[0].needs = ['path:installed'];
    c.checks[0].run = command('const fs=require("node:fs");if(fs.readFileSync("installed","utf8")!==fs.readFileSync("package-lock.json","utf8"))process.exit(1)');
  });
  facts(f.cli('--all', '--json'));
  f.write('real-lock', 'new\n');
  const next = facts(f.cli('--all', '--json'));
  assert.equal(next.preparation.prepared, true);
  assert.equal(next.results[0].reused, false);
  assert.equal(readFileSync(join(f.repo, 'installed'), 'utf8'), 'new\n');
});

test('I9 preparation never certifies a stamp changed while installation consumed old bytes', async t => {
  const { f } = setup(t, (c, f) => {
    f.write('.gitignore', 'installed\n');
    f.write('package-lock.json', 'old\n');
    c.prepare = { stamps: ['package-lock.json'], run: command(`const fs=require('node:fs');fs.writeFileSync("installed",fs.readFileSync("package-lock.json"));fs.writeFileSync(${JSON.stringify(join(f.home, 'prepared'))},"yes");setTimeout(()=>{},450)`) };
    c.checks[0].needs = ['path:installed'];
    c.checks[0].run = command('const fs=require("node:fs");if(fs.readFileSync("installed","utf8")!==fs.readFileSync("package-lock.json","utf8"))process.exit(1)');
  });
  const first = f.start(['--all', '--json']);
  await until(() => existsSync(join(f.home, 'prepared')));
  f.write('package-lock.json', 'new\n');
  const prior = await first.done;
  assert.ok([1, 2].includes(prior.status), prior.stdout + prior.stderr);
  const repaired = facts(f.cli('--all', '--json'));
  assert.equal(repaired.preparation.prepared, true);
  assert.equal(readFileSync(join(f.repo, 'installed'), 'utf8'), 'new\n');
});

test('I10 disappearance of the loaded engine produces JSON exit 70', t => {
  const f = fixture(t);
  const engine = join(f.home, 'check.mjs');
  copyFileSync(new URL('../check.mjs', import.meta.url), engine);
  copyFileSync(new URL('../checks.schema.json', import.meta.url), join(f.home, 'checks.schema.json'));
  const hook = join(f.home, 'delete-engine.mjs');
  f.write('../home/delete-engine.mjs', `import {registerHooks} from 'node:module';import {unlinkSync} from 'node:fs';registerHooks({load(url,context,next){const result=next(url,context);if(url===${JSON.stringify(pathToFileURL(realpathSync(engine)).href)})unlinkSync(new URL(url));return result;}});\n`);
  f.write('scripts/check', `#!/bin/sh\nexec ${quote(process.execPath)} --import ${quote(hook)} ${quote(engine)} "$@"\n`);
  const value = facts(f.cli('--all', '--json'), 70);
  assert.ok(value.events.some(x => x.type === 'ERROR' && /ENOENT/.test(x.message)));
});

for (const failure of ['uncaughtException', 'unhandledRejection']) for (const delay of [100, 1500]) {
  test(`I10 asynchronous ${failure} at ${delay}ms preserves sibling completion and emits JSON 70`, t => {
    const { f } = setup(t, c => { c.checks[0].run = command('setTimeout(()=>console.log("completed"),350)'); });
    const hook = join(f.home, 'async-failure.mjs');
    f.write('../home/async-failure.mjs', `if(process.argv.includes('--json'))setTimeout(()=>{${failure === 'uncaughtException' ? 'throw new Error("async engine failure")' : 'Promise.reject(new Error("async engine failure"))'}},${delay});\n`);
    f.write('scripts/check', `#!/bin/sh\nexec ${quote(process.execPath)} --import ${quote(hook)} ${quote(new URL('../check.mjs', import.meta.url).pathname)} "$@"\n`);
    const value = facts(f.cli('--all', '--json'), 70);
    assert.equal(value.summary.selected, 1);
    assert.equal(value.summary.passed, 1);
    assert.ok(value.events.some(x => x.type === 'ERROR' && x.message === 'async engine failure'));
    assert.match(readFileSync(value.results[0].log, 'utf8'), /completed/);
    assert.deepEqual(JSON.parse(readFileSync(value.storage.record)), value);
  });
}
