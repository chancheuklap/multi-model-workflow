import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import { cleanConfig, fixture } from './fixture.mjs';

const quote = value => `'${value.replaceAll("'", "'\\''")}'`;
const command = source => `${quote(process.execPath)} -e ${quote(source)}`;

function setup(t, configure = () => {}) {
  const f = fixture(t);
  const c = cleanConfig();
  c.test_files = ['tests/**/*.py', 'tests/**/*.test.mjs'];
  c.inert.push('.gitignore');
  configure(c, f);
  f.config(c);
  f.commit('Configure manifest and deferral fixture');
  f.git('push', 'origin', 'main');
  return { f, c };
}

function runJson(f, args = [], status = 0) {
  const r = f.cli(...args, '--json');
  assert.equal(r.status, status, r.stdout + r.stderr);
  assert.equal(r.stderr, '');
  const facts = JSON.parse(r.stdout);
  assert.equal(facts.exit_code, status);
  return facts;
}

function parseManifest(text) {
  return text.split('\n').filter(line => line.trim()).map(line => {
    const parts = line.trim().split(/\s+/);
    assert.equal(parts.length, 2, `Expected two columns in manifest line: ${JSON.stringify(line)}`);
    return parts;
  });
}

test('MMW_REPO_CHECKS_SELECTION_MANIFEST expands whole globs, keeps narrowed selector tests, and omits unselected checks', t => {
  const { f } = setup(t, (c, f) => {
    f.write('.gitignore', 'tests/alpha/test_ignored.py\n');
    f.write('tests/alpha/test_one.py', '# one\n');
    f.write('tests/alpha/sub/test_two.py', '# two\n');
    f.write('tests/alpha/test_ignored.py', '# ignored\n');
    f.write('tests/alpha/helper.txt', 'not a test\n');
    f.write('tests/beta/test_sel.py', '# selected\n');
    f.write('tests/beta/test_other.py', '# not selected\n');
    f.write('tests/gamma/test_unselected.py', '# unselected\n');
    c.inert.push('tests/alpha/helper.txt');
    c.checks = [
      {
        id: 'alpha',
        run: command('console.log("alpha ran")'),
        inputs: ['src/alpha/**', 'tests/alpha/**'],
        tests: ['tests/alpha/**/test_*.py'],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
      {
        id: 'beta',
        run: `${command('console.log("beta ran")')} -- {tests}`,
        run_all: command('console.log("beta all")'),
        inputs: ['tests/beta/**'],
        sources: ['src/beta/**'],
        select: command('console.log(JSON.stringify(["tests/beta/test_sel.py"]))'),
        tests: ['tests/beta/**/*.py'],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
      {
        id: 'gamma',
        run: command('console.log("gamma ran")'),
        inputs: ['src/gamma/**', 'tests/gamma/**'],
        tests: ['tests/gamma/**/*.py'],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
      {
        id: 'consumer',
        run: command('const fs=require("node:fs");const p=process.env.MMW_REPO_CHECKS_SELECTION_MANIFEST;console.log(JSON.stringify({path:p??null,body:p?fs.readFileSync(p,"utf8"):null}))'),
        inputs: ['src/consumer/**'],
        tests: [],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
    ];
  });
  f.write('src/alpha/a.js', 'changed\n');
  f.write('src/beta/b.js', 'changed\n');
  f.write('src/consumer/c.js', 'changed\n');
  const facts = runJson(f);
  const consumer = facts.results.find(item => item.id === 'consumer');
  const observed = JSON.parse(readFileSync(consumer.log, 'utf8'));
  assert.ok(observed.path, 'MMW_REPO_CHECKS_SELECTION_MANIFEST must be set');
  assert.deepEqual(parseManifest(observed.body), [
    ['alpha', 'tests/alpha/sub/test_two.py'],
    ['alpha', 'tests/alpha/test_one.py'],
    ['beta', 'tests/beta/test_sel.py'],
  ]);
});

test('MMW_REPO_CHECKS_SELECTION_MANIFEST includes clean reused siblings and excludes pre-run skipped checks', t => {
  const { f } = setup(t, (c, f) => {
    c.ci_workflow = 'gate.yml';
    f.write('tests/clean/test_a.py', '# clean\n');
    f.write('tests/skipped/test_b.py', '# skipped\n');
    c.checks = [
      {
        id: 'clean',
        run: command('console.log("clean ran")'),
        inputs: ['src/clean/**', 'tests/clean/**'],
        tests: ['tests/clean/**/*.py'],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
      {
        id: 'skipped',
        run: command('console.log("skipped ran")'),
        inputs: ['src/skipped/**', 'tests/skipped/**'],
        tests: ['tests/skipped/**/*.py'],
        needs: ['env:MMW_TEST_MISSING_PREREQ'],
        ci: true,
        ci_run: 'pytest tests/skipped',
      },
      {
        id: 'consumer',
        run: command('const fs=require("node:fs");console.log(fs.readFileSync(process.env.MMW_REPO_CHECKS_SELECTION_MANIFEST,"utf8"))'),
        inputs: ['src/consumer/**'],
        tests: [],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
    ];
  });
  delete f.env.MMW_TEST_MISSING_PREREQ;
  const seed = runJson(f, ['--all', '--only', 'clean']);
  assert.equal(seed.results[0].status, 'passed');
  assert.equal(seed.results[0].reusable, true);

  const facts = runJson(f, ['--all']);
  const cleanResult = facts.results.find(item => item.id === 'clean');
  const skippedResult = facts.results.find(item => item.id === 'skipped');
  const consumerResult = facts.results.find(item => item.id === 'consumer');
  assert.equal(cleanResult.status, 'passed');
  assert.equal(cleanResult.reused, true);
  assert.equal(skippedResult.status, 'skipped');
  const manifest = readFileSync(consumerResult.log, 'utf8');
  assert.deepEqual(parseManifest(manifest), [
    ['clean', 'tests/clean/test_a.py'],
  ]);
});

test('MMW_REPO_CHECKS_DEFERRED_MARKER is unlinked before retry attempts so a clean recovery stays reusable', t => {
  const { f } = setup(t, (c, f) => {
    const counter = `${f.home}/flaky-attempts`;
    c.checks = [
      {
        id: 'flaky',
        retry: 1,
        run: command(`
          const fs = require('node:fs');
          const marker = process.env.MMW_REPO_CHECKS_DEFERRED_MARKER;
          if (!marker) process.exit(2);
          const countPath = ${JSON.stringify(counter)};
          const attempt = (fs.existsSync(countPath) ? Number(fs.readFileSync(countPath, 'utf8')) : 0) + 1;
          fs.writeFileSync(countPath, String(attempt));
          if (attempt === 1) {
            fs.writeFileSync(marker, 'deferred-on-failed-attempt');
            process.exit(1);
          }
          if (fs.existsSync(marker)) {
            console.error('stale deferred marker survived retry cleanup');
            process.exit(3);
          }
          console.log('clean recovery');
        `),
        inputs: ['src/flaky/**'],
        tests: [],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
    ];
  });
  const facts = runJson(f, ['--all']);
  assert.equal(facts.results[0].status, 'passed');
  assert.equal(facts.results[0].recovered, true);
  assert.equal(facts.results[0].reusable, true);
  const rerun = runJson(f, ['--all']);
  assert.equal(rerun.results[0].reused, true);
});

test('deferred pass on retry persists reusable false and cannot be reused', t => {
  const { f } = setup(t, (c, f) => {
    const counter = `${f.home}/deferred-retry-attempts`;
    c.checks = [
      {
        id: 'flaky',
        retry: 1,
        run: command(`
          const fs = require('node:fs');
          const countPath = ${JSON.stringify(counter)};
          const attempt = (fs.existsSync(countPath) ? Number(fs.readFileSync(countPath, 'utf8')) : 0) + 1;
          fs.writeFileSync(countPath, String(attempt));
          if (attempt === 1) process.exit(1);
          fs.writeFileSync(process.env.MMW_REPO_CHECKS_DEFERRED_MARKER, 'deferred-on-retry');
          console.log('deferred recovery');
        `),
        inputs: ['src/flaky/**'],
        tests: [],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
    ];
  });
  const first = runJson(f, ['--all']);
  assert.equal(first.results[0].status, 'passed');
  assert.equal(first.results[0].recovered, true);
  assert.equal(first.results[0].reusable, false);
  const saved = JSON.parse(readFileSync(first.storage.record, 'utf8'));
  assert.equal(saved.results[0].reusable, false);
  const second = runJson(f, ['--all']);
  assert.equal(second.results[0].reused, false);
});

test('deferred pass while sibling fails persists reusable false and forces re-execution on follow-up --only', t => {
  const { f } = setup(t, (c, f) => {
    const runs = `${f.home}/deferred-runs`;
    f.write('tests/deferred/test_d.py', '# deferred\n');
    f.write('tests/sibling/test_s.py', '# sibling\n');
    c.checks = [
      {
        id: 'deferred',
        run: command(`
          const fs = require('node:fs');
          const countPath = ${JSON.stringify(runs)};
          const count = (fs.existsSync(countPath) ? Number(fs.readFileSync(countPath, 'utf8')) : 0) + 1;
          fs.writeFileSync(countPath, String(count));
          const manifest = fs.readFileSync(process.env.MMW_REPO_CHECKS_SELECTION_MANIFEST, 'utf8');
          const hasSibling = manifest.split('\\n').some(line => line.startsWith('sibling '));
          if (hasSibling) {
            fs.writeFileSync(process.env.MMW_REPO_CHECKS_DEFERRED_MARKER, 'deferred-to-sibling');
            console.log('deferred run ' + count);
          } else {
            console.log('full run ' + count);
          }
        `),
        inputs: ['src/deferred/**', 'tests/deferred/**'],
        tests: ['tests/deferred/**/*.py'],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
      {
        id: 'sibling',
        run: command('console.error("sibling failed"); process.exit(1)'),
        inputs: ['src/sibling/**', 'tests/sibling/**'],
        tests: ['tests/sibling/**/*.py'],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
      {
        id: 'observer',
        run: command('const fs=require("node:fs");console.log(fs.readFileSync(process.env.MMW_REPO_CHECKS_SELECTION_MANIFEST,"utf8"))'),
        inputs: ['src/observer/**'],
        tests: [],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
    ];
  });

  const failedPush = runJson(f, ['--only', 'deferred,sibling', '--all'], 1);
  const deferredInPush = failedPush.results.find(item => item.id === 'deferred');
  const siblingInPush = failedPush.results.find(item => item.id === 'sibling');
  assert.equal(deferredInPush.status, 'passed');
  assert.equal(deferredInPush.reusable, false);
  assert.equal(siblingInPush.status, 'failed');
  const saved = JSON.parse(readFileSync(failedPush.storage.record, 'utf8'));
  assert.equal(saved.results.find(item => item.id === 'deferred').reusable, false);

  const retryAll = runJson(f, ['--only', 'deferred,sibling', '--all'], 1);
  assert.equal(retryAll.results.find(item => item.id === 'deferred').reused, false);
  assert.equal(retryAll.results.find(item => item.id === 'deferred').reusable, false);

  const text = f.cli('--only', 'deferred', '--all');
  assert.equal(text.status, 0, text.stdout + text.stderr);
  assert.doesNotMatch(text.stdout, /\(reused\)/);
  assert.match(text.stdout, /PASS deferred [\d.]+s\n/);

  const observedAfterClean = runJson(f, ['--only', 'deferred,observer', '--all']);
  const deferredCached = observedAfterClean.results.find(item => item.id === 'deferred');
  const observerResult = observedAfterClean.results.find(item => item.id === 'observer');
  assert.equal(deferredCached.reused, true);
  assert.match(readFileSync(deferredCached.log, 'utf8'), /^full run 3\n$/);
  assert.deepEqual(parseManifest(readFileSync(observerResult.log, 'utf8')), [
    ['deferred', 'tests/deferred/test_d.py'],
  ]);
});

test('deferred pass while sibling blocks persists reusable false and re-executes on follow-up --only', async t => {
  const lockName = `manifest-block-${Date.now()}-${process.pid}`;
  const blocker = setup(t, (c, f) => {
    c.checks = [
      {
        id: 'holder',
        lock: lockName,
        timeout_s: 30,
        run: command(`
          const fs = require('node:fs');
          fs.writeFileSync(${JSON.stringify(join(f.home, 'lock-held'))}, '1');
          const timer = setInterval(() => {
            if (fs.existsSync(${JSON.stringify(join(f.home, 'release-lock'))})) clearInterval(timer);
          }, 20);
        `),
        inputs: ['src/holder/**'],
        tests: [],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
    ];
  }).f;

  const { f } = setup(t, (c, f) => {
    f.write('tests/sibling/test_s.py', '# sibling\n');
    c.checks = [
      {
        id: 'deferred',
        run: command(`
          const fs = require('node:fs');
          const manifest = fs.readFileSync(process.env.MMW_REPO_CHECKS_SELECTION_MANIFEST, 'utf8');
          if (manifest.split('\\n').some(line => line.startsWith('sibling '))) {
            fs.writeFileSync(process.env.MMW_REPO_CHECKS_DEFERRED_MARKER, 'deferred-to-blocked-sibling');
            console.log('deferred while sibling blocked');
          } else {
            console.log('full after unblock');
          }
        `),
        inputs: ['src/deferred/**'],
        tests: [],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
      {
        id: 'sibling',
        lock: lockName,
        timeout_s: 0.25,
        run: command('console.log("sibling ran")'),
        inputs: ['src/sibling/**', 'tests/sibling/**'],
        tests: ['tests/sibling/**/*.py'],
        ci: false,
        ci_reason: 'Local fixture check.',
      },
    ];
  });

  const holdRun = blocker.start(['--all']);
  const heldFlag = join(blocker.home, 'lock-held');
  const deadline = Date.now() + 10_000;
  while (!existsSync(heldFlag) && Date.now() < deadline) await new Promise(resolve => setTimeout(resolve, 20));
  assert.ok(existsSync(heldFlag), 'Blocker must hold the shared lock');

  try {
    const blocked = await f.start(['--all', '--json'], {
      env: { ...f.env, HOME: blocker.home, XDG_CACHE_HOME: blocker.env.XDG_CACHE_HOME },
    }).done;
    assert.equal(blocked.status, 2, blocked.stdout + blocked.stderr);
    const facts = JSON.parse(blocked.stdout);
    assert.equal(facts.results.find(item => item.id === 'deferred').status, 'passed');
    assert.equal(facts.results.find(item => item.id === 'deferred').reusable, false);
    assert.equal(facts.results.find(item => item.id === 'sibling').status, 'blocked');
    const saved = JSON.parse(readFileSync(facts.storage.record, 'utf8'));
    assert.equal(saved.results.find(item => item.id === 'deferred').reusable, false);
  } finally {
    writeFileSync(join(blocker.home, 'release-lock'), '1');
  }
  assert.equal((await holdRun.done).status, 0);

  const followUp = f.cli('--only', 'deferred', '--all');
  assert.equal(followUp.status, 0, followUp.stdout + followUp.stderr);
  assert.doesNotMatch(followUp.stdout, /\(reused\)/);
  const followUpJson = runJson(f, ['--only', 'deferred', '--all']);
  assert.equal(followUpJson.results[0].reused, true);
  assert.match(readFileSync(followUpJson.results[0].log, 'utf8'), /^full after unblock\n$/);
});
